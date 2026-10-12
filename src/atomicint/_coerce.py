"""Turn caller input into a plain int, or refuse it."""

from __future__ import annotations

import operator
from typing import SupportsIndex


def as_int(value: SupportsIndex, name: str) -> int:
    # bool is an int subclass, but a counter set to True is almost always a bug.
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, not bool")
    try:
        return operator.index(value)
    except TypeError:
        kind = type(value).__name__
        raise TypeError(f"{name} must be an integer, not {kind}") from None
