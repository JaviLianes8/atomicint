"""A thread-safe integer backed by a single lock."""

from __future__ import annotations

import threading


class AtomicInt:
    """An integer whose read-modify-write operations are safe across threads.

    Each method holds one internal lock for the whole operation, so compound
    actions such as increment or compare-and-set never interleave with another
    thread. Plain CPython ``int`` reads and writes are atomic on their own, but
    ``x += 1`` is not: it reads, adds and writes as separate steps.
    """

    __slots__ = ("_lock", "_value")

    def __init__(self, value: int = 0) -> None:
        self._value = int(value)
        self._lock = threading.Lock()

    def get(self) -> int:
        """Return the current value."""
        with self._lock:
            return self._value

    def set(self, value: int) -> None:
        """Replace the current value."""
        with self._lock:
            self._value = int(value)

    def add(self, amount: int) -> int:
        """Add ``amount`` and return the new value."""
        with self._lock:
            self._value += int(amount)
            return self._value

    def increment(self) -> int:
        """Add one and return the new value."""
        return self.add(1)

    def decrement(self) -> int:
        """Subtract one and return the new value."""
        return self.add(-1)

    def compare_and_set(self, expect: int, new: int) -> bool:
        """Set the value to ``new`` only if it currently equals ``expect``.

        Return ``True`` when the swap happened, ``False`` otherwise.
        """
        with self._lock:
            if self._value != expect:
                return False
            self._value = int(new)
            return True

    def get_and_set(self, value: int) -> int:
        """Replace the value and return what it was before the swap."""
        with self._lock:
            previous = self._value
            self._value = int(value)
            return previous

    def __repr__(self) -> str:
        return f"AtomicInt({self.get()})"
