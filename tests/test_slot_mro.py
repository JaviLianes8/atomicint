"""Copies take the slots along the MRO Python keeps, and only the class's own __slots__.

A metaclass ``mro()`` may leave a slotted base out of a class's MRO: that base's slots are
then not attributes of the class and must not be copied, while a subclass whose MRO does
hold the base keeps them. A subclass without ``__slots__`` lists no slot of its own, even
when a base's ``__slots__`` is inherited.
"""

from __future__ import annotations

from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt

from .test_copy_slots import CLONE_IDS, CLONES, Clone

_NAME = vars(type)["__name__"]
# The base each named class leaves out of its MRO.
HIDE: dict[str, type] = {}


class Dropping(type):
    def mro(cls) -> list[type]:
        found = super().mro()
        hidden = HIDE.get(_NAME.__get__(cls))
        return [klass for klass in found if klass is not hidden]


class HiddenPlain(AtomicInt):
    __slots__ = ("b",)


class HiddenGauge(BoundedAtomicInt):
    __slots__ = ("b",)


class Shadow:
    __slots__ = ()
    b = 7


HIDE.update(ChildPlain=HiddenPlain, ChildGauge=HiddenGauge)
HIDE.update(KnownPlain=HiddenPlain, KnownGauge=HiddenGauge)


class ChildPlain(Shadow, HiddenPlain, metaclass=Dropping):
    __slots__ = ()


class ChildGauge(Shadow, HiddenGauge, metaclass=Dropping):
    __slots__ = ()


class KnownPlain(HiddenPlain, metaclass=Dropping):
    __slots__ = ()


class KnownGauge(HiddenGauge, metaclass=Dropping):
    __slots__ = ()


class BelowPlain(KnownPlain, HiddenPlain):
    __slots__ = ()


class BelowGauge(KnownGauge, HiddenGauge):
    __slots__ = ()


@pytest.mark.parametrize("child", [ChildPlain, ChildGauge])
@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_a_slot_of_a_base_left_out_of_the_mro_is_not_copied(clone: Clone, child: Any) -> None:
    assert HiddenPlain not in child.__mro__ and HiddenGauge not in child.__mro__
    original = child(5)
    twin = clone(original)
    assert (twin.get(), twin.b, twin.increment(), original.get()) == (5, 7, 6, 5)


@pytest.mark.parametrize("below", [BelowPlain, BelowGauge])
@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_a_base_whose_mro_leaves_a_slotted_class_out_does_not_hide_its_slots(
    clone: Clone, below: Any
) -> None:
    original = below(5)
    original.b = "kept"
    twin = clone(original)
    assert (twin.get(), twin.b) == (5, "kept")


class PrivatePlain(AtomicInt):
    __slots__ = ("__x",)


class PrivateGauge(BoundedAtomicInt):
    __slots__ = ("__x",)


class OpenPlain(PrivatePlain):
    # No __slots__: instances get a __dict__, and the inherited ("__x",) lists nothing here.
    def __x(self) -> int:
        return self.get()

    def read(self) -> int:
        return self.__x()


class OpenGauge(PrivateGauge):
    def __x(self) -> int:
        return self.get()

    def read(self) -> int:
        return self.__x()


@pytest.mark.parametrize("open_class", [OpenPlain, OpenGauge])
@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_an_inherited_slots_list_adds_no_attribute_to_a_copy(clone: Clone, open_class: Any) -> None:
    original = open_class(1, maximum=10) if open_class is OpenGauge else open_class(1)
    private = "_PrivateGauge__x" if open_class is OpenGauge else "_PrivatePlain__x"
    setattr(original, private, "kept")
    twin = clone(original)
    twin.set(9)
    assert (twin.read(), original.read(), dict(vars(twin))) == (9, 1, {})
    assert getattr(twin, private) == "kept"
