"""A metaclass cannot change what the counter reads from a class: name, MRO or namespace.

Each metaclass below answers for one attribute Python keeps on every class. The
interpreter itself never asks the metaclass for these, so neither may the counter: its
messages, repr, copies and pickles must come out as they do for a plain class.
"""

from __future__ import annotations

import operator
from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt

from .test_copy_slots import CLONE_IDS, CLONES, Clone


def _raise(cls: type) -> Any:
    raise RuntimeError("read through the metaclass")


NAMES: dict[str, Any] = {
    "raising": _raise,
    "a number": lambda cls: 12345,
    "injected text": lambda cls: "Odd, and more text of its own",
    "a huge list": lambda cls: [0] * 1000,
}
MRO_ANSWERS: dict[str, Any] = {
    "hiding the bases": lambda cls: (cls, object),
    "not iterable": lambda cls: 5,
    "raising": _raise,
}
# Not one that raises: the doctest collector reads the __dict__ of every class it finds.
NAMESPACES: dict[str, Any] = {
    "empty": lambda cls: {},
    "a fake slot": lambda cls: {"__slots__": ("fake",), "fake": None},
}


def _meta(attribute: str, answer: Any) -> Any:
    return type("Hostile", (type,), {attribute: property(answer)})


@pytest.mark.parametrize("answer", list(NAMES))
def test_a_metaclass_name_cannot_change_an_input_error(answer: str) -> None:
    meta = _meta("__name__", NAMES[answer])
    odd = meta("Odd", (), {})
    with pytest.raises(TypeError, match=r"^value must be an integer, not Odd$"):
        AtomicInt(odd())
    with pytest.raises(TypeError, match=r"^overflow must be a plain str, not P$"):
        BoundedAtomicInt(overflow=meta("P", (str,), {})("raise"))
    hook = type("Hook", (), {"__index__": lambda self: odd()})
    with pytest.raises(
        TypeError, match=r"^value must be an integer, but its __index__ returned Odd$"
    ):
        AtomicInt(hook())
    with pytest.raises(TypeError, match=r"^update result must be an integer, not Odd$"):
        AtomicInt(1).update(lambda value: odd())


def _module_level(meta: Any, name: str, bases: tuple[type, ...], slots: Any) -> Any:
    # __qualname__ names it here, so a pickle finds it by name.
    qualname = f"{name}_{len(MADE)}"
    made = meta(name, bases, {"__slots__": slots, "__qualname__": qualname})
    MADE[qualname] = made
    globals()[qualname] = made
    return made


MADE: dict[str, Any] = {}
NAMED = {
    answer: (
        _module_level(_meta("__name__", NAMES[answer]), "Plain", (AtomicInt,), ("tag",)),
        _module_level(_meta("__name__", NAMES[answer]), "Gauge", (BoundedAtomicInt,), ("tag",)),
    )
    for answer in NAMES
}


@pytest.mark.parametrize("answer", list(NAMES))
@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_a_subclass_under_a_metaclass_name_is_made_shown_and_copied(
    clone: Clone, answer: str
) -> None:
    plain_class, gauge_class = NAMED[answer]
    plain, gauge = plain_class(3), gauge_class(5, minimum=0, maximum=9, overflow="wrap")
    plain.tag, gauge.tag = "blue", "red"
    assert repr(plain) == "Plain(3)"
    assert repr(gauge) == "Gauge(5, minimum=0, maximum=9, overflow='wrap')"
    twin, other = clone(plain), clone(gauge)
    assert (twin.tag, twin.increment(), other.tag, other.add(7)) == ("blue", 4, "red", 2)


_NAMESPACE = vars(type)["__dict__"]
_NAME = vars(type)["__name__"]


class Wrapping(BoundedAtomicInt):
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        # Wraps the new slots before the counter's own hook runs, so the counter must find
        # them in __slots__; this hook reads the class as Python keeps it.
        namespace, stem = _NAMESPACE.__get__(cls), _NAME.__get__(cls).lstrip("_")
        for name in namespace.get("__slots__", ()):
            name = f"_{stem}{name}" if name.startswith("__") else name
            raw = namespace[name]
            type.__setattr__(cls, name, property(raw.__get__, raw.__set__))
        super().__init_subclass__(**kwargs)


def _hierarchies(attribute: str, answers: dict[str, Any]) -> dict[str, Any]:
    made = {}
    for answer in answers:
        meta = _meta(attribute, answers[answer])
        # Not wrapped, and listed by an iterator: only the slots Python made can show it.
        base = _module_level(meta, "Base", (BoundedAtomicInt,), iter(["base"]))
        holder = _module_level(meta, "Holder", (base, Wrapping), ("tag", "__pv"))
        made[f"{attribute} {answer}"] = _module_level(meta, "Leaf", (holder,), ("leaf",))
    return made


HIERARCHIES = {
    **_hierarchies("__name__", NAMES),
    **_hierarchies("__mro__", MRO_ANSWERS),
    **_hierarchies("__dict__", NAMESPACES),
}


@pytest.mark.parametrize("label", list(HIERARCHIES))
@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_a_metaclass_name_mro_or_namespace_cannot_drop_a_slot(clone: Clone, label: str) -> None:
    original = HIERARCHIES[label](5, minimum=0, maximum=9, overflow="wrap")
    original.base, original.tag, original._Holder__pv, original.leaf = "a", "b", "c", "d"
    twin = clone(original)
    assert (twin.minimum, twin.maximum, twin.overflow) == (0, 9, "wrap")
    assert (twin.base, twin.tag, twin._Holder__pv, twin.leaf) == ("a", "b", "c", "d")
    assert (twin.add(7), original.get()) == (2, 5)


def test_an_index_hook_is_bound_as_python_binds_it_whatever_its_metaclass_says() -> None:
    # The hook's class has no __get__ of its own, so Python calls the hook as it is; a
    # __get__ its metaclass answers for is not the hook's.
    meta = _meta("__get__", lambda cls: lambda *args: lambda: 99)
    hook = meta("Hook", (), {"__call__": lambda self: 7})
    number = type("Number", (), {"__index__": hook()})
    assert operator.index(number()) == 7
    assert AtomicInt(number()).get() == 7
    assert BoundedAtomicInt(0, maximum=number()).maximum == 7
