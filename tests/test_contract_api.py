"""The complete promise of every public name: signatures, members, types and errors."""

from __future__ import annotations

import inspect
import typing
from typing import Any

import pytest

import atomicint
from atomicint import AtomicInt, BoundedAtomicInt, Overflow

SIGNATURES = {
    "__init__": "(self, value: 'SupportsIndex' = 0) -> 'None'",
    "get": "(self) -> 'int'",
    "set": "(self, value: 'SupportsIndex') -> 'None'",
    "add": "(self, amount: 'SupportsIndex') -> 'int'",
    "get_and_add": "(self, amount: 'SupportsIndex') -> 'int'",
    "increment": "(self) -> 'int'",
    "decrement": "(self) -> 'int'",
    "get_and_set": "(self, value: 'SupportsIndex') -> 'int'",
    "compare_and_set": "(self, expect: 'SupportsIndex', new: 'SupportsIndex') -> 'bool'",
    "compare_and_exchange": "(self, expect: 'SupportsIndex', new: 'SupportsIndex') -> 'int'",
    "update": "(self, function: 'Callable[[int], SupportsIndex]') -> 'int'",
    "get_and_update": "(self, function: 'Callable[[int], SupportsIndex]') -> 'int'",
}
BOUNDED_INIT = (
    "(self, value: 'SupportsIndex' = 0, *, minimum: 'SupportsIndex | None' = None, "
    "maximum: 'SupportsIndex | None' = None, overflow: 'Overflow' = 'raise') -> 'None'"
)
PROPERTIES = {"minimum", "maximum", "overflow"}
# Typed as Any: these are the wrong types the checks below are about.
FLOAT: Any = 1.5
TEXT: Any = "1"


def _public(cls: type) -> set[str]:
    return {name for name in dir(cls) if not name.startswith("_")}


@pytest.mark.parametrize("name", sorted(SIGNATURES))
def test_atomic_int_signatures_are_pinned(name: str) -> None:
    assert str(inspect.signature(getattr(AtomicInt, name))) == SIGNATURES[name]


def test_the_bounded_constructor_is_pinned_and_inherits_every_operation() -> None:
    assert str(inspect.signature(BoundedAtomicInt.__init__)) == BOUNDED_INIT
    for name in SIGNATURES:
        if name != "__init__":
            assert getattr(BoundedAtomicInt, name) is getattr(AtomicInt, name), name


def test_the_public_members_are_exactly_the_documented_ones() -> None:
    methods = set(SIGNATURES) - {"__init__"}
    assert _public(AtomicInt) == methods
    assert _public(BoundedAtomicInt) == methods | PROPERTIES
    for name in PROPERTIES:
        assert isinstance(vars(BoundedAtomicInt)[name], property)
        assert vars(BoundedAtomicInt)[name].fset is None, name


def test_the_overflow_type_lists_the_three_policies() -> None:
    assert typing.get_origin(Overflow) is typing.Literal
    assert typing.get_args(Overflow) == ("raise", "saturate", "wrap")


def test_the_classes_belong_to_the_package_and_use_slots() -> None:
    for cls in (AtomicInt, BoundedAtomicInt):
        assert cls.__module__ == "atomicint"
        assert "__slots__" in vars(cls)
        with pytest.raises(AttributeError):
            cls().anything = 1  # type: ignore[attr-defined]
    assert issubclass(BoundedAtomicInt, AtomicInt)


def test_every_public_name_and_member_has_a_runnable_example() -> None:
    assert ">>> " in (atomicint.__doc__ or "")
    for cls in (AtomicInt, BoundedAtomicInt):
        assert ">>> " in (inspect.getdoc(cls) or ""), cls
    members = [getattr(AtomicInt, name) for name in SIGNATURES if name != "__init__"]
    members += [vars(BoundedAtomicInt)[name] for name in PROPERTIES]
    for member in members:
        assert ">>> " in (inspect.getdoc(member) or ""), member


def test_counters_are_always_truthy_and_compare_by_identity() -> None:
    zero = AtomicInt(0)
    assert bool(zero) is True
    assert zero == zero and zero != AtomicInt(0)
    assert hash(zero) == object.__hash__(zero)


@pytest.mark.parametrize(
    ("call", "error"),
    [
        (lambda: AtomicInt(FLOAT), TypeError),
        (lambda: AtomicInt().add(TEXT), TypeError),
        (lambda: AtomicInt().update(lambda v: FLOAT), TypeError),
        (lambda: BoundedAtomicInt(minimum=2, maximum=1), ValueError),
        (lambda: BoundedAtomicInt(overflow=TEXT), ValueError),
        (lambda: BoundedAtomicInt(overflow="wrap", minimum=0), ValueError),
        (lambda: BoundedAtomicInt(5, maximum=4), OverflowError),
        (lambda: BoundedAtomicInt(minimum=FLOAT), TypeError),
    ],
)
def test_each_failure_raises_its_documented_builtin_error(call: Any, error: type) -> None:
    with pytest.raises(error) as caught:
        call()
    assert type(caught.value) is error
