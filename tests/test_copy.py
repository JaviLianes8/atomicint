"""Pickling and copying make an independent counter with the same value and bounds."""

from __future__ import annotations

import copy
import pickle
import threading
import weakref
from collections.abc import Callable
from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt

Clone = Callable[[Any], Any]
CLONES: list[Clone] = [copy.copy, copy.deepcopy, lambda c: pickle.loads(pickle.dumps(c))]


class Tagged(AtomicInt):
    __slots__ = ()


@pytest.mark.parametrize(
    "clone", [copy.copy, copy.deepcopy, lambda c: pickle.loads(pickle.dumps(c))]
)
def test_a_copy_keeps_the_value_but_not_the_identity(clone: object) -> None:
    original = AtomicInt(41)
    twin = clone(original)  # type: ignore[operator]
    assert type(twin) is AtomicInt
    assert twin.get() == 41
    twin.increment()
    assert (original.get(), twin.get()) == (41, 42)


def test_every_pickle_protocol_round_trips_a_bounded_counter() -> None:
    original = BoundedAtomicInt(7, minimum=0, maximum=9, overflow="wrap")
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        twin = pickle.loads(pickle.dumps(original, protocol=protocol))
        assert type(twin) is BoundedAtomicInt
        assert repr(twin) == repr(original)
        assert twin.add(5) == 2


def test_a_subclass_survives_a_copy_and_shows_its_own_name() -> None:
    twin = copy.deepcopy(Tagged(3))
    assert type(twin) is Tagged
    assert repr(twin) == "Tagged(3)"


def test_a_copy_inside_a_container_is_independent() -> None:
    config = {"hits": AtomicInt(1)}
    clone = copy.deepcopy(config)
    clone["hits"].add(10)
    assert config["hits"].get() == 1


class Named(AtomicInt):
    __slots__ = ("__secret", "name")

    def __init__(self, name: str, value: int = 0) -> None:
        self.name = name
        self.__secret = name.upper()
        super().__init__(value)

    def secret(self) -> str:
        return self.__secret


class Loose(AtomicInt):
    label: str


class Gauge(BoundedAtomicInt):
    __slots__ = ("unit",)
    unit: str


@pytest.mark.parametrize("clone", CLONES)
def test_a_subclass_with_its_own_constructor_keeps_every_attribute(clone: Clone) -> None:
    twin = clone(Named("hits", 3))
    assert isinstance(twin, Named)
    assert (twin.name, twin.secret(), twin.get()) == ("hits", "HITS", 3)
    assert twin.increment() == 4


@pytest.mark.parametrize("clone", CLONES)
def test_a_subclass_without_slots_keeps_its_instance_attributes(clone: Clone) -> None:
    original = Loose(1)
    original.label = "x"
    twin = clone(original)
    assert (twin.label, twin.get()) == ("x", 1)


@pytest.mark.parametrize("clone", CLONES)
def test_a_bounded_subclass_keeps_bounds_attributes_and_its_name(clone: Clone) -> None:
    original = Gauge(9, minimum=0, maximum=9, overflow="wrap")
    original.unit = "ms"
    twin = clone(original)
    assert twin.unit == "ms"
    assert repr(twin) == "Gauge(9, minimum=0, maximum=9, overflow='wrap')"
    assert twin.increment() == 0
    assert original.get() == 9


def test_an_unset_slot_stays_unset_in_the_copy() -> None:
    twin = copy.copy(Gauge(1))
    assert not hasattr(twin, "unit")


class _Private(AtomicInt):
    """A class name with a leading underscore and a private slot: mangled as _Private__tag."""

    __slots__ = ("__tag",)

    def __init__(self, value: int, tag: str) -> None:
        super().__init__(value)
        self.__tag = tag

    @property
    def tag(self) -> str:
        return self.__tag


class _(AtomicInt):
    """A class name of underscores only: Python does not mangle its private names at all."""

    __slots__ = ("__tag",)

    def __init__(self, value: int, tag: str) -> None:
        super().__init__(value)
        self.__tag = tag

    @property
    def tag(self) -> str:
        return self.__tag


class __(BoundedAtomicInt):
    __slots__ = ("__tag",)

    def __init__(self, value: int, tag: str) -> None:
        super().__init__(value, maximum=9)
        self.__tag = tag

    @property
    def tag(self) -> str:
        return self.__tag


class Tracked(AtomicInt):
    __slots__ = ("__weakref__",)


def _pickled(protocol: int) -> Clone:
    return lambda counter: pickle.loads(pickle.dumps(counter, protocol=protocol))


PROTOCOLS = [_pickled(protocol) for protocol in range(pickle.HIGHEST_PROTOCOL + 1)]


@pytest.mark.parametrize("cls", [_Private, _, __])
@pytest.mark.parametrize("clone", [copy.copy, copy.deepcopy, *PROTOCOLS])
def test_a_private_slot_of_an_underscored_subclass_is_copied(clone: Clone, cls: Any) -> None:
    twin = clone(cls(3, "blue"))
    assert (type(twin), twin.tag, twin.get()) == (cls, "blue", 3)


@pytest.mark.parametrize("clone", [copy.copy, copy.deepcopy, *PROTOCOLS])
def test_a_weakly_referenced_subclass_is_copied(clone: Clone) -> None:
    original = Tracked(3)
    alive = weakref.ref(original)
    twin = clone(original)
    assert (type(twin), twin.get(), twin.increment(), original.get()) == (Tracked, 3, 4, 3)
    assert alive() is original
    assert weakref.ref(twin)() is twin


@pytest.mark.parametrize("clone", CLONES)
def test_a_copy_has_a_lock_of_its_own(clone: Clone) -> None:
    original = BoundedAtomicInt(1, minimum=0, maximum=9)
    first, second = clone(original), clone(original)
    assert len({id(original._lock), id(first._lock), id(second._lock)}) == 3
    done: list[int] = []
    with first._lock:
        # Another thread must not wait for the lock this thread holds on a sibling copy.
        worker = threading.Thread(
            target=lambda: done.extend((second.increment(), original.increment())), daemon=True
        )
        worker.start()
        worker.join(timeout=30)
    assert done == [2, 2]
    assert first.increment() == 2
