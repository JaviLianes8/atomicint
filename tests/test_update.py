"""update and get_and_update apply a function atomically, retrying when raced."""

from __future__ import annotations

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
