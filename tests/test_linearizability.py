"""Recorded concurrent histories of every operation are linearizable, under every policy.

Threads run random operations on one counter while each call's start and end times are
recorded. A history is linearizable when its operations can be put in one sequential
order that respects real time (an operation that ended before another started comes
first) and in which every result is what the sequential operation returns. The checker
is the Wing and Gong search, written by hand for these tests, with memoisation; its own
tests below show it accepts and rejects the textbook cases.
"""

from __future__ import annotations

import functools
import random
import time
from typing import Any, NamedTuple

import pytest

from atomicint import AtomicInt, BoundedAtomicInt, Overflow

from ._helpers import run_threads, tight_switching


class Call(NamedTuple):
    start: int
    end: int
    name: str
    args: tuple[int, ...]
    result: Any


RAISED = "OverflowError"  # the result recorded for a call that raised it


def _fit(new: int, low: int, high: int, policy: str) -> int | None:
    # What the policy stores for new, or None when it refuses the write.
    if low <= new <= high:
        return new
    if policy == "raise":
        return None
    if policy == "saturate":
        return low if new < low else high
    return low + (new - low) % (high - low + 1)


def _target(name: str, args: tuple[int, ...], value: int) -> int | None:
    # The value a call tries to write from value, or None when it writes nothing.
    if name in ("set", "get_and_set"):
        return args[0]
    if name in ("add", "get_and_add", "update", "get_and_update"):
        return value + args[0]
    if name in ("increment", "decrement"):
        return value + (1 if name == "increment" else -1)
    if name.startswith("compare"):
        return args[1] if value == args[0] else None
    return None  # get


def _step(call: Call, value: int, low: int, high: int, policy: str) -> tuple[bool, int]:
    """Whether ``call`` could have returned its result from ``value``, and the next value."""
    name, result = call.name, call.result
    target = _target(name, call.args, value)
    stored = value if target is None else _fit(target, low, high, policy)
    if stored is None:  # refused: the call raised and the value stays
        return result == RAISED, value
    if result == RAISED:
        return False, value
    if name in ("add", "update", "increment", "decrement"):
        return result == stored, stored
    if name == "set":
        return result is None, stored
    if name == "compare_and_set":
        return result is (value == call.args[0]), stored
    return result == value, stored  # get, get_and_*, compare_and_exchange


def linearizable(
    history: list[Call], initial: int, low: int, high: int, policy: str = "wrap"
) -> bool:
    full = (1 << len(history)) - 1
    seen: set[tuple[int, int]] = set()

    def search(done: int, value: int) -> bool:
        if done == full:
            return True
        if (done, value) in seen:
            return False
        seen.add((done, value))
        pending = [i for i in range(len(history)) if not done >> i & 1]
        horizon = min(history[i].end for i in pending)
        for i in pending:
            if history[i].start > horizon:
                continue  # another pending call ended before this one began
            fits, after = _step(history[i], value, low, high, policy)
            if fits and search(done | 1 << i, after):
                return True
        return False

    return search(0, initial)


def test_the_checker_accepts_overlapping_calls_in_either_order() -> None:
    history = [Call(0, 10, "add", (1,), 2), Call(1, 11, "add", (1,), 1)]
    assert linearizable(history, 0, -100, 100)


def test_the_checker_rejects_a_lost_update_and_a_stale_read() -> None:
    lost = [Call(0, 10, "add", (1,), 1), Call(1, 11, "add", (1,), 1)]
    assert not linearizable(lost, 0, -100, 100)
    stale = [Call(0, 1, "set", (5,), None), Call(2, 3, "get", (), 0)]
    assert not linearizable(stale, 0, -100, 100)
    assert linearizable([Call(0, 3, "set", (5,), None), Call(2, 4, "get", (), 0)], 0, -9, 9)


def test_the_checker_knows_each_policy() -> None:
    # From 4 in 0..5, an increment then add(3): 5, then a raise, a clamp to 5 or a wrap to 2.
    def history(second: object) -> list[Call]:
        return [Call(0, 1, "increment", (), 5), Call(2, 3, "add", (3,), second)]

    assert linearizable(history(RAISED), 4, 0, 5, "raise")
    assert not linearizable(history(8), 4, 0, 5, "raise")
    assert linearizable(history(5), 4, 0, 5, "saturate")
    assert not linearizable(history(RAISED), 4, 0, 5, "saturate")
    assert linearizable(history(2), 4, 0, 5, "wrap")
    assert not linearizable(history(5), 4, 0, 5, "wrap")
    # A refused write leaves the value: a later read must still see 5.
    read = [*history(RAISED), Call(4, 5, "get", (), 5)]
    assert linearizable(read, 4, 0, 5, "raise")
    assert not linearizable([*read[:2], Call(4, 5, "get", (), 8)], 4, 0, 5, "raise")


OPERATIONS = [
    "get",
    "set",
    "add",
    "get_and_add",
    "increment",
    "decrement",
    "get_and_set",
    "compare_and_set",
    "compare_and_exchange",
    "update",
    "get_and_update",
]


def test_the_histories_draw_every_public_operation() -> None:
    public = {name for name in vars(AtomicInt) if not name.startswith("_")}
    assert set(OPERATIONS) == public


def _random_call(counter: AtomicInt, rng: random.Random) -> Call:
    name = rng.choice(OPERATIONS)
    # Deltas and expected values in -5..5, the bounded range; written values past it too.
    a, b, c = rng.randint(-5, 5), rng.randint(-5, 5), rng.randint(-8, 8)
    fixed: dict[str, tuple[int, ...]] = {"set": (c,), "get_and_set": (c,), "get": ()}
    args = fixed.get(name, () if "crement" in name else (b, c) if "compare" in name else (a,))
    method = getattr(counter, name)
    start = time.perf_counter_ns()
    try:
        result = method(lambda v: v + a) if "update" in name else method(*args)
    except OverflowError:
        result = RAISED
    return Call(start, time.perf_counter_ns(), name, args, result)


POLICIES: list[Overflow | None] = [None, "raise", "saturate", "wrap"]


@pytest.mark.parametrize("policy", POLICIES)
def test_every_recorded_history_is_linearizable(policy: Overflow | None) -> None:
    low, high = (-(10**9), 10**9) if policy is None else (-5, 5)
    rng = random.Random(f"linearizable {policy}")
    checked = refused = 0
    with tight_switching():
        for _ in range(150):
            counter = (
                AtomicInt(0)
                if policy is None
                else BoundedAtomicInt(0, minimum=low, maximum=high, overflow=policy)
            )
            logs: list[list[Call]] = [[] for _ in range(4)]

            def worker(log: list[Call], seed: int, counter: AtomicInt = counter) -> None:
                local = random.Random(seed)
                log.extend(_random_call(counter, local) for _ in range(6))

            seeds = [rng.randrange(2**32) for _ in logs]
            run_threads(
                [functools.partial(worker, log, s) for log, s in zip(logs, seeds, strict=True)]
            )
            history = [call for log in logs for call in log]
            assert linearizable(history, 0, low, high, policy or "raise"), history
            checked += 1
            refused += sum(call.result == RAISED for call in history)
    assert checked == 150
    assert (refused > 0) == (policy == "raise")  # the raise histories hold refused writes
