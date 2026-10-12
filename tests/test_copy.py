"""Pickling and copying make an independent counter with the same value and bounds."""

from __future__ import annotations

import copy
import pickle

import pytest

from atomicint import AtomicInt, BoundedAtomicInt


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


def test_a_subclass_survives_a_copy() -> None:
    assert type(copy.deepcopy(Tagged(3))) is Tagged


def test_a_copy_inside_a_container_is_independent() -> None:
    config = {"hits": AtomicInt(1)}
    clone = copy.deepcopy(config)
    clone["hits"].add(10)
    assert config["hits"].get() == 1
