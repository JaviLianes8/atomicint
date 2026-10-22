"""The locking discipline: no Python code ever runs while a counter's lock is held."""

from __future__ import annotations

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
    finds it changed and computes again.
    """

    __slots__ = ("_lock", "_value")
    _lock: threading.RLock
    _value: int
    # True while _fit is the identity: a new value then needs no Python code to check.
    _exact: ClassVar[bool] = True

    def _fit(self, value: int) -> int:
        # Hook for subclasses that restrict the range (they set _exact to False); never
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
        with lock:
            current = self._value
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
        if self._exact:
            with lock:
                seen = self._value
                if seen == wanted:
                    self._value = replacement
            return seen
        # A failed compare stores nothing, so it never checks the range of replacement.
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
