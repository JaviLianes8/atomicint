"""An atomic integer kept inside a range, with a choice of overflow policy."""

from __future__ import annotations

from typing import Literal, SupportsIndex

from ._atomic import AtomicInt
from ._coerce import as_int

Overflow = Literal["raise", "saturate", "wrap"]
_POLICIES = ("raise", "saturate", "wrap")


class BoundedAtomicInt(AtomicInt):
    """An :class:`AtomicInt` whose value stays within ``[minimum, maximum]``.

    Every write, the initial value included, goes through the overflow policy:
    ``"raise"`` raises :class:`OverflowError` and leaves the value untouched,
    ``"saturate"`` clamps to the nearest bound, and ``"wrap"`` wraps around like
    a fixed-width integer (both bounds required). A missing bound means no limit
    on that side.
    """

    __slots__ = ("_maximum", "_minimum", "_overflow")

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
            raise ValueError(f"minimum {low} is greater than maximum {high}")
        policy: object = overflow  # compared exactly: a str subclass or odd __eq__ is refused
        if type(policy) is not str or policy not in _POLICIES:
            raise ValueError(f"overflow must be one of {_POLICIES}, not {policy!r}")
        if overflow == "wrap" and (low is None or high is None):
            raise ValueError("overflow='wrap' needs both minimum and maximum")
        self._minimum: int | None = low
        self._maximum: int | None = high
        self._overflow: Overflow = overflow
        super().__init__(value)

    @property
    def minimum(self) -> int | None:
        """The lowest allowed value, or ``None`` for no lower limit."""
        return self._minimum

    @property
    def maximum(self) -> int | None:
        """The highest allowed value, or ``None`` for no upper limit."""
        return self._maximum

    @property
    def overflow(self) -> Overflow:
        """The policy applied to a write that falls outside the range."""
        return self._overflow

    def _fit(self, value: int) -> int:
        low, high = self._minimum, self._maximum
        below = low is not None and value < low
        above = high is not None and value > high
        if not (below or above):
            return value
        if self._overflow == "raise":
            raise OverflowError(f"{value} is outside [{_show(low)}, {_show(high)}]")
        if self._overflow == "saturate":
            clamp = low if below else high
            assert clamp is not None
            return clamp
        assert low is not None and high is not None
        return low + (value - low) % (high - low + 1)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({self.get()}, minimum={self._minimum}, "
            f"maximum={self._maximum}, overflow={self._overflow!r})"
        )


def _show(bound: int | None) -> str:
    return "unbounded" if bound is None else str(bound)
