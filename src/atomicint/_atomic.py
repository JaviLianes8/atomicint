"""A thread-safe integer backed by a single lock."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any, SupportsIndex

from ._coerce import as_int


class AtomicInt:
    """An integer whose read-modify-write operations are safe across threads.

    Each method holds one internal lock for the whole operation, so compound
    actions such as increment or compare-and-set never interleave with another
    thread, with or without the GIL. Every operation takes effect at a single
    instant between its call and its return (it is linearizable).
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
        """Return the current value."""
        with self._lock:
            return self._value

    def set(self, value: SupportsIndex) -> None:
        """Replace the current value."""
        new = as_int(value, "value")
        with self._lock:
            self._value = self._fit(new)

    def add(self, amount: SupportsIndex) -> int:
        """Add ``amount`` and return the new value."""
        delta = as_int(amount, "amount")
        with self._lock:
            self._value = self._fit(self._value + delta)
            return self._value

    def get_and_add(self, amount: SupportsIndex) -> int:
        """Add ``amount`` and return the value from before the addition."""
        delta = as_int(amount, "amount")
        with self._lock:
            previous = self._value
            self._value = self._fit(previous + delta)
            return previous

    def increment(self) -> int:
        """Add one and return the new value."""
        return self.add(1)

    def decrement(self) -> int:
        """Subtract one and return the new value."""
        return self.add(-1)

    def get_and_set(self, value: SupportsIndex) -> int:
        """Replace the value and return what it was before the swap."""
        new = as_int(value, "value")
        with self._lock:
            previous = self._value
            self._value = self._fit(new)
            return previous

    def compare_and_set(self, expect: SupportsIndex, new: SupportsIndex) -> bool:
        """Set the value to ``new`` only if it currently equals ``expect``.

        Return ``True`` when the swap happened, ``False`` otherwise.
        """
        # Convert once: an __index__ that answers differently each call must not
        # make a successful swap report False.
        wanted = as_int(expect, "expect")
        return self.compare_and_exchange(wanted, new) == wanted

    def compare_and_exchange(self, expect: SupportsIndex, new: SupportsIndex) -> int:
        """Set the value to ``new`` only if it currently equals ``expect``.

        Return the value seen at that instant: equal to ``expect`` when the swap
        happened, the current value (to retry with) when it did not.
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
        """
        return self._apply(function)[1]

    def get_and_update(self, function: Callable[[int], SupportsIndex]) -> int:
        """Like :meth:`update`, but return the value from before the update."""
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

    def __reduce__(self) -> tuple[Any, ...]:
        # The lock cannot be pickled. Rebuild without calling __init__, so subclasses
        # with their own constructor or extra attributes come back intact.
        return (_blank, (type(self),), self.__getstate__())

    def __getstate__(self) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        with self._lock:
            slots = {n: getattr(self, n) for n in _slot_names(type(self)) if hasattr(self, n)}
        return (getattr(self, "__dict__", None), slots)

    def __setstate__(self, state: tuple[dict[str, Any] | None, dict[str, Any]]) -> None:
        extra, slots = state
        if extra:
            vars(self).update(extra)
        for name, value in slots.items():
            object.__setattr__(self, name, value)
        object.__setattr__(self, "_lock", threading.Lock())

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.get()})"


def _blank(cls: type[AtomicInt]) -> AtomicInt:
    return cls.__new__(cls)


def _slot_names(cls: type) -> list[str]:
    names: list[str] = []
    for klass in cls.__mro__:
        declared = klass.__dict__.get("__slots__", ())
        for name in (declared,) if isinstance(declared, str) else declared:
            if name.startswith("__") and not name.endswith("__"):
                name = f"_{klass.__name__.lstrip('_')}{name}"  # private names are mangled
            if name not in ("_lock", "__dict__", "__weakref__"):
                names.append(name)
    return names
