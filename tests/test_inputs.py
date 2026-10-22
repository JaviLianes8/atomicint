"""Every value is a real integer: nothing is truncated, parsed or silently compared."""

from __future__ import annotations

import operator
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


class Flip:
    """An __index__ that answers 0 the first time and 1 afterwards."""

    def __init__(self) -> None:
        self.calls = 0

    def __index__(self) -> int:
        self.calls += 1
        return 0 if self.calls == 1 else 1


class Truthy:
    def __index__(self) -> int:
        return True


class Wordy:
    def __index__(self) -> int:
        return "3"  # type: ignore[return-value]


class Big(int):
    pass


def test_compare_and_set_reads_expect_once_and_reports_the_swap() -> None:
    counter = AtomicInt(0)
    flip = Flip()
    assert counter.compare_and_set(flip, 7) is True
    assert counter.get() == 7
    assert flip.calls == 1


@pytest.mark.filterwarnings("error")
@pytest.mark.parametrize("odd", [Truthy(), Wordy()])
def test_an_index_hook_returning_a_non_integer_is_refused(odd: Any) -> None:
    with pytest.raises(TypeError, match=r"value must be an integer, but its __index__ returned"):
        AtomicInt(odd)
    counter = AtomicInt(2)
    with pytest.raises(TypeError, match=r"amount must be an integer"):
        counter.add(odd)
    assert counter.get() == 2


def test_an_int_subclass_is_stored_as_a_plain_int() -> None:
    counter = AtomicInt(Big(5))
    assert type(counter.get()) is int
    assert type(counter.add(Big(1))) is int


class GivesBig:
    def __index__(self) -> int:
        return Big(3)


def test_an_index_hook_returning_an_int_subclass_is_stored_as_a_plain_int() -> None:
    assert type(AtomicInt(GivesBig()).get()) is int


class ClassHook:
    @classmethod
    def __index__(cls) -> int:
        return 3


class StaticHook:
    @staticmethod
    def __index__() -> int:
        return 4


@pytest.mark.parametrize(("odd", "value"), [(ClassHook(), 3), (StaticHook(), 4)])
def test_an_index_hook_is_bound_the_way_python_binds_it(odd: Any, value: int) -> None:
    assert operator.index(odd) == value
    assert [0, 1, 2, 3, 4][odd] == value
    counter = AtomicInt(odd)
    assert (counter.get(), type(counter.get())) == (value, int)
    assert counter.add(odd) == 2 * value


class Pretender:
    """Claims to be an int through __class__, and answers True from __index__."""

    @property  # type: ignore[misc]
    def __class__(self) -> type:
        return int

    def __index__(self) -> int:
        return True


class EmptyPretender:
    @property  # type: ignore[misc]
    def __class__(self) -> type:
        return int


class GivesPretender:
    def __index__(self) -> Any:
        return Pretender()


@pytest.mark.filterwarnings("error")
def test_a_spoofed_class_does_not_get_past_the_checks() -> None:
    assert isinstance(Pretender(), int)
    with pytest.raises(TypeError) as caught:
        AtomicInt(Pretender())
    assert str(caught.value) == "value must be an integer, but its __index__ returned bool"
    with pytest.raises(TypeError) as caught:
        AtomicInt(EmptyPretender())  # type: ignore[arg-type]
    assert str(caught.value) == "value must be an integer, not EmptyPretender"
    with pytest.raises(TypeError) as caught:
        AtomicInt(GivesPretender())
    assert str(caught.value) == "value must be an integer, but its __index__ returned Pretender"


class Parent:
    def __index__(self) -> int:
        return 1


class Child(Parent):
    def __index__(self) -> int:
        return 2


def test_the_nearest_index_hook_in_the_class_hierarchy_wins() -> None:
    assert AtomicInt(Child()).get() == operator.index(Child()) == 2
