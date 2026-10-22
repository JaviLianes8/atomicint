"""A copy never reads the class dictionary as it is now, and costs one pass over the slots."""

from __future__ import annotations

import copy
import functools
import itertools
import pickle
import sys
import threading
import time
from collections.abc import Callable, Iterator
from typing import Any

import pytest

from atomicint import AtomicInt


class Tagged(AtomicInt):
    __slots__ = ("tag",)
    tag: str


class Quiet(AtomicInt):
    __slots__ = ("tag",)
    tag: str

    def __init_subclass__(cls) -> None:
        pass  # no super() call: the copy of a subclass works its slot names out each time


class Unhooked(Quiet):
    __slots__ = ()


@pytest.fixture
def fast_switching() -> Iterator[None]:
    # Switch threads as often as possible, so a copy keeps meeting the class change.
    previous = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    try:
        yield
    finally:
        sys.setswitchinterval(previous)


@pytest.mark.usefixtures("fast_switching")
@pytest.mark.parametrize("cls", [Tagged, Unhooked])
@pytest.mark.parametrize("clone", [copy.copy, copy.deepcopy, pickle.dumps])
def test_a_copy_is_safe_while_another_thread_changes_the_class(
    clone: Callable[[Any], object], cls: type[Tagged | Quiet]
) -> None:
    counter = cls(1)
    counter.tag = "t"
    stop = threading.Event()
    errors: list[BaseException] = []
    lost: list[object] = []

    def change_the_class() -> None:
        for turn in itertools.count():
            if stop.is_set():
                return
            name = f"cache_{turn % 50}"
            setattr(cls, name, turn)
            delattr(cls, name)

    def copy_it() -> None:
        while not stop.is_set():
            try:
                twin = clone(counter)
                if isinstance(twin, bytes):
                    twin = pickle.loads(twin)
            except RuntimeError as error:
                errors.append(error)
                continue
            if getattr(twin, "tag", None) != "t":
                lost.append(twin)

    threads = [threading.Thread(target=change_the_class)]
    threads += [threading.Thread(target=copy_it) for _ in range(2)]
    for thread in threads:
        thread.start()
    time.sleep(1.0)
    stop.set()
    for thread in threads:
        thread.join()
    assert (errors[:1], len(lost)) == ([], 0)


def _fill(cls: type[Any], names: list[str]) -> Any:
    obj = cls(1) if issubclass(cls, AtomicInt) else cls()
    for name in names:
        setattr(obj, name, name)
    return obj


def _best(action: Callable[[], object], rounds: int = 5) -> float:
    times = []
    for _ in range(rounds):
        start = time.perf_counter()
        action()
        times.append(time.perf_counter() - start)
    return min(times)


def test_a_copy_costs_about_what_the_standard_copy_of_a_plain_class_costs() -> None:
    # Measured against copy.copy of a plain class with the same 8000 slots, which reads
    # each slot once. Code that looks every name up in a list is ~100 times slower here.
    names = [f"s{i}" for i in range(8000)]
    wide = _fill(type("Wide", (AtomicInt,), {"__slots__": tuple(names)}), names)
    plain = _fill(type("Plain", (), {"__slots__": tuple(names)}), names)
    assert copy.copy(wide).s7999 == "s7999"
    ratio = _best(lambda: copy.copy(wide)) / _best(lambda: copy.copy(plain))
    assert ratio < 10, f"a copy took {ratio:.1f} times the standard copy"


def test_the_first_copy_under_a_base_that_skipped_the_hook_costs_one_pass() -> None:
    # No class hook ran for these, so their names are worked out at the first copy.
    names = [f"s{i}" for i in range(8000)]
    plain = _fill(type("Plain", (), {"__slots__": tuple(names)}), names)
    firsts = []
    for _ in range(3):
        wide = _fill(type("WideQuiet", (Quiet,), {"__slots__": tuple(names)}), names)
        firsts.append(_best(functools.partial(copy.copy, wide), rounds=1))
    assert copy.copy(wide).s7999 == "s7999"
    ratio = min(firsts) / _best(lambda: copy.copy(plain))
    assert ratio < 10, f"a first copy took {ratio:.1f} times the standard copy"


def _chain(base: type, depth: int) -> type:
    for level in range(depth):
        base = type(f"L{level}", (base,), {"__slots__": (f"s{level}",)})
    return base


def test_making_a_class_costs_about_what_python_takes_whatever_the_depth() -> None:
    # Each class's stored names already hold those of its bases: merging them all again
    # at every level made one class cost the square of the depth (20 times Python at 400).
    deep, plain = _chain(AtomicInt, 600), _chain(object, 600)

    def make(base: type) -> Callable[[], object]:
        return lambda: type("Next", (base,), {"__slots__": ("x",)})

    ratio = _best(make(deep), rounds=20) / _best(make(plain), rounds=20)
    assert ratio < 5, f"making a class took {ratio:.1f} times what Python takes"


def test_making_a_wide_class_costs_about_what_python_takes() -> None:
    names = tuple(f"s{i}" for i in range(8000))
    ratio = _best(lambda: type("Wide", (AtomicInt,), {"__slots__": names})) / _best(
        lambda: type("Plain", (), {"__slots__": names})
    )
    assert ratio < 10, f"making a wide class took {ratio:.1f} times what Python takes"
