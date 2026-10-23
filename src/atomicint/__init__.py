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

# The classes keep the module that defines them, so tools find their source. Pickles name
# atomicint._atomic.AtomicInt and atomicint._bounded.BoundedAtomicInt (0.2.0 ones too):
# those paths stay importable for the whole 1.x series.
__all__ = ["AtomicInt", "BoundedAtomicInt", "Overflow"]
