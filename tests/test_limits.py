"""Where the promise about finalizers and signal handlers stops, as the guide documents it.

Both cases are pinned so that the guide changes with the code: if one of them is ever
closed, its test fails and the guide's "Limits" paragraph must be updated.
"""

from __future__ import annotations

import sys
import threading
from types import FrameType
from typing import Any

from atomicint import AtomicInt, BoundedAtomicInt


def test_a_trace_hook_inside_a_locked_step_can_lose_a_nested_update() -> None:
    # A trace hook runs Python code at every line, also between the read and the store
    # of an operation. What a finalizer or signal handler started there does is lost.
    counter = AtomicInt()
    nested: list[int] = []

    def hook(frame: FrameType, event: str, arg: Any) -> Any:
        inside = frame.f_code.co_name == "_add" and "current" in frame.f_locals
        if event == "line" and inside and not nested:
            nested.append(counter.decrement())
        return hook

    previous = sys.gettrace()
    sys.settrace(hook)
    try:
        counter.increment()
    finally:
        sys.settrace(previous)
    assert nested == [-1]
    assert counter.get() == 1  # 0 without the hook


class _InterruptedAfterTaking:
    """A lock whose ``with`` is interrupted just after taking it, before the block starts.

    CPython 3.14 can deliver a signal handler's exception (KeyboardInterrupt) there.
    """

    def __init__(self) -> None:
        self.inner = threading.RLock()

    def __enter__(self) -> None:
        self.inner.acquire()
        raise KeyboardInterrupt

    def __exit__(self, *exc: object) -> None:
        self.inner.release()


def _free_for_another_thread(lock: Any) -> bool:
    taken: list[bool] = []

    def attempt() -> None:
        taken.append(lock.acquire(timeout=0.2))
        if taken[0]:
            lock.release()

    worker = threading.Thread(target=attempt)
    worker.start()
    worker.join()
    return taken[0]


def test_an_exception_just_after_the_lock_is_taken_leaves_it_held() -> None:
    for counter in (AtomicInt(5), BoundedAtomicInt(5, maximum=9)):
        lock = _InterruptedAfterTaking()
        counter._lock = lock  # type: ignore[assignment]
        try:
            counter.increment()
        except KeyboardInterrupt:
            pass
        else:
            raise AssertionError("the interrupt was not raised")
        assert counter._value == 5  # abandoned before anything was read or stored
        assert not _free_for_another_thread(lock.inner)
        lock.inner.release()
        assert _free_for_another_thread(lock.inner)
