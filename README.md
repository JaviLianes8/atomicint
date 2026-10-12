# atomicint

Thread-safe atomic integer with get, set, add, increment, decrement, compare-and-set and get-and-set, backed by a lock, zero dependencies, fully typed

## Install

```
pip install atomicint
```

## Usage

```python
from atomicint import AtomicInt

counter = AtomicInt(0)

counter.increment()  # 1
counter.add(10)  # 11
counter.decrement()  # 10

counter.get()  # 10
counter.set(5)
counter.get_and_set(99)  # returns 5, value is now 99

# compare-and-set: only swaps when the current value matches
counter.compare_and_set(99, 0)  # True, value is now 0
counter.compare_and_set(99, 1)  # False, value stays 0
```

Every method takes one internal lock for the whole operation, so compound
actions stay consistent even when many threads call them at once:

```python
import threading
from atomicint import AtomicInt

hits = AtomicInt(0)


def worker() -> None:
    for _ in range(1000):
        hits.increment()


threads = [threading.Thread(target=worker) for _ in range(8)]
for t in threads:
    t.start()
for t in threads:
    t.join()

assert hits.get() == 8000
```

## Why

CPython makes a single `int` read or write atomic, but a read-modify-write such
as `x += 1` is not: under threads it can lose updates. The usual answer is to
wrap a counter in your own `threading.Lock`, which is boilerplate repeated in
every project.

The existing packages solve a different problem. `atomicx`, `atomics` and
`pyzas` are compiled extensions (Rust or C) built for lock-free performance, and
`cereggii` targets free-threaded (nogil) builds. They pull in a toolchain or a
special interpreter for a job most code does not need that hard. `atomicity` is
early-stage and has no compare-and-set.

`atomicint` fills the plain gap: a small, fully typed, zero-dependency
`AtomicInt` that runs on any CPython from 3.10, with the operations people
expect, including compare-and-set and get-and-set.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
