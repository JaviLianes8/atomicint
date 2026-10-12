"""Pickling and copying make an independent counter with the same value and bounds."""

from __future__ import annotations

import copy
import pickle
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
