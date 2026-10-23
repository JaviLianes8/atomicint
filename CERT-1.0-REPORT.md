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
| 18 | Contracts bite (mutations) | PASS: author 45 mutants, 44 killed at once, the survivor closed by a new contract; after QA round 1, 22 more over the new code, all killed (one after a new contract); after QA round 2, the four survivors of the mutation lens and three new mutants, all killed by new contracts; after the round 2 re-check, the lens's eight survivors and six mutants of the rewritten slot lookup, all killed; after QA round 3, the lens's five survivors and four mutants of the stored slot names, all killed, one more equivalent; after QA round 4, the lens's six survivors (V19, V20, S06, S09, S12, S15), three more allocation mutants and nine mutants of the new slot code, all killed; after the fixes of the round 5 probes, 22 mutants of the new code, 19 killed and 3 explained (two equivalent, one with no effect on a copy); after QA round 6, 14 mutants of the new code and the stronger tests, all killed (lens e's S10 among them); after QA round 7, lens e's seven survivors and five mutants of the new code, all killed |
| 19 | Five independent QA lenses | round 1: 18 findings, all fixed; round 2 (lenses a, c, d and e at 51e2af2): 11 findings, all fixed, none disputed (see QA lenses); round 2 re-check (lenses c and e at 08186fc): 9 findings, all fixed, none disputed; round 3 (lenses c and e at 90eab2e): 6 findings (plus a closed re-check and a summary), all fixed, none disputed; round 4 (lenses c and e at b7e720a): 7 findings (plus four closed re-checks and a summary), all fixed, none disputed; round 5 (lenses c and e at 54db276) was interrupted before it reported, and the four defects its probes show are fixed (see Round 5 probes); round 6 (lenses a, c, d and e at a270808): 7 findings (plus two summaries), all fixed, none disputed; round 7 (lenses a, c, d and e at 3d26d7b): every round 6 finding confirmed fixed, 12 new findings (10 distinct: three lenses reported the same `__get__ = None` gap) plus a closed re-check and a summary, all fixed, none disputed; re-verification by the lenses pending |

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

### Round 2 re-check (lenses c and e at 08186fc)

Lens e confirmed the four findings of its round 2 fixed at 08186fc (each mutant killed by
the contract added for it, each probe correct) and reported eight surviving mutants. Lens
c found one new defect in the slot code changed by 1cb8697.

| Lens | Id | Severity | Finding | What changed |
| --- | --- | --- | --- | --- |
| c | F4 | low | A subclass whose `__slots__` is an iterator (allowed by the language reference) lost its slot values in copies, deep copies and pickles: the iterator is used up when the class is made, so the copy found no names to read. The standard library refuses such a copy with `TypeError` instead of losing data | `slot_names` no longer reads `__slots__` or mangles names itself: it lists the member descriptors Python created on each class of the hierarchy (`types.MemberDescriptorType` whose `__objclass__` is that class), minus `_lock`. The names are exactly the ones Python uses, so a class renamed after it was made keeps its private slots too, and `__dict__` and `__weakref__` (not members) need no skip list. Red before, green after: `tests/test_copy_slots.py` (iterator slots on `AtomicInt` and `BoundedAtomicInt`, the renamed class) under copy, deepcopy and every pickle protocol. CHANGELOG "Fixed" and the GUIDE copies section updated |
| e | N1-P30 | medium | Nothing pinned that the in-range compare-and-set makes no call under the lock: a mutant that called `self._within(seen)` there survived on 3.14 and 3.14t, breaking the finalizer and signal handler promise | `tests/test_lock_calls.py`: the lock is replaced by one that knows when it is held, and a profile hook records every Python and C call made while it is. CPython runs a finalizer or signal handler only at a call or a backward jump, so an empty record is the promise itself. 19 operations (each compare in range, out of range, won and lost; adds and sets in and out of range; updates, `int`, `repr`, copy, pickle) on `AtomicInt` and under each bounded policy. Deterministic, unlike a timing probe |
| e | N2-P13 | medium | Nothing pinned a private slot declared by an intermediate class | Case `Child` (a subclass of a class that declares `__tag`) in `test_every_declared_slot_is_kept` |
| e | N3-P18 | low | Nothing pinned a class whose `__qualname__` differs from `__name__` | Case `Outer.Inner` (a class nested in another, picklable) |
| e | N4-P19 | low | Nothing pinned a class name with a trailing underscore | Case `Tag_` (`__tag` is `_Tag___tag`) |
| e | N5-P16 | low | Nothing pinned slot names that also end in `__`, which Python does not mangle | Case `Meta` (`__tag__`) |
| e | N6-P17 | low | Nothing pinned `__slots__` given as one string | Case `One` (`__slots__ = "tag"`) |
| e | N7-P20 | low | Nothing pinned a subclass that declares a `__dict__` slot | `test_a_declared_instance_dict_is_copied_not_shared`: after copy, deepcopy and every pickle protocol, the twin has its own dictionary and writing to it leaves the original alone |
| e | N8-P33 | low | Nothing pinned the 121-bit edge of a bound in an `OverflowError` | `test_bounds_past_120_bits_are_described_by_their_size` gained bounds of exactly 121 bits on both sides |

Lens e's note on an earlier unreported attempt at 51e2af2 (its survivors in `_coerce`, on
code unchanged since then, are outside this re-check) and lens c's note on renamed classes
need no other change: renamed classes are covered by the F4 fix. The GUIDE's cost figures
were not re-measured: this round changes no operation path, only the copy code and tests.
No finding is disputed.

Verification:

- Red before the fix: on 08186fc the new slot contract failed 24 cases (iterator slots on
  both classes and the renamed class, under copy, deepcopy and pickle protocols 0 to 5).
- Mutants: N1-P30 is killed by
  `tests/test_lock_calls.py::test_no_operation_makes_a_call_while_it_holds_the_lock[cas_won-plain]`
  and N8-P33 by `tests/test_messages.py::test_bounds_past_120_bits_are_described_by_their_size`,
  each applied alone to the fixed tree. N2 to N7 mutate the mangling code that the fix
  removed; applied to the 08186fc `_state.py`, each is killed by the case added for it
  (`Child`, `Outer.Inner`, `Tag_`, `Meta`, `One`, the `__dict__` test) with the iterator
  and renamed cases left out. Six mutants of the new slot lookup are killed too
  ([CERT-1.0-MUTANTS.md](https://github.com/JaviLianes8/atomicint/blob/main/CERT-1.0-MUTANTS.md)).
- Gates at 729224f on another machine from a clone, CPython 3.14.2, fetched reference
  files present, `ATOMICINT_E2E=1`: `ruff format --check .`, `ruff check .`,
  `mypy --strict src`, `mypy --strict src tests` and `pytest` (582 passed, 7 skipped: the
  two free-threading tests and the five Java oracle tests, no Java there) each exit 0.
- The suite at 729224f on every interpreter of this PC (e2e off): 580 passed and 9 skipped
  on CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2 and 3.14.2; 582 passed and 7 skipped on
  3.14.2t with the GIL disabled.

Commits of this round: 7b09994 (slot lookup from the member descriptors, CHANGELOG,
GUIDE), 729224f (lock-call and 121-bit contracts), and the commit that records this section.

### Round 3 (lenses c and e at 90eab2e)

Lens c confirmed its F4 fixed at 90eab2e on all six interpreters and found three new
defects in the slot lookup that 7b09994 introduced. Lens e confirmed all eight findings of
its re-check fixed, proved four of its survivors equivalent (M05, M09, M10, M12) and
reported three gaps in the contracts.

| Lens | Id | Severity | Finding | What changed |
| --- | --- | --- | --- | --- |
| c | F4 | low | Re-check: iterator `__slots__` kept through copy, deepcopy and pickle | Nothing to change; still pinned by the `Streamed` cases |
| c | F5 | medium | `slot_names` iterated the live dictionary of every class in the MRO on each copy, so a copy raised an undocumented `RuntimeError` while another thread set or deleted a class attribute, and on 3.14t could lose a slot | A class's slot names are worked out once, when the class is made (`Copyable.__init_subclass__`), and stored on the class; a copy reads that tuple and iterates no class dictionary. Where the names must still be worked out at copy time (a subclass of a class whose `__init_subclass__` skips `super()`), each dictionary is copied before it is read. Contract `tests/test_copy_cost.py::test_a_copy_is_safe_while_another_thread_changes_the_class`: two threads copy (copy, deepcopy, pickle) for 1 s while a third sets and deletes class attributes, for a plain subclass and one under a base that skipped the hook; no error and no slot missing |
| c | F6 | low | A slot whose member descriptor was replaced on the class by a wrapping property was silently dropped from copies, deep copies and pickles | Fixed by the same change: the names are fixed before any wrapper can replace a descriptor. Cases `Wrapped` and `WrappedChild` (a subclass made after the wrap) in `tests/test_copy_slots.py::test_inherited_and_wrapped_slots_are_kept` |
| c | F7 | low | De-duplication searched a list inside the loop over slots: one copy cost O(slots squared), 305 ms for 8000 slots | Names collected into a dict and stored per class, so a copy is one pass over the stored names. `test_a_copy_costs_about_what_the_standard_copy_of_a_plain_class_costs`: with 8000 slots, a copy must take less than 10 times `copy.copy` of a plain class with the same slots (161.7 times at 90eab2e, about 1 now) |
| e | F1-V01-V04-V06 | medium | A call of a type (`int(...)`, `bool(...)`) under the lock broke the finalizer and signal handler promise and survived the suite: the profile hook of `test_lock_calls.py` does not see calls of types | `tests/test_lock_calls.py` also records the `sys.monitoring` CALL events on 3.12 and later, which fire for every call, types included (the lock's own `__exit__` is the one call allowed). Deterministic, so it was chosen over the timing-based signal probe. 3.10 and 3.11 have no such API and keep the profile hook alone; the interpreter matrix of every certification run includes 3.12 to 3.14t |
| e | F2-M02 | low | Nothing pinned a slot declared two or more levels above the copied class | Cases `Leaf` (slot two levels up) and `QuietLeaf` (two levels up, past a base that skipped the hook) for every clone, and `test_a_grandchild_keeps_its_bounds_and_policy` (a grandchild of `BoundedAtomicInt`: value, bounds, policy, repr). With names stored per class, the M02 mutation in `_collect` changes the result only on the fallback path, so `QuietLeaf` is the case that kills it |
| e | F3-M19 | low | Nothing pinned that a copy is rebuilt past a subclass's own `__setattr__` | `test_a_copy_is_rebuilt_past_the_subclass_setattr`: a subclass whose `__setattr__` refuses its slot after construction, under copy, deepcopy and every pickle protocol |

Lens e's summary entry needs no change. CHANGELOG "Fixed" (slot entry) and the GUIDE copies
section now say the names are read once when the class is made, that a wrapped slot is
still copied and that a copy is safe while another thread changes the class. The GUIDE's
cost figures were not re-measured: no operation path changed. No finding is disputed.

Verification:

- Red before the fix: the 90eab2e `_state.py` with the new tests fails 23 cases (16 for
  `Wrapped` and `WrappedChild` under copy, deepcopy and pickle protocols 0 to 5, the 6
  race cases, the cost test). The lens's probes on the fixed tree: `p21_class_dict_race.py`
  0 errors on 3.13.2 (84837 copies) and 3.14.2t (81570), `p12_wrapped_slot.py` keeps
  `primary`, `p22_scaling.py` 1.80 ms per copy at 8000 slots.
- Mutants, each alone on a copy of the fixed tree, CPython 3.13.2 on this PC: V01, V04,
  V06, M02 and M19 from the lens and four of the new code (S1, S2, S4, S5), all killed;
  a fifth of the new code (S3) is equivalent (see CERT-1.0-MUTANTS.md).
- Gates at 04d028d on another machine from a clone, CPython 3.14.2, fetched reference
  files present, `ATOMICINT_E2E=1`: `ruff format --check .`, `ruff check .`,
  `mypy --strict src`, `mypy --strict src tests` and `pytest` (637 passed, 7 skipped: the
  two free-threading tests and the five Java oracle tests, no Java there) each exit 0.
- The suite at 04d028d on every interpreter of this PC (e2e off): 635 passed and 9 skipped
  on CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2 and 3.14.2; 637 passed and 7 skipped on
  3.14.2t with the GIL disabled.

Commits of this round: 04d028d (slot names stored per class, lock-call monitoring, new
contracts, CHANGELOG, GUIDE) and the commit that records this section.

### Round 4 (lenses c and e at b7e720a)

Lens c confirmed F4 to F7 fixed on all six interpreters and found three new defects in the
per-class slot names that 04d028d introduced. Lens e confirmed all five of its round 3
findings fixed, proved three survivors equivalent (V17, V18, S08) and reported four gaps
in the contracts.

| Lens | Id | Severity | Finding | What changed |
| --- | --- | --- | --- | --- |
| c | F4, F5, F6, F7 | low | Re-checks: iterator `__slots__`, the class change race, the wrapped slot and the copy cost all fixed | Nothing to change; still pinned by their round 3 contracts |
| c | N1 | medium | The stored names were an attribute on the class, so a class rebuilt from a copy of another's namespace (`dataclass(slots=True)`, attrs, `type(name, bases, dict(cls.__dict__))`) took the stale tuple and copies silently dropped its new slots; a class attribute of that name lost the slots, and a slot of that name failed class creation | The names are kept in a `weakref.WeakKeyDictionary` keyed by the class itself, so nothing is added to a subclass's namespace and a rebuilt class is a new key. This goes one step past the suggested owner check: with the owner stored on the class, a slot of that name would still be replaced by the tuple. Contracts in `tests/test_class_hooks.py`: `Point` and `Reading` (`dataclass(slots=True)` over both classes), `Rebuilt` (a hand-made rebuild), `Clash` (a slot named `_atomicint_slot_names`), `Shadow` (a class attribute of that name), under copy, deepcopy and pickle protocols 0 to 5, and `test_a_subclass_namespace_gets_nothing_added` |
| c | N2 | low | A slot was dropped when a base's `__init_subclass__` wrapped the subclass's slots before calling `super()` | The names listed in `__slots__` are added to the member scan when `__slots__` can be read again (a string, tuple, list, dict, set or frozenset), private ones mangled with the class name stripped of leading underscores, as Python does. Cases `Checked`, `Private` (list, private name), `Documented` (dict) and `_Hidden` (one string, a class name with a leading underscore) under a wrapping base |
| c | N3 | low | Making a class cost the square of its hierarchy depth: every stored tuple in the MRO was merged although each already holds its bases' names | `_collect` skips the classes a used tuple already covers. `test_making_a_class_costs_about_what_python_takes_whatever_the_depth`: one more class on a chain of 600 must cost less than 5 times the same class on a plain chain (21.1 times at b7e720a, 1.2 now) |
| e | SUMMARY | low | Run summary, not a defect | Nothing to change |
| e | N1-V19-V20 | medium | Nothing pinned "creates no object the collector tracks": a set made under the lock loses finalizer updates on 3.10 and 3.11 and survived the suite | `tests/test_reentry_lost.py`: in a fresh interpreter, a cyclic object whose `__del__` adds to the counter is made before each of 10000 operations at each collector threshold 1, 2, 3, 4, 5, 7 and 10, for `get_and_set`, `compare_and_set`, `compare_and_exchange`, `update`, `get_and_update`, `add` and `get_and_add`, on a plain counter and a bounded one under each policy; finalizers must have run and the total must balance. `set` is left out on purpose: a store that wipes an add made just before it is the expected order of two writes, so no total can tell a lost update from it |
| e | N2-S06-S12 | low | Nothing pinned a slot declared on a class made under a base that skips `super().__init_subclass__()` | Cases `QuietChild` (its own slot), `QuietGrand` (that slot one level up, both slots) and `QuietHeir` (a slot one level up on a base never copied itself, since a base copied first keeps its names and hides S12) |
| e | N3-S09 | low | Nothing pinned that the class hook chains to `super().__init_subclass__(**kwargs)` | `test_a_mixin_class_hook_after_the_counter_still_runs` (a cooperative mixin after `AtomicInt` or `BoundedAtomicInt` still runs) and `test_an_unknown_class_keyword_still_raises` (`TypeError`) |
| e | N4-S15 | low | The copy cost promise was pinned only for a class with stored names, and the GUIDE said the names are read when the class is made, which is not so under a hook-skipping base | Under such a base the names are now worked out at the first copy and kept, and the GUIDE says so. `test_the_first_copy_under_a_base_that_skipped_the_hook_costs_one_pass` (first copy of an 8000-slot class under `Quiet` against the standard copy, bound 10, 1.2 now) and `test_making_a_wide_class_costs_about_what_python_takes`; `test_under_a_base_that_skipped_the_hook_the_names_are_kept_from_the_first_copy` pins the kept names |

CHANGELOG "Fixed" (slot entry) and the GUIDE copies section describe the rebuilt classes,
the wrapping base, the untouched namespace, the class creation cost and the first-copy
rule under a hook-skipping base. The GUIDE's operation cost figures were not re-measured:
no operation path changed. No finding is disputed.

Verification:

- Red before the fix: the b7e720a `_state.py` with the new tests fails at collection
  (`Clash`: `TypeError: 'member_descriptor' object is not iterable`); without `Clash` and
  `Shadow`, 59 cases fail (`Point`, `Reading`, `Rebuilt`, `Checked`, `Private`,
  `Documented` and `_Hidden` under all 8 clones, the namespace test, the depth cost test,
  the first-copy names test), and `Shadow` loses its slot.
  The finalizer program: V19 and V20 lose updates on CPython 3.10.19 and 3.11.5 for all
  four counters; the fixed tree balances everywhere.
- The lenses' probes on the fixed tree, CPython 3.13.2: `p23_rebuilt_class.py` keeps
  every row; `sweep4.py` P01, P02, P04, P05, P08, P10 to P17 and P20 (47172 rounds, no
  error, no loss) OK, P18 one more class at depth 800 0.86 ms against 0.82 ms plain,
  P19 2.02 ms per copy at 8000 slots; P03 (wrap before the first copy under a
  hook-skipping base) is the documented exception, as at b7e720a; P06 and P07 raise as
  the standard library does (P21); P09 deletes the attribute that no longer exists.
  `p_quiet.py`: `QuietChild` and `QuietGrand` keep both slots, the mixin hook runs, the
  unknown keyword raises, the S15 cost ratio is 1.2.
- Mutants: 18, all killed (see
  [CERT-1.0-MUTANTS.md](https://github.com/JaviLianes8/atomicint/blob/main/CERT-1.0-MUTANTS.md)).
- Gates at 28f1dd0 from a clone on this PC, CPython 3.14.2, fetched reference files
  present, `ATOMICINT_E2E=1`: `ruff format --check .`, `ruff check .`,
  `mypy --strict src`, `mypy --strict src tests` and `pytest` (770 passed, 2 skipped: the
  two free-threading tests) each exit 0.
- The suite at 28f1dd0 on every interpreter of this PC (e2e off): 763 passed and 9
  skipped on CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2 and 3.14.2; 765 passed and 7
  skipped on 3.14.2t with the GIL disabled.

Commits of this round: 28f1dd0 (slot names keyed by class, listed slots, covered bases,
first-copy names, new contracts, CHANGELOG, GUIDE) and the commit that records this
section.

### Round 5 probes (lenses c and e at 54db276, interrupted)

The round 5 re-check of lenses c and e at 54db276 stopped before either lens reported.
Lens e's probe logs, left in its working folder, show two defects in the per-class slot
names of 28f1dd0, and lens c's unfinished sweep script, run here against the first fix,
found two more; all four are fixed here without waiting for the lenses to report them.
Lens e's other probes (wrapped slots under classes named `_` and `__`, `__tag__`, dict, list and
frozenset `__slots__`, a `__weakref__` or `__dict__` slot beside a wrapped one, 50 dynamic
classes freed) kept every slot under copy and deepcopy on CPython 3.10.19 and 3.14.2; the
pickle errors in those logs come from the probe's classes not being reachable by name.

| Lens | Id | Severity | Finding | What changed |
| --- | --- | --- | --- | --- |
| e | P6 | medium | A subclass whose metaclass defines `__eq__` without `__hash__` (so its classes are unhashable) could not be made at all: `__init_subclass__` used the class as a key of the `WeakKeyDictionary` and as a set member, and raised `TypeError`. 0.2.0 made and ran such a class | The table of names is a plain dict keyed by `id(cls)`, each entry holding a weak reference to its class whose callback removes the entry when the class dies (before CPython can reuse the id); a lookup also checks that the reference still points at the class. `_collect` tracks covered bases by id. `tests/test_class_identity.py::test_a_subclass_of_an_unhashable_metaclass_can_be_made_and_used` (both classes, a grandchild, the state handed to `copy` and `pickle`) |
| e | P7 | medium | Two classes that a metaclass makes equal by name, with a matching hash, shared one entry, so the second class's copies used the first one's names and silently dropped a slot (a slot on its base, an iterator slot) | Fixed by the same change. `tests/test_class_identity.py::test_classes_equal_by_name_keep_their_own_slots` under copy, deepcopy and pickle protocols 0 to 5 |
| c | Q07 | low | Found by running lens c's unfinished round 5 sweep (`sweep5.py`, no output of its own was left) against 692f501: a slot that a base's `__init_subclass__` wrapped before `super()` was dropped from copies when `__slots__` was a deque or a dict view, as only tuple, list, dict, set and frozenset were read again | `_listed` reads any `__slots__` again unless it is an iterator (`iter(x) is x`). `tests/test_slot_forms.py::test_a_wrapped_slot_is_kept_whatever_iterable_listed_it` (deque, `OrderedDict`, dict keys, a tuple subclass) under copy, deepcopy and every pickle protocol |
| c | Q11 | low | Same sweep: a slot named by a `str` subclass whose `__eq__` raises made class creation fail (0.2.0 made the class and failed only at copy), and anything else a base's hook left in `__slots__` (a number, an object that cannot be iterated) failed the same way | Each listed name is read as a plain string through `str.__str__`, and what cannot be read again is skipped; the member scan still finds every slot Python created. `test_slot_names_given_as_a_hostile_str_subclass_are_kept` (tuple and one-string forms, and a wrapped one) and `test_whatever_a_hook_leaves_in_slots_is_skipped` |

New contracts for the new table: `test_a_class_is_freed_and_its_id_reused_safely` (200
classes that each die before the next is made, so CPython hands each new one the id of the
last; every copy keeps its own slot, every class is freed, the table does not grow; under
`AtomicInt`, `BoundedAtomicInt` and a base that skipped the hook) and
`test_classes_alive_at_exit_leave_no_message` (classes held by a cycle at exit: the callbacks
run during teardown and print nothing). CHANGELOG "Fixed" (slot entry) and the GUIDE copies
section say the names are kept by the class's identity. No operation path changed, so the
GUIDE's cost figures were not re-measured.

Verification:

- Red before the fix: the 54db276 `_state.py` with the new tests fails 18 cases (the two
  equal-by-name cases under all 8 clones, and the unhashable test for both classes). With
  the 692f501 `_state.py`, `tests/test_slot_forms.py` fails at collection (the hostile
  `str` subclass and the left-over number raise at class creation); without those classes,
  16 cases fail (deque and dict keys under all 8 clones).
- The rest of the sweep on the fixed tree, CPython 3.13.2: unhashable and name-equal
  metaclasses, a metaclass whose `__hash__` raises, 3000 dead classes freed with the table
  back to its size, about 3990 id reuses with no slot lost, threads making, copying and
  dropping classes under the collector, 1500 seeded random hierarchies: all kept. Its Q13
  (a hook that puts a method's name in `__slots__`) fails exactly as the standard library
  does for a plain class.
- Mutants: 13 of the identity code, 11 killed, I1 and I6 equivalent on CPython; I7, run
  against 861a812, showed a condition that could never be false, removed in 692f501. 9 of
  the slot form code, 8 killed, L1 explained
  ([CERT-1.0-MUTANTS.md](https://github.com/JaviLianes8/atomicint/blob/main/CERT-1.0-MUTANTS.md)).
- Gates at 692f501 on another machine from a fresh clone, CPython 3.14.2, fetched reference
  files present, `ATOMICINT_E2E=1`: all five exit 0 (803 passed, 7 skipped). Again at
  90f1001 on a third machine, CPython 3.14.6, the same way: `ruff format --check .`,
  `ruff check .`, `mypy --strict src`, `mypy --strict src tests` and `pytest` (859 passed,
  7 skipped: the two free-threading tests and the five Java oracle tests, no Java there)
  each exit 0. That run also showed that CPython 3.14.6 calls `__str__` on a `str`
  subclass slot name while making the class, so the hostile name in the test overrides
  only `__eq__` (90f1001).
- The suite at 90f1001 from a fresh clone on every interpreter of this PC (Java 21 and
  Node.js present, e2e off): 857 passed and 9 skipped on CPython 3.10.19, 3.11.5, 3.12.12,
  3.13.2 and 3.14.2; 859 passed and 7 skipped on 3.14.2t with the GIL disabled. (At
  692f501: 801 passed and 9 skipped, 803 and 7 on 3.14.2t.) Lens c's sweep on the fixed
  tree is summarised above.

Commits of this round: 861a812 (identity-keyed names, contracts, CHANGELOG, GUIDE), 692f501
(callback simplified), fd5af23, 659f7ff, 3365d13 and 90f1001 (slot forms, contracts,
CHANGELOG, GUIDE), and the commit that records this section.

### Round 6 (lenses a, c, d and e at a270808)

Lens a found every README and GUIDE example and all doctests right on six interpreters,
the public API unchanged from 0.2.0, and two gaps in the docs. Lens c found no crash,
hang, blowup or leak (37 hostile inputs on 15 input slots, sizes up to 32M bits, 6M fuzzed
operations against its own model, thread, finalizer and collector stress, all on several
interpreters) and three ways a metaclass or a later property could still change what the
counter reads from a class. Lens d found the builds reproducible, the wheel and sdist
clean and installable on six interpreters, the upgrade from 0.2.0 clean, and one test that
was not hermetic. Lens e's mutation round left one survivor, S10, which a new contract
now kills.

| Lens | Id | Severity | Finding | What changed |
| --- | --- | --- | --- | --- |
| a | F1 | medium | README "Why atomicint" said every other atomic integer package on PyPI is a compiled extension with a fixed-width integer; `atomos` 0.3.1 and `fastcounter` 1.1.0 are pure Python | README: "Most" of them are compiled, and a new list names the two pure Python ones with facts checked on 2026-10-23 from their PyPI metadata and released source (`atomos`: last upload 2015-07-05, classifiers up to Python 3.4, `AtomicInteger` with `get_and_add` and `compare_and_set` under a lock, integers of any size, no bounds, policy or type hints, `six` and `tox` required at run time; `fastcounter`: June 2021, counters with `increment` and a value, no compare-and-set) |
| a | F2 | low | The docs claimed linearizability tests of every operation, but the histories left out `increment` and `decrement` and only built wrapping bounded counters; JavaScript cannot cover every operation | `tests/test_linearizability.py` draws all eleven operations, checked against `vars(AtomicInt)` by `test_the_histories_draw_every_public_operation`; the history test runs on a plain counter and under `raise`, `saturate` and `wrap`, the model knows each policy and records a refused write as such, and written values reach past the range so every policy is applied; `test_the_checker_knows_each_policy` tests the model. README and GUIDE now say exactly that, and that the wrap and saturate policies (not every operation) are compared with JavaScript |
| c | C1 | low | `kind()` read `type(value).__name__`, which a metaclass property can answer: the documented `TypeError` became another exception, an unrelated message, or carried the metaclass's text | The name is read through `type`'s own `__name__` descriptor (`class_name()` in `_coerce.py`), for every message and for `repr()` as well. The `__get__` that binds an `__index__` hook is looked up along its class's MRO, as Python does, not through `getattr` (a metaclass could answer it too and the counter stored 99 where `operator.index` gives 7). `tests/test_metaclass.py`: four `__name__` answers (raising, a number, injected text, a huge list) for the input, policy, hook result and update result messages, `repr()` of both classes, and the hook binding |
| c | C2 | low | `_state.py` read `klass.__name__` and `__mro__` through the metaclass: such a subclass could not be made, or its copies silently lost slots (the bounds of a `BoundedAtomicInt` among them) | `_state.py` reads the name, the MRO and the namespace through `type`'s descriptors (the namespace too: a metaclass `__dict__` property hid slots the same way). `tests/test_metaclass.py::test_a_metaclass_name_mro_or_namespace_cannot_drop_a_slot`: hierarchies under each hostile `__name__`, `__mro__` and `__dict__` answer, with a slot listed by an iterator, two slots a base hook wraps before `super()` (one private) and a plain one, under copy, deepcopy and every pickle protocol |
| c | C3 | low | The GUIDE promised that a slot later hidden by a property "that calls it, say" is still copied; with a read-only property copies raise `AttributeError`, as for any slotted class | Fixed in the GUIDE: a slot replaced later by a property that reads and writes it is copied through that property, and a read-only one makes the copy raise `AttributeError`, as the standard library does. Reading and writing slots through the descriptors kept at class creation was tried and dropped: a member descriptor holds its class and cannot be weakly referenced, so keeping it outside the class kept every subclass alive (`test_a_class_is_freed_and_its_id_reused_safely` failed, 200 of 200 classes never freed). `tests/test_slot_descriptors.py` pins both cases, the read-only one against a plain slotted class |
| c | INFO-evidence | low | Summary of what passed, not a defect | Nothing to change |
| d | F1 | low | The e2e strict type check ran mypy in process with no cache folder and no config file: it wrote `.mypy_cache` into the project root and checked the consumer with this project's settings | The check passes an empty `mypy.ini` and a cache folder of its own, both in the test's temporary folder, and asserts the cache is there. Run from the tree after deleting `.mypy_cache`: no `.mypy_cache` in the root afterwards, and the cache folder is named after the running Python (3.14), not the project's 3.10 |
| d | NOTE-report-file | low | Summary of what passed, not a defect | Nothing to change |
| e | F1 | low | Mutant S10 (no `__objclass__ is klass` filter in `_declared`) survived: nothing pinned that another class's slot descriptor in a subclass's namespace is not copied | `tests/test_slot_descriptors.py::test_another_class_slot_descriptor_in_the_namespace_is_not_copied` (an `AtomicInt` and a `BoundedAtomicInt` subclass, copy, deepcopy and every pickle protocol); S10 is killed (N10 below) |

CHANGELOG "Fixed": the `__index__` entry says the hook is bound exactly as Python binds
it; a new entry says messages and `repr()` use the name Python keeps; the slot entry says
the class's name, MRO and namespace are read as Python keeps them and that a later
wrapper needs a getter and a setter. The GUIDE errors, threads and copies sections say
the same. No finding is disputed.

Verification:

- Red before the fix: with the a270808 sources, `tests/test_metaclass.py` fails at
  collection (`RuntimeError` from the raising `__name__` while a subclass is made). Each
  scenario run on its own by a probe script against both trees (CPython 3.13.2): on
  a270808 all four `__name__` answers break the input message (`RuntimeError`, a
  `TypeError` about `len()`, a list concatenation error, the metaclass's text in the
  message), three of them also break making a subclass, all three `__mro__` answers and
  both `__dict__` answers lose a slot or raise, and the hook test stores 99 where
  `operator.index` gives 7; on the fixed tree all 14 pass. Lens e's S10 is a mutant, so
  its contract passes on both trees and kills the mutant.
- Mutants: 14 of the new code and the stronger tests, all killed
  ([CERT-1.0-MUTANTS.md](https://github.com/JaviLianes8/atomicint/blob/main/CERT-1.0-MUTANTS.md)).
- Gates at 7259f05 on another machine from the committed tree, CPython 3.14.2, fetched
  reference files present, `ATOMICINT_E2E=1`: `ruff format --check .`, `ruff check .`,
  `mypy --strict src`, `mypy --strict src tests` and `pytest` (996 passed, 7 skipped: the
  two free-threading tests and the five Java oracle tests, no Java there) each exit 0.
  The same five, run on a third machine (CPython 3.14.6) before the commits, also exit 0
  with the same counts.
- The suite on every interpreter of this PC (Java 21.0.8 and Node.js 24.18.0 present, e2e
  off), on the fixed tree before one answer in `tests/test_metaclass.py` was reworded:
  994 passed and 9 skipped on CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2 and 3.14.2; 996
  passed and 7 skipped on 3.14.2t with the GIL disabled.

Commits of this round: ce86c58 (class data read as Python keeps it, contracts, CHANGELOG,
GUIDE), a33dca1 (linearizability of every operation and policy, README), 026bd39 (e2e type
check), and the commit that records this section.

### Round 7 (lenses a, c, d and e at 3d26d7b)

Every round 6 finding was re-checked by its own lens and found fixed: lens a's README
comparison and linearizability scope (its own linearizability checker found 0 of 1200
histories wrong on 3.13.2 and 3.14.2t), lens c's C1 and C2 on 3.10 to 3.14t and C3 resolved
in the GUIDE, lens d's e2e type check (3 passed from a fresh sdist on three interpreters,
no cache left in the project), and lens e's S10. Lens a ran every README and GUIDE block
and the doctests; lens c ran 29 hostile scenarios; lens d rebuilt the wheel and sdist
reproducibly, ran a 128-check consumer from both on six interpreters and the suite from
the sdist; lens e ran a new mutation round. Together they found one wrong word in the
README, one gap in the `__index__` lookup (reported by three lenses), one in how a class
name is read, and seven mutants no contract killed.

| Lens | Id | Severity | Finding | What changed |
| --- | --- | --- | --- | --- |
| a | N1 | low | README said `atomos` needs `six` and `tox` installed at run time; it lists `tox` as an install dependency but never imports it | README: it imports `six` at run time and also lists `tox` as an install dependency, which it never imports |
| a, c, d | N2, N2, F2 | low | An `__index__` hook whose class sets `__get__ = None` was called unbound and its result stored; Python calls that `None` and raises `TypeError`. `_lookup` returned `None` both for a missing name and for one set to `None` | `_lookup` returns a private sentinel for a missing name. A `__get__` that is there is called as Python calls it, so `None` raises Python's own `TypeError` ("'NoneType' object is not callable"); an `__index__` set to `None` is refused with the documented message. `tests/test_index_lookup.py`: both cases against `operator.index`, for the constructor, an operation and a bound, with the value left unchanged. CHANGELOG "Fixed" and GUIDE inputs |
| c | N1 | low | `class_name()` returned the name Python keeps as is; that may be a `str` subclass (from `type()` or by assigning `__name__`), whose methods turned the documented `TypeError` into a `RuntimeError`, put text of any length (a secret, 10M characters) into the message, made `repr()` raise, or stopped a subclass of the counter from being made | `class_name()` returns `str.__str__` of that name, a plain copy of the text, as `_listed` already does for slot names. `tests/test_name_subclass.py`: a raising and a lying name for the input, hook result, update result and policy messages, the 60-character cut, a subclass made, shown and deep-copied, and `repr()` after a rename. CHANGELOG "Fixed" and GUIDE errors |
| d | NOTE-recheck-summary | low | Summary of what passed, not a defect | Nothing to change |
| e | F1-recheck | low | S10 is killed: the round 6 finding is closed | Nothing to change |
| e | G1 | medium | Mutant N13 (`_lookup` reads only the class's own namespace) survived: no contract covered an `__index__` inherited from a base | `tests/test_index_lookup.py::test_an_inherited_index_hook_is_found`: one and two levels up, through the constructor, every operation that takes an integer and the bounds |
| e | G2 | low | Mutant N11 (`_lookup` walks `cls.__mro__`) survived | `test_a_metaclass_mro_cannot_hide_an_inherited_index_hook`, under each hostile `__mro__` answer of `tests/test_metaclass.py` |
| e | G3 | low | Mutant N14 (`_lookup` reads `vars(klass)`) survived | `test_a_metaclass_namespace_cannot_hide_or_replace_an_index_hook`: a metaclass `__dict__` answering `{}` or another hook |
| e | G4 | low | Mutant N12 (`_lookup` walks `type.mro(cls)`) survived | `test_the_hook_comes_from_the_order_a_metaclass_mro_made`: a metaclass `mro()` that reorders two hooked bases |
| e | G5 | low | Mutant N17 (`_listed` reads an inherited `__slots__`) survived | `tests/test_slot_mro.py::test_an_inherited_slots_list_adds_no_attribute_to_a_copy`: a subclass without `__slots__` under a base with a private slot, for both classes, copy, deepcopy and every pickle protocol |
| e | G6 | low | Mutant N21 (`_collect` walks `type.mro(cls)`) survived | `test_a_slot_of_a_base_left_out_of_the_mro_is_not_copied`: a metaclass `mro()` drops a slotted base |
| e | G7 | low | Mutant N24 (covered bases taken from `type.mro(klass)`) survived | `test_a_base_whose_mro_leaves_a_slotted_class_out_does_not_hide_its_slots` |

G1 to G7 are missing contracts, not defects: the code was right and is unchanged for
them. No finding is disputed.

Verification:

- Red before the fix: the three new test files run against the 3d26d7b sources (CPython
  3.13.2): 10 failed, 57 passed. The failures are the `__get__ = None` case and the nine
  `str` subclass name cases (`RuntimeError`, the injected text in `repr()`); the 57 that
  pass on both trees pin lens e's mutants and the refused `__index__ = None`. On the
  fixed tree the three files and `tests/test_metaclass.py` pass on CPython 3.10.19,
  3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2t (176 passed on each).
- Mutants: lens e's seven survivors and five mutants of the new code, each alone on a
  copy of the fixed tree, all killed
  ([CERT-1.0-MUTANTS.md](https://github.com/JaviLianes8/atomicint/blob/main/CERT-1.0-MUTANTS.md)).
- Gates at a6bc329 on another machine from a fresh clone, CPython 3.14.2: `ruff format
  --check .`, `ruff check .`, `mypy --strict src`, `mypy --strict src tests` and `pytest`
  (1029 passed, 41 skipped: the seven e2e tests, which this round's changes do not touch,
  the two free-threading tests, the five Java oracle tests with no Java there, and 27
  tests of the fetched reference files, not present there) each exit 0.

Commits of this round: a6bc329 (sentinel lookup, plain class name, contracts, README,
CHANGELOG, GUIDE) and the commit that records this section.
