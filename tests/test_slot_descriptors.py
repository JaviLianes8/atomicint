"""What a copy makes of slot descriptors the class did not get from Python as they are.

A slot whose name a class later gives to a property is copied through that property, as
the standard library copies any slotted class: one with a getter and a setter keeps the
slot, a read-only one makes the copy fail the same way. A slot descriptor that belongs to
another class, placed in a subclass's namespace, is not one of its slots.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt

from .test_copy_slots import CLONE_IDS, CLONES, Clone


class Tagged(AtomicInt):
    __slots__ = ("tag",)
    tag: str


class TaggedGauge(BoundedAtomicInt):
    __slots__ = ("tag",)
    tag: str


class Fixed(AtomicInt):
    __slots__ = ("tag",)
    tag: str


class PlainFixed:  # the same class without the counter, copied by the standard library
    __slots__ = ("tag",)
    tag: str


RAW: dict[type, Any] = {cls: vars(cls)["tag"] for cls in (Tagged, TaggedGauge, Fixed, PlainFixed)}
for _cls in (Tagged, TaggedGauge):  # replaced after the classes were made, calling the slot
    type.__setattr__(_cls, "tag", property(RAW[_cls].__get__, RAW[_cls].__set__))
for _fixed in (Fixed, PlainFixed):  # read-only
    type.__setattr__(_fixed, "tag", property(RAW[_fixed].__get__))


@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_a_slot_behind_a_property_with_a_setter_is_copied(clone: Clone) -> None:
    plain, gauge = Tagged(3), TaggedGauge(5, minimum=0, maximum=9, overflow="wrap")
    plain.tag, gauge.tag = "kept", "held"
    twin, other = clone(plain), clone(gauge)
    assert (twin.tag, twin.get(), other.tag, other.add(7)) == ("kept", 3, "held", 2)
    empty = clone(Tagged(4))  # a slot never set stays unset
    assert (hasattr(empty, "tag"), empty.get()) == (False, 4)


@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_a_slot_behind_a_read_only_property_fails_as_for_any_slotted_class(clone: Clone) -> None:
    counter, plain = Fixed(3), PlainFixed()
    RAW[Fixed].__set__(counter, "kept")
    RAW[PlainFixed].__set__(plain, "kept")
    with pytest.raises(AttributeError):
        copy.copy(plain)
    with pytest.raises(AttributeError):
        clone(counter)
    assert (counter.tag, counter.get()) == ("kept", 3)


class Other:
    __slots__ = ("z",)


class Borrower(AtomicInt):
    __slots__ = ()
    z = vars(Other)["z"]  # another class's slot descriptor, not a slot of this class


class BorrowerGauge(BoundedAtomicInt):
    __slots__ = ("tag",)
    tag: str
    z = vars(Other)["z"]


@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_another_class_slot_descriptor_in_the_namespace_is_not_copied(clone: Clone) -> None:
    assert clone(Borrower(5)).get() == 5
    gauge = BorrowerGauge(5, minimum=0, maximum=9, overflow="wrap")
    gauge.tag = "blue"
    twin = clone(gauge)
    assert (twin.tag, twin.add(7), twin.minimum, twin.maximum) == ("blue", 2, 0, 9)
