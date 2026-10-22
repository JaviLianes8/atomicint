"""Turn caller input into a plain int, or refuse it; write values into messages."""

from __future__ import annotations

import operator
from typing import SupportsIndex

# An int of at most this many bits has at most 37 decimal digits. Longer ones are
# described by their size: str() of a huge int is slow, fails past the interpreter's
# digit limit and would flood the message.
_MESSAGE_BITS = 120
_NAME_CHARS = 60
# repr() writes every digit up to this size (541 digits, below the smallest digit limit
# Python can be set to), so it never fails; a larger value is described by its size.
REPR_BITS = 1800


def as_int(value: SupportsIndex, name: str) -> int:
    # bool is an int subclass, but a counter set to True is almost always a bug.
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, not bool")
    if isinstance(value, int):
        return operator.index(value)
    hook = getattr(type(value), "__index__", None)
    if hook is None:
        raise TypeError(f"{name} must be an integer, not {kind(value)}")
    # Called directly so a hook that answers True is caught here; operator.index
    # would turn it into 1 with only a deprecation warning.
    result = hook(value)
    if isinstance(result, bool) or not isinstance(result, int):
        raise TypeError(f"{name} must be an integer, but its __index__ returned {kind(result)}")
    return operator.index(result)


def kind(value: object) -> str:
    """The type name of ``value``, cut short if a class has a very long name."""
    name = type(value).__name__
    return name if len(name) <= _NAME_CHARS else name[:_NAME_CHARS] + "..."


def show_int(value: int, bits: int = _MESSAGE_BITS) -> str:
    """Write ``value`` exactly when it has at most ``bits`` bits, else describe its size."""
    size = value.bit_length()
    if size <= bits:
        return str(value)
    return f"{'-' if value < 0 else ''}<{size}-bit integer>"
