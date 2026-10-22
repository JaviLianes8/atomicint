"""The locking discipline: an operation runs no Python code of its own under the lock."""

from __future__ import annotations

import math
import threading
from collections.abc import Callable
from typing import ClassVar, SupportsIndex

from ._coerce import as_int


class Committing:
    """Reads under the lock; writes computed outside it, then stored by a check-then-store.

    CPython may run a garbage collector finalizer or a signal handler at a call, in the
    thread that holds the lock. So each locked block below makes no call and creates no
    object the collector tracks: handler code that uses this counter can only run just
    after the lock is taken, before anything is read. The lock is reentrant, so that code
    finishes its own operation there; the interrupted one then reads the new value, or
    finds it changed and computes again. A trace or monitoring hook runs Python code at
    every line, here too, so with one installed that guarantee is gone (see the guide).
    """

    __slots__ = ("_lock", "_value")
    _lock: threading.RLock
    _value: int
    # True when every int is in range: no check at all (BoundedAtomicInt sets False).
    _exact: ClassVar[bool] = True

    def _limits(self) -> tuple[float, float]:
        # The range a value may take as it is. Infinities compare with any int in C, so
        # checking a value against these runs no Python code, even under the lock.
        return (-math.inf, math.inf)

    def _within(self, value: int) -> bool:
        floor, ceiling = self._limits()
        return floor <= value <= ceiling

    def _fit(self, value: int) -> int:
        # The value the overflow policy stores for value (itself when in range); never
        # called with the lock held. Raising here must leave the value as it was.
        return value

    def _store(self, new: int) -> int:
        with self._lock:
            previous = self._value
            self._value = new
        return previous

    def _add(self, delta: int) -> tuple[int, int]:
        lock = self._lock
        if self._exact:
            with lock:
                current = self._value
                new = current + delta
                self._value = new
            return current, new
        floor, ceiling = self._limits()
        with lock:
            current = self._value
            new = current + delta
            fits = floor <= new <= ceiling
            if fits:
                self._value = new
        if fits:
            return current, new
        # Out of range: the policy decides, without the lock.
        while True:
            new = self._fit(current + delta)
            # Identity, not equality: current is the very object read, and `is` costs nothing.
            with lock:
                seen = self._value
                if seen is current:
                    self._value = new
            if seen is current:
                return current, new
            current = seen

    def _exchange(self, wanted: int, replacement: int) -> int:
        lock = self._lock
        if self._exact or self._within(replacement):
            with lock:
                seen = self._value
                if seen == wanted:
                    self._value = replacement
            return seen
        # replacement is out of range. A failed compare stores nothing, so it never
        # applies the policy; a successful one stores what the policy makes of it.
        fitted: int | None = None
        with lock:
            seen = self._value
        while seen == wanted:
            if fitted is None:
                fitted = self._fit(replacement)
            with lock:
                now = self._value
                if now is seen:
                    self._value = fitted
            if now is seen:
                break
            seen = now
        return seen

    def _apply(self, function: Callable[[int], SupportsIndex]) -> tuple[int, int]:
        # The function runs without the lock, so it may read this counter.
        lock = self._lock
        with lock:
            current = self._value
        while True:
            new = self._fit(as_int(function(current), "update result"))
            with lock:
                seen = self._value
                if seen is current:
                    self._value = new
            if seen is current:
                return current, new
            current = seen
