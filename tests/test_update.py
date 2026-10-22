"""update and get_and_update apply a function atomically, retrying when raced."""

from __future__ import annotations

import threading
from collections.abc import Callable

import pytest

from atomicint import AtomicInt


def test_update_returns_the_new_value() -> None:
    counter = AtomicInt(3)
    assert counter.update(lambda v: v * 10) == 30
    assert counter.get() == 30


def test_get_and_update_returns_the_previous_value() -> None:
    counter = AtomicInt(3)
    assert counter.get_and_update(lambda v: v * 10) == 3
    assert counter.get() == 30


def test_the_function_can_read_the_counter_without_deadlocking() -> None:
    counter = AtomicInt(4)
    assert counter.update(lambda v: v + counter.get()) == 8


def test_a_raced_update_is_retried_with_the_fresh_value() -> None:
    counter = AtomicInt(1)
    seen: list[int] = []

    def double(value: int) -> int:
        seen.append(value)
        if len(seen) == 1:
            counter.set(50)  # another writer slips in between read and commit
        return value * 2

    assert counter.update(double) == 100
    assert seen == [1, 50]


def test_a_raised_exception_leaves_the_value_untouched() -> None:
    counter = AtomicInt(9)

    def boom(value: int) -> int:
        raise ValueError("no")

    with pytest.raises(ValueError, match="no"):
        counter.update(boom)
    assert counter.get() == 9


def test_an_update_that_keeps_the_value_still_succeeds() -> None:
    counter = AtomicInt(6)
    assert counter.get_and_update(lambda v: v) == 6
    assert counter.get() == 6


def _in_another_thread(action: Callable[[], object]) -> bool:
    # True when the action finished: a lock held by this thread would keep it waiting.
    worker = threading.Thread(target=action, daemon=True)
    worker.start()
    worker.join(timeout=10)
    return not worker.is_alive()


@pytest.mark.parametrize("which", ["update", "get_and_update"])
def test_the_function_runs_without_the_lock(which: str) -> None:
    counter = AtomicInt(5)
    seen: list[int] = []
    reads: list[int] = []

    def step(value: int) -> int:
        seen.append(value)
        if len(seen) == 1:
            # Another thread can read the counter, and its write makes the update retry.
            assert _in_another_thread(lambda: reads.append(counter.get()))
            assert _in_another_thread(lambda: counter.set(50))
        return value + 1

    assert getattr(counter, which)(step) == (51 if which == "update" else 50)
    assert (seen, reads, counter.get()) == ([5, 50], [5], 51)
