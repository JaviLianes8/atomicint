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
    hook = _lookup(cls, "__index__")
    if hook is None:
        raise TypeError(f"{name} must be an integer, not {kind(value)}")
    # Called here, bound as Python binds it, so a hook that answers True is caught;
    # operator.index would turn it into 1 with only a deprecation warning.
    bind = _lookup(type(hook), "__get__")
    result = (hook if bind is None else bind(hook, value, cls))()
    kind_of_result = type(result)
    if kind_of_result is bool or not issubclass(kind_of_result, int):
        raise TypeError(f"{name} must be an integer, but its __index__ returned {kind(result)}")
    return operator.index(result)


def _lookup(cls: type, name: str) -> Any:
    # The class attribute as the interpreter finds it: along the real MRO, never through
    # the metaclass.
    for klass in MRO.__get__(cls):
        namespace = NAMESPACE.__get__(klass)
        if name in namespace:
            return namespace[name]
    return None


def class_name(cls: type) -> str:
    """The name Python keeps for ``cls``, whatever its metaclass answers for ``__name__``."""
    name: str = _NAME.__get__(cls)
    return name


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
