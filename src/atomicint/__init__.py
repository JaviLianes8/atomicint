"""Thread-safe atomic integers with the operations the stdlib leaves out."""

from __future__ import annotations

from ._atomic import AtomicInt
from ._bounded import BoundedAtomicInt, Overflow

__version__ = "0.2.0"

__all__ = ["AtomicInt", "BoundedAtomicInt", "Overflow"]
