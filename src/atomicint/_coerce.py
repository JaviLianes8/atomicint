"""Turn caller input into a plain int, or refuse it."""

from __future__ import annotations

import operator
from typing import SupportsIndex


def as_int(value: SupportsIndex, name: str) -> int:
    # bool is an int subclass, but a counter set to True is almost always a bug.
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, not bool")
    if isinstance(value, int):
        return operator.index(value)
    hook = getattr(type(value), "__index__", None)
    if hook is None:
        raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    # Called directly so a hook that answers True is caught here; operator.index
    # would turn it into 1 with only a deprecation warning.
    result = hook(value)
    if isinstance(result, bool) or not isinstance(result, int):
        kind = type(result).__name__
        raise TypeError(f"{name} must be an integer, but its __index__ returned {kind}")
    return operator.index(result)
