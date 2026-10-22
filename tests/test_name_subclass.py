"""A class name that is a str subclass is read as the plain text Python holds.

Python keeps whatever str subclass a class was named with, by ``type(...)`` or by
assigning ``__name__``, and its own messages use the text alone. The counter's messages,
``repr()`` and copies must too: the subclass's methods may raise or answer anything.
"""

from __future__ import annotations

import copy
import operator
from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt


def _refuse(*args: Any) -> Any:
    raise RuntimeError("hostile name")


HOSTILE = {
    method: _refuse
    for method in ("__len__", "__format__", "__getitem__", "__str__", "__add__", "lstrip")
}
Raising: Any = type("Raising", (str,), HOSTILE)
SECRET = "sk_live_SECRET_" + "A" * 10_000
Lying: Any = type(
    "Lying",
    (str,),
    {
        "__len__": lambda self: 3,
        "__format__": lambda self, spec: SECRET,
        "__str__": lambda self: SECRET,
    },
)
Whole: Any = type("Whole", (str,), {"__getitem__": lambda self, key: self})
NAMES = {"raising": Raising, "lying": Lying}


@pytest.mark.parametrize("kind", list(NAMES))
def test_a_str_subclass_name_gives_the_documented_message(kind: str) -> None:
    odd = type(NAMES[kind]("Odd"), (), {})
    with pytest.raises(TypeError) as python:
        operator.index(odd())
    assert "'Odd'" in str(python.value)
    with pytest.raises(TypeError) as caught:
        AtomicInt(odd())
    assert str(caught.value) == "value must be an integer, not Odd"
    with pytest.raises(TypeError) as caught:
        AtomicInt(1).update(lambda value: odd())
    assert str(caught.value) == "update result must be an integer, not Odd"
    hook = type("Hook", (), {"__index__": lambda self: odd()})
    with pytest.raises(TypeError) as caught:
        AtomicInt(hook())
    assert str(caught.value) == "value must be an integer, but its __index__ returned Odd"
    policy = type(NAMES[kind]("P"), (str,), {})("raise")
    with pytest.raises(TypeError) as caught:
        BoundedAtomicInt(overflow=policy)
    assert str(caught.value) == "overflow must be a plain str, not P"


def test_a_long_str_subclass_name_is_still_cut_short() -> None:
    odd = type(Whole("Q" * 100_000), (), {})
    with pytest.raises(TypeError) as caught:
        AtomicInt(odd())
    assert str(caught.value) == "value must be an integer, not " + "Q" * 60 + "..."


@pytest.mark.parametrize("kind", list(NAMES))
@pytest.mark.parametrize("base", [AtomicInt, BoundedAtomicInt])
def test_a_subclass_named_by_a_str_subclass_is_made_shown_and_copied(
    base: type[AtomicInt], kind: str
) -> None:
    made: Any = type(NAMES[kind]("Named"), (base,), {"__slots__": ("__tag", "plain")})
    counter = made(4)
    counter._Named__tag, counter.plain = "a", "b"
    assert repr(counter).startswith("Named(4")
    twin = copy.deepcopy(counter)
    assert (twin.get(), twin._Named__tag, twin.plain) == (4, "a", "b")


@pytest.mark.parametrize("kind", list(NAMES))
def test_repr_after_renaming_with_a_str_subclass(kind: str) -> None:
    plain: Any = type("Plain", (AtomicInt,), {"__slots__": ()})
    gauge: Any = type("Gauge", (BoundedAtomicInt,), {"__slots__": ()})
    plain.__name__, gauge.__name__ = NAMES[kind]("Later"), NAMES[kind]("Bounded")
    assert object.__repr__(plain(1)).startswith("<")
    assert repr(plain(1)) == "Later(1)"
    assert (
        repr(gauge(2, minimum=0, maximum=3)) == "Bounded(2, minimum=0, maximum=3, overflow='raise')"
    )
