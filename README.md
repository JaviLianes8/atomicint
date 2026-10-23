# atomicint

[![Lianes8 Certified](https://lianes8studio.com/certified/lianes8-certified-badge.svg)](https://lianes8studio.com/certified)

Thread-safe atomic integers for Python: get, set, add, fetch-and-add, compare-and-set,
compare-and-exchange, atomic update functions, and a bounded counter that raises,
saturates or wraps. Pure Python, zero dependencies, fully typed, safe on free-threaded
CPython.

## The problem

CPython makes a single read or write of an `int` atomic, but a read-modify-write such as
`x += 1` is not: two threads can read the same value and one increment is lost. The
Python FAQ lists `i = i+1` among the operations that are not atomic and says "When in
doubt, use a mutex!". So every project writes the same small class around a
`threading.Lock`, and the retry loops built on top of it (high-water marks,
compare-and-set, capped or wrapping counters) are easy to get wrong.

## Install

```
pip install atomicint
```

Python 3.10 or newer, any platform. Nothing to compile.

## Quick start

```python
from atomicint import AtomicInt

counter = AtomicInt(0)
print(counter.increment())  # 1
print(counter.add(10))  # 11
print(counter.get_and_add(5))  # 11
print(counter.get())  # 16
print(counter.get_and_set(99))  # 16
print(int(counter))  # 99
```

Compare-and-set swaps only when the value is what you expect; compare-and-exchange
returns the value it saw, so a failed attempt already tells you what to retry with.

```python
from atomicint import AtomicInt

version = AtomicInt(7)
print(version.compare_and_set(6, 10))  # False
print(version.compare_and_exchange(6, 10))  # 7
print(version.compare_and_exchange(7, 10))  # 7
print(version.get())  # 10
```

`update(function)` applies a function atomically and returns the new value;
`get_and_update(function)` returns the old one. The function may run more than once under contention, so keep it
free of side effects.

```python
from atomicint import AtomicInt

peak = AtomicInt(3)
for sample in (5, 2, 9, 4):
    peak.update(lambda current: max(current, sample))
print(peak.get())  # 9
```

`BoundedAtomicInt` keeps the value inside `[minimum, maximum]`. A write outside the range
raises `OverflowError` and changes nothing, or saturates at the bound, or wraps around
like a fixed-width integer:

```python
from atomicint import BoundedAtomicInt

slots = BoundedAtomicInt(2, minimum=0, maximum=2)
try:
    slots.increment()
except OverflowError as error:
    print(error)  # 3 is outside [0, 2]
print(slots.get())  # 2

volume = BoundedAtomicInt(8, minimum=0, maximum=10, overflow="saturate")
print(volume.add(5))  # 10

sequence = BoundedAtomicInt(254, minimum=0, maximum=255, overflow="wrap")
print([sequence.get_and_add(1) for _ in range(4)])  # [254, 255, 0, 1]
```

Every value must be a real integer: floats, strings and `bool` raise `TypeError` instead
of being truncated or parsed, and the counter keeps its value.

```python
from atomicint import AtomicInt

counter = AtomicInt(1)
try:
    counter.add(0.5)
except TypeError as error:
    print(error)  # amount must be an integer, not float
print(counter.get())  # 1
```

The [guide](https://github.com/JaviLianes8/atomicint/blob/main/GUIDE.md) covers every
operation, the overflow policies, errors, threads and free threading, copies and pickling,
and typing. The [changelog](https://github.com/JaviLianes8/atomicint/blob/main/CHANGELOG.md)
lists what changed in each release.

## API

| Name | Description |
| --- | --- |
| `AtomicInt(value=0)` | A thread-safe integer. |
| `get()` | The current value. |
| `set(value)` | Replace the value. |
| `add(amount)` | Add and return the new value. |
| `get_and_add(amount)` | Add and return the previous value. |
| `increment()` / `decrement()` | Add or subtract one, return the new value. |
| `get_and_set(value)` | Replace the value, return the previous one. |
| `compare_and_set(expect, new)` | Swap if equal to `expect`; `True` if it swapped. |
| `compare_and_exchange(expect, new)` | Swap if equal to `expect`; return the value seen. |
| `update(function)` / `get_and_update(function)` | Apply `function` atomically; return the new or previous value. |
| `int(counter)`, `operator.index(counter)` | A snapshot of the value. |
| `BoundedAtomicInt(value=0, *, minimum=None, maximum=None, overflow="raise")` | An `AtomicInt` kept inside a range; exposes `minimum`, `maximum` and `overflow`. |
| `Overflow` | The type of the overflow policy: `Literal["raise", "saturate", "wrap"]`. |

## Why atomicint

Most atomic integer packages on PyPI are compiled extensions built for lock-free speed,
and they store a fixed-width machine integer. Checked on 2026-10-22 against their PyPI
releases:

- `atomicx` 0.0.15 (Rust): its `AtomicInt` is 64 bits wide; adding 1 to `2**63 - 1`
  silently gives `-2**63`.
- `cereggii` 1.0.1 (C extension, a wider toolkit for free threading): `AtomicInt64`
  raises `OverflowError` past `2**63 - 1`.
- `atomics` 1.0.3: binds a C library through `cffi`, a runtime dependency; integers wrap
  on overflow, and its wheels are tagged for Python 3.6 to 3.11.
- `pyzas` 1.0.1: requires Python 3.13 or newer and ships wheels for free-threaded 3.13
  only.
- `atomicity` 0.0.3 (Rust): describes itself as at a very early stage.

The pure Python ones are older and narrower (checked on 2026-10-23):

- `atomos` 0.3.1 (last release July 2015, classifiers up to Python 3.4): its
  `AtomicInteger` updates integers of any size under a lock, with `get_and_add` and
  `compare_and_set`, but has no bounds or overflow policy and no type hints. It imports
  `six` at run time and also lists `tox` as an install dependency, which it never imports.
- `fastcounter` 1.1.0 (June 2021): thread-safe counters with an `increment` method and a
  value to read, and no compare-and-set.

`atomicint` takes the other trade from the compiled packages and does more than the pure
Python ones. It is plain Python with one lock per counter, so it installs anywhere
CPython 3.10+ runs, with or without the GIL, and holds integers of any size. Overflow is
a choice you make per counter (raise, saturate or wrap at any range, not only at 64
bits). It is fully typed and checks its inputs. Every operation is tested
for linearizability under contention, on a plain counter and under each overflow policy,
and compared with Java's `AtomicLong`; the wrap and saturate policies are also compared
with JavaScript's `Atomics` and typed arrays.

The cost is speed: a lock per operation is slower than a hardware atomic instruction.
If a counter sits on a hot path of a free-threaded program and 64-bit wraparound is what
you want, one of the compiled packages is the better fit.

## License

MIT. See [LICENSE](https://github.com/JaviLianes8/atomicint/blob/main/LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
