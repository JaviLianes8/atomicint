# atomicint guide

The full behaviour of `AtomicInt` and `BoundedAtomicInt`. Every example below runs as
part of the test suite, and each `print` shows its output in the comment after it.

## The model

An `AtomicInt` is a Python integer guarded by one reentrant lock (`threading.RLock`)
that belongs to the counter. The lock is held only to read the value, compare it and store
a new one: inputs are converted, overflow policies applied, error messages written and
update functions called outside it, and a value computed outside it is stored only if the
value it was computed from is still there (otherwise the operation computes again). So
each operation takes effect at a single instant between its call and its return (it is
linearizable), and two operations on the same counter never interleave, with or without
the GIL. Values are Python integers of any size; there is no overflow unless you ask for
one with `BoundedAtomicInt`.

## Operations

| Method | Does | Returns |
| --- | --- | --- |
| `get()` | nothing | the value |
| `set(value)` | stores `value` | `None` |
| `add(amount)` | adds `amount` (may be negative) | the new value |
| `get_and_add(amount)` | adds `amount` | the value before |
| `increment()` / `decrement()` | adds 1 or -1 | the new value |
| `get_and_set(value)` | stores `value` | the value before |
| `compare_and_set(expect, new)` | stores `new` if the value equals `expect` | `True` if it stored |
| `compare_and_exchange(expect, new)` | stores `new` if the value equals `expect` | the value seen |
| `update(function)` | stores `function(value)` | the new value |
| `get_and_update(function)` | stores `function(value)` | the value before |

`int(counter)` and `operator.index(counter)` return a snapshot, so a counter can be used
wherever Python expects an integer index. The names follow Java's `AtomicLong`:
`get_and_add` is `getAndAdd`, `add` is `addAndGet`, `update` is `updateAndGet`, and the
tests check each one against the Java runtime.

```python
from atomicint import AtomicInt

counter = AtomicInt(10)
print(counter.get_and_add(5), counter.get())  # 10 15
print(counter.decrement())  # 14
print(counter.compare_and_set(14, 0), counter.get())  # True 0
print(["a", "b", "c"][AtomicInt(2)])  # c
```

## Integer inputs

Every value, amount, expected value, bound and update result must be an integer: an
`int`, or an object with `__index__` (NumPy integers, another `AtomicInt`), found and
called the way Python itself does it, so a `classmethod` or `staticmethod` `__index__`
works too, and a hook whose class sets `__get__` to `None` is refused as Python refuses
it. The check uses an object's real type: one that claims to be an `int` through
`__class__` is not taken for one. Anything else raises `TypeError` before the counter is
touched. In particular a float is never
truncated, a string is never parsed, and `bool` is refused even though it is an `int`
subclass, because a counter set to `True` is almost always a bug. Type checkers accept
`bool` where an `int` is expected, so that case is caught at run time only. An `int`
subclass is stored as a plain `int`.

```python
from atomicint import AtomicInt

counter = AtomicInt(1)
try:
    counter.set(2.5)
except TypeError as error:
    print(error)  # value must be an integer, not float
try:
    counter.set(True)
except TypeError as error:
    print(error)  # value must be an integer, not bool
print(counter.get())  # 1
print(AtomicInt(AtomicInt(4)).get())  # 4
```

Inputs are converted before the lock is taken, so an `__index__` method may itself read
or change the counter without a deadlock, and an exception from it leaves the value as
it was. `compare_and_set` converts `expect` once, so a strange `__index__` that answers
differently on each call cannot make a successful swap report `False`.

## Compare-and-set loops

`compare_and_exchange` returns the value it saw, which is exactly what a retry loop needs
next. This loop doubles the value, whatever other threads do meanwhile:

```python
from atomicint import AtomicInt

value = AtomicInt(21)
seen = value.get()
while (witness := value.compare_and_exchange(seen, seen * 2)) != seen:
    seen = witness
print(value.get())  # 42
```

`update` writes that loop for you.

## Update functions

`update(function)` and `get_and_update(function)` read the value, call `function` on it
without holding the lock, and store the result only if the value has not changed in the
meantime; otherwise they call `function` again with the fresh value. So:

- `function` may read the counter,
- `function` may be called more than once under contention, so it should have no side
  effects,
- an exception from `function` propagates and leaves the value untouched,
- the result of `function` must be an integer, or `TypeError` is raised and nothing is
  stored.

```python
from atomicint import AtomicInt

hits = AtomicInt(4)
print(hits.update(lambda current: current + hits.get()))  # 8
try:
    hits.update(lambda current: current / 2)
except TypeError as error:
    print(error)  # update result must be an integer, not float
print(hits.get())  # 8
```

`function` must not change the counter it updates: each attempt would then see a changed
value and try again, forever.

## Bounded counters

`BoundedAtomicInt(value=0, *, minimum=None, maximum=None, overflow="raise")` is an
`AtomicInt` whose value stays within `[minimum, maximum]`. A missing bound means no limit
on that side. Every write goes through the overflow policy, the initial value included:

| `overflow` | An out-of-range write |
| --- | --- |
| `"raise"` (default) | raises `OverflowError`; the value is left as it was |
| `"saturate"` | stores the nearest bound |
| `"wrap"` | stores `minimum + (result - minimum) % (maximum - minimum + 1)` (both bounds required) |

The operation returns what it would without bounds, applied to the stored value: `add`
returns the clamped or wrapped value, `get_and_add` the value before. A failed
compare-and-set stores nothing and so never checks the range; a successful one stores
`new` through the policy. `expect` is compared with the value exactly, never wrapped or
clamped first: a wrapping counter on `[0, 255]` that holds 44 does not swap on
`compare_and_exchange(300, 5)`, where an 8-bit compare-exchange in C or JavaScript would
narrow 300 to 44 and swap.

```python
from atomicint import BoundedAtomicInt

level = BoundedAtomicInt(5, minimum=0, maximum=10, overflow="saturate")
print(level.add(-50), level.add(7))  # 0 7

byte = BoundedAtomicInt(-128, minimum=-128, maximum=127, overflow="wrap")
print(byte.decrement())  # 127
print(BoundedAtomicInt(300, minimum=0, maximum=255, overflow="wrap").get())  # 44

pool = BoundedAtomicInt(0, minimum=0, maximum=3)
print(pool.compare_and_set(1, 99))  # False
try:
    pool.compare_and_set(0, 99)
except OverflowError as error:
    print(error)  # 99 is outside [0, 3]
print(pool.get(), pool.minimum, pool.maximum, pool.overflow)  # 0 0 3 raise
```

Wrapping on `[-2**(n-1), 2**(n-1) - 1]` or `[0, 2**n - 1]` gives exactly the result of
an `n`-bit machine integer; the tests compare it with Java's narrowing conversions and
64-bit arithmetic and with JavaScript's typed arrays at 8, 16, 32 and 64 bits.
Saturating matches Java's `Math.clamp`.

The bounds and the policy are fixed when the counter is made. `ValueError` is raised for
`minimum` greater than `maximum`, for `"wrap"` without both bounds, and for a string that
is not one of the three names. A policy that is not a plain `str` raises `TypeError`, a
`str` subclass included, because its comparisons could be changed.

## Errors

| Error | When |
| --- | --- |
| `TypeError` | an input or update result is not an integer (see above), or the overflow policy is not a plain `str` |
| `ValueError` | `BoundedAtomicInt` gets an impossible range or an unknown policy name |
| `OverflowError` | a write falls outside the range of a `"raise"` counter |

All three are the built-in exceptions. No operation changes the value when it raises.
Messages stay short: an integer of more than 120 bits is written by its size, a class
name is cut after 60 characters, and an unknown policy string after 40. The class name is
the one Python keeps for the class (as in its own messages), whatever a metaclass answers
for `__name__`, and as the plain text it holds even when it is a `str` subclass; `repr()`
uses it too.

```python
from atomicint import BoundedAtomicInt

small = BoundedAtomicInt(0, minimum=0, maximum=9)
try:
    small.set(10**100)
except OverflowError as error:
    print(error)  # <333-bit integer> is outside [0, 9]
```

## Threads and free threading

An operation holds only the counter's own lock, and runs no Python code of its own while
it does, so counters never deadlock with each other. That also makes a counter safe to use
from a `__del__` method, a weakref callback or a signal handler: CPython may run such code
in the middle of an operation, in the same thread, even one on the same counter, and the
operation still finishes without losing either update.

```python
import gc

from atomicint import AtomicInt

open_sessions = AtomicInt()


class Session:
    def __init__(self) -> None:
        open_sessions.increment()
        self.me = self  # a reference cycle, so the garbage collector frees it, at any moment

    def __del__(self) -> None:
        open_sessions.decrement()


for _ in range(10_000):
    Session()
gc.collect()
print(open_sessions.get())  # 0
```

That promise has two limits, which no pure Python code can close:

- It holds while no trace, profile or monitoring hook is installed (`sys.settrace`,
  `sys.setprofile`, `sys.monitoring`: debuggers, profilers, coverage tools and the
  `trace` module install them). A hook runs Python code at every line, also between an
  operation's read and its store; if a finalizer or a signal handler runs there and
  updates the same counter, that update is lost. The operation itself is not lost, nothing
  hangs, and threads never lose updates.
- On CPython 3.14 and later, an exception raised by a signal handler, such as
  `KeyboardInterrupt` on Ctrl-C, can arrive just after an operation took the lock and
  before the block that releases it begins. This is the `with` statement's own behaviour:
  a plain `with lock:` does the same. The operation is abandoned with the value unchanged,
  but the lock stays held by that thread. The thread itself can still use the counter;
  any other thread that touches it waits forever. A program that catches
  `KeyboardInterrupt` and carries on should not share that counter with other threads.

The test suite checks the promise under heavy contention: every increment returns a
distinct value and none is lost, compare-and-set lets exactly one thread claim each value,
bounded counters never leave their range, and recorded histories of all eleven operations
mixed together are linearizable, on a plain counter and under each overflow policy. It
also runs every operation while finalizers and signal handlers use the same counter, and
counts that no update is lost.

On free-threaded CPython the package keeps the GIL disabled; the suite runs on CPython
3.14t with `sys._is_gil_enabled()` false. Counters are for threads in one process: a
pickled or copied counter is a new, independent one.

## Copies and pickling

`copy.copy`, `copy.deepcopy` and `pickle` make an independent counter with the same
value, bounds, policy and subclass attributes, and a fresh lock. A subclass keeps its type
and its attributes, also when its own `__init__` takes different arguments, because a
copy is rebuilt without calling `__init__`. Every slot Python created for the subclass is
copied, however `__slots__` was written (one string, any iterable, an iterator) and under
the name Python gave a private one (`__tag`), also when a decorator rebuilds the class
(`dataclass(slots=True)`) or a base's `__init_subclass__` wraps the new slots before it
calls `super()` (that last case needs a `__slots__` that can be read again, so not an
iterator). The names are read once, when the class is made, so a slot whose descriptor
is later replaced on the class by a property that reads and writes it (a getter and a
setter that call the slot, say) is still copied, through that property. A copy reads and
writes each slot by its name, as the standard library copies any slotted class, so a
read-only property there makes the copy raise `AttributeError`, as it would without
atomicint. A copy never reads the class dictionary (another thread may change the class
meanwhile), and its cost grows only in step with the number of slots. Nothing is added to
the subclass's namespace, and the names are kept by the class's identity. The class's
name, MRO and dictionary are read as Python keeps them, so a metaclass that makes classes
equal by name or unhashable, or that answers for `__name__`, `__mro__` or `__dict__`,
changes nothing. One exception: a class made under a base whose `__init_subclass__` does
not call `super()` is not seen when it is made, so its names are read at its first copy
and kept from then on. A pickle refers only to the counter's class
and the standard `copyreg` module. The classes keep the module that defines them, so a
pickle names `atomicint._atomic.AtomicInt` or `atomicint._bounded.BoundedAtomicInt`: those
paths stay importable for the whole 1.x series, and counters pickled by 0.2.0 still load.
Import the classes from `atomicint` itself; the paths are only for pickles.

```python
import pickle

from atomicint import BoundedAtomicInt

original = BoundedAtomicInt(5, minimum=0, maximum=9, overflow="wrap")
twin = pickle.loads(pickle.dumps(original))
twin.add(7)
print(original.get(), twin.get())  # 5 2
print(twin)  # BoundedAtomicInt(2, minimum=0, maximum=9, overflow='wrap')
```

## Identity, truth and repr

Counters compare and hash by identity, never by value, so they can be dictionary keys
while their value changes. A counter is always true in a boolean context, even at zero:
compare `counter.get()` instead. `repr()` shows the class name and the value (and the
bounds); values of up to 1800 bits are written in full, larger ones by their size, so
`repr()` never fails, whatever `sys.set_int_max_str_digits` says.

```python
from atomicint import AtomicInt

zero = AtomicInt(0)
print(bool(zero), zero == AtomicInt(0), zero.get() == 0)  # True False True
print(repr(AtomicInt(2**4000)))  # AtomicInt(<4001-bit integer>)
```

## Typing

The package ships `py.typed` and passes `mypy --strict`. Inputs are typed
`SupportsIndex`, results `int` (`bool` for `compare_and_set`), bounds `int | None`, and
the policy `Overflow`, which is `Literal["raise", "saturate", "wrap"]`, so a type checker
rejects `overflow="clamp"`, `add("1")` or an update function that returns a `str`. The
bounded constructor takes its range and policy by keyword only.

## Cost

An operation takes the counter's lock once, around a few integer operations and a range
check. Three cases take it twice, reading first and storing after a computation done
without the lock: `update` and `get_and_update`, a bounded addition whose result falls
outside the range, and a successful compare-and-set whose `new` is outside it. Measured on CPython
3.13.2 on an AMD Zen 3 desktop (2026-10-22, best of five runs of 500,000 calls): `get`
160 ns, `increment` 350 ns, `compare_and_set` 510 ns, and `increment` on a
`BoundedAtomicInt` 470 ns. On the same machine
`atomicx` 0.0.15, a lock-free Rust extension, increments in 45 ns; see the README for
when to pick a compiled package. Arithmetic on huge integers costs what Python's own
does: `"wrap"` uses `%`, whose time grows with the size of the numbers.

## Versioning

From 1.0.0 the public names (`AtomicInt`, `BoundedAtomicInt`, `Overflow`), their methods,
parameter names, defaults, return values and error types follow Semantic Versioning: they
change only in a new major version. Error message wording and `repr()` text may be
improved in minor versions.
