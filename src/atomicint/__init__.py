"""Thread-safe atomic integers with the operations the stdlib leaves out.

:class:`AtomicInt` is a plain counter; :class:`BoundedAtomicInt` keeps its value inside
a range. ``Overflow`` is the type of the bounded counter's policy, one of three names:

>>> import typing
>>> from atomicint import BoundedAtomicInt, Overflow
>>> typing.get_args(Overflow)
('raise', 'saturate', 'wrap')
>>> policy: Overflow = "saturate"
>>> BoundedAtomicInt(9, maximum=10, overflow=policy).add(5)
10
"""

from __future__ import annotations

from ._atomic import AtomicInt
from ._bounded import BoundedAtomicInt, Overflow

__version__ = "1.0.0"

# The public classes show and pickle as atomicint.<Name>, so a pickle never depends on
# the private module that defines them.
for _cls in (AtomicInt, BoundedAtomicInt):
    _cls.__module__ = __name__
    # Methods follow, so doctest finds their examples here (it takes properties anyway).
    for _member in vars(_cls).values():
        if callable(_member) and str(getattr(_member, "__module__", "")).startswith("atomicint._"):
            _member.__module__ = __name__
del _cls, _member

__all__ = ["AtomicInt", "BoundedAtomicInt", "Overflow"]
