# atomicint

Thread-safe atomic integers for Python: get, set, add, fetch-and-add, compare-and-set,
compare-and-exchange, atomic update functions and a bounded variant that raises,
saturates or wraps. Zero dependencies, fully typed, safe on free-threaded CPython.

## Install

```
pip install atomicint
```

## Usage

```python
from atomicint import AtomicInt

counter = AtomicInt(0)
print(counter.increment())  # 1
print(counter.add(10))  # 11
print(counter.decrement())  # 10
print(counter.get_and_add(5))  # 10
print(counter.get())  # 15
print(counter.get_and_set(99))  # 15
print(int(counter))  # 99
```

Every value must be a real integer. Floats, strings and `bool` raise `TypeError` instead
of being truncated or parsed; integer-like objects such as NumPy integers are accepted.
Type checkers treat `bool` as an integer, so that one is caught at run time only.

```python
from atomicint import AtomicInt

counter = AtomicInt(1)
try:
    counter.add(0.5)
except TypeError as error:
    print(error)  # amount must be an integer, not float
print(counter.get())  # 1
```

## Compare-and-set and compare-and-exchange

`compare_and_set(expect, new)` swaps only when the value equals `expect` and says whether
it did. `compare_and_exchange(expect, new)` returns the value it saw instead, so a failed
attempt already tells you what to retry with.

```python
from atomicint import AtomicInt

flag = AtomicInt(0)
print(flag.compare_and_set(0, 1))  # True
print(flag.compare_and_set(0, 1))  # False

version = AtomicInt(7)
print(version.compare_and_exchange(6, 10))  # 7
print(version.compare_and_exchange(7, 10))  # 7
print(version.get())  # 10
```

## Atomic updates

`update(fn)` replaces the value with `fn(value)` and returns the new value;
`get_and_update(fn)` returns the old one. The function runs outside the lock, so it may
read the counter, and it is called again with the fresh value if another thread changed
it meanwhile. Keep it free of side effects.

```python
from atomicint import AtomicInt

peak = AtomicInt(3)
for sample in (5, 2, 9, 4):
    peak.update(lambda current, s=sample: max(current, s))
print(peak.get())  # 9
print(peak.get_and_update(lambda v: v * 2))  # 9
print(peak.get())  # 18
```

## Bounded counters

`BoundedAtomicInt` keeps the value inside `[minimum, maximum]`. Either bound may be left
out. Every write, the initial value included, follows one overflow policy:

| `overflow` | What an out-of-range write does |
| --- | --- |
| `"raise"` (default) | raises `OverflowError`, the value is left untouched |
| `"saturate"` | stores the nearest bound |
| `"wrap"` | wraps around like a fixed-width integer (needs both bounds) |

```python
from atomicint import BoundedAtomicInt

slots = BoundedAtomicInt(0, minimum=0, maximum=2)
slots.increment()
slots.increment()
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

## Threads

Each operation holds one internal lock for its whole duration, so it takes effect at a
single instant between call and return (it is linearizable). That holds with or without
the GIL, and the test suite checks it on a free-threaded build too.

```python
import threading

from atomicint import AtomicInt

tickets = AtomicInt(0)
issued: list[int] = []


def worker() -> None:
    for _ in range(1000):
        issued.append(tickets.increment())


threads = [threading.Thread(target=worker) for _ in range(8)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(tickets.get())  # 8000
print(sorted(issued) == list(range(1, 8001)))  # True
```

## Copies and pickling

A counter can be copied, deep-copied and pickled (to send it to a process pool, for
instance). The copy is a new, independent counter with the same value, bounds and
subclass attributes; it does not share updates with the original. Counters compare by identity, never by value.

```python
import pickle

from atomicint import BoundedAtomicInt

original = BoundedAtomicInt(5, minimum=0, maximum=9, overflow="wrap")
twin = pickle.loads(pickle.dumps(original))
twin.add(7)
print(original.get(), twin.get())  # 5 2
print(twin)  # BoundedAtomicInt(2, minimum=0, maximum=9, overflow='wrap')
```

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
| `update(fn)` / `get_and_update(fn)` | Apply `fn` atomically; return the new or previous value. |
| `int(counter)`, `operator.index(counter)` | A snapshot of the value. |
| `BoundedAtomicInt(value=0, *, minimum=None, maximum=None, overflow="raise")` | An `AtomicInt` kept inside a range; exposes `minimum`, `maximum` and `overflow`. |
| `Overflow` | The type of the overflow policy: `Literal["raise", "saturate", "wrap"]`. |

## Why

CPython makes a single `int` read or write atomic, but a read-modify-write such
as `x += 1` is not: under threads it can lose updates. The usual answer is to
wrap a counter in your own `threading.Lock`, which is boilerplate repeated in
every project, and the retry loops around it are easy to get wrong.

The existing packages solve a different problem. `atomicx`, `atomics` and
`pyzas` are compiled extensions (Rust or C) built for lock-free performance, and
`cereggii` targets free-threaded (nogil) builds. They pull in a toolchain or a
special interpreter for a job most code does not need that hard. `atomicity` is
early-stage and has no compare-and-set.

`atomicint` fills the plain gap: a small, fully typed, zero-dependency atomic
integer that runs on any CPython from 3.10, free-threaded builds included, with the
operations people expect.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
