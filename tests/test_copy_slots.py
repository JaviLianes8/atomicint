"""Copies and pickles keep every slot Python created, however the subclass declared it."""

from __future__ import annotations

import copy
import pickle
from collections.abc import Callable
from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt

Clone = Callable[[Any], Any]


def _pickled(protocol: int) -> Clone:
    return lambda counter: pickle.loads(pickle.dumps(counter, protocol=protocol))


PROTOCOLS = range(pickle.HIGHEST_PROTOCOL + 1)
CLONES: list[Clone] = [copy.copy, copy.deepcopy, *(_pickled(protocol) for protocol in PROTOCOLS)]
CLONE_IDS = ["copy", "deepcopy", *(f"pickle{protocol}" for protocol in PROTOCOLS)]


class Streamed(AtomicInt):
    # The language allows any iterable; an iterator is used up when the class is made.
    __slots__ = iter(["tag"])


class StreamedGauge(BoundedAtomicInt):
    __slots__ = iter(["tag"])


class One(AtomicInt):
    __slots__ = "tag"


class Meta(AtomicInt):
    __slots__ = ("__tag__",)  # Python does not mangle a name that also ends in "__"


class Tag_(AtomicInt):
    __slots__ = ("__tag",)  # mangled as _Tag___tag: only leading underscores are stripped


class Base(AtomicInt):
    __slots__ = ("__tag",)  # mangled with Base, the class that declares it


class Child(Base):
    __slots__ = ()


class Renamed(AtomicInt):
    __slots__ = ("__tag",)


Renamed.__name__ = "Moved"


class Outer:
    class Inner(AtomicInt):  # __qualname__ "Outer.Inner", mangled with the name only
        __slots__ = ("__tag",)


def _tagged(cls: type[AtomicInt], name: str) -> AtomicInt:
    counter = cls(3)
    object.__setattr__(counter, name, "blue")
    return counter


CASES = [
    (Streamed, "tag"),
    (StreamedGauge, "tag"),
    (One, "tag"),
    (Meta, "__tag__"),
    (Tag_, "_Tag___tag"),
    (Child, "_Base__tag"),
    (Renamed, "_Renamed__tag"),
    (Outer.Inner, "_Inner__tag"),
]


@pytest.mark.parametrize(("cls", "name"), CASES, ids=[cls.__qualname__ for cls, _ in CASES])
@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_every_declared_slot_is_kept(clone: Clone, cls: type[AtomicInt], name: str) -> None:
    original = _tagged(cls, name)
    twin = clone(original)
    assert (type(twin), getattr(twin, name, "<missing>"), twin.get()) == (cls, "blue", 3)
    assert twin.increment() == 4
    assert original.get() == 3


class Open(AtomicInt):
    __slots__ = ("__dict__",)


@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_a_declared_instance_dict_is_copied_not_shared(clone: Clone) -> None:
    original = Open(3)
    original.note = "a"  # type: ignore[attr-defined]
    twin = clone(original)
    twin.note = "b"
    assert (original.note, twin.note) == ("a", "b")  # type: ignore[attr-defined]
    assert vars(twin) is not vars(original)
    assert twin.get() == 3
