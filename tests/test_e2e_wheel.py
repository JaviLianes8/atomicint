"""Install the built wheel in a throwaway venv and use it as an outside program would.

Slow and needs the build backend, so it runs only with ATOMICINT_E2E=1. The package has
no command line, so the consumer is a script run by subprocess from an empty folder.
"""

from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path

import pytest

PROGRAM = r"""
import copy, importlib.metadata, importlib.resources, inspect, pickle, sys, threading
import atomicint
from atomicint import AtomicInt, BoundedAtomicInt

assert "site-packages" in atomicint.__file__, atomicint.__file__
assert importlib.metadata.version("atomicint") == atomicint.__version__ == "1.0.0"
assert importlib.resources.files("atomicint").joinpath("py.typed").is_file()
assert sorted(atomicint.__all__) == ["AtomicInt", "BoundedAtomicInt", "Overflow"]

counter = AtomicInt(0)
seen = []
def work():
    for _ in range(500):
        seen.append(counter.increment())
threads = [threading.Thread(target=work) for _ in range(8)]
for t in threads: t.start()
for t in threads: t.join()
assert sorted(seen) == list(range(1, 4001)), "lost or duplicated update"

assert counter.compare_and_exchange(1, 5) == 4000
assert counter.update(lambda v: v // 2) == 2000
for bad in (1.5, "1", True):
    try:
        counter.add(bad)
    except TypeError:
        pass
    else:
        raise AssertionError(f"{bad!r} accepted")

pool = BoundedAtomicInt(0, minimum=0, maximum=1)
pool.increment()
try:
    pool.increment()
except OverflowError as error:
    assert str(error) == "2 is outside [0, 1]"
else:
    raise AssertionError("bound not enforced")
wrap = BoundedAtomicInt(255, minimum=0, maximum=255, overflow="wrap")
assert wrap.increment() == 0
twin = pickle.loads(pickle.dumps(wrap))
assert repr(twin) == repr(wrap) and twin is not wrap
data = pickle.dumps(wrap)
assert b"atomicint._bounded" in data and b"_blank" not in data
for cls in (AtomicInt, BoundedAtomicInt):
    assert "site-packages" in inspect.getsourcefile(cls)
    assert inspect.getsource(cls).startswith(f"class {cls.__name__}(")
assert copy.deepcopy(counter).get() == 2000
print("e2e ok")
"""

CONSUMER = """
from atomicint import AtomicInt, BoundedAtomicInt, Overflow

def total(counter: AtomicInt) -> int:
    return counter.add(1) + counter.get_and_add(2)

policy: Overflow = "wrap"
bounded = BoundedAtomicInt(0, minimum=0, maximum=9, overflow=policy)
low: int | None = bounded.minimum
swapped: bool = bounded.compare_and_set(0, 1)
print(total(bounded), low, swapped)
"""


def _run(*cmd: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, check=False
    )


@pytest.fixture(scope="module")
def installed(built_dist: dict[str, Path], tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A fresh venv with only the built wheel installed; returns its Python."""
    env_dir = tmp_path_factory.mktemp("venv")
    venv.create(env_dir, with_pip=True)
    python = env_dir / ("Scripts" if sys.platform == "win32" else "bin") / "python"
    done = _run(python, "-m", "pip", "install", "-q", "--no-index", built_dist["wheel"])
    assert done.returncode == 0, done.stderr
    return python


def test_the_installed_wheel_works_from_an_empty_folder(installed: Path, tmp_path: Path) -> None:
    # -I and an empty folder: the source tree cannot shadow the install.
    result = _run(installed, "-I", "-c", PROGRAM, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "e2e ok"


def test_the_installed_wheel_lists_no_dependencies(installed: Path, tmp_path: Path) -> None:
    done = _run(installed, "-m", "pip", "list", "--format=freeze", cwd=tmp_path)
    names = {line.split("==")[0].lower() for line in done.stdout.split()}
    assert names - {"pip", "setuptools"} == {"atomicint"}, names


def test_a_strict_type_checker_accepts_a_consumer_of_the_installed_wheel(
    installed: Path, tmp_path: Path
) -> None:
    api = pytest.importorskip("mypy.api")
    script = tmp_path / "consumer.py"
    script.write_text(CONSUMER, encoding="utf-8")
    out, err, status = api.run(
        ["--strict", "--python-executable", str(installed), "--no-incremental", str(script)]
    )
    assert status == 0, out + err
    result = _run(installed, "-I", script, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "4 0 True"
