"""Copy and pickle support: a copy is rebuilt from its slots with a fresh lock."""

from __future__ import annotations

import copyreg
import threading
import weakref
from types import MemberDescriptorType
from typing import Any

State = tuple[dict[str, Any] | None, dict[str, Any]]

# The slot names of each class, keyed by the class itself. An attribute on the class would
# be copied into any class rebuilt from its namespace (dataclass(slots=True) does that),
# and its name could clash with a slot or an attribute of a subclass.
_NAMES: weakref.WeakKeyDictionary[type, tuple[str, ...]] = weakref.WeakKeyDictionary()

_NOT_COPIED = ("_lock", "__dict__", "__weakref__")


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


def _listed(klass: type) -> dict[str, None]:
    # A base's own class hook may replace a slot's descriptor (with a validating property,
    # say) before this one runs, so the names in __slots__ count too when it can be read
    # again. While the class hooks run, the class still has the name Python mangled with.
    listed = vars(klass).get("__slots__", ())
    if isinstance(listed, str):
        listed = (listed,)
    if not isinstance(listed, (tuple, list, dict, set, frozenset)):
        return {}  # an iterator, used up when the class was made
    stem = klass.__name__.lstrip("_")
    names: dict[str, None] = {}
    for name in listed:
        if stem and name.startswith("__") and not name.endswith("__"):
            name = f"_{stem}{name}"
        if name not in _NOT_COPIED:
            names[name] = None
    return names


def _collect(cls: type) -> tuple[str, ...]:
    names: dict[str, None] = {}
    covered: set[type] = set()
    for klass in cls.__mro__:
        if klass in covered:
            continue
        known = _NAMES.get(klass)
        if known is None:
            names.update(_declared(klass))
        else:
            # Stored names already hold those of every class above klass: skipping them
            # keeps making a class linear in the depth of its hierarchy.
            names.update(dict.fromkeys(known))
            covered.update(klass.__mro__)
    return tuple(names)


def slot_names(cls: type) -> tuple[str, ...]:
    """Every slot Python created along the class hierarchy, except the lock."""
    known = _NAMES.get(cls)
    if known is None:
        # Only a subclass whose base skipped super().__init_subclass__() gets here: its
        # names are worked out at its first copy and kept from then on.
        known = _NAMES[cls] = _collect(cls)
    return known


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
        _NAMES[cls] = tuple(dict.fromkeys(_collect(cls)) | _listed(cls))

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
