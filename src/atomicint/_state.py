"""Copy and pickle support: a copy is rebuilt from its slots with a fresh lock."""

from __future__ import annotations

import copyreg
import threading
from typing import Any

State = tuple[dict[str, Any] | None, dict[str, Any]]

# Never copied: the lock is replaced, the others are handled by Python itself.
_SKIPPED = ("_lock", "__dict__", "__weakref__")


def slot_names(cls: type) -> list[str]:
    """Every slot declared along the class hierarchy, private names mangled."""
    names: list[str] = []
    for klass in cls.__mro__:
        declared = klass.__dict__.get("__slots__", ())
        for name in (declared,) if isinstance(declared, str) else declared:
            if name.startswith("__") and not name.endswith("__"):
                name = f"_{klass.__name__.lstrip('_')}{name}"
            if name not in _SKIPPED:
                names.append(name)
    return names


def capture(obj: object) -> State:
    """The instance dictionary (if any) and every slot that holds a value."""
    slots = {n: getattr(obj, n) for n in slot_names(type(obj)) if hasattr(obj, n)}
    return (getattr(obj, "__dict__", None), slots)


def restore(obj: object, state: State) -> None:
    """Put a captured state back on a blank instance (the caller adds the lock)."""
    extra, slots = state
    if extra:
        vars(obj).update(extra)
    for name, value in slots.items():
        object.__setattr__(obj, name, value)


class Copyable:
    """Copy, deep copy and pickle for a class that keeps its lock in ``_lock``."""

    __slots__ = ()
    _lock: threading.RLock
    _value: int

    def __reduce__(self) -> tuple[Any, ...]:
        # The lock cannot be pickled. Rebuild without calling __init__, so subclasses
        # with their own constructor or extra attributes come back intact.
        return (copyreg.__newobj__, (type(self),), self.__getstate__())  # type: ignore[attr-defined]

    def __getstate__(self) -> State:
        # The value is read under the lock; the rest is built after it is released, so
        # a finalizer or signal handler run meanwhile never finds the lock taken.
        with self._lock:
            value = self._value
        extra, slots = capture(self)
        slots["_value"] = value
        return (extra, slots)

    def __setstate__(self, state: State) -> None:
        restore(self, state)
        object.__setattr__(self, "_lock", threading.RLock())
