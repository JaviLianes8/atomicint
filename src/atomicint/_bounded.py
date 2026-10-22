"""An atomic integer kept inside a range, with a choice of overflow policy."""

from __future__ import annotations

from typing import Literal, SupportsIndex

from ._atomic import AtomicInt
from ._coerce import REPR_BITS, as_int, kind, show_int

# A nested Literal is the same type once flattened. Spelled this way the alias is an
# object of its own: typing caches Literal[...] by its arguments, and the docstring set
# here must not land on an identical alias in someone else's code.
Overflow = Literal["raise", Literal["saturate", "wrap"]]  # noqa: RUF041
Overflow.__doc__ = """The overflow policy of a :class:`BoundedAtomicInt`, one of three names.

``"raise"`` refuses an out-of-range write with :class:`OverflowError`, ``"saturate"``
stores the nearest bound, and ``"wrap"`` wraps around the range like a fixed-width
integer.

>>> import typing
>>> from atomicint import BoundedAtomicInt, Overflow
>>> typing.get_args(Overflow)
('raise', 'saturate', 'wrap')
>>> policy: Overflow = "wrap"
>>> BoundedAtomicInt(255, minimum=0, maximum=255, overflow=policy).increment()
0
"""
# The alias is not a class or a function, so doctest finds its example only here.
__test__ = {"Overflow": Overflow.__doc__}
_POLICIES = ("raise", "saturate", "wrap")
_POLICY_CHARS = 40


class BoundedAtomicInt(AtomicInt):
    """An :class:`AtomicInt` whose value stays within ``[minimum, maximum]``.

    Every write, the initial value included, goes through the overflow policy:
    ``"raise"`` raises :class:`OverflowError` and leaves the value untouched,
    ``"saturate"`` clamps to the nearest bound, and ``"wrap"`` wraps around like
    a fixed-width integer (both bounds required). A missing bound means no limit
    on that side. Bounds and policy are fixed at construction; a bad combination
    raises :class:`ValueError`.

    >>> byte = BoundedAtomicInt(255, minimum=0, maximum=255, overflow="wrap")
    >>> byte.increment()
    0
    >>> volume = BoundedAtomicInt(8, minimum=0, maximum=10, overflow="saturate")
    >>> volume.add(5)
    10
    >>> BoundedAtomicInt(3, maximum=3).increment()
    Traceback (most recent call last):
    ...
    OverflowError: 4 is outside [unbounded, 3]
    """

    __slots__ = ("_maximum", "_minimum", "_overflow")
    _exact = False

    def __init__(
        self,
        value: SupportsIndex = 0,
        *,
        minimum: SupportsIndex | None = None,
        maximum: SupportsIndex | None = None,
        overflow: Overflow = "raise",
    ) -> None:
        low = None if minimum is None else as_int(minimum, "minimum")
        high = None if maximum is None else as_int(maximum, "maximum")
        if low is not None and high is not None and low > high:
            raise ValueError(f"minimum {show_int(low)} is greater than maximum {show_int(high)}")
        policy: object = overflow  # compared exactly: a str subclass or odd __eq__ is refused
        if type(policy) is not str or policy not in _POLICIES:
            raise ValueError(f"overflow must be 'raise', 'saturate' or 'wrap', not {_name(policy)}")
        if overflow == "wrap" and (low is None or high is None):
            raise ValueError("overflow='wrap' needs both minimum and maximum")
        self._minimum: int | None = low
        self._maximum: int | None = high
        self._overflow: Overflow = overflow
        super().__init__(value)

    @property
    def minimum(self) -> int | None:
        """The lowest allowed value, or ``None`` for no lower limit.

        >>> BoundedAtomicInt(minimum=-1).minimum
        -1
        """
        return self._minimum

    @property
    def maximum(self) -> int | None:
        """The highest allowed value, or ``None`` for no upper limit.

        >>> print(BoundedAtomicInt(minimum=-1).maximum)
        None
        """
        return self._maximum

    @property
    def overflow(self) -> Overflow:
        """The policy applied to a write that falls outside the range.

        >>> BoundedAtomicInt().overflow
        'raise'
        """
        return self._overflow

    def _fit(self, value: int) -> int:
        low, high = self._minimum, self._maximum
        below = low is not None and value < low
        above = high is not None and value > high
        if not (below or above):
            return value
        if self._overflow == "raise":
            raise OverflowError(f"{show_int(value)} is outside [{_show(low)}, {_show(high)}]")
        if self._overflow == "saturate":
            clamp = low if below else high
            assert clamp is not None
            return clamp
        assert low is not None and high is not None
        return low + (value - low) % (high - low + 1)

    def __repr__(self) -> str:
        value = show_int(self.get(), REPR_BITS)
        low = _show(self._minimum, "None", REPR_BITS)
        high = _show(self._maximum, "None", REPR_BITS)
        policy = self._overflow
        return f"{type(self).__name__}({value}, minimum={low}, maximum={high}, overflow={policy!r})"


def _show(bound: int | None, missing: str = "unbounded", bits: int = 120) -> str:
    return missing if bound is None else show_int(bound, bits)


def _name(policy: object) -> str:
    if type(policy) is not str:
        return kind(policy)
    text = repr(policy[:_POLICY_CHARS])
    return text if len(policy) <= _POLICY_CHARS else text + "..."
