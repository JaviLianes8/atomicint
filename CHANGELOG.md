# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0]

### Added

- `get_and_add(amount)`: add and return the previous value.
- `compare_and_exchange(expect, new)`: swap if equal and return the value seen, so a
  failed attempt tells the caller what to retry with.
- `update(fn)` and `get_and_update(fn)`: apply a function atomically. The function runs
  outside the lock and is retried with the fresh value when another thread wins the race.
- `BoundedAtomicInt`: an `AtomicInt` kept inside `[minimum, maximum]` with an overflow
  policy of `"raise"`, `"saturate"` or `"wrap"`, and the `Overflow` type for it.
- Copy, deep copy and pickle support: the copy is an independent counter with the same
  value and bounds.
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
