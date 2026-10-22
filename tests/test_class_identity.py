"""Subclasses whose metaclass redefines equality and hashing are told apart by identity."""

from __future__ import annotations

import copy
import gc
import os
import subprocess
import sys
import weakref
from typing import Any

import pytest

import atomicint
from atomicint import AtomicInt, BoundedAtomicInt, _state

from .test_copy_slots import CLONE_IDS, CLONES, Clone


class Quiet(AtomicInt):
    __slots__ = ()

    def __init_subclass__(cls) -> None:
        pass  # no super() call: names of its subclasses are kept at their first copy


class Unhashable(type):
    # Defining __eq__ alone sets __hash__ to None, so these classes cannot be dict keys.
    def __eq__(cls, other: object) -> bool:
        return cls is other


class ByName(type):
    # Classes equal when their names are, with a hash to match.
    def __eq__(cls, other: object) -> bool:
        return isinstance(other, type) and cls.__name__ == other.__name__

    def __hash__(cls) -> int:
        return hash(cls.__name__)


def _make(meta: type, name: str, bases: tuple[type, ...], slots: Any) -> Any:
    # __qualname__ differs from __name__, so a pickle finds each class under its own name.
    qualname = f"{name}_{len(_made)}"
    made = meta(name, bases, {"__slots__": slots, "__qualname__": qualname})
    _made[qualname] = made
    globals()[qualname] = made
    return made


_made: dict[str, Any] = {}

First = _make(ByName, "Same", (AtomicInt,), ("a",))
Holder = type("Holder", (AtomicInt,), {"__slots__": ("z",)})
Middle = _make(ByName, "Middle", (Holder,), ())
Second = _make(ByName, "Same", (Middle,), ())  # equal to First, with a slot one level up
Gauge = _make(ByName, "Gauge", (BoundedAtomicInt,), ("a",))
Streamed = _make(ByName, "Gauge", (BoundedAtomicInt,), iter(["d"]))  # equal to Gauge

CASES: list[tuple[Any, str]] = [
    (First, "a"),
    (Second, "z"),
    (Gauge, "a"),
    (Streamed, "d"),
]


@pytest.mark.parametrize(
    ("cls", "name"), CASES, ids=[f"{cls.__qualname__}.{name}" for cls, name in CASES]
)
@pytest.mark.parametrize("clone", CLONES, ids=CLONE_IDS)
def test_classes_equal_by_name_keep_their_own_slots(clone: Clone, cls: Any, name: str) -> None:
    original = cls(3)
    setattr(original, name, "blue")
    twin = clone(original)
    assert (type(twin), getattr(twin, name, "<missing>"), twin.get()) == (cls, "blue", 3)
    assert twin.increment() == 4


@pytest.mark.parametrize("base", [AtomicInt, BoundedAtomicInt])
def test_a_subclass_of_an_unhashable_metaclass_can_be_made_and_used(base: type) -> None:
    cls: Any = Unhashable("Odd", (base,), {"__slots__": ("tag",)})
    counter = cls(3)
    counter.tag = "blue"
    assert (counter.increment(), counter.get_and_add(2), counter.compare_and_set(6, 1)) == (
        4,
        4,
        True,
    )
    # The standard copy module looks the class up in its own tables, which an unhashable
    # class cannot enter; the state the counter hands to it is complete all the same.
    extra, slots = counter.__getstate__()
    assert (extra, slots["tag"], slots["_value"]) == (None, "blue", 1)
    grand: Any = Unhashable("Odder", (cls,), {"__slots__": ("more",)})
    late = grand(5)
    late.more = "red"
    late.tag = "green"
    extra, slots = late.__getstate__()
    assert (extra, slots["more"], slots["tag"], slots["_value"]) == (None, "red", "green", 5)


@pytest.mark.parametrize("base", [AtomicInt, BoundedAtomicInt, Quiet])
def test_a_class_is_freed_and_its_id_reused_safely(base: type) -> None:
    # Each class lives only for its turn of the loop, so CPython often hands a new class
    # the memory, and so the id, of one that died: it must still get its own names.
    alive = []
    gc.collect()
    kept = len(_state._NAMES)
    for turn in range(200):
        cls: Any = type("Passing", (base,), {"__slots__": (f"tag{turn}",)})
        counter = cls(turn)
        setattr(counter, f"tag{turn}", turn)
        twin = copy.copy(counter)
        assert (getattr(twin, f"tag{turn}", None), twin.get()) == (turn, turn)
        alive.append(weakref.ref(cls))
        del cls, counter, twin
        gc.collect()
    assert sum(ref() is not None for ref in alive) == 0
    assert len(_state._NAMES) <= kept  # nothing is left behind for the dead classes


_AT_EXIT = """
import atomicint
made = [type(f"K{i}", (atomicint.AtomicInt,), {"__slots__": ("t",)}) for i in range(50)]
class Cycle:
    pass
cycle = Cycle()
cycle.me, cycle.made = cycle, made
atomicint._held_by_a_cycle = cycle
"""


def test_classes_alive_at_exit_leave_no_message() -> None:
    # Their weak references fire while the interpreter tears its modules down. The child
    # imports the same package as this test, from the source tree or an installed wheel.
    home = os.path.dirname(os.path.dirname(os.path.abspath(atomicint.__file__)))
    done = subprocess.run(
        [sys.executable, "-c", _AT_EXIT],
        capture_output=True,
        text=True,
        timeout=120,
        env=dict(os.environ, PYTHONPATH=home),
    )
    assert (done.returncode, done.stdout, done.stderr) == (0, "", "")
