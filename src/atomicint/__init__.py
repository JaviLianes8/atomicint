"""Thread-safe atomic integer with the operations the stdlib leaves out."""

from __future__ import annotations

from ._atomic import AtomicInt

__version__ = "0.1.0"

__all__ = ["AtomicInt"]
