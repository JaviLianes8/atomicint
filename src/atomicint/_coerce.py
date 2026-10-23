"""Turn caller input into a plain int, or refuse it; write values into messages."""

from __future__ import annotations

import operator
from typing import Any, SupportsIndex

# An int of at most this many bits has at most 37 decimal digits. Longer ones are
# described by their size: str() of a huge int is slow, fails past the interpreter's
# digit limit and would flood the message.
_MESSAGE_BITS = 120
_NAME_CHARS = 60
# repr() writes every digit up to this size (542 digits, below the smallest digit limit
# Python can be set to), so it never fails; a larger value is described by its size.
REPR_BITS = 1800
# type's own descriptors, so a metaclass cannot answer for what Python keeps on a class.
MRO = vars(type)["__mro__"]
NAMESPACE = vars(type)["__dict__"]
_NAME = vars(type)["__name__"]


def as_int(value: SupportsIndex, name: str) -> int:
    # The real type, never isinstance: an object can claim any class through __class__.
    cls = type(value)
    # bool is an int subclass, but a counter set to True is almost always a bug.
    if cls is bool:
        raise TypeError(f"{name} must be an integer, not bool")
    if issubclass(cls, int):
        return operator.index(value)
    found = _lookup(cls, "__index__")
    if not found or found[0] is None:
        raise TypeError(f"{name} must be an integer, not {kind(value)}")
    hook = found[0]
    # Called here, bound as Python binds it, so a hook that answers True is caught;
    # operator.index would turn it into 1 with only a deprecation warning.
    # A __get__ that is there is called, as Python calls it, whatever it is.
    bind = _lookup(type(hook), "__get__")
    result = (bind[0](hook, value, cls) if bind else hook)()
    kind_of_result = type(result)
    if kind_of_result is bool or not issubclass(kind_of_result, int):
        raise TypeError(f"{name} must be an integer, but its __index__ returned {kind(result)}")
    return operator.index(result)


def _lookup(cls: type, name: str) -> tuple[Any, ...]:
    # The class attribute as the interpreter finds it, as a 1-tuple, or () when there is
    # none: a class may hold any object, None or one of ours included, so no value can
    # stand for "absent". Along the real MRO, never through the metaclass, one read per
    # class: between two reads another thread may delete the name, or a key equal to it
    # may change its answer. A key that fails to compare ends the search with nothing
    # found, as Python's own lookup does; an interrupt or exit still goes through.
    absent = object()
    for klass in MRO.__get__(cls):
        try:
            found = NAMESPACE.__get__(klass).get(name, absent)
        except Exception:
            return ()
        if found is not absent:
            return (found,)
    return ()


def class_name(cls: type) -> str:
    """The name Python keeps for ``cls``, whatever its metaclass answers for ``__name__``."""
    # A plain copy: the name may be a str subclass, whose methods could raise or answer
    # anything, while Python's own messages use the text it holds.
    return str.__str__(_NAME.__get__(cls))


def kind(value: object) -> str:
    """The type name of ``value``, cut short if a class has a very long name."""
    name = class_name(type(value))
    return name if len(name) <= _NAME_CHARS else name[:_NAME_CHARS] + "..."


def show_int(value: int, bits: int = _MESSAGE_BITS) -> str:
    """Write ``value`` exactly when it has at most ``bits`` bits, else describe its size."""
    size = value.bit_length()
    if size <= bits:
        return str(value)
    return f"{'-' if value < 0 else ''}<{size}-bit integer>"
