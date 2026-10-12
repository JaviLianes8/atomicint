"""Every value is a real integer: nothing is truncated, parsed or silently compared."""

from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction
from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt


class Seven:
    def __index__(self) -> int:
        return 7


BAD = [2.9, "7", True, None, Fraction(3, 1), b"1"]

CALLS: list[Callable[[AtomicInt, Any], object]] = [
    lambda c, v: c.set(v),
    lambda c, v: c.add(v),
    lambda c, v: c.get_and_add(v),
    lambda c, v: c.get_and_set(v),
    lambda c, v: c.compare_and_set(v, 1),
    lambda c, v: c.compare_and_set(5, v),
    lambda c, v: c.compare_and_exchange(v, 1),
    lambda c, v: c.compare_and_exchange(5, v),
    lambda c, v: c.update(lambda _: v),
    lambda c, v: c.get_and_update(lambda _: v),
]


@pytest.mark.parametrize("bad", BAD)
def test_the_constructor_rejects_non_integers(bad: Any) -> None:
    with pytest.raises(TypeError, match="must be an integer"):
        AtomicInt(bad)


@pytest.mark.parametrize("bad", BAD)
@pytest.mark.parametrize("call", CALLS)
def test_every_operation_rejects_non_integers_and_keeps_the_value(
    call: Callable[[AtomicInt, Any], object], bad: Any
) -> None:
    counter = AtomicInt(5)
    with pytest.raises(TypeError, match="must be an integer"):
        call(counter, bad)
    assert counter.get() == 5


def test_integer_like_objects_are_accepted_as_plain_ints() -> None:
    counter = AtomicInt(Seven())
    assert counter.add(Seven()) == 14
    assert counter.compare_and_set(14, Seven())
    assert type(counter.get()) is int


def test_huge_values_are_kept_exactly() -> None:
    counter = AtomicInt(2**200)
    assert counter.add(1) == 2**200 + 1


@pytest.mark.parametrize("name", ["minimum", "maximum"])
def test_bounds_must_be_integers(name: str) -> None:
    with pytest.raises(TypeError, match=f"{name} must be an integer"):
        kwargs: dict[str, Any] = {name: 1.5}
        BoundedAtomicInt(0, **kwargs)
