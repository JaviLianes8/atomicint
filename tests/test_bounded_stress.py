"""Bounded counters never leave their range, whatever the contention."""

from __future__ import annotations

import functools
import random

from atomicint import BoundedAtomicInt

from ._helpers import run_threads, tight_switching

THREADS = 16
ROUNDS = 1500


def test_raise_mode_works_as_a_permit_pool_that_never_overbooks() -> None:
    permits = BoundedAtomicInt(0, minimum=0, maximum=5)
    holders = BoundedAtomicInt(0)
    peak: list[int] = []
    refused: list[int] = []

    def worker() -> None:
        for _ in range(ROUNDS):
            try:
                permits.increment()
            except OverflowError:
                refused.append(1)
                continue
            peak.append(holders.increment())
            holders.decrement()
            permits.decrement()

    with tight_switching():
        run_threads([worker] * THREADS)
    assert max(peak) <= 5
    assert refused, "the pool was never full, the test proved nothing"
    assert permits.get() == 0


def test_saturate_mode_stays_in_range_under_random_traffic() -> None:
    level = BoundedAtomicInt(0, minimum=-3, maximum=7, overflow="saturate")
    outside: list[int] = []

    def worker(seed: int) -> None:
        rng = random.Random(seed)
        for _ in range(ROUNDS):
            value = level.add(rng.choice((-4, -1, 1, 4)))
            if not -3 <= value <= 7:
                outside.append(value)
            outside.extend(v for v in (level.get(),) if not -3 <= v <= 7)

    with tight_switching():
        run_threads([functools.partial(worker, seed) for seed in range(THREADS)])
    assert outside == []


def test_wrap_mode_hands_out_each_sequence_number_equally_often() -> None:
    sequence = BoundedAtomicInt(0, minimum=0, maximum=255, overflow="wrap")
    seen: list[int] = []

    def worker() -> None:
        seen.extend(sequence.get_and_add(1) for _ in range(256 * 4))

    with tight_switching():
        run_threads([worker] * THREADS)
    assert sorted(seen) == sorted(list(range(256)) * THREADS * 4)
    assert sequence.get() == 0
