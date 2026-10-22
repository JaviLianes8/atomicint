"""A thread-safe integer backed by a single lock."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import SupportsIndex

from ._coerce import REPR_BITS, as_int, show_int
from ._state import Copyable


class AtomicInt(Copyable):
    """An integer whose read-modify-write operations are safe across threads.

    Each method holds one internal lock for the whole operation, so compound
    actions such as increment or compare-and-set never interleave with another
    thread, with or without the GIL. Every operation takes effect at a single
    instant between its call and its return (it is linearizable). Values are
    Python integers of any size; anything else raises :class:`TypeError`.

    >>> hits = AtomicInt()
    >>> hits.increment()
    1
    >>> hits.add(10)
    11
    """

    __slots__ = ("_lock", "_value")

    def __init__(self, value: SupportsIndex = 0) -> None:
        self._lock = threading.Lock()
        self._value = self._fit(as_int(value, "value"))

    def _fit(self, value: int) -> int:
        # Hook for subclasses that restrict the range; called with the lock held,
        # or before the object is shared. Raising here must leave the value as it was.
        return value

    def get(self) -> int:
        """Return the current value.

        >>> AtomicInt(7).get()
        7
        """
        with self._lock:
            return self._value

    def set(self, value: SupportsIndex) -> None:
        """Replace the current value.

        >>> counter = AtomicInt(1)
        >>> counter.set(42)
        >>> counter.get()
        42
        """
        new = as_int(value, "value")
        with self._lock:
            self._value = self._fit(new)

    def add(self, amount: SupportsIndex) -> int:
        """Add ``amount`` (which may be negative) and return the new value.

        >>> AtomicInt(10).add(-4)
        6
        """
        delta = as_int(amount, "amount")
        with self._lock:
            self._value = self._fit(self._value + delta)
            return self._value

    def get_and_add(self, amount: SupportsIndex) -> int:
        """Add ``amount`` and return the value from before the addition.

        >>> AtomicInt(100).get_and_add(5)
        100
        """
        delta = as_int(amount, "amount")
        with self._lock:
            previous = self._value
            self._value = self._fit(previous + delta)
            return previous

    def increment(self) -> int:
        """Add one and return the new value.

        >>> AtomicInt(1).increment()
        2
        """
        return self.add(1)

    def decrement(self) -> int:
        """Subtract one and return the new value.

        >>> AtomicInt(1).decrement()
        0
        """
        return self.add(-1)

    def get_and_set(self, value: SupportsIndex) -> int:
        """Replace the value and return what it was before the swap.

        >>> slot = AtomicInt(3)
        >>> slot.get_and_set(8)
        3
        >>> slot.get()
        8
        """
        new = as_int(value, "value")
        with self._lock:
            previous = self._value
            self._value = self._fit(new)
            return previous

    def compare_and_set(self, expect: SupportsIndex, new: SupportsIndex) -> bool:
        """Set the value to ``new`` only if it currently equals ``expect``.

        Return ``True`` when the swap happened, ``False`` otherwise.

        >>> flag = AtomicInt(0)
        >>> flag.compare_and_set(0, 1)
        True
        >>> flag.compare_and_set(0, 1)
        False
        """
        # Convert once: an __index__ that answers differently each call must not
        # make a successful swap report False.
        wanted = as_int(expect, "expect")
        return self.compare_and_exchange(wanted, new) == wanted

    def compare_and_exchange(self, expect: SupportsIndex, new: SupportsIndex) -> int:
        """Set the value to ``new`` only if it currently equals ``expect``.

        Return the value seen at that instant: equal to ``expect`` when the swap
        happened, the current value (to retry with) when it did not.

        >>> version = AtomicInt(7)
        >>> version.compare_and_exchange(6, 10)
        7
        >>> version.compare_and_exchange(7, 10)
        7
        >>> version.get()
        10
        """
        wanted = as_int(expect, "expect")
        replacement = as_int(new, "new")
        with self._lock:
            seen = self._value
            if seen == wanted:
                self._value = self._fit(replacement)
            return seen

    def update(self, function: Callable[[int], SupportsIndex]) -> int:
        """Replace the value with ``function(value)`` atomically; return the new value.

        ``function`` runs outside the lock and may be called more than once when
        other threads change the value meanwhile, so it should have no side effects.

        >>> peak = AtomicInt(3)
        >>> peak.update(lambda current: max(current, 9))
        9
        """
        return self._apply(function)[1]

    def get_and_update(self, function: Callable[[int], SupportsIndex]) -> int:
        """Like :meth:`update`, but return the value from before the update.

        >>> size = AtomicInt(4)
        >>> size.get_and_update(lambda current: current * 2)
        4
        >>> size.get()
        8
        """
        return self._apply(function)[0]

    def _apply(self, function: Callable[[int], SupportsIndex]) -> tuple[int, int]:
        # Optimistic loop: compute without the lock so the function may read this
        # counter (the lock is not reentrant), then commit only if nothing changed.
        current = self.get()
        while True:
            candidate = as_int(function(current), "update result")
            with self._lock:
                if self._value == current:
                    self._value = self._fit(candidate)
                    return current, self._value
                current = self._value

    def __index__(self) -> int:
        # Also serves int(), which falls back to __index__.
        return self.get()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({show_int(self.get(), REPR_BITS)})"


def _blank(cls: type[AtomicInt]) -> AtomicInt:
    # Pickles written by 0.2.0 name this function; kept so they still load.
    return cls.__new__(cls)
