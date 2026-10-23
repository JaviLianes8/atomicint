"""The complete promise of every public name: signatures, members, types and errors."""

from __future__ import annotations

import doctest
import inspect
import operator
import pydoc
import typing
from pathlib import Path
from typing import Any

import pytest

import atomicint
from atomicint import AtomicInt, BoundedAtomicInt, Overflow, _atomic, _bounded

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
NOTHING: Any = None


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


def test_the_classes_use_slots_and_name_the_module_that_defines_them() -> None:
    # Pickles name these paths, so they stay importable for the whole 1.x series.
    for cls, module in ((AtomicInt, _atomic), (BoundedAtomicInt, _bounded)):
        assert cls.__module__ == module.__name__
        assert getattr(module, cls.__name__) is cls is getattr(atomicint, cls.__name__)
        assert "__slots__" in vars(cls)
        with pytest.raises(AttributeError):
            cls().anything = 1  # type: ignore[attr-defined]
    assert issubclass(BoundedAtomicInt, AtomicInt)


def test_tools_find_the_source_of_every_class_method_and_example() -> None:
    # What IPython's ??, debuggers, Sphinx viewcode and doctest failure reports rely on.
    for cls, module in ((AtomicInt, _atomic), (BoundedAtomicInt, _bounded)):
        assert Path(inspect.getsourcefile(cls) or "") == Path(module.__file__ or "")
        assert inspect.getsource(cls).startswith(f"class {cls.__name__}(")
        tests = {t.name: t for t in doctest.DocTestFinder().find(module)}
        example = tests[f"{module.__name__}.{cls.__name__}"]
        assert (Path(example.filename or ""), example.lineno) == (
            Path(module.__file__ or ""),
            inspect.getsourcelines(cls)[1],
        )
    examples = {t.name: t.lineno for t in doctest.DocTestFinder().find(_atomic)}
    for name in SIGNATURES:
        assert inspect.getsource(getattr(AtomicInt, name)).lstrip().startswith(f"def {name}(")
        if name != "__init__":
            assert examples[f"atomicint._atomic.AtomicInt.{name}"], name


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
        (lambda: BoundedAtomicInt(overflow=NOTHING), TypeError),
        (lambda: BoundedAtomicInt(overflow=FLOAT), TypeError),
        (lambda: BoundedAtomicInt(overflow="wrap", minimum=0), ValueError),
        (lambda: BoundedAtomicInt(5, maximum=4), OverflowError),
        (lambda: BoundedAtomicInt(minimum=FLOAT), TypeError),
    ],
)
def test_each_failure_raises_its_documented_builtin_error(call: Any, error: type) -> None:
    with pytest.raises(error) as caught:
        call()
    assert type(caught.value) is error


@pytest.mark.parametrize("value", [-(2**200), -5, -1, 0, 1, 7, 2**200])
@pytest.mark.parametrize("cls", [AtomicInt, BoundedAtomicInt])
def test_int_and_index_give_the_current_value(cls: type[AtomicInt], value: int) -> None:
    counter = cls(value)
    for snapshot in (int(counter), operator.index(counter)):
        assert (snapshot, type(snapshot)) == (value, int)


def test_a_counter_indexes_a_sequence_from_either_end() -> None:
    items = [10, 20, 30]
    assert [items[AtomicInt(i)] for i in (-3, -1, 0, 2)] == [10, 30, 10, 30]
    assert items[AtomicInt(-2) : AtomicInt(3)] == [20, 30]


def test_overflow_has_its_own_docstring_with_a_runnable_example() -> None:
    doc = Overflow.__doc__ or ""
    assert ">>> " in doc
    assert all(policy in doc for policy in typing.get_args(Overflow))
    assert "saturate" in pydoc.render_doc(Overflow, renderer=pydoc.TextDoc())
    # Set on an alias of its own, never on the one typing shares with other code.
    assert typing.Literal["raise", "saturate", "wrap"].__doc__ != doc
    assert any(t.name.endswith("Overflow") for t in doctest.DocTestFinder().find(_bounded))
