"""Recorded concurrent histories of every operation are linearizable.

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

from atomicint import AtomicInt, BoundedAtomicInt

from ._helpers import run_threads, tight_switching


class Call(NamedTuple):
    start: int
    end: int
    name: str
    args: tuple[int, ...]
    result: Any


def _step(call: Call, value: int, low: int, high: int) -> tuple[bool, int]:
    """Whether ``call`` could have returned its result from ``value``, and the next value."""
    name, args, result = call.name, call.args, call.result

    def fit(new: int) -> int:
        return low + (new - low) % (high - low + 1)

    if name == "get":
        return result == value, value
    if name == "set":
        return result is None, fit(args[0])
    if name in ("add", "update"):
        return result == fit(value + args[0]), fit(value + args[0])
    if name in ("get_and_add", "get_and_update"):
        return result == value, fit(value + args[0])
    if name == "get_and_set":
        return result == value, fit(args[0])
    swapped = fit(args[1]) if value == args[0] else value
    if name == "compare_and_set":
        return result is (value == args[0]), swapped
    return result == value, swapped  # compare_and_exchange


def linearizable(history: list[Call], initial: int, low: int, high: int) -> bool:
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
            fits, after = _step(history[i], value, low, high)
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


OPERATIONS = [
    "get",
    "set",
    "add",
    "get_and_add",
    "get_and_set",
    "compare_and_set",
    "compare_and_exchange",
    "update",
    "get_and_update",
]


def _random_call(counter: AtomicInt, rng: random.Random) -> Call:
    name = rng.choice(OPERATIONS)
    a, b = rng.randint(-3, 3), rng.randint(-3, 3)
    args: tuple[int, ...] = {"get": ()}.get(name, (a,) if "compare" not in name else (a, b))
    method = getattr(counter, name)
    start = time.perf_counter_ns()
    result = method(lambda v: v + a) if "update" in name else method(*args)
    return Call(start, time.perf_counter_ns(), name, args, result)


@pytest.mark.parametrize("bounded", [False, True])
def test_every_recorded_history_is_linearizable(bounded: bool) -> None:
    low, high = (-5, 5) if bounded else (-(10**9), 10**9)
    rng = random.Random(11 + bounded)
    checked = 0
    with tight_switching():
        for _ in range(150):
            counter = (
                BoundedAtomicInt(0, minimum=low, maximum=high, overflow="wrap")
                if bounded
                else AtomicInt(0)
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
            assert linearizable(history, 0, low, high), history
            checked += 1
    assert checked == 150
