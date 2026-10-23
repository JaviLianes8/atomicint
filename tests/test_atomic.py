"""Single-threaded behaviour of every AtomicInt operation."""

from __future__ import annotations

import pytest

from atomicint import AtomicInt, BoundedAtomicInt


def test_get_returns_the_initial_value() -> None:
    assert AtomicInt(7).get() == 7


def test_default_value_is_zero() -> None:
    assert AtomicInt().get() == 0


def test_set_replaces_the_value() -> None:
    counter = AtomicInt(1)
    counter.set(42)
    assert counter.get() == 42


def test_add_returns_the_new_value() -> None:
    counter = AtomicInt(10)
    assert counter.add(5) == 15
    assert counter.get() == 15


def test_add_accepts_a_negative_amount() -> None:
    counter = AtomicInt(10)
    assert counter.add(-4) == 6


def test_increment_returns_the_new_value() -> None:
    counter = AtomicInt(0)
    assert counter.increment() == 1
    assert counter.increment() == 2


def test_decrement_returns_the_new_value() -> None:
    counter = AtomicInt(3)
    assert counter.decrement() == 2
    assert counter.get() == 2


def test_compare_and_set_swaps_when_the_value_matches() -> None:
    counter = AtomicInt(5)
    assert counter.compare_and_set(5, 9) is True
    assert counter.get() == 9


def test_compare_and_set_leaves_the_value_when_it_does_not_match() -> None:
    counter = AtomicInt(5)
    assert counter.compare_and_set(4, 9) is False
    assert counter.get() == 5


def test_get_and_set_returns_the_previous_value() -> None:
    counter = AtomicInt(1)
    assert counter.get_and_set(8) == 1
    assert counter.get() == 8


def test_repr_shows_the_current_value() -> None:
    assert repr(AtomicInt(3)) == "AtomicInt(3)"


def test_get_and_add_returns_the_previous_value() -> None:
    counter = AtomicInt(10)
    assert counter.get_and_add(5) == 10
    assert counter.get() == 15


def test_compare_and_exchange_returns_the_expected_value_when_it_swaps() -> None:
    counter = AtomicInt(5)
    assert counter.compare_and_exchange(5, 9) == 5
    assert counter.get() == 9


def test_compare_and_exchange_returns_the_current_value_when_it_does_not_swap() -> None:
    counter = AtomicInt(5)
    assert counter.compare_and_exchange(4, 9) == 5
    assert counter.get() == 5


def test_int_and_index_give_a_snapshot() -> None:
    counter = AtomicInt(4)
    assert int(counter) == 4
    assert [10, 11, 12, 13, 14][counter] == 14
    assert type(int(counter)) is int


def test_atomic_ints_compare_by_identity() -> None:
    assert AtomicInt(1) != AtomicInt(1)
    assert len({AtomicInt(1), AtomicInt(1)}) == 2


@pytest.mark.parametrize("cls", [AtomicInt, BoundedAtomicInt])
def test_compare_and_set_compares_values_not_objects(cls: type[AtomicInt]) -> None:
    for value in (1000, 10**30):
        stored, expected = int(str(value)), int(str(value))
        assert stored == expected and stored is not expected
        counter = cls(stored)
        assert counter.compare_and_exchange(expected, 7) == value
        assert counter.get() == 7
        counter.set(int(str(value)))
        assert counter.compare_and_set(int(str(value)), 8) is True
        assert counter.get() == 8
