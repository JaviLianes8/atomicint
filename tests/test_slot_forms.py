"""Every form `__slots__` may take is read again for slots a base's class hook wrapped."""

from __future__ import annotations

import collections
from collections.abc import Callable, Iterable
from typing import Any

import pytest

from atomicint import AtomicInt

from .test_class_hooks import Validating
from .test_copy_slots import CLONE_IDS, CLONES, Clone

NAMES = ("tag", "__pv")

FORMS: dict[str, Callable[[tuple[str, ...]], Iterable[str]]] = {
    "deque": collections.deque,
    "OrderedDict": collections.OrderedDict.fromkeys,
    "dict keys": lambda names: dict.fromkeys(names).keys(),
    "tuple subclass": type("Row", (tuple,), {}),
}


def _form(label: str) -> Any:
    # Module level, so pickles find each class by name.
    made = type("Form", (Validating,), {"__slots__": FORMS[label](NAMES)})
    made.__qualname__ = f"Form_{len(MADE)}"
    globals()[made.__qualname__] = made
    return made


MADE: dict[str, Any] = {}
for _label in FORMS:
    MADE[_label] = _form(_label)


@pytest.mark.parametrize("label", list(FORMS))
@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_a_wrapped_slot_is_kept_whatever_iterable_listed_it(clone: Clone, label: str) -> None:
    original = MADE[label](3)
    original.tag, original._Form__pv = "blue", "red"
    twin = clone(original)
    assert (twin.tag, twin._Form__pv, twin.get()) == ("blue", "red", 3)


class Touchy(str):
    # A str subclass that refuses to be compared or formatted: Python accepts it as a slot.
    __hash__ = str.__hash__

    def __eq__(self, other: object) -> bool:
        raise RuntimeError("compared")

    def __str__(self) -> str:
        raise RuntimeError("formatted")


Odd: Any = type("Odd", (AtomicInt,), {"__slots__": (Touchy("tag"), Touchy("__pv"))})
Lone: Any = type("Lone", (AtomicInt,), {"__slots__": Touchy("tag")})


@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_slot_names_given_as_a_hostile_str_subclass_are_kept(clone: Clone) -> None:
    original = Odd(3)
    original.tag, original._Odd__pv = "blue", "red"
    assert original.increment() == 4
    twin = clone(original)
    assert (twin.tag, twin._Odd__pv, twin.get()) == ("blue", "red", 4)
    lone = Lone(5)
    lone.tag = "green"
    assert (clone(lone).tag, clone(lone).get()) == ("green", 5)


class Replacing(AtomicInt):
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        # A base hook may leave anything in __slots__ once the class is made.
        type.__setattr__(cls, "__slots__", [1, "tag"])
        super().__init_subclass__(**kwargs)


class Replaced(Replacing):
    __slots__ = ("tag",)
    tag: str


@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_a_non_str_left_in_slots_by_a_hook_is_skipped(clone: Clone) -> None:
    original = Replaced(3)
    original.tag = "blue"
    twin = clone(original)
    assert (twin.tag, twin.get()) == ("blue", 3)
