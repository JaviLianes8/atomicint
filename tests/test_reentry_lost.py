"""No update a finalizer makes in the middle of an operation is lost, whatever the operation.

On CPython 3.10 and 3.11 the cyclic collector starts inside the allocation of an object it
tracks, and runs finalizers there. So a locked step that created such an object (a set, a
list) could let a finalizer add to the counter between the read and the store, and the
store would then wipe that add out. Low collector thresholds make collections start at
every few allocations, at each offset from the locked steps. Each case runs in a fresh
interpreter, so a hang fails the test instead of the run.
"""

from __future__ import annotations

import pytest

from .test_reentry import WATCHDOG, _run

LOST = """
import faulthandler, gc
from atomicint import AtomicInt, BoundedAtomicInt
faulthandler.dump_traceback_later({watchdog}, exit=True)
finalized = AtomicInt()

def counters():
    yield AtomicInt()
    for policy in ("raise", "saturate", "wrap"):
        yield BoundedAtomicInt(0, minimum=-10**9, maximum=10**9, overflow=policy)

def won(c, op):
    # One operation; returns what it adds to the total on its own.
    if op == "get_and_set":
        return c.get_and_set(0)  # the old value moves out of the counter into the total
    v = c.get()
    if op == "compare_and_set":
        return int(c.compare_and_set(v, v + 1))
    if op == "compare_and_exchange":
        return int(c.compare_and_exchange(v, v + 1) == v)
    getattr(c, op)((lambda v: v + 1) if op.endswith("update") else 1)
    return 1

results = []
for c in counters():
    class Node:
        def __init__(self):
            self.me = self  # a cycle, so only the cyclic collector frees it

        def __del__(self, c=c):
            c.add(1)
            finalized.increment()

    before, mine = finalized.get(), 0
    for threshold in (1, 2, 3, 4, 5, 7, 10):
        gc.set_threshold(threshold)
        for _ in range(10_000):
            Node()
            mine += won(c, {op!r})
    gc.collect()
    gc.set_threshold(700)
    adds = finalized.get() - before
    total = c.get() if {op!r} != "get_and_set" else c.get() + mine
    want = adds + (mine if {op!r} != "get_and_set" else 0)
    results.append((adds > 0, total == want))
print(results)
"""

OPERATIONS = [
    "get_and_set",
    "compare_and_set",
    "compare_and_exchange",
    "update",
    "get_and_update",
    "add",
    "get_and_add",
]


@pytest.mark.parametrize("op", OPERATIONS)
def test_no_update_from_a_finalizer_is_lost_during_any_operation(op: str) -> None:
    # Every counter (plain, and bounded under each policy) saw finalizers and lost nothing.
    assert _run(LOST.format(watchdog=WATCHDOG, op=op)) == str([(True, True)] * 4)
