"""Seeded random programs against a plain model, and hostile inputs.

The model is written by hand from the documented rules (README and GUIDE): a plain int
and the overflow policy table. Every operation, result, error type and the value left
behind must match it, on random ranges from one value wide to hundreds of bits, with
wrong-typed inputs mixed in.
"""

from __future__ import annotations

import copy
import pickle
import random
import threading
from collections.abc import Callable
from fractions import Fraction
from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt

BAD: list[Any] = [1.5, "3", True, None, Fraction(1, 2), b"1", [1]]
CLONES: list[Callable[[Any], Any]] = [
    copy.copy,
    copy.deepcopy,
    lambda c: pickle.loads(pickle.dumps(c)),
]
FUNCTIONS = [lambda v: v + 1, lambda v: -v, lambda v: v * 3, lambda v: v // 2, lambda v: 0]


class Model:
    def __init__(self, low: int | None, high: int | None, policy: str) -> None:
        self.low, self.high, self.policy, self.value = low, high, policy, 0

    def fit(self, value: int) -> int:
        low, high = self.low, self.high
        if (low is None or value >= low) and (high is None or value <= high):
            return value
        if self.policy == "raise":
            raise OverflowError
        if self.policy == "saturate":
            return low if low is not None and value < low else high  # type: ignore[return-value]
        assert low is not None and high is not None
        return (value - low) % (high - low + 1) + low

    def run(self, name: str, args: tuple[Any, ...]) -> Any:
        if any(type(a) is not int for a in args if not callable(a)):
            raise TypeError
        v = self.value
        if name in ("update", "get_and_update"):
            new = args[0](v)
            if type(new) is not int:
                raise TypeError
            self.value = self.fit(new)
            return self.value if name == "update" else v
        steps = {
            "get": (v, v),
            "set": (None, args[0] if args else 0),
            "add": (None, v + (args[0] if args else 0)),
            "get_and_add": (v, v + (args[0] if args else 0)),
            "increment": (None, v + 1),
            "decrement": (None, v - 1),
            "get_and_set": (v, args[0] if args else 0),
        }
        if name in steps:
            result, new = steps[name]
            self.value = self.fit(new)
            return self.value if result is None and name != "set" else result
        expect, new = args
        if v == expect:
            self.value = self.fit(new)
        return (v == expect) if name == "compare_and_set" else v


def _config(rng: random.Random) -> tuple[int | None, int | None, str]:
    size = rng.choice([1, 8, 64, 300])
    first = rng.randint(-(2**size), 2**size)
    low: int | None = first
    high: int | None = first + rng.choice([0, 1, rng.randint(0, 2**size)])
    policy = rng.choice(["raise", "saturate", "wrap"])
    if policy != "wrap":
        low, high = rng.choice([low, None]), rng.choice([high, None])
    return low, high, policy


def _value(rng: random.Random, model: Model) -> Any:
    if rng.random() < 0.05:
        return rng.choice(BAD)
    near = [b for b in (model.low, model.high, model.value) if b is not None]
    base = rng.choice(near or [0])
    return base + rng.choice([-1, 0, 1, rng.randint(-(2**70), 2**70)])


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_random_programs_match_the_model(seed: int) -> None:
    rng = random.Random(seed)
    names = ["get", "set", "add", "get_and_add", "increment", "decrement", "get_and_set"]
    names += ["compare_and_set", "compare_and_exchange", "update", "get_and_update"]
    checked = 0
    for _ in range(1000):
        low, high, policy = _config(rng)
        model = Model(low, high, policy)
        try:
            model.value = model.fit(0)
        except OverflowError:
            model.value = model.fit(low if low is not None else high)  # type: ignore[arg-type]
        counter = BoundedAtomicInt(model.value, minimum=low, maximum=high, overflow=policy)  # type: ignore[arg-type]
        for _ in range(60):
            name = rng.choice(names)
            if name in ("get", "increment", "decrement"):
                args: tuple[Any, ...] = ()
            elif name in ("update", "get_and_update"):
                args = (rng.choice([*FUNCTIONS, lambda v: 0.5]),)
            elif name.startswith("compare"):
                args = (rng.choice([model.value, _value(rng, model)]), _value(rng, model))
            else:
                args = (_value(rng, model),)
            before = model.value
            try:
                expected: Any = model.run(name, args)
            except (OverflowError, TypeError) as error:
                with pytest.raises(type(error)):
                    getattr(counter, name)(*args)
                model.value = before
            else:
                assert getattr(counter, name)(*args) == expected, (name, args)
            assert counter.get() == model.value, (name, args, policy, low, high)
        twin = rng.choice(CLONES)
        assert repr(twin(counter)) == repr(counter)
        checked += 1
    assert checked == 1000


def test_an_index_hook_may_use_the_counter_because_it_runs_before_the_lock() -> None:
    counter = AtomicInt(1)

    class Sneaky:
        def __index__(self) -> int:
            counter.set(100)
            return 5

    done: list[int] = []
    worker = threading.Thread(target=lambda: done.append(counter.add(Sneaky())), daemon=True)
    worker.start()
    worker.join(timeout=30)
    assert done == [105], "deadlock: the input was converted while holding the lock"


def test_an_index_hook_that_raises_leaves_the_value_untouched() -> None:
    class Broken:
        def __index__(self) -> int:
            raise ZeroDivisionError("hook")

    counter = BoundedAtomicInt(3, maximum=10)
    for call in (
        counter.set,
        counter.add,
        counter.get_and_set,
        lambda x: counter.update(lambda v: x),
    ):
        with pytest.raises(ZeroDivisionError):
            call(Broken())
    assert counter.get() == 3
