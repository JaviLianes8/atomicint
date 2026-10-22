"""A write from another thread that lands while an operation works outside the lock.

A bounded counter applies its overflow policy without holding the lock, then stores the
result only if the value it read is still there. These cases put another thread's write
exactly in that gap, deterministically, through the policy step of a subclass.
"""

from __future__ import annotations

import threading
from collections.abc import Callable

import pytest

from atomicint import BoundedAtomicInt


class Raced(BoundedAtomicInt):
    """Runs ``race`` in another thread, once, the first time the policy is applied."""

    __slots__ = ("race",)
    race: Callable[[], object] | None

    def _fit(self, value: int) -> int:
        race, self.race = getattr(self, "race", None), None
        if race is not None:
            worker = threading.Thread(target=race, daemon=True)
            worker.start()
            worker.join(timeout=10)
            assert not worker.is_alive(), "the policy was applied while holding the lock"
        return super()._fit(value)


def _counter(value: int, policy: str, race: Callable[[Raced], object]) -> Raced:
    counter = Raced(value, minimum=0, maximum=2000, overflow=policy)  # type: ignore[arg-type]
    counter.race = lambda: race(counter)
    return counter


@pytest.mark.parametrize(("policy", "stored"), [("saturate", 2000), ("wrap", 5000 % 2001)])
def test_a_compare_and_set_that_loses_to_an_equal_write_still_stores(
    policy: str, stored: int
) -> None:
    # The racing write stores an equal value as a new object; the compare still holds,
    # so the swap must happen after it, never report success without storing.
    counter = _counter(1000, policy, lambda c: c.set(int("1000")))
    assert counter.compare_and_set(1000, 5000) is True
    assert counter.get() == stored
    counter = _counter(1000, policy, lambda c: c.set(int("1000")))
    assert counter.compare_and_exchange(1000, 5000) == 1000
    assert counter.get() == stored


@pytest.mark.parametrize("policy", ["saturate", "wrap"])
def test_a_compare_and_set_that_loses_to_a_different_write_fails(policy: str) -> None:
    counter = _counter(1000, policy, lambda c: c.set(7))
    assert counter.compare_and_set(1000, 5000) is False
    assert counter.get() == 7
    counter = _counter(1000, policy, lambda c: c.set(7))
    assert counter.compare_and_exchange(1000, 5000) == 7
    assert counter.get() == 7


@pytest.mark.parametrize(("policy", "stored"), [("saturate", 2000), ("wrap", 3040 % 2001)])
def test_an_out_of_range_add_that_loses_a_race_adds_to_the_new_value(
    policy: str, stored: int
) -> None:
    counter = _counter(1990, policy, lambda c: c.set(1000))
    assert counter.get_and_add(2040) == 1000
    assert counter.get() == stored
