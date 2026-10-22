"""Copy and pickle support: a copy is rebuilt from its slots with a fresh lock."""

from __future__ import annotations

import copyreg
import threading
from types import MemberDescriptorType
from typing import Any

State = tuple[dict[str, Any] | None, dict[str, Any]]


# Where each class keeps its slot names, worked out once when the class is made.
_CACHE = "_atomicint_slot_names"


def _declared(klass: type) -> dict[str, None]:
    # Read the slots Python built, not __slots__ itself: that may be an iterator already
    # used up, and the names come mangled exactly as Python mangled them, whatever the
    # class is called now. "__dict__" and "__weakref__" are not members, so they never
    # appear: capture() takes the instance dictionary on its own. The dictionary is copied
    # first, as another thread may set or delete a class attribute meanwhile.
    return {
        member.__name__: None
        for member in vars(klass).copy().values()
        if isinstance(member, MemberDescriptorType)
        and member.__objclass__ is klass
        and member.__name__ != "_lock"
    }


def _collect(cls: type) -> tuple[str, ...]:
    names: dict[str, None] = {}
    for klass in cls.__mro__:
        known = vars(klass).get(_CACHE)
        names.update(dict.fromkeys(known) if known is not None else _declared(klass))
    return tuple(names)


def slot_names(cls: type) -> tuple[str, ...]:
    """Every slot Python created along the class hierarchy, except the lock."""
    known: tuple[str, ...] | None = vars(cls).get(_CACHE)
    # Only a subclass whose base skipped super().__init_subclass__() has no names stored.
    return known if known is not None else _collect(cls)


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

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Fixed now, while every slot still has the descriptor Python made: a wrapper may
        # replace one on the class later, and a copy then reads no class dictionary at all.
        type.__setattr__(cls, _CACHE, _collect(cls))

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
