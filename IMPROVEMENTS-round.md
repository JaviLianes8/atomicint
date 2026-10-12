# atomicint improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Strict integer inputs: `operator.index`, no silent truncation, no `bool`
- [x] Fetch-then-modify operations: `get_and_add`, `compare_and_exchange`, `update`, `get_and_update`
- [x] `BoundedAtomicInt`: range with `raise`, `saturate` or `wrap` on overflow
- [x] Pickle, copy and `int()` support
- [x] Contracts: linearizability stress tests, free-threaded run, typing, README examples, installed wheel e2e
- [x] Docs: README, CHANGELOG, docstrings, packaging metadata
- [x] Gates: ruff format, ruff check, mypy --strict, pytest
- [ ] Independent review findings fixed with regression tests
- [ ] Pull request opened, guard clean

## Starting point

`0.1.0` gives `AtomicInt` with `get`, `set`, `add`, `increment`, `decrement`,
`compare_and_set` and `get_and_set`, each under one `threading.Lock`. Reading it against
the Python documentation and real use:

- Every write goes through `int(value)`, so `AtomicInt(2.9)` silently stores `2` and
  `counter.set("7")` stores `7`. A counter that accepts strings and truncates floats hides
  bugs instead of reporting them.
- `compare_and_set(expect, new)` compares `expect` with `!=`, so `compare_and_set(5.0, 1)`
  succeeds on `5` and `compare_and_set("5", 1)` fails silently.
- There is no fetch-and-add (the old value of an add), no way to learn what the value was
  when a compare-and-set failed, and no atomic "apply this function" (high-water marks,
  doubling, clamping), so callers write their own retry loops and get them wrong.
- No way to keep a value inside a range: sequence numbers that wrap at `2**32`, pools that
  must not go negative, rate counters that saturate.
- The object cannot be pickled or copied (the lock inside is not picklable), so it cannot
  be sent to a process pool or deep-copied with a config object, and `int(counter)` fails.
- Tests show one exact total and one compare-and-set winner. Nothing proves that every
  operation takes effect at a single instant (linearizability) under heavy contention, on
  the free-threaded build in particular, where there is no GIL to hide a race.

## Sources (fetched 2026-10-12)

- https://docs.python.org/3/faq/library.html
  (sha256 9983bb85a43997c6f79d163b903360f31f95a991ec1474b772263bb737e3c236).
  "What kinds of global value mutation are thread-safe?": `i = i+1` is listed among the
  operations that are not atomic; "When in doubt, use a mutex!"
- https://docs.python.org/3/howto/free-threading-python.html
  (sha256 398fad2bea9aa36c5179f2ba45e66d1b7b7bba8a59958ea34af4bae69fecf476).
  "The new sys._is_gil_enabled() function can be used to check whether the GIL is actually
  disabled in the running process"; `sysconfig.get_config_var("Py_GIL_DISABLED")` tells
  whether the build supports free threading.
- https://docs.python.org/3/library/sys.html
  (sha256 695a3a619b986c8286ed25870b936bfbef6194c52420eb90c6451396469c3541).
  `sys._is_gil_enabled()`: "Added in version 3.13", "not guaranteed to exist in all
  implementations".
- https://docs.python.org/3/library/threading.html
  (sha256 551db9a4e51cdbaf6246b942cf4bbb7c6ff642ac1b54285c8a646ccf9ad0e6b7).
  A primitive lock "is not owned by a particular thread"; RLock may be acquired again by
  the same thread. A non-reentrant lock is why user callbacks must run outside it.
- https://docs.python.org/3/library/operator.html
  (sha256 15fca04fa9d557dbf35a800b1a2d82d1a80cb7a011bed4b0687f60c3f94a0e20).
  `operator.index(a)`: "Return a converted to an integer"; since 3.10 "the result always
  has exact type int".
- https://docs.python.org/3/library/pickle.html
  (sha256 259b6a60b0503bdfb062ab5ec64fa4cea9fc84c8e460a2f586a5556489fd5d1d).
  `object.__reduce__()` returns a callable and its arguments to rebuild the object.
- https://pypi.org/classifiers/
  (sha256 39f03d9d3d2ac2f11f6335ce6c4bfd9cee8005456b7df242638c3365636d6fbc).
  `Programming Language :: Python :: Free Threading :: 3 - Stable` and the per-version
  classifiers up to `3.14` exist.

## Ranked improvements

1. **Strict integer inputs.** Every value, amount and expected value goes through
   `operator.index`: real integers and integer-like objects (NumPy integers) pass, floats,
   strings and `bool` raise `TypeError` before anything changes.
2. **Fetch-then-modify operations.** `get_and_add(amount)` returns the old value;
   `compare_and_exchange(expect, new)` returns the value it saw, so a failed swap tells the
   caller what to retry with; `update(fn)` and `get_and_update(fn)` apply a function
   atomically. The function runs outside the lock in a compare-and-set loop, so it may run
   more than once under contention but can read the counter without deadlocking.
3. **`BoundedAtomicInt`.** An `AtomicInt` kept inside `[minimum, maximum]` (either side
   optional) with one overflow policy for every write: `raise` (`OverflowError`, value
   untouched), `saturate` (clamp to the nearest bound) or `wrap` (modular, both bounds
   required). Bad bounds or an unknown policy raise at construction.
4. **Linearizability contracts.** Dozens of threads with the switch interval lowered to
   force interleaving: every `increment` returns a distinct value and together they are
   exactly `1..N`; every read lies between the increments that finished before it started
   and those that started before it ended; compare-and-set loops never lose an update;
   bounded counters never leave their range and `raise` mode never changes the value.
5. **Free-threaded CPython.** The same suite runs on a free-threaded 3.14 interpreter with
   the GIL disabled (checked with `sys._is_gil_enabled()`), and the package declares the
   free-threading classifier.
6. **Pickle, copy and `int()`.** `__reduce__` rebuilds an independent counter with the
   same value (and bounds); `__int__` and `__index__` give a snapshot.
7. **Typed public API, proven.** mypy reveals the documented types and rejects wrong
   arguments (`add("1")`, an unknown overflow policy, a function returning `str`).
8. **Docs and packaging.** Every README example runs in the suite with its printed output
   checked, API table complete, CHANGELOG with the behaviour changes, version 0.2.0,
   Python version classifiers, installed-wheel e2e test.

## Out of scope

- A lock-free implementation: pure Python has no hardware compare-and-swap, and the
  compiled packages that do are the dependency this library exists to avoid.
- `__eq__`, `__hash__` and arithmetic dunders (`counter += 1`): a mutable counter that
  compares by value breaks dict keys, and `counter = counter + 1` would rebind the name
  instead of updating the shared object.
- Sharing one counter between processes: that needs shared memory; pickling produces an
  independent copy, which is documented.

## Verification

- Gates on CPython 3.13.2: `ruff format --check .`, `ruff check .`, `mypy --strict src tests`
  and `pytest` (with `ATOMICINT_E2E=1` the installed-wheel test runs too).
- The suite also passes on CPython 3.10.19 and on the free-threaded CPython 3.14.2 build,
  where `sys._is_gil_enabled()` is `False` for the whole run and a fresh interpreter that
  imports and uses the package keeps the GIL off.
- Guarded logic was removed one piece at a time (40 mutations: each lock, each range
  check, each coercion, each return value, the pickling hooks). The suite fails for every
  one, the lock removals also on the free-threaded build. The one survivor is removing
  the lock from `get()`: a single attribute read is already atomic, so no test can tell.
  The lock stays so the read is ordered with the writes by the same primitive.
