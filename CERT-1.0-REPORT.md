# atomicint 1.0.0 certification report

The 1.0.0 certification bar (19 items) applied to atomicint. Nothing named `atomicint`
(or a confusable spelling) is on PyPI (`https://pypi.org/pypi/atomicint/json` answered
404 on 2026-10-22), so 1.0.0 is the first upload and there is no PyPI release to upgrade
from. The CHANGELOG still lists every change against 0.2.0, the last version on `main`.

Progress:
- [x] Branch `release/1.0.0` created from `main` (f173b53, 0.2.0)
- [x] Baseline gates on 0.2.0
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: reference documents fetched live, Java and JavaScript runtimes (item 7)
- [x] Contract, fuzz, linearizability and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [x] Packaging, e2e, every Python on this PC (items 8, 10, 13, 14)
- [x] Gates (item 15)
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer reports PASS (item 16)
- [x] PR #3 and trace guard CLEAN (item 17); merge and publish left to the maintainer

## Scorecard

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed for stability | PASS: the 3 names, 11 methods, 3 properties, parameter names and defaults of 0.2.0 kept and pinned (`tests/test_contract_api.py`); every change in CHANGELOG 1.0.0 |
| 2 | `__all__` exact, no private imports in docs | PASS: `AtomicInt`, `BoundedAtomicInt`, `Overflow`; the classes report `atomicint` as their module |
| 3 | Docstrings with runnable examples, doctests | PASS: 17 doctests (package, both classes, every method and property); README (5 blocks) and GUIDE (8 blocks) examples run with their printed output checked |
| 4 | Typed end to end | PASS: `mypy --strict src tests`, `py.typed`, revealed types and rejected misuse (`tests/test_typing.py`), a strict consumer type-checked against the installed wheel |
| 5 | Typed, documented, bounded errors | PASS: built-in `TypeError`, `ValueError`, `OverflowError`, GUIDE error table, messages at most 200 characters for any input |
| 6 | Contract tests of every public name | PASS |
| 7 | Real ground truth | PASS: 9 reference documents fetched with a hash manifest; Java 21 and Node.js run live as oracles |
| 8 | Real e2e from the wheel | PASS: sdist built, wheel built from it, installed offline into a fresh venv, driven from an empty folder with `-I`; no CLI exists; no PyPI release to upgrade from |
| 9 | Seeded fuzz, no crash, hang or blowup | PASS |
| 10 | Supported Pythons | PASS: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2, 3.14.2t; 3.8 and 3.9 are below `requires-python`; no 3.13t on this PC |
| 11 | README and `twine check` | PASS: `twine check --strict` PASSED for both files |
| 12 | Dated CHANGELOG section | PASS: `## [1.0.0] - 2026-10-21` |
| 13 | pyproject 1.0.0, Production/Stable | PASS |
| 14 | sdist and wheel contents | PASS |
| 15 | Gates each exit 0 | PASS: see Gates |
| 16 | Independent reviewer | pending (orchestrator) |
| 17 | PR and trace guard | PR #3 from `release/1.0.0`, trace guard CLEAN; merge and publish left to the maintainer |
| 18 | Contracts bite (mutations) | PASS: author 45 mutants, 44 killed at once, the survivor closed by a new contract |
| 19 | Five independent QA lenses | pending (orchestrator) |

## Baseline on 0.2.0 (before any change)

Fresh clone of `release/1.0.0` at f173b53 on another machine, CPython 3.14.2: `ruff format
--check .`, `ruff check .`, `mypy --strict src tests` exit 0; `pytest` with
`ATOMICINT_E2E=1` passed, the two free-threading tests skipped.

Defects found in 0.2.0 by reading and then reproducing with the 0.2.0 code:

- `BoundedAtomicInt(0, maximum=5).set(10**5000)` raised `ValueError` ("Exceeds the limit
  (4300 digits) for integer string conversion") instead of `OverflowError`, because the
  message called `str()` on the value; the same for `minimum` greater than `maximum`
  with such bounds.
- `repr(AtomicInt(10**5000))` raised that `ValueError`.
- An unknown policy string of 100,000 characters produced a 100,061-character message;
  a class name of 5,000 characters a 5,030-character `TypeError`.
- Pickles referred to the private `atomicint._atomic._blank` helper and private modules.
- No docstring had an example; the README linked LICENSE relatively; no GUIDE.

## API review (item 1)

Kept: `AtomicInt(value=0)` with `get`, `set`, `add`, `get_and_add`, `increment`,
`decrement`, `get_and_set`, `compare_and_set`, `compare_and_exchange`, `update`,
`get_and_update`; `BoundedAtomicInt(value=0, *, minimum=None, maximum=None,
overflow="raise")` with the read-only `minimum`, `maximum`, `overflow`; `Overflow`. The
names follow Java's `AtomicLong` (checked against its documentation in the tests).
Considered and left out: `get_and_increment` (`get_and_add(1)` covers it and it can be
added in a minor release), value equality and arithmetic operators (a mutable counter
that hashes by value breaks dictionaries), truthiness by value (would change existing
`if counter:` code). Changed, all in the CHANGELOG and GUIDE: bounded messages and
`repr`, the policy message wording, public module names and pickles. Internal: the
copy and pickle support moved to `_state.py` to keep every file under 200 lines.

## Ground truth (item 7)

Fetched on 2026-10-22 by `scripts/fetch_upstream.py` into the ignored `tests/upstream`
folder; `tests/upstream/MANIFEST.json` records URL, revision, size, sha256 and licence,
the tests check the hash before reading, and a second fetch on another machine matched
every hash. Nothing fetched is committed or shipped.

- Java SE 21 `AtomicLong` documentation (`tests/test_spec.py`): the "Returns:" rule of
  `getAndAdd`, `addAndGet`, `incrementAndGet`, `decrementAndGet`, `getAndSet`,
  `compareAndExchange`, `updateAndGet`, `getAndUpdate` is read from the page and checked
  on the matching method; `compareAndSet` success and failure; "may be re-applied when
  attempted updates fail due to contention" checked with a raced update.
- Java SE 21 `Math.clamp(long, long, long)`: its three rules and its
  `IllegalArgumentException` for `min > max` against the saturate policy.
- Java Language Specification SE 21, section 5.1.3: the narrowing rule ("discards all but
  the n lowest order bits") implemented from the sentence and compared with wrap on
  8, 16, 32 and 64 bits, signed and unsigned, 502 values each up to 200 bits.
- MDN (`mdn/content` 468fcd167cd6): `Atomics.compareExchange` and `Atomics.add` return
  the old value, `Uint8ClampedArray` clamps to 0..255.
- CPython v3.14.0 docs: the FAQ lists `i = i+1` as not atomic (the README's claim);
  the free-threading HOWTO documents `sys._is_gil_enabled()` and `Py_GIL_DISABLED`.
- trove-classifiers 2026.9.21.13: every classifier in `pyproject.toml` exists.

Reference runtimes run live (`scripts/oracle`, `tests/test_oracle_java.py`,
`tests/test_oracle_node.py`): Java 21's `AtomicLong` on 9,000 seeded operations of all
eleven kinds, `Math.clamp`, Java narrowing casts and 64-bit `long` addition on 16,308 more;
JavaScript `Atomics` on all eight integer typed arrays (320 programs of 60 operations, 8 to
64 bits, signed and unsigned) and `Uint8ClampedArray` (200 programs). No difference.

Upgrade: counters pickled by the 0.2.0 code (real output, protocols 0, 2 and 5) load and
work (`tests/test_upgrade.py`).

## Contracts, fuzz and concurrency (items 6, 9)

- `tests/test_contract_api.py`: signatures, members, slots, module names, the `Overflow`
  arguments, identity and truthiness, an example in every docstring, the error type of
  each failure.
- `tests/test_fuzz.py`: three seeds of 1,000 random configurations (ranges of 1 to 300
  bits, one or no bound, all three policies) with 60 operations each, wrong-typed inputs
  mixed in, against a model written by hand from the documented rules; result, error
  type and remaining value must match; copies at the end. Hooks that raise or use the
  counter themselves (no deadlock, value untouched).
- `tests/test_messages.py`: integers past the digit limit under the strictest digit
  setting, 100,000-character policies, 5,000-character class names: every message at
  most 200 characters, `repr` never fails.
- `tests/test_linearizability.py`: 300 recorded four-thread histories of all nine
  read/write operations mixed, plain and wrapping, checked by a hand-written Wing and Gong
  search (itself tested on accept and reject cases); about a third of neighbouring calls
  overlap in time.
- Existing stress tests: distinct increments, ticket hand-out, read ordering, CAS loops,
  bounded permit pools, saturate and wrap under 16 threads with a 1 µs switch interval.

## Author mutation round (item 18)

45 mutants over every module, each alone on a copy of the branch at 4d3f9ec, full
suite with `-x` on another machine with Java, Node.js and the fetched files present. 44
killed at once; B10 (repr of bounds between 121 and 1800 bits) survived and is killed by
the contract added in b9c1f15. Table: [CERT-1.0-MUTANTS.md](https://github.com/JaviLianes8/atomicint/blob/main/CERT-1.0-MUTANTS.md).

## Packaging, e2e and Pythons (items 8, 10, 13, 14)

- `tests/test_e2e_dist.py` and `tests/test_e2e_wheel.py` (with `ATOMICINT_E2E=1`): the
  sdist is built, the wheel built from it; wheel members are exactly the six package files
  and the metadata files with the licence; the sdist holds sources, tests, scripts, docs
  and only the manifest of the fetched folder; metadata 1.0.0, `Requires-Python >=3.10`,
  no runtime dependency, Production/Stable, 3.10 to 3.14, MIT, the four project URLs;
  `twine check --strict` passes; the wheel installed with `--no-index` into a fresh venv
  runs a threaded consumer from an empty folder with `-I`, and `mypy --strict` accepts a
  consumer script against that install. atomicint has no command line.
- Every interpreter on this PC from `requires-python` up, at 4d3f9ec: the built wheel in
  a fresh venv, the sdist's suite with `src` removed (fetched files, Java 21.0.8 and
  Node.js 24.18.0 present) and the doctests of the installed package: CPython 3.10.19,
  3.11.5, 3.12.12, 3.13.2 and 3.14.2: 266 passed, 9 skipped (the e2e tests, which run
  separately, and the two free-threading tests); 3.14.2t: 268 passed, 7 skipped, GIL
  disabled; 17 doctests passed on each.

## Gates (item 15)

At b9c1f15 on another machine from a fresh clone, CPython 3.14.2, each command on its
own, with the fetched files, Java 21.0.12 and Node.js 25.5.0, `ATOMICINT_E2E=1`:
`ruff format --check .`, `ruff check .`, `mypy --strict src`, `mypy --strict src tests`
and `pytest` (291 passed, 2 skipped: the free-threading tests) all exit 0.
