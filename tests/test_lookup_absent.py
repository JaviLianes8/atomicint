"""What a class holds under a name, and a class dict that fails to answer, as Python sees it.

A class that holds any object under ``__index__`` (or a hook's class under ``__get__``)
stops the search there, whatever that object is, and a class dictionary whose key fails
to compare ends the search with nothing found, as Python's own type lookup does. Each
case is checked against ``operator.index``.
"""

from __future__ import annotations

from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt, _coerce

from .test_index_lookup import _refused_everywhere, _taken_everywhere

# Any plain object, including any the library itself keeps, held under the name.
HELD = [object(), *(item for item in vars(_coerce).values() if type(item) is object)]
NOT_CALLABLE = r"^'object' object is not callable$"


class Five:
    def __index__(self) -> int:
        return 5


@pytest.mark.parametrize("held", HELD)
def test_an_object_held_under_index_hides_the_base_hook(held: object) -> None:
    _refused_everywhere(type("Shadow", (Five,), {"__index__": held})(), NOT_CALLABLE)
    later: Any = type("Later", (Five,), {})
    later.__index__ = held
    _refused_everywhere(later(), NOT_CALLABLE)


class Binds:
    def __get__(self, value: object, owner: type) -> Any:
        return lambda: 21

    def __call__(self) -> int:
        return 4


@pytest.mark.parametrize("held", HELD)
def test_an_object_held_under_get_on_the_hook_class_is_called(held: object) -> None:
    hook = type("Hook", (Binds,), {"__get__": held})()
    _refused_everywhere(type("Number", (), {"__index__": hook})(), NOT_CALLABLE)


class Bad(str):
    """A class dict key that hashes like ``target`` and fails when compared."""

    target = ""
    unanswerable = False

    def __hash__(self) -> int:
        return hash(self.target)

    def __eq__(self, other: object) -> Any:
        if self.unanswerable:
            return Unanswerable()
        raise RuntimeError("compare")


class Unanswerable:
    def __bool__(self) -> bool:
        raise ValueError("no answer")


def _bad(target: str, unanswerable: bool = False) -> Bad:
    key = Bad("key")
    key.target, key.unanswerable = target, unanswerable
    return key


@pytest.mark.parametrize("unanswerable", [False, True], ids=["raises", "unanswerable"])
def test_a_class_dict_that_fails_to_answer_has_no_hook(unanswerable: bool) -> None:
    lone = type("Lone", (), {_bad("__index__", unanswerable): 1})
    _refused_everywhere(lone(), r"must be an integer, not Lone$")
    # Python stops at the class that failed, so a base's hook is not reached.
    child = type("Child", (Five,), {_bad("__index__", unanswerable): 1})
    _refused_everywhere(child(), r"must be an integer, not Child$")


def test_a_hook_class_that_fails_to_answer_for_get_is_called_unbound() -> None:
    hook = type("Hook", (Binds,), {_bad("__get__"): 1})()
    _taken_everywhere(type("Number", (), {"__index__": hook})(), 4)


class Agreeable:
    """A hook object that claims to equal everything, or refuses every comparison."""

    def __init__(self, answer: int, raising: bool) -> None:
        self.answer, self.raising = answer, raising

    def __call__(self, *args: Any) -> Any:
        return self.answer if not args else (lambda: self.answer)

    def __eq__(self, other: object) -> bool:
        if self.raising:
            raise RuntimeError("compare")
        return True

    def __ne__(self, other: object) -> bool:
        if self.raising:
            raise RuntimeError("compare")
        return False

    __hash__ = object.__hash__


@pytest.mark.parametrize("raising", [False, True], ids=["equal", "raising"])
def test_a_found_hook_is_judged_by_identity_never_by_equality(raising: bool) -> None:
    _taken_everywhere(type("Number", (), {"__index__": Agreeable(6, raising)})(), 6)
    binder = type("Hook", (), {"__get__": Agreeable(8, raising), "__call__": lambda s: 0})
    _taken_everywhere(type("Number", (), {"__index__": binder()})(), 8)


def test_a_failing_class_dict_leaves_the_counter_and_bounds_untouched() -> None:
    counter = AtomicInt(1)
    lone = type("Lone", (), {_bad("__index__"): 1})
    with pytest.raises(TypeError):
        counter.compare_and_set(1, lone())
    with pytest.raises(TypeError):
        BoundedAtomicInt(0, minimum=lone())
    assert counter.get() == 1
