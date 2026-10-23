"""No locked step makes a call: the base of the finalizer and signal handler promise.

CPython runs a finalizer or a signal handler only at a call (or at a loop back edge,
and no locked step has a loop). A profile hook sees calls of Python and built-in functions
but not calls of a type (``int(x)``, ``bool(x)``), which CPython follows with the same
check; on 3.12 and later the CALL events of ``sys.monitoring`` see every call. Recording
the calls made while the lock is held proves no such code can run between a read and its
store.
"""

from __future__ import annotations

import contextlib
import copy
import pickle
import sys
import threading
from collections.abc import Callable, Iterator
from types import FrameType
from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt


class _Watched:
    """A reentrant lock that knows whether this thread is inside a locked step."""

    def __init__(self) -> None:
        self.inner = threading.RLock()
        self.depth = 0

    def __enter__(self) -> None:
        self.inner.acquire()
        self.depth += 1

    def __exit__(self, *exc: object) -> None:
        self.depth -= 1
        self.inner.release()


def _calls_under_the_lock(counter: AtomicInt, operation: Callable[[], object]) -> list[str]:
    lock = _Watched()
    counter._lock = lock  # type: ignore[assignment]
    leaving = _Watched.__exit__.__code__
    seen: list[str] = []

    def hook(frame: FrameType, event: str, arg: Any) -> None:
        if lock.depth and event in ("call", "c_call"):
            if event == "call" and frame.f_code is leaving:
                return
            seen.append(frame.f_code.co_name if event == "call" else repr(arg))

    previous = sys.getprofile()
    sys.setprofile(hook)
    try:
        with contextlib.suppress(OverflowError), _every_call(lock, seen):
            operation()
    finally:
        sys.setprofile(previous)
    return seen


@contextlib.contextmanager
def _every_call(lock: _Watched, seen: list[str]) -> Iterator[None]:
    monitoring = getattr(sys, "monitoring", None)
    if monitoring is None:  # before 3.12 the profile hook is all there is
        yield
        return
    tool = next(i for i in range(6) if monitoring.get_tool(i) is None)

    def on_call(code: object, offset: int, called: object, arg0: object) -> None:
        if lock.depth and getattr(called, "__func__", called) is not _Watched.__exit__:
            seen.append(f"CALL {called!r}")

    monitoring.use_tool_id(tool, "lock-calls")
    monitoring.register_callback(tool, monitoring.events.CALL, on_call)
    monitoring.set_events(tool, monitoring.events.CALL)
    try:
        yield
    finally:
        monitoring.set_events(tool, 0)
        monitoring.register_callback(tool, monitoring.events.CALL, None)
        monitoring.free_tool_id(tool)


def _bounded(policy: Any) -> Callable[[], AtomicInt]:
    return lambda: BoundedAtomicInt(5, minimum=0, maximum=9, overflow=policy)


MAKERS = [AtomicInt, *(_bounded(policy) for policy in ("raise", "saturate", "wrap"))]
OPERATIONS: dict[str, Callable[[AtomicInt], object]] = {
    "get": lambda c: c.get(),
    "set": lambda c: c.set(7),
    "set_outside": lambda c: c.set(12),
    "add": lambda c: c.add(1),
    "add_outside": lambda c: c.add(10),
    "get_and_add": lambda c: c.get_and_add(-1),
    "get_and_set": lambda c: c.get_and_set(2),
    "cas_won": lambda c: c.compare_and_set(5, 6),
    "cas_lost": lambda c: c.compare_and_set(4, 6),
    "cas_outside": lambda c: c.compare_and_set(5, 12),
    "cax_won": lambda c: c.compare_and_exchange(5, 6),
    "cax_lost": lambda c: c.compare_and_exchange(4, 6),
    "cax_outside": lambda c: c.compare_and_exchange(5, -3),
    "update": lambda c: c.update(lambda v: v + 1),
    "get_and_update": lambda c: c.get_and_update(lambda v: v * 3),
    "int": int,
    "repr": repr,
    "copy": copy.copy,
    "pickle": pickle.dumps,
}


@pytest.mark.parametrize("make", MAKERS, ids=["plain", "raise", "saturate", "wrap"])
@pytest.mark.parametrize("name", list(OPERATIONS))
def test_no_operation_makes_a_call_while_it_holds_the_lock(
    make: Callable[[], AtomicInt], name: str
) -> None:
    counter = make()
    assert _calls_under_the_lock(counter, lambda: OPERATIONS[name](counter)) == []
