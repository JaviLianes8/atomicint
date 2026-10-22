"""Results compared with the JavaScript runtime, run live (scripts/oracle/atomics_oracle.js).

The Atomics functions on every integer typed array answer for the wrap policy at 8, 16,
32 and 64 bits, signed and unsigned, and Uint8ClampedArray for saturate on 0..255. The
tests skip when Node.js is not installed. Operations are drawn from seeded generators.
"""

from __future__ import annotations

import json
import random

from atomicint import BoundedAtomicInt

from ._oracle import edges, run_oracle

ARRAYS = {
    "Int8Array": 8,
    "Uint8Array": -8,
    "Int16Array": 16,
    "Uint16Array": -16,
    "Int32Array": 32,
    "Uint32Array": -32,
    "BigInt64Array": 64,
    "BigUint64Array": -64,
}


def _typed_array_case(
    rng: random.Random, array: str, bits: int
) -> tuple[dict[str, object], list[str]]:
    size = abs(bits)
    low, high = (0, 2**size - 1) if bits < 0 else (-(2 ** (size - 1)), 2 ** (size - 1) - 1)
    span = 2**70 if size == 64 else 2**52  # Node's plain numbers are exact below 2**53
    start = rng.choice([*edges(low, high), rng.randint(-span, span)])
    counter = BoundedAtomicInt(start, minimum=low, maximum=high, overflow="wrap")
    ops: list[list[str]] = []
    answers = [str(counter.get())]
    for _ in range(60):
        value = rng.choice([1, -1, *edges(low, high), rng.randint(-span, span)])
        expect = counter.get() if rng.random() < 0.5 else rng.randint(low, high)
        name = rng.choice(["store", "load", "add", "sub", "exchange", "compareExchange"])
        if name == "store":
            counter.set(value)
            result = counter.get()
        elif name == "load":
            result = counter.get()
        elif name == "add":
            result = counter.get_and_add(value)
        elif name == "sub":
            result = counter.get_and_add(-value)
        elif name == "exchange":
            result = counter.get_and_set(value)
        else:
            result = counter.compare_and_exchange(expect, value)
        ops.append(
            [name, str(expect), str(value)] if name == "compareExchange" else [name, str(value)]
        )
        answers.append(str(result))
    return {"array": array, "start": str(start), "ops": ops}, answers


def test_wrap_agrees_with_javascript_atomics_on_every_integer_typed_array() -> None:
    rng = random.Random(7)
    cases, expected = [], []
    for array, bits in ARRAYS.items():
        for _ in range(40):
            case, answers = _typed_array_case(rng, array, bits)
            cases.append(case)
            expected.append(answers)
    assert json.loads(run_oracle("node", "atomics_oracle.js", json.dumps(cases))) == expected


def test_saturate_agrees_with_a_javascript_clamped_byte_array() -> None:
    rng = random.Random(8)
    cases, expected = [], []
    for _ in range(200):
        start = rng.randint(-1000, 1000)
        counter = BoundedAtomicInt(start, minimum=0, maximum=255, overflow="saturate")
        ops, answers = [], [str(counter.get())]
        for _ in range(30):
            value = rng.choice([1, -1, 255, 256, -256, rng.randint(-1000, 1000)])
            if rng.random() < 0.5:
                ops.append(["store", str(value)])
                counter.set(value)
                answers.append(str(counter.get()))
            else:
                ops.append(["add", str(value)])
                answers.append(str(counter.add(value)))
        cases.append({"array": "Uint8ClampedArray", "start": str(start), "ops": ops})
        expected.append(answers)
    assert json.loads(run_oracle("node", "atomics_oracle.js", json.dumps(cases))) == expected
