"""Every form `__slots__` may take is read again for slots a base's class hook wrapped."""

from __future__ import annotations

import collections
from collections.abc import Callable, Iterable
from typing import Any

import pytest

from atomicint import AtomicInt

from .test_class_hooks import Validating, _wrap
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
    # A str subclass that refuses to be compared: Python accepts it as a slot name.
    __hash__ = str.__hash__

    def __eq__(self, other: object) -> bool:
        raise RuntimeError("compared")


class Plainly(AtomicInt):
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        # Wraps the new slots first, as Validating does, reading the names as plain strings.
        for name in map(str.__str__, vars(cls)["__slots__"]):
            _wrap(cls, f"_{cls.__name__}{name}" if name.startswith("__") else name)
        super().__init_subclass__(**kwargs)


Odd: Any = type("Odd", (AtomicInt,), {"__slots__": (Touchy("tag"), Touchy("__pv"))})
Lone: Any = type("Lone", (AtomicInt,), {"__slots__": Touchy("tag")})
Guarded: Any = type("Guarded", (Plainly,), {"__slots__": [Touchy("tag"), Touchy("__pv")]})


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
    guarded = Guarded(6)  # its slots were wrapped before the counter's hook ran
    guarded.tag, guarded._Guarded__pv = "pink", "grey"
    assert (clone(guarded).tag, clone(guarded)._Guarded__pv) == ("pink", "grey")


class Unreadable:
    def __iter__(self) -> Any:
        raise RuntimeError("cannot be read again")


LEFTOVERS: dict[str, object] = {"a number": [1, "tag"], "an unreadable object": Unreadable()}


def _replaced(label: str) -> Any:
    class Replacing(AtomicInt):
        __slots__ = ()

        def __init_subclass__(cls, **kwargs: Any) -> None:
            # A base hook may leave anything in __slots__ once the class is made.
            type.__setattr__(cls, "__slots__", LEFTOVERS[label])
            super().__init_subclass__(**kwargs)

    made: Any = type("Replaced", (Replacing,), {"__slots__": ("tag",)})
    made.__qualname__ = f"Replaced_{len(REPLACED)}"
    globals()[made.__qualname__] = made
    return made


REPLACED: dict[str, Any] = {}
for _label in LEFTOVERS:
    REPLACED[_label] = _replaced(_label)


@pytest.mark.parametrize("label", list(LEFTOVERS))
@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_whatever_a_hook_leaves_in_slots_is_skipped(clone: Clone, label: str) -> None:
    original = REPLACED[label](3)
    original.tag = "blue"
    twin = clone(original)
    assert (twin.tag, twin.get()) == ("blue", 3)
