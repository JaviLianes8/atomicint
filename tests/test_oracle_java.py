"""Results compared with the Java runtime, run live (scripts/oracle/AtomicOracle.java).

java.util.concurrent.atomic.AtomicLong answers for every AtomicInt operation, Math.clamp
for the saturate policy, and Java's narrowing conversions and 64-bit long addition for
the wrap policy. The tests skip when Java is not installed. Operations are drawn from
seeded generators, so every run is the same.
"""

from __future__ import annotations

import random
from collections.abc import Callable

import pytest

from atomicint import AtomicInt, BoundedAtomicInt

from ._oracle import edges, run_oracle

LONG = 2**63
FUNCTIONS: dict[str, Callable[[int], int]] = {
    "double": lambda v: v * 2,
    "negate": lambda v: -v,
    "plus7": lambda v: v + 7,
    "halve": lambda v: v // 2,
}
WIDTHS = {"wrap8": (-(2**7), 2**7 - 1), "wrap16": (-(2**15), 2**15 - 1)}
WIDTHS |= {"wrap32": (-(2**31), 2**31 - 1), "uwrap8": (0, 255), "uwrap16": (0, 2**16 - 1)}
WIDTHS |= {"uwrap32": (0, 2**32 - 1)}


def _atomic_commands(rng: random.Random, count: int) -> tuple[list[str], list[str]]:
    """Commands for the Java AtomicLong and what atomicint answers to each of them."""
    start = rng.randint(-1000, 1000)
    counter = AtomicInt(start)
    commands, answers = [f"new {start}"], [str(start)]
    for _ in range(count):
        value = counter.get()
        if abs(value) > 2**40:  # keep every Java result inside a long
            commands.append("set 3")
            counter.set(3)
            answers.append("3")
            continue
        amount = rng.randint(-(10**6), 10**6)
        expect = value if rng.random() < 0.5 else value + rng.randint(-2, 2)
        name = rng.choice(list(FUNCTIONS))
        command = rng.choice(JAVA_OPS)
        result = _apply(counter, command, amount, expect, name)
        command += {0: "", 1: f" {amount}", 2: f" {expect} {amount}", 3: f" {name}"}[
            JAVA_OPS_ARGS[command]
        ]
        commands.append(command)
        answers.append(str(result).lower() if isinstance(result, bool) else str(result))
    return commands, answers


JAVA_OPS_ARGS = {
    "get": 0,
    "set": 1,
    "addAndGet": 1,
    "getAndAdd": 1,
    "incrementAndGet": 0,
    "decrementAndGet": 0,
    "getAndSet": 1,
    "compareAndSet": 2,
    "compareAndExchange": 2,
    "updateAndGet": 3,
    "getAndUpdate": 3,
}
JAVA_OPS = list(JAVA_OPS_ARGS)


def _apply(counter: AtomicInt, command: str, amount: int, expect: int, name: str) -> object:
    if command == "get":
        return counter.get()
    if command == "set":
        counter.set(amount)
        return counter.get()
    calls: dict[str, Callable[[], object]] = {
        "addAndGet": lambda: counter.add(amount),
        "getAndAdd": lambda: counter.get_and_add(amount),
        "incrementAndGet": counter.increment,
        "decrementAndGet": counter.decrement,
        "getAndSet": lambda: counter.get_and_set(amount),
        "compareAndSet": lambda: counter.compare_and_set(expect, amount),
        "compareAndExchange": lambda: counter.compare_and_exchange(expect, amount),
        "updateAndGet": lambda: counter.update(FUNCTIONS[name]),
        "getAndUpdate": lambda: counter.get_and_update(FUNCTIONS[name]),
    }
    return calls[command]()


def _range_commands(rng: random.Random, count: int) -> tuple[list[str], list[str]]:
    """Commands for Math.clamp, the narrowing conversions and long addition, with answers."""
    commands: list[str] = []
    answers: list[int] = []
    for _ in range(count):
        low = rng.randint(-(2**61), 2**61)
        high = rng.choice([low, low + rng.randint(0, 9), rng.randint(low, 2**61)])
        start = rng.randint(low, high)
        for value in [*edges(low, high), rng.randint(-(2**61), 2**61)]:
            commands.append(f"clamp {value} {low} {high}")
            answers.append(
                BoundedAtomicInt(value, minimum=low, maximum=high, overflow="saturate").get()
            )
            saturated = BoundedAtomicInt(start, minimum=low, maximum=high, overflow="saturate")
            commands.append(f"clamp {start + value} {low} {high}")
            answers.append(saturated.add(value))
    for name, (low, high) in WIDTHS.items():
        for value in [*edges(low, high), *(rng.randint(-(2**62), 2**62) for _ in range(count))]:
            commands.append(f"{name} {value}")
            answers.append(
                BoundedAtomicInt(value, minimum=low, maximum=high, overflow="wrap").get()
            )
    for _ in range(count):
        first = rng.choice([LONG - 1, -LONG, rng.randint(-LONG, LONG - 1)])
        second = rng.choice([1, -1, rng.randint(-LONG, LONG - 1)])
        commands.append(f"add64 {first} {second}")
        wrapped = BoundedAtomicInt(first, minimum=-LONG, maximum=LONG - 1, overflow="wrap")
        answers.append(wrapped.add(second))
    return commands, [str(a) for a in answers]


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_every_operation_agrees_with_java_atomic_long(seed: int) -> None:
    commands, answers = _atomic_commands(random.Random(seed), 3000)
    out = run_oracle("java", "AtomicOracle.java", "\n".join(commands) + "\n").split()
    assert len(out) == len(answers)
    mismatches = [(c, a, o) for c, a, o in zip(commands, answers, out, strict=True) if a != o]
    assert mismatches == []


@pytest.mark.parametrize("seed", [1, 2])
def test_saturate_and_wrap_agree_with_java(seed: int) -> None:
    commands, answers = _range_commands(random.Random(seed), 300)
    out = run_oracle("java", "AtomicOracle.java", "\n".join(commands) + "\n").split()
    assert len(out) == len(answers)
    assert [(c, a, o) for c, a, o in zip(commands, answers, out, strict=True) if a != o] == []
