"""An operation that starts while its own thread is inside a locked step still finishes.

That is where CPython can run a finalizer or a signal handler during an operation: just
after the lock is taken. Running the nested operation there directly makes the case
deterministic; tests/test_reentry.py drives the real finalizers and signals.
"""

from __future__ import annotations

import copy
import pickle
import threading
from collections.abc import Callable
from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt


def _inside_a_locked_step(counter: AtomicInt, operation: Callable[[], object]) -> list[object]:
    # Where CPython can interrupt an operation: just after it takes the lock. Run the
    # nested operation there, in a worker thread so a hang fails instead of blocking.
    done: list[object] = []

    def nested() -> None:
        with counter._lock:
            done.append(operation())

    worker = threading.Thread(target=nested, daemon=True)
    worker.start()
    worker.join(timeout=30)
    return done


@pytest.mark.parametrize("clone", [lambda c: c, copy.copy, lambda c: pickle.loads(pickle.dumps(c))])
@pytest.mark.parametrize("cls", [AtomicInt, BoundedAtomicInt])
def test_an_operation_nested_inside_a_locked_step_finishes(cls: Any, clone: Any) -> None:
    counter = clone(cls(1))
    assert _inside_a_locked_step(counter, counter.increment) == [2]
    assert _inside_a_locked_step(counter, lambda: counter.update(lambda v: v * 5)) == [10]
    assert _inside_a_locked_step(counter, lambda: copy.copy(counter).get()) == [10]
    assert counter.get() == 10
