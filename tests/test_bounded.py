"""BoundedAtomicInt keeps every write inside its range, by the chosen policy."""

from __future__ import annotations

from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt


def test_it_is_an_atomic_int_with_its_bounds_exposed() -> None:
    counter = BoundedAtomicInt(3, minimum=0, maximum=9, overflow="saturate")
    assert isinstance(counter, AtomicInt)
    assert (counter.minimum, counter.maximum, counter.overflow) == (0, 9, "saturate")


def test_the_default_policy_is_raise_and_no_bound_means_no_limit() -> None:
    counter = BoundedAtomicInt()
    assert (counter.minimum, counter.maximum, counter.overflow) == (None, None, "raise")
    assert counter.add(10**30) == 10**30
    assert counter.add(-(10**31)) == 10**30 - 10**31


@pytest.mark.parametrize(
    ("operation", "args"),
    [
        ("set", (11,)),
        ("add", (8,)),
        ("get_and_add", (-6,)),
        ("get_and_set", (-1,)),
        ("compare_and_set", (5, 99)),
        ("compare_and_exchange", (5, -99)),
        ("update", (lambda v: v + 6,)),
        ("get_and_update", (lambda v: v - 6,)),
    ],
)
def test_raise_refuses_an_out_of_range_write_and_keeps_the_value(
    operation: str, args: tuple[Any, ...]
) -> None:
    counter = BoundedAtomicInt(5, minimum=0, maximum=10)
    with pytest.raises(OverflowError, match=r"outside \[0, 10\]"):
        getattr(counter, operation)(*args)
    assert counter.get() == 5


def test_raise_allows_both_bounds_exactly() -> None:
    counter = BoundedAtomicInt(0, minimum=0, maximum=10)
    assert counter.add(10) == 10
    assert counter.add(-10) == 0


def test_increment_at_the_top_raises() -> None:
    counter = BoundedAtomicInt(3, maximum=3)
    with pytest.raises(OverflowError, match=r"outside \[unbounded, 3\]"):
        counter.increment()
    assert counter.decrement() == 2


def test_a_failed_compare_and_set_never_checks_the_range() -> None:
    counter = BoundedAtomicInt(5, minimum=0, maximum=10)
    assert counter.compare_and_set(4, 99) is False
    assert counter.get() == 5


def test_an_out_of_range_initial_value_follows_the_policy() -> None:
    with pytest.raises(OverflowError):
        BoundedAtomicInt(11, maximum=10)
    assert BoundedAtomicInt(11, maximum=10, overflow="saturate").get() == 10
    assert BoundedAtomicInt(11, minimum=0, maximum=9, overflow="wrap").get() == 1


def test_saturate_clamps_to_the_nearest_bound() -> None:
    counter = BoundedAtomicInt(5, minimum=-2, maximum=10, overflow="saturate")
    assert counter.add(100) == 10
    assert counter.get_and_add(-100) == 10
    assert counter.get() == -2
    assert counter.update(lambda v: v * 1000) == -2


def test_saturate_with_one_bound_only() -> None:
    floor = BoundedAtomicInt(1, minimum=0, overflow="saturate")
    assert floor.add(-5) == 0
    assert floor.add(10**20) == 10**20


@pytest.mark.parametrize(
    ("start", "delta", "expected"),
    [(255, 1, 0), (0, -1, 255), (200, 600, 32), (5, -1029, 0), (0, 256 * 7, 0)],
)
def test_wrap_behaves_like_an_unsigned_byte(start: int, delta: int, expected: int) -> None:
    counter = BoundedAtomicInt(start, minimum=0, maximum=255, overflow="wrap")
    assert counter.add(delta) == expected


def test_wrap_on_a_signed_range() -> None:
    counter = BoundedAtomicInt(127, minimum=-128, maximum=127, overflow="wrap")
    assert counter.increment() == -128
    assert counter.add(-1) == 127


def test_a_single_value_range_is_allowed() -> None:
    counter = BoundedAtomicInt(4, minimum=4, maximum=4, overflow="wrap")
    assert counter.add(1000) == 4


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"minimum": 5, "maximum": 4}, "greater than maximum"),
        ({"overflow": "clamp"}, "overflow must be "),
        ({"overflow": "wrap", "maximum": 9}, "needs both"),
        ({"overflow": "wrap", "minimum": 0}, "needs both"),
    ],
)
def test_bad_configuration_is_rejected(kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        BoundedAtomicInt(5, **kwargs)


def test_repr_shows_value_bounds_and_policy() -> None:
    counter = BoundedAtomicInt(3, minimum=0, maximum=9, overflow="wrap")
    assert repr(counter) == "BoundedAtomicInt(3, minimum=0, maximum=9, overflow='wrap')"


class Loud(str):
    pass


class Anything:
    def __eq__(self, other: object) -> bool:
        return True

    __hash__ = object.__hash__


@pytest.mark.parametrize("policy", [Loud("raise"), Anything(), None, 1])
def test_the_overflow_policy_must_be_one_of_the_exact_names(policy: Any) -> None:
    with pytest.raises(ValueError, match="overflow must be "):
        BoundedAtomicInt(0, overflow=policy)
