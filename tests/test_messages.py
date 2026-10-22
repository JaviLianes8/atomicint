"""Error messages and repr stay short and never fail, whatever the input size."""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterator
from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt

HUGE = 10**5000  # past the default 4300-digit limit of str(int) since Python 3.11
LIMIT = 200


@pytest.fixture(autouse=True)
def _lowest_digit_limit() -> Iterator[None]:
    # The strictest setting an application can choose; nothing below may depend on it.
    if not hasattr(sys, "set_int_max_str_digits"):
        yield
        return
    previous = sys.get_int_max_str_digits()
    sys.set_int_max_str_digits(640)
    try:
        yield
    finally:
        sys.set_int_max_str_digits(previous)


def _message(call: Callable[[], object], error: type[Exception]) -> str:
    with pytest.raises(error) as caught:
        call()
    text = str(caught.value)
    assert len(text) <= LIMIT, text[:300]
    return text


@pytest.mark.parametrize(
    "value", [HUGE, -HUGE, 2**1000, -(2**121)], ids=["10**5000", "-10**5000", "2**1000", "-2**121"]
)
def test_an_out_of_range_huge_value_raises_overflow_error_with_its_size(value: int) -> None:
    counter = BoundedAtomicInt(0, minimum=-5, maximum=5)
    sign = "-" if value < 0 else ""
    text = _message(lambda: counter.set(value), OverflowError)
    assert text == f"{sign}<{value.bit_length()}-bit integer> is outside [-5, 5]"
    assert counter.get() == 0


def test_a_value_up_to_120_bits_is_written_out_in_full() -> None:
    counter = BoundedAtomicInt(0, maximum=0)
    assert _message(lambda: counter.set(2**120 - 1), OverflowError) == (
        f"{2**120 - 1} is outside [unbounded, 0]"
    )
    assert _message(lambda: counter.set(2**120), OverflowError) == (
        "<121-bit integer> is outside [unbounded, 0]"
    )


def test_huge_bounds_are_described_by_their_size() -> None:
    counter = BoundedAtomicInt(0, minimum=-HUGE, maximum=0)
    text = _message(lambda: counter.add(1), OverflowError)
    assert text == f"1 is outside [-<{HUGE.bit_length()}-bit integer>, 0]"
    text = _message(lambda: BoundedAtomicInt(0, minimum=HUGE, maximum=-HUGE), ValueError)
    assert text.startswith("minimum <16610-bit integer> is greater than maximum -<16610")


@pytest.mark.parametrize(
    ("policy", "shown"),
    [("clamp", "'clamp'"), ("x" * 100_000, "'" + "x" * 40 + "'...")],
    ids=["clamp", "long"],
)
def test_an_unknown_policy_is_named_briefly(policy: Any, shown: str) -> None:
    text = _message(lambda: BoundedAtomicInt(0, overflow=policy), ValueError)
    assert text == f"overflow must be 'raise', 'saturate' or 'wrap', not {shown}"


@pytest.mark.parametrize(
    ("policy", "shown"),
    [
        (None, "NoneType"),
        (b"raise", "bytes"),
        (type("P" * 5000, (str,), {})("wrap"), "P" * 60 + "..."),
    ],
    ids=["none", "bytes", "long-subclass-name"],
)
def test_a_policy_of_the_wrong_type_is_named_by_its_type(policy: Any, shown: str) -> None:
    text = _message(lambda: BoundedAtomicInt(0, overflow=policy), TypeError)
    assert text == f"overflow must be a plain str, not {shown}"


def test_bounds_past_120_bits_are_described_by_their_size() -> None:
    # Only the value was tested huge before: a bound must be cut at the same size.
    counter = BoundedAtomicInt(0, maximum=2**1000)
    assert _message(lambda: counter.set(2**1001), OverflowError) == (
        "<1002-bit integer> is outside [unbounded, <1001-bit integer>]"
    )
    counter = BoundedAtomicInt(0, minimum=-(2**121), maximum=2**120 - 1)
    assert _message(lambda: counter.set(-(2**122)), OverflowError) == (
        f"-<123-bit integer> is outside [-<122-bit integer>, {2**120 - 1}]"
    )


def test_a_very_long_type_name_is_cut_short() -> None:
    odd = type("N" * 5000, (), {})()
    text = _message(lambda: AtomicInt(odd), TypeError)
    assert text == f"value must be an integer, not {'N' * 60}..."

    class Hook:
        def __index__(self) -> Any:
            return odd

    text = _message(lambda: AtomicInt(Hook()), TypeError)
    assert text.endswith(f"__index__ returned {'N' * 60}...")


def test_repr_writes_values_up_to_1800_bits_and_never_fails() -> None:
    exact = 2**1800 - 1
    assert repr(AtomicInt(exact)) == f"AtomicInt({exact})"
    assert repr(AtomicInt(-HUGE)) == f"AtomicInt(-<{HUGE.bit_length()}-bit integer>)"
    bounded = BoundedAtomicInt(HUGE, minimum=-HUGE, maximum=HUGE, overflow="wrap")
    size = HUGE.bit_length()
    assert repr(bounded) == (
        f"BoundedAtomicInt(<{size}-bit integer>, minimum=-<{size}-bit integer>, "
        f"maximum=<{size}-bit integer>, overflow='wrap')"
    )


def test_repr_writes_bounds_up_to_1800_bits_in_full_too() -> None:
    low, high = -(2**500), 2**1800 - 1
    counter = BoundedAtomicInt(7, minimum=low, maximum=high, overflow="saturate")
    assert repr(counter) == (
        f"BoundedAtomicInt(7, minimum={low}, maximum={high}, overflow='saturate')"
    )


def test_huge_values_still_compute_exactly() -> None:
    counter = BoundedAtomicInt(HUGE, minimum=0, maximum=HUGE, overflow="wrap")
    assert counter.add(1) == 0
    assert counter.get_and_add(HUGE + 5) == 0
    assert counter.get() == 4
    assert AtomicInt(HUGE).compare_and_exchange(HUGE, -HUGE) == HUGE


@pytest.mark.parametrize(("size", "cut"), [(59, False), (60, False), (61, True)])
def test_a_type_name_is_cut_only_past_60_characters(size: int, cut: bool) -> None:
    odd = type("N" * size, (), {})()
    text = _message(lambda: AtomicInt(odd), TypeError)
    assert text == f"value must be an integer, not {'N' * min(size, 60)}{'...' if cut else ''}"


@pytest.mark.parametrize(("size", "cut"), [(39, False), (40, False), (41, True)])
def test_a_policy_is_cut_only_past_40_characters(size: int, cut: bool) -> None:
    text = _message(lambda: BoundedAtomicInt(0, overflow="p" * size), ValueError)  # type: ignore[arg-type]
    shown = "'" + "p" * min(size, 40) + "'" + ("..." if cut else "")
    assert text == f"overflow must be 'raise', 'saturate' or 'wrap', not {shown}"
