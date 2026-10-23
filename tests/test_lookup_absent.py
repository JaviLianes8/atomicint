"""What a class holds under a name, and a class dict that fails to answer, as Python sees it.

A class that holds any object under ``__index__`` (or a hook's class under ``__get__``)
stops the search there, whatever that object is, and a class dictionary whose key fails
to compare (raises an ``Exception``) ends the search with nothing found, as Python's own
type lookup does. Each case is checked against ``operator.index``. An interrupt or exit
raised by that comparison reaches the caller instead, with the counter untouched.
"""

from __future__ import annotations

from collections.abc import Callable
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
    """A class dict key that hashes like ``target`` and, once armed, fails when compared."""

    target = ""
    unanswerable = False
    armed = True
    error: type[BaseException] = RuntimeError

    def __hash__(self) -> int:
        return hash(self.target)

    def __eq__(self, other: object) -> Any:
        if not self.armed:
            return False
        if self.unanswerable:
            return Unanswerable()
        raise self.error("compare")


class Unanswerable:
    def __bool__(self) -> bool:
        raise ValueError("no answer")


def _bad(target: str, unanswerable: bool = False, error: type[BaseException] = RuntimeError) -> Bad:
    key = Bad("key")
    key.target, key.unanswerable, key.error = target, unanswerable, error
    return key


Custom = type("Custom", (Exception,), {})
# Each way a comparison can fail: any Exception, a KeyError (which a read with [] would
# take for "absent"), and an answer whose truth value raises.
FAILURES = {
    "raises": (False, RuntimeError),
    "key error": (False, KeyError),
    "custom": (False, Custom),
    "unanswerable": (True, RuntimeError),
}


@pytest.mark.parametrize("failure", list(FAILURES))
def test_a_class_dict_that_fails_to_answer_has_no_hook(failure: str) -> None:
    lone = type("Lone", (), {_bad("__index__", *FAILURES[failure]): 1})
    _refused_everywhere(lone(), r"must be an integer, not Lone$")
    # Python stops at the class that failed, so a base's hook is not reached.
    child = type("Child", (Five,), {_bad("__index__", *FAILURES[failure]): 1})
    _refused_everywhere(child(), r"must be an integer, not Child$")


Halt = type("Halt", (BaseException,), {})


@pytest.mark.parametrize(
    "error", [KeyboardInterrupt, SystemExit, GeneratorExit, Halt], ids=lambda e: e.__name__
)
def test_an_interrupt_or_exit_from_a_failing_key_reaches_the_caller(
    error: type[BaseException],
) -> None:
    # Python's lookup drops it; the counter lets it through, so Ctrl-C is never lost.
    counter = AtomicInt(1)
    calls: list[Callable[[Any], object]] = [
        AtomicInt,
        counter.add,
        counter.set,
        lambda value: counter.compare_and_set(1, value),
        lambda value: BoundedAtomicInt(0, minimum=value),
    ]
    for base in [(), (Five,)]:
        value = type("Number", base, {_bad("__index__", error=error): 1})()
        for call in calls:
            with pytest.raises(error, match=r"^compare$"):
                call(value)
    assert counter.get() == 1


def test_a_failing_key_stored_after_the_hook_does_not_hide_it() -> None:
    # The hook is found by identity before the failing key is ever compared.
    index_key, get_key = _bad("__index__"), _bad("__get__")
    index_key.armed = get_key.armed = False
    number = type("Number", (), {"__index__": lambda self: 7, index_key: 1})
    hook = type("Hook", (), {"__get__": Binds.__get__, "__call__": Binds.__call__, get_key: 1})
    bound = type("Bound", (), {"__index__": hook()})
    index_key.armed = get_key.armed = True
    _taken_everywhere(number(), 7)
    _taken_everywhere(bound(), 21)


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


class Falsy(Agreeable):
    """A hook object that is false in a truth test, or whose truth test raises."""

    def __bool__(self) -> bool:
        if self.raising:
            raise RuntimeError("truth")
        return False


@pytest.mark.parametrize("raising", [False, True], ids=["equal", "raising"])
@pytest.mark.parametrize("kind", [Agreeable, Falsy])
def test_a_found_hook_is_judged_by_identity_never_by_equality_or_truth(
    kind: type[Agreeable], raising: bool
) -> None:
    _taken_everywhere(type("Number", (), {"__index__": kind(6, raising)})(), 6)
    binder = type("Hook", (), {"__get__": kind(8, raising), "__call__": lambda s: 0})
    _taken_everywhere(type("Number", (), {"__index__": binder()})(), 8)


def test_a_failing_class_dict_leaves_the_counter_and_bounds_untouched() -> None:
    counter = AtomicInt(1)
    lone = type("Lone", (), {_bad("__index__"): 1})
    with pytest.raises(TypeError):
        counter.compare_and_set(1, lone())
    with pytest.raises(TypeError):
        BoundedAtomicInt(0, minimum=lone())
    assert counter.get() == 1
