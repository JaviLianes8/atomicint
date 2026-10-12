"""Linearizability under contention: every operation takes effect at one instant.

The switch interval is lowered so a GIL build interleaves threads as often as it
can; on a free-threaded build the threads run truly in parallel.
"""

from __future__ import annotations

import bisect
import functools
import time
from collections import Counter

from atomicint import AtomicInt

from ._helpers import run_threads, tight_switching

THREADS = 16
PER_THREAD = 2000


def test_every_increment_returns_a_distinct_value_and_none_is_lost() -> None:
    counter = AtomicInt(0)
    results: list[list[int]] = [[] for _ in range(THREADS)]

    def worker(out: list[int]) -> None:
        for _ in range(PER_THREAD):
            out.append(counter.increment())

    with tight_switching():
        run_threads([functools.partial(worker, out) for out in results])
    total = THREADS * PER_THREAD
    assert sorted(v for out in results for v in out) == list(range(1, total + 1))
    assert counter.get() == total


def test_get_and_add_hands_out_every_ticket_exactly_once() -> None:
    counter = AtomicInt(100)
    taken: list[int] = []

    def worker() -> None:
        mine = [counter.get_and_add(3) for _ in range(PER_THREAD)]
        taken.extend(mine)

    with tight_switching():
        run_threads([worker] * THREADS)
    assert sorted(taken) == list(range(100, 100 + 3 * THREADS * PER_THREAD, 3))


def test_reads_respect_real_time_order_with_concurrent_increments() -> None:
    counter = AtomicInt(0)
    incs: list[tuple[int, int]] = []
    reads: list[tuple[int, int, int]] = []

    def writer() -> None:
        for _ in range(PER_THREAD):
            begin = time.perf_counter_ns()
            counter.increment()
            incs.append((begin, time.perf_counter_ns()))

    def reader() -> None:
        for _ in range(PER_THREAD):
            begin = time.perf_counter_ns()
            value = counter.get()
            reads.append((begin, time.perf_counter_ns(), value))

    with tight_switching():
        run_threads([writer, reader] * (THREADS // 2))
    starts = sorted(begin for begin, _ in incs)
    ends = sorted(end for _, end in incs)
    for begin, end, value in reads:
        finished_before = bisect.bisect_left(ends, begin)
        started_before = bisect.bisect_right(starts, end)
        assert finished_before <= value <= started_before, (finished_before, value)


def test_compare_and_exchange_retry_loops_never_lose_an_update() -> None:
    counter = AtomicInt(0)

    def worker() -> None:
        for _ in range(PER_THREAD // 2):
            seen = counter.get()
            while (witness := counter.compare_and_exchange(seen, seen + 1)) != seen:
                seen = witness

    with tight_switching():
        run_threads([worker] * THREADS)
    assert counter.get() == THREADS * PER_THREAD // 2


def test_compare_and_set_lets_exactly_one_thread_claim_each_value() -> None:
    counter = AtomicInt(0)
    claims: Counter[int] = Counter()

    def worker() -> None:
        while (seen := counter.get()) < 500:
            if counter.compare_and_set(seen, seen + 1):
                claims[seen] += 1

    with tight_switching():
        run_threads([worker] * THREADS)
    assert counter.get() == 500
    assert claims == Counter(range(500))


def test_concurrent_updates_and_mixed_operations_add_up() -> None:
    counter = AtomicInt(0)
    olds: list[int] = []
    rounds = PER_THREAD // 4

    def updater() -> None:
        for _ in range(rounds):
            olds.append(counter.get_and_update(lambda v: v + 2))

    def mixer() -> None:
        for _ in range(rounds):
            counter.add(3)
            counter.increment()

    with tight_switching():
        run_threads([updater, mixer] * (THREADS // 2))
    # Every operation only grows the value, so no two updates can start from the same one.
    assert len(olds) == len(set(olds))
    assert counter.get() == (THREADS // 2) * rounds * (2 + 4)
