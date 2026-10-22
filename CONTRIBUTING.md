# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
python scripts/fetch_upstream.py
```

The second command fetches the reference documents some tests quote (Java, MDN and
CPython documentation, the trove classifiers) into the ignored `tests/upstream` folder;
without them those tests skip. The oracle tests also run Java 21 or newer and Node.js
when they are installed, and skip otherwise.

## Before you open a pull request

- Keep public API in `src/atomicint/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. Tests inject time, disk and network; they
  never touch the real thing.
- Run `scripts/check.ps1` (format, lint, types, tests) and make sure it passes. Set
  `ATOMICINT_E2E=1` to also build the sdist and wheel, inspect them and drive the
  installed wheel from a throwaway virtual environment.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.
