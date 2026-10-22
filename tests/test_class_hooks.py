"""Copies keep the slots of classes that decorators and class hooks rebuild or wrap."""

from __future__ import annotations

import copy
import dataclasses
from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt

from .test_copy_slots import CLONE_IDS, CLONES, Clone


@dataclasses.dataclass(slots=True, init=False, eq=False)
class Point(AtomicInt):
    # dataclass(slots=True) makes a new class from a copy of this one's namespace.
    tag: str = ""


@dataclasses.dataclass(slots=True, init=False, eq=False)
class Reading(BoundedAtomicInt):
    tag: str = ""


class Draft(AtomicInt):
    pass


# The same rebuild by hand, as class decorators commonly do it.
_namespace = {k: v for k, v in vars(Draft).items() if k not in ("__dict__", "__weakref__")}
Rebuilt: Any = type("Rebuilt", Draft.__bases__, {**_namespace, "__slots__": ("tag",)})


def _wrap(cls: type, name: str) -> None:
    raw = vars(cls)[name]
    setattr(cls, name, property(lambda s: raw.__get__(s, type(s)), lambda s, v: raw.__set__(s, v)))


class Validating(AtomicInt):
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        # A common order: wrap the new slots first, then let the bases run their hooks.
        listed = vars(cls).get("__slots__", ())
        for name in (listed,) if isinstance(listed, str) else listed:
            private = name.startswith("__")
            _wrap(cls, f"_{cls.__name__.lstrip('_')}{name}" if private else name)
        super().__init_subclass__(**kwargs)


class Checked(Validating):
    __slots__ = ("tag",)


class Private(Validating):
    __slots__ = ["__tag"]


class Documented(Validating):
    __slots__ = {"tag": "a slot with a docstring"}


class _Hidden(Validating):  # Python strips the class name's leading underscores to mangle
    __slots__ = "__tag"


class Quiet(AtomicInt):
    __slots__ = ("tag",)

    def __init_subclass__(cls) -> None:
        pass  # no super() call: its subclasses are made without the base's class hook


class QuietChild(Quiet):
    __slots__ = ("extra",)  # a slot of its own, on a class no hook saw


class QuietGrand(QuietChild):  # that slot one level up
    __slots__ = ()


class QuietOwner(Quiet):
    __slots__ = ("own",)


class QuietHeir(QuietOwner):  # only the heir is copied: no names were kept for its base
    __slots__ = ()


class Clash(AtomicInt):
    # A slot with a name the library could pick for its own bookkeeping.
    __slots__ = ("_atomicint_slot_names", "tag")


class Shadow(AtomicInt):
    __slots__ = ("tag",)
    _atomicint_slot_names = ("nothing",)  # the same name as a class attribute


CASES: list[tuple[type[AtomicInt], str]] = [
    (Point, "tag"),
    (Reading, "tag"),
    (Rebuilt, "tag"),
    (Checked, "tag"),
    (Private, "_Private__tag"),
    (Documented, "tag"),
    (_Hidden, "_Hidden__tag"),
    (QuietChild, "extra"),
    (QuietGrand, "extra"),
    (QuietGrand, "tag"),
    (QuietHeir, "own"),
    (Clash, "tag"),
    (Clash, "_atomicint_slot_names"),
    (Shadow, "tag"),
]


@pytest.mark.parametrize(
    ("cls", "name"), CASES, ids=[f"{cls.__name__}.{name}" for cls, name in CASES]
)
@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_a_rebuilt_or_wrapped_slot_is_kept(clone: Clone, cls: type[AtomicInt], name: str) -> None:
    original = cls(3)
    setattr(original, name, "blue")
    twin = clone(original)
    assert (type(twin), getattr(twin, name, "<missing>"), twin.get()) == (cls, "blue", 3)
    assert twin.increment() == 4
    assert original.get() == 3


def test_under_a_base_that_skipped_the_hook_the_names_are_kept_from_the_first_copy() -> None:
    late: Any = type("Late", (Quiet,), {"__slots__": ("extra",)})
    original = late(3)
    original.extra = "red"
    assert copy.copy(original).extra == "red"
    _wrap(late, "extra")  # after the first copy, the names no longer come from the class
    assert getattr(copy.copy(original), "extra", "<missing>") == "red"


def test_a_subclass_namespace_gets_nothing_added() -> None:
    class Plain(AtomicInt):
        __slots__ = ("tag",)

    class Bare:
        __slots__ = ("tag",)

    assert sorted(vars(Plain)) == sorted(vars(Bare))


registry: list[str] = []


class Registered:
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        registry.append(cls.__name__)


@pytest.mark.parametrize("base", [AtomicInt, BoundedAtomicInt])
def test_a_mixin_class_hook_after_the_counter_still_runs(base: type[AtomicInt]) -> None:
    plugin = type("Plugin", (base, Registered), {"__slots__": ("tag",)})
    assert registry[-1:] == ["Plugin"]
    counter = plugin(3)
    counter.tag = "blue"
    assert copy.copy(counter).tag == "blue"


@pytest.mark.parametrize("base", [AtomicInt, BoundedAtomicInt])
def test_an_unknown_class_keyword_still_raises(base: type[AtomicInt]) -> None:
    with pytest.raises(TypeError, match="keyword"):
        type("Keyed", (base,), {"__slots__": ()}, colour="blue")
