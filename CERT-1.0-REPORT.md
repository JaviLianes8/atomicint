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
| 2 | `__all__` exact, no private imports in docs | PASS: `AtomicInt`, `BoundedAtomicInt`, `Overflow`; the classes keep the module that defines them, so tools find their source, and the paths pickles name are pinned |
| 3 | Docstrings with runnable examples, doctests | PASS: 18 doctests (package, `Overflow`, both classes, every method and property); README (5 blocks) and GUIDE (9 blocks) examples run with their printed output checked, and pass `mypy --strict` |
| 4 | Typed end to end | PASS: `mypy --strict src tests`, `py.typed`, revealed types and rejected misuse (`tests/test_typing.py`), a strict consumer type-checked against the installed wheel |
| 5 | Typed, documented, bounded errors | PASS: built-in `TypeError`, `ValueError`, `OverflowError`, GUIDE error table, messages at most 200 characters for any input |
| 6 | Contract tests of every public name | PASS |
| 7 | Real ground truth | PASS: 9 reference documents fetched with a hash manifest; Java 21 and Node.js run live as oracles |
| 8 | Real e2e from the wheel | PASS: sdist built, wheel built from it, installed offline into a fresh venv, driven from an empty folder with `-I`; no CLI exists; no PyPI release to upgrade from |
| 9 | Seeded fuzz, no crash, hang or blowup | PASS |
| 10 | Supported Pythons | PASS: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2, 3.14.2t; 3.8 and 3.9 are below `requires-python`; no 3.13t on this PC |
| 11 | README and `twine check` | PASS: `twine check --strict` PASSED for both files |
| 12 | Dated CHANGELOG section | PASS: `## [1.0.0] - 2026-10-22` (moved from 2026-10-21 in QA round 1; it must name the upload day if that is later) |
| 13 | pyproject 1.0.0, Production/Stable | PASS |
| 14 | sdist and wheel contents | PASS |
| 15 | Gates each exit 0 | PASS: see Gates |
| 16 | Independent reviewer | pending (orchestrator) |
| 17 | PR and trace guard | PR #3 from `release/1.0.0`, trace guard CLEAN; merge and publish left to the maintainer |
| 18 | Contracts bite (mutations) | PASS: author 45 mutants, 44 killed at once, the survivor closed by a new contract; after QA round 1, 22 more over the new code, all killed (one after a new contract); after QA round 2, the four survivors of the mutation lens and three new mutants, all killed by new contracts |
| 19 | Five independent QA lenses | round 1: 18 findings, all fixed; round 2 (lenses a, c, d and e at 51e2af2): 11 findings, all fixed, none disputed (see QA lenses); re-verification by the lenses pending |

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
  sdist is built, the wheel built from it; wheel members are exactly the package files
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

## QA lenses (item 19)

### Round 1 (lenses a to e at cd17c8b)

| Lens | Id | Severity | Finding | What changed |
| --- | --- | --- | --- | --- |
| c | F1 | high | A counter used from a finalizer (`__del__`, weakref callback) or a signal handler that interrupts an operation on the same counter hangs the process: operations ran Python code (`_fit`, messages, `capture`) while holding a non-reentrant lock | No Python code runs under the lock any more (new `_commit.py`): inputs, overflow policies, messages, update functions and copy state are computed outside it; a value computed outside is stored only if the value it came from is still there; the in-range check of a bounded add is a comparison with infinities, which runs in C; the lock is a `threading.RLock`. CHANGELOG "Fixed", GUIDE model, threads (with a runnable `__del__` example) and cost sections |
| c | F2 | low | `__index__` was fetched from the type and called unbound (a `classmethod` or `staticmethod` hook failed), and `isinstance` trusted a spoofed `__class__` (a hook answering `True` got past the `bool` check) | The real type is checked; the hook is found along the real MRO and bound through its descriptor as CPython does; the result's real type is checked. CHANGELOG "Fixed", GUIDE inputs |
| a | A1 | low | README and GUIDE named the update parameter `fn`; the keyword is `function` | README, GUIDE and the CHANGELOG 0.2.0 entry say `function`; the signature is unchanged and stays pinned |
| a, b | A2, F1 | low | "1800 bits (541 digits)": the maximum is 542 | CHANGELOG and the `_coerce.py` comment say 542 |
| a | A3 | low | `Overflow` had no docstring of its own | `Overflow` has one with a runnable example, collected as a doctest. It is set on an alias object of its own (a nested `Literal`, the same type once flattened): typing caches `Literal[...]` by its arguments, and setting `__doc__` on the cached object changed `help()` for any identical alias elsewhere (checked on 3.10 to 3.14) |
| a, b, d | A4, F2, D1 | low | CHANGELOG dated 1.0.0 2026-10-21, before its own commits; 0.1.0 had no date | 1.0.0 dated 2026-10-22, 0.1.0 dated 2026-10-11 (its git date) |
| b | OBS1 | low | `expect` is compared exactly, not narrowed into the range as C and JavaScript do | Kept (deliberate); the GUIDE states it with the 8-bit example |
| d | D2 | low | CONTRIBUTING said tests never touch the network, yet `ATOMICINT_E2E=1` fetches the build backend | CONTRIBUTING and the conftest docstring say the e2e mode needs the package index; a failed build names that cause first |
| e | F1-M28 | medium | Nothing checked that `int()` and `operator.index()` return the value | `test_int_and_index_give_the_current_value` (negative, zero, positive, 200-bit, both classes) and negative indexing and slicing with counters |
| e | F2-M47 | medium | Copies of an underscored subclass with a private slot were never tested | `test_a_private_slot_of_an_underscored_subclass_is_copied` under copy, deepcopy and every pickle protocol |
| e | F3-M48 | low | Nothing checked that a copy gets a lock of its own | `test_a_copy_has_a_lock_of_its_own`: distinct locks, and a sibling copy stays usable from another thread while one copy's lock is held |
| e | F4-M06 | low | The 60-character cut of type names was not tested at its boundary | `test_a_type_name_is_cut_only_past_60_characters` (59, 60, 61) |
| e | F5-M44 | low | The 40-character cut of policy strings was not tested at its boundary | `test_a_policy_is_cut_only_past_40_characters` (39, 40, 41) |

The lenses' run summaries and observations (the GUIDE link that answers 404 until the pull
request is merged, CPython 3.10 missing on one lens's machine) need no change in the
repository. No finding is disputed.

How the behaviour bugs were fixed, test first:

- c/F1: `tests/test_reentry.py` runs, in a fresh interpreter each, a cyclic object whose
  `__del__` writes to the counter during every operation (13 on `AtomicInt`, 13 under each
  bounded policy, plus a refused write), a finalizer balance count, and a signal handler
  that adds to the counter its own thread is adding to, counting that nothing is lost.
  On cd17c8b with CPython 3.13.2, 37 of 59 failed (hangs). `tests/test_reentry_lock.py`
  runs an operation inside a locked step of the same thread, deterministically, also on
  copies and unpickled counters. Why a reentrant lock: on CPython 3.14.2 a signal handler
  runs right after `with lock:` acquires, even around a body with no calls (a plain `Lock`
  hung in a probe, an `RLock` did not). Why no update is lost: in each locked block the
  only conditional jump that can be taken before the store is the one that skips it;
  CPython 3.11 and later check for pending calls only at calls and backward jumps, and
  3.10 also at taken conditional jumps (read in `Python/ceval.c` of v3.10.19).
- c/F2: `tests/test_inputs.py` gained the `classmethod`, `staticmethod`, spoofed
  `__class__` (with and without a hook, and as a hook result) and hook-override cases;
  red on cd17c8b, green after.
- a/A3 got its contract first:
  `test_overflow_has_its_own_docstring_with_a_runnable_example`.

Verification after the fixes:

- The reentry programs on CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2t
  (GIL disabled): 57 programs each, 0 failures. A mixed probe (four threads adding, the
  main thread adding while a signal handler and finalizers add too) ends with the exact
  total on 3.10, 3.11, 3.13, 3.14 and 3.14t.
- The suite at 4f02eac on every interpreter of this PC (Java 21 and Node.js present,
  e2e off): 387 passed and 9 skipped on 3.10.19, 3.11.5, 3.12.12, 3.13.2 and 3.14.2
  (the seven e2e tests and the two free-threading tests); 389 passed and 7 skipped on
  3.14.2t.
- Gates at 4f02eac on another machine from a clone, CPython 3.14.2, `ATOMICINT_E2E=1`,
  fetched reference files present (no Java there, so the five Java oracle tests skipped;
  they pass in the run above): `ruff format --check .`, `ruff check .`,
  `mypy --strict src`, `mypy --strict src tests` and `pytest` (389 passed, 7 skipped)
  each exit 0.
- Mutations: the lens's five survivors are killed, and 22 author mutants over the new
  code are killed ([CERT-1.0-MUTANTS.md](https://github.com/JaviLianes8/atomicint/blob/main/CERT-1.0-MUTANTS.md)).
- Cost on CPython 3.13.2, same machine and method as the GUIDE: `get` 157 ns, `increment`
  351 ns, `compare_and_set` 508 ns, bounded `increment` 471 ns (cd17c8b in the same
  session: about 152, 322, 520 and 461 ns).

Commits of this round: 230f5d6 (lock discipline, index binding, docs, contracts), 7aaed46,
69996f5, 0641a20, 98138e8 (range check under the lock), 0024069, 4f02eac, and the commit
that records this section.

### Round 2 (lenses a, c, d and e at 51e2af2)

| Lens | Id | Severity | Finding | What changed |
| --- | --- | --- | --- | --- |
| a, d | F1, D1 | medium | Setting `__module__ = "atomicint"` on the classes (and their methods) broke source lookup: `inspect.getsource` raised `OSError` on 3.10 to 3.14t, `getsourcefile` named `__init__.py`, doctest reported the examples in `__init__.py` with no line | The rewrite is gone: the classes keep `atomicint._atomic` and `atomicint._bounded`. Pickles name those class paths and `copyreg.__newobj__` only (no helper function); 0.2.0 pickles already name the same paths, so they had to stay importable anyway, and the GUIDE and CHANGELOG now say they do for the whole 1.x series. Contracts: source file, class source, method source, and doctest file and line of every class and method; the pickle names; the e2e consumer calls `inspect.getsource` on the installed wheel |
| a | F2 | low | The README update example (`lambda current, s=sample: ...`) failed `mypy --strict` ("Cannot infer type of lambda") | The example is `lambda current: max(current, sample)`. New `test_the_doc_examples_pass_strict_type_checking` runs `mypy --strict` over every README and GUIDE block; only the first line of a `try` block (a refused input written on purpose) may be an error |
| a | F3 | low | A policy of the wrong type (`None`, `5`, a `str` subclass) raised `ValueError`, while every other wrongly typed argument raises `TypeError` | A policy that is not a plain `str` raises `TypeError` ("overflow must be a plain str, not NoneType"); an unknown string still raises `ValueError`. CHANGELOG "Changed" (the 1.0.0 summary names this one change of error type from 0.2.0), GUIDE bounded section and error table |
| c | F1 | medium | With a trace, profile or monitoring hook installed, a finalizer or signal handler run by the hook between an operation's read and its store loses its update, which the GUIDE, the class docstring and the CHANGELOG promised could not happen | Documented, as no pure Python code can close it (a hook can run at any line or instruction): the GUIDE threads section has a "two limits" paragraph, the `AtomicInt` docstring and the CHANGELOG entry name the limit, and "runs no Python code" now reads "no Python code of its own". `tests/test_limits.py` pins the limit deterministically with the lens's tracer |
| c | F2 | low | Copies and pickles of a subclass named only with underscores (`_`, `__`) dropped its private slots: the copy looked for `___tag`, Python keeps `__tag` | `slot_names` mangles only when the class name has something left after stripping underscores, as `copyreg._slotnames` does. Classes `_` and `__` added to the copy, deepcopy and pickle contract (red before, green after). CHANGELOG "Fixed" (0.2.0 had the same bug) |
| c | F3 | low | On CPython 3.14 a `KeyboardInterrupt` that arrives just after `with lock:` took the lock leaves it held; other threads then wait forever | Documented in the GUIDE's "two limits" paragraph and the CHANGELOG, with what a program should do. The root cause is the 3.14 `with` statement (the lens's control leaked a bare `RLock` the same way); a mitigation would need private `RLock` methods and a call on every operation. `tests/test_limits.py` pins the behaviour with a lock that is interrupted right after it is taken |
| e | F1-X33 | high | The retry loop of an out-of-range compare-and-set was not pinned: a mutant that reported success without storing, after losing a race to an equal-valued write, survived | `tests/test_races.py`: another thread's write lands exactly while the policy is applied outside the lock (through the policy step of a subclass): an equal value as a new object, a different value, and an out-of-range add, for saturate and wrap |
| e | F2-X31 | medium | Nothing checked that update functions run outside the lock | `test_the_function_runs_without_the_lock`: while the function runs, another thread reads the counter, and its write makes the update retry, for `update` and `get_and_update` |
| e | F3-X62 | medium | The 120-bit cut was not pinned for the bounds in an `OverflowError` | `test_bounds_past_120_bits_are_described_by_their_size`: both bounds, and a 120-bit bound written in full |
| e | F4-X13 | low | Copying or pickling a subclass with a `__weakref__` slot was not pinned | `test_a_weakly_referenced_subclass_is_copied`, with a live weak reference, under copy, deepcopy and every pickle protocol |

Lens a's evidence notes (`dir(atomicint)` showing `annotations`, `help()` showing the
private bases) and lens d's process note need no change. The GUIDE's cost figures were not
re-measured: this round changes no locked step and no operation path, only the
constructor's policy check and the module attribute. No finding is disputed.

Verification:

- The new contracts were red on the code before each fix: the policy type (10 cases),
  source lookup and module paths (2 tests), the pickle names (6 protocols), the underscore-only
  class names (16 cases) and the doc type check.
- Mutations, each alone on a copy of the fixed tree, CPython 3.13.2 on this PC with Java
  21.0.8 and Node.js present, `tests` with `-x`, fetched reference files absent: X33, X31,
  X62 and X13 from the lens, plus the mangling of `_`-only class names, `ValueError` for a
  wrongly typed policy and the old `__module__` rewrite: all killed, each by the contract
  added for it ([CERT-1.0-MUTANTS.md](https://github.com/JaviLianes8/atomicint/blob/main/CERT-1.0-MUTANTS.md)).
- Gates at 046aaac on another machine from a fresh clone, CPython 3.14.2, fetched
  reference files present, `ATOMICINT_E2E=1`: `ruff format --check .`, `ruff check .`,
  `mypy --strict src`, `mypy --strict src tests` and `pytest` (434 passed, 7 skipped: the
  two free-threading tests and the five Java oracle tests, no Java there) each exit 0.
- The suite at 046aaac on every interpreter of this PC (Java 21 and Node.js present, e2e
  off): 432 passed and 9 skipped on CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2 and 3.14.2;
  434 passed and 7 skipped on 3.14.2t with the GIL disabled.

Commits of this round: 016f1ab (policy type), da6f468 (module and source lookup),
1cb8697 (underscore-only class names), 3f82b99 (race and update contracts), e692e78
(limits pinned, docstrings), 886c376 (doc type check, README example), 05e12ea
(CHANGELOG and GUIDE), 046aaac (wheel e2e), and the commit that records this section.
