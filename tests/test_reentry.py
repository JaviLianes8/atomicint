"""A counter used again from the same thread mid-operation: finalizers and signal handlers.

CPython may run a garbage collector finalizer (``__del__``, a weakref callback) or a
signal handler between any two steps of an operation, in the thread that is running it.
If that code uses the same counter, the operation must neither hang nor lose an update.
Each case runs in a fresh interpreter, so a hang fails the test instead of the run.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
WATCHDOG = 60

FINALIZER = """
import copy, faulthandler, gc, pickle, sys
from atomicint import AtomicInt, BoundedAtomicInt
faulthandler.dump_traceback_later({watchdog}, exit=True)
c = AtomicInt()
if {bounded}:
    c = BoundedAtomicInt(0, minimum=-10**9, maximum=10**9, overflow={policy!r})
touches = AtomicInt()

class Node:
    def __init__(self):
        self.me = self  # a cycle, so only the cyclic collector frees it, at any step

    def __del__(self):
        c.add(1)
        touches.increment()

def outside():
    try:
        c.set(-10**10)
    except OverflowError:
        pass

calls = {{
    "get": c.get, "add": lambda: c.add(-1), "get_and_add": lambda: c.get_and_add(-1),
    "set": lambda: c.set(5), "get_and_set": lambda: c.get_and_set(5),
    "compare_and_set": lambda: c.compare_and_set(c.get(), 3),
    "compare_and_exchange": lambda: c.compare_and_exchange(c.get(), 3),
    "update": lambda: c.update(lambda v: v - 1), "get_and_update": lambda: c.get_and_update(abs),
    "int": lambda: int(c), "repr": lambda: repr(c), "copy": lambda: copy.copy(c),
    "pickle": lambda: pickle.dumps(c), "outside": outside,
}}
gc.set_threshold(1)
for _ in range(20_000):
    Node()
    calls[{op!r}]()
gc.collect()
print(touches.get() > 0)
"""

OPERATIONS = [
    "get",
    "add",
    "get_and_add",
    "set",
    "get_and_set",
    "compare_and_set",
    "compare_and_exchange",
    "update",
    "get_and_update",
    "int",
    "repr",
    "copy",
    "pickle",
]


def _run(program: str) -> str:
    env = dict(os.environ, PYTHONPATH=SRC)
    done = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=WATCHDOG * 2,
    )
    assert done.returncode == 0, done.stderr[-3000:]
    return done.stdout.strip()


@pytest.mark.parametrize("op", OPERATIONS)
def test_a_finalizer_may_use_the_counter_during_any_operation(op: str) -> None:
    program = FINALIZER.format(watchdog=WATCHDOG, bounded=False, policy="raise", op=op)
    assert _run(program) == "True"


@pytest.mark.parametrize("policy", ["raise", "saturate", "wrap"])
@pytest.mark.parametrize("op", [*OPERATIONS, "outside"])
def test_a_finalizer_may_use_a_bounded_counter_during_any_operation(op: str, policy: str) -> None:
    if op == "outside" and policy != "raise":
        pytest.skip("only the raise policy refuses a write")
    program = FINALIZER.format(watchdog=WATCHDOG, bounded=True, policy=policy, op=op)
    assert _run(program) == "True"


BALANCE = """
import faulthandler, gc
from atomicint import {cls}
faulthandler.dump_traceback_later({watchdog}, exit=True)
live = {cls}({args})

class Node:
    def __init__(self):
        live.increment()
        self.me = self

    def __del__(self):
        live.decrement()

gc.set_threshold(1)
for _ in range(100_000):
    Node()
gc.collect()
print(live.get())
"""


@pytest.mark.parametrize(
    ("cls", "args"),
    [("AtomicInt", ""), ("BoundedAtomicInt", "0, minimum=0, maximum=10**9")],
)
def test_no_update_from_a_finalizer_is_lost(cls: str, args: str) -> None:
    assert _run(BALANCE.format(cls=cls, args=args, watchdog=WATCHDOG)) == "0"


SIGNALS = """
import _thread, faulthandler, signal, threading, time
from atomicint import {cls}
faulthandler.dump_traceback_later({watchdog}, exit=True)
work = {cls}({args})
handled = []

def handler(signum, frame):
    work.add(1)
    handled.append(1)

signal.signal(signal.SIGINT, handler)
stop = threading.Event()

def pinger():
    while not stop.is_set():
        _thread.interrupt_main(signal.SIGINT)
        time.sleep(0.0002)

thread = threading.Thread(target=pinger, daemon=True)
thread.start()
for _ in range(400_000):
    work.add(1)
stop.set()
thread.join()
time.sleep(0.05)
print(len(handled) > 0, work.get() == 400_000 + len(handled))
"""


@pytest.mark.parametrize(
    ("cls", "args"),
    [("AtomicInt", ""), ("BoundedAtomicInt", "0, minimum=0, maximum=10**9")],
)
def test_a_signal_handler_may_use_the_counter_and_loses_nothing(cls: str, args: str) -> None:
    assert _run(SIGNALS.format(cls=cls, args=args, watchdog=WATCHDOG)) == "True True"
