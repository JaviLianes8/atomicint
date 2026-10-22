# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-21

The first release on PyPI, and the API is now stable: `AtomicInt`, `BoundedAtomicInt`
and `Overflow`, with the names, signatures, defaults and error types of 0.2.0, are kept
for the whole 1.x series. Semantic Versioning applies from here on.

### Changed

- Error messages stay short whatever the input. An integer of more than 120 bits is
  written by its size (`<16610-bit integer> is outside [0, 5]`), a class name is cut
  after 60 characters, and an unknown overflow policy is shown by its first 40
  characters or by its type. Before, a value past Python's 4300-digit limit for
  `str(int)` turned the `OverflowError` of a bounded counter, and the `ValueError` for
  `minimum` greater than `maximum`, into an unrelated `ValueError` about that limit, and
  a long policy string or class name was copied into the message whole.
- `repr()` never fails: values of up to 1800 bits (541 digits) are written in full, larger
  ones by their size. Before, the repr of a value past the digit limit raised `ValueError`.
- The message for an unknown overflow policy reads
  `overflow must be 'raise', 'saturate' or 'wrap', not 'clamp'`.
- `AtomicInt` and `BoundedAtomicInt` report `atomicint` as their module, and a pickle now
  refers only to them and to the standard `copyreg` module, never to a private module.
  Counters pickled by 0.2.0 still load.

### Added

- A runnable example in the docstring of every public name, method and property; the
  examples run as doctests.
- `GUIDE.md`: the full behaviour of every operation, the overflow policies, errors,
  threads, copies and typing.
- Tests against independent references: Java's `AtomicLong`, `Math.clamp` and narrowing
  conversions, and JavaScript's `Atomics` on typed arrays, run live, plus the rules
  quoted from their fetched documentation.

## [0.2.0] - 2026-10-12

### Added

- `get_and_add(amount)`: add and return the previous value.
- `compare_and_exchange(expect, new)`: swap if equal and return the value seen, so a
  failed attempt tells the caller what to retry with.
- `update(fn)` and `get_and_update(fn)`: apply a function atomically. The function runs
  outside the lock and is retried with the fresh value when another thread wins the race.
- `BoundedAtomicInt`: an `AtomicInt` kept inside `[minimum, maximum]` with an overflow
  policy of `"raise"`, `"saturate"` or `"wrap"`, and the `Overflow` type for it.
- Copy, deep copy and pickle support: the copy is an independent counter with the same
  value, bounds and subclass attributes.
- `int(counter)` and `operator.index(counter)` return a snapshot.
- Tested on free-threaded CPython with the GIL disabled; free-threading classifier.

### Changed

- Values, amounts and expected values must be integers (anything with `__index__`).
  Floats and strings used to be converted with `int()`, truncating or parsing them; they
  and `bool` now raise `TypeError` and leave the value unchanged.
- `compare_and_set` rejects a non-integer `expect` instead of comparing it with `==`.
- `repr()` shows the subclass name.

## [0.1.0]

- First release.
- `AtomicInt` with `get`, `set`, `add`, `increment`, `decrement`,
  `compare_and_set` and `get_and_set`, each guarded by a single internal lock.
