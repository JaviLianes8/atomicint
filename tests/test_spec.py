"""Behaviour checked against reference texts fetched by scripts/fetch_upstream.py.

Each test reads the rule from the fetched source (the Java SE 21 API documentation, the
Java Language Specification, MDN, the CPython documentation, trove-classifiers) and
checks atomicint against it; tests/upstream/MANIFEST.json records the URLs, revisions
and hashes. The tests skip when the files have not been fetched.
"""

from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Any

import pytest

from atomicint import AtomicInt, BoundedAtomicInt

from ._upstream import javadoc_member, plain_text, upstream_text

ROOT = Path(__file__).resolve().parents[1]

# java.util.concurrent.atomic.AtomicLong member -> (atomicint method, its "Returns:" rule).
JAVA = {
    "getAndAdd(long)": ("get_and_add", "the previous value"),
    "addAndGet(long)": ("add", "the updated value"),
    "incrementAndGet()": ("increment", "the updated value"),
    "decrementAndGet()": ("decrement", "the updated value"),
    "getAndSet(long)": ("get_and_set", "the previous value"),
    "compareAndExchange(long,long)": ("compare_and_exchange", "the witness value"),
    "updateAndGet(java.util.function.LongUnaryOperator)": ("update", "the updated value"),
    "getAndUpdate(java.util.function.LongUnaryOperator)": ("get_and_update", "the previous value"),
}
CALLS: dict[str, tuple[Any, ...]] = {
    "get_and_add": (5,),
    "add": (5,),
    "increment": (),
    "decrement": (),
    "get_and_set": (3,),
    "compare_and_exchange": (10, 3),
    "update": (lambda v: v * 2,),
    "get_and_update": (lambda v: v * 2,),
}


def _member(anchor: str) -> str:
    return javadoc_member(upstream_text("AtomicLong.html"), anchor)


@pytest.mark.parametrize("anchor", sorted(JAVA))
def test_each_method_returns_what_its_java_counterpart_promises(anchor: str) -> None:
    method, promise = JAVA[anchor]
    assert f"Returns: {promise}" in _member(anchor)
    counter = AtomicInt(10)
    result = getattr(counter, method)(*CALLS[method])
    previous, updated = 10, counter.get()
    assert previous != updated  # the call changed the value, so the two promises differ
    # A successful exchange returns the witness value, "the same as the expected value".
    assert result == (updated if promise == "the updated value" else previous)


def test_increment_and_decrement_are_add_of_one_as_in_java() -> None:
    assert "Equivalent to addAndGet(1)" in _member("incrementAndGet()")
    assert "Equivalent to addAndGet(-1)" in _member("decrementAndGet()")
    for start in (-3, 0, 7):
        assert AtomicInt(start).increment() == AtomicInt(start).add(1)
        assert AtomicInt(start).decrement() == AtomicInt(start).add(-1)


def test_compare_and_set_reports_success_and_failure_as_in_java() -> None:
    doc = _member("compareAndSet(long,long)")
    assert "sets the value to newValue if the current value == expectedValue" in doc
    assert "Returns: true if successful. False return indicates that the actual value" in doc
    counter = AtomicInt(4)
    assert counter.compare_and_set(5, 9) is False and counter.get() == 4
    assert counter.compare_and_set(4, 9) is True and counter.get() == 9


def test_a_failed_exchange_returns_the_witness_value() -> None:
    doc = _member("compareAndExchange(long,long)")
    assert "the current value, referred to as the witness value, == expectedValue" in doc
    counter = AtomicInt(4)
    assert counter.compare_and_exchange(5, 9) == 4 and counter.get() == 4


@pytest.mark.parametrize("anchor", ["getAndUpdate", "updateAndGet"])
def test_the_update_function_is_reapplied_after_contention(anchor: str) -> None:
    doc = _member(f"{anchor}(java.util.function.LongUnaryOperator)")
    assert "may be re-applied when attempted updates fail due to contention" in doc
    counter = AtomicInt(1)
    seen: list[int] = []

    def double(value: int) -> int:
        seen.append(value)
        if len(seen) == 1:
            counter.set(50)  # another thread wins the race between read and commit
        return value * 2

    method = counter.update if anchor == "updateAndGet" else counter.get_and_update
    assert method(double) == (100 if anchor == "updateAndGet" else 50)
    assert seen == [1, 50] and counter.get() == 100


def test_saturate_follows_math_clamp() -> None:
    doc = javadoc_member(upstream_text("Math.html"), "clamp(long,long,long)")
    assert "If the value is less than min, then min is returned." in doc
    assert "If the value is greater than max, then max is returned." in doc
    assert "Otherwise, the original value is returned." in doc
    assert "Throws: IllegalArgumentException - if min > max" in doc
    for value, expected in ((-50, -2), (-2, -2), (4, 4), (10, 10), (99, 10)):
        assert (
            BoundedAtomicInt(value, minimum=-2, maximum=10, overflow="saturate").get() == expected
        )
    with pytest.raises(ValueError, match="greater than maximum"):
        BoundedAtomicInt(0, minimum=3, maximum=2, overflow="saturate")


def _narrow(value: int, bits: int, signed: bool) -> int:
    # Written from the JLS 5.1.3 sentence: keep the n lowest order bits.
    low = value & ((1 << bits) - 1)
    return low - (1 << bits) if signed and low >> (bits - 1) else low


@pytest.mark.parametrize("bits", [8, 16, 32, 64])
@pytest.mark.parametrize("signed", [True, False])
def test_wrap_on_a_fixed_width_range_is_a_java_narrowing_conversion(
    bits: int, signed: bool
) -> None:
    text = plain_text(upstream_text("jls-5.html"))
    assert (
        "A narrowing conversion of a signed integer to an integral type T simply discards all "
        "but the n lowest order bits, where n is the number of bits used to represent type T"
    ) in text
    low, high = (-(2 ** (bits - 1)), 2 ** (bits - 1) - 1) if signed else (0, 2**bits - 1)
    rng = random.Random(bits * 2 + signed)
    for value in [low - 1, high + 1, *(rng.randint(-(2**200), 2**200) for _ in range(500))]:
        counter = BoundedAtomicInt(value, minimum=low, maximum=high, overflow="wrap")
        assert counter.get() == _narrow(value, bits, signed), value


def test_exchange_and_add_return_the_old_value_as_javascript_atomics_do() -> None:
    exchange = upstream_text("mdn-atomics-compareexchange.md")
    assert "It returns the old value at that position whether it was equal to the expected" in (
        " ".join(exchange.split())
    )
    assert "returns the old value at that position" in upstream_text("mdn-atomics-add.md")
    counter = AtomicInt(7)
    assert counter.compare_and_exchange(7, 12) == 7  # the MDN example: 7, the old value
    assert counter.compare_and_exchange(7, 1) == 12
    assert AtomicInt(7).get_and_add(12) == 7


def test_saturate_on_a_byte_range_matches_a_clamped_byte() -> None:
    assert "8-bit unsigned integers clamped to 0" in upstream_text("mdn-uint8clampedarray.md")
    byte = BoundedAtomicInt(0, minimum=0, maximum=255, overflow="saturate")
    assert [byte.add(d) for d in (300, -1000, 255, 1)] == [255, 0, 255, 255]


def test_the_python_faq_lists_an_increment_as_not_atomic() -> None:
    faq = upstream_text("faq-library.rst")
    not_atomic = faq.split("These aren't::", 1)[1].split("\n\n", 2)[1]
    assert "i = i+1" in not_atomic
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "a read-modify-write such as `x += 1` is not" in " ".join(readme.split())


def test_the_free_threading_checks_used_by_the_tests_are_documented() -> None:
    howto = upstream_text("free-threading-python.rst")
    assert "sys._is_gil_enabled" in howto
    assert 'sysconfig.get_config_var("Py_GIL_DISABLED")' in howto


def test_every_classifier_is_a_real_trove_classifier() -> None:
    known = set(re.findall(r'^\s+"([^"]+)",$', upstream_text("trove-classifiers.py.txt"), re.M))
    assert len(known) > 500
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    block = pyproject.split("classifiers = [", 1)[1].split("]", 1)[0]
    ours = re.findall(r'"([^"]+)"', block)
    assert ours and set(ours) <= known, set(ours) - known
