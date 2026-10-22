"""An __index__ hook is found and called the way Python finds and calls it.

The interpreter looks a special method up along the MRO it keeps for the class, never
through the metaclass, and binds the hook with the __get__ its own class holds. Each case
below is checked against ``operator.index``: the counter takes the same value, or refuses
the input with the same exception type.
"""

from __future__ import annotations

import operator
from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt

from .test_metaclass import MRO_ANSWERS, _meta


class Seven:
    def __index__(self) -> int:
        return 7


class Inherits(Seven):
    pass


class Deeper(Inherits):
    pass


def _taken_everywhere(value: Any, expected: int) -> None:
    assert operator.index(value) == expected
    assert AtomicInt(value).get() == expected
    counter = AtomicInt(1)
    assert (counter.add(value), counter.get_and_add(value)) == (1 + expected, 1 + expected)
    assert counter.compare_and_set(1 + 2 * expected, value) is True
    assert counter.compare_and_exchange(value, 0) == expected
    assert (counter.get_and_set(value), counter.update(lambda _: value)) == (0, expected)
    assert counter.get_and_update(lambda _: value) == expected
    counter.set(value)
    assert counter.get() == expected
    gauge = BoundedAtomicInt(value, minimum=value, maximum=value)
    assert (gauge.get(), gauge.minimum, gauge.maximum) == (expected, expected, expected)


@pytest.mark.parametrize("value", [Inherits(), Deeper()], ids=["one level", "two levels"])
def test_an_inherited_index_hook_is_found(value: Any) -> None:
    _taken_everywhere(value, 7)


@pytest.mark.parametrize("answer", list(MRO_ANSWERS))
def test_a_metaclass_mro_cannot_hide_an_inherited_index_hook(answer: str) -> None:
    number = _meta("__mro__", MRO_ANSWERS[answer])("Number", (Seven,), {})
    _taken_everywhere(number(), 7)


@pytest.mark.parametrize(
    "answer",
    [lambda cls: {}, lambda cls: {"__index__": lambda self: 99}],
    ids=["empty", "another hook"],
)
def test_a_metaclass_namespace_cannot_hide_or_replace_an_index_hook(answer: Any) -> None:
    number = _meta("__dict__", answer)("Number", (), {"__index__": lambda self: 7})
    _taken_everywhere(number(), 7)


class One:
    def __index__(self) -> int:
        return 1


class Two:
    def __index__(self) -> int:
        return 2


class Reordering(type):
    def mro(cls) -> list[type]:
        return [cls, Two, One, object]


def test_the_hook_comes_from_the_order_a_metaclass_mro_made() -> None:
    number = Reordering("Number", (One, Two), {})
    _taken_everywhere(number(), 2)


class NoGet:
    __get__ = None

    def __call__(self, *args: Any) -> int:
        return 8


class Unbindable:
    __index__ = NoGet()


class NoHook:
    __index__ = None


def _refused_everywhere(value: Any, message: str) -> None:
    with pytest.raises(TypeError) as expected:
        operator.index(value)
    with pytest.raises(TypeError, match=message) as caught:
        AtomicInt(value)
    counter = AtomicInt(3)
    with pytest.raises(TypeError, match=message):
        counter.add(value)
    with pytest.raises(TypeError, match=message):
        BoundedAtomicInt(0, maximum=value)
    assert counter.get() == 3
    assert type(caught.value) is type(expected.value)


def test_a_hook_whose_class_sets_get_to_none_is_refused_as_python_refuses_it() -> None:
    _refused_everywhere(Unbindable(), r"^'NoneType' object is not callable$")


def test_an_index_hook_set_to_none_is_refused() -> None:
    _refused_everywhere(NoHook(), r"must be an integer, not NoHook$")
