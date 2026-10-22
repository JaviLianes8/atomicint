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


class Plain(AtomicInt):
    __slots__ = ("tag",)


class Mid(Plain):
    __slots__ = ()


class Leaf(Mid):  # the slot is declared two levels up
    __slots__ = ()


class Quiet(AtomicInt):
    __slots__ = ("tag",)

    def __init_subclass__(cls) -> None:
        pass  # no super() call: its subclasses are made without the base's class hook


class QuietMid(Quiet):
    __slots__ = ()


class QuietLeaf(QuietMid):  # the slot is two levels up, past a class that skipped the hook
    __slots__ = ()


class Wrapped(AtomicInt):
    __slots__ = ("tag",)
    tag: str


# A common wrapper: the slot's descriptor on the class is replaced by a property that
# calls it (to validate or log), after the class was made.
_raw = Wrapped.__dict__["tag"]
type.__setattr__(Wrapped, "tag", property(_raw.__get__, _raw.__set__))


class WrappedChild(Wrapped):  # made after the wrapper replaced its base's descriptor
    __slots__ = ()


@pytest.mark.parametrize(
    ("cls", "name"),
    [(Leaf, "tag"), (QuietLeaf, "tag"), (Wrapped, "tag"), (WrappedChild, "tag")],
    ids=["Leaf", "QuietLeaf", "Wrapped", "WrappedChild"],
)
@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_inherited_and_wrapped_slots_are_kept(
    clone: Clone, cls: type[AtomicInt], name: str
) -> None:
    test_every_declared_slot_is_kept(clone, cls, name)


class Gauge(BoundedAtomicInt):
    __slots__ = ()


class Dial(Gauge):
    __slots__ = ()


@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_a_grandchild_keeps_its_bounds_and_policy(clone: Clone) -> None:
    twin = clone(Dial(5, minimum=0, maximum=9, overflow="wrap"))
    assert repr(twin) == "Dial(5, minimum=0, maximum=9, overflow='wrap')"
    assert (type(twin), twin.minimum, twin.maximum, twin.overflow) == (Dial, 0, 9, "wrap")
    assert twin.add(7) == 2


class Frozen(AtomicInt):
    __slots__ = ("tag",)

    def __init__(self, value: int, tag: str) -> None:
        super().__init__(value)
        object.__setattr__(self, "tag", tag)

    def __setattr__(self, name: str, value: object) -> None:
        if name == "tag":
            raise AttributeError("tag is read-only")
        super().__setattr__(name, value)


@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_a_copy_is_rebuilt_past_the_subclass_setattr(clone: Clone) -> None:
    twin = clone(Frozen(3, "blue"))
    assert (type(twin), twin.tag, twin.get(), twin.increment()) == (Frozen, "blue", 3, 4)
