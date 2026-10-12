"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with ATOMICINT_E2E=1.
"""

from __future__ import annotations

import os
import subprocess
import sys
import venv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("ATOMICINT_E2E") != "1", reason="set ATOMICINT_E2E=1 to build and install"
)

PROGRAM = r"""
import copy, importlib.metadata, importlib.resources, pickle, threading
import atomicint
from atomicint import AtomicInt, BoundedAtomicInt

assert "site-packages" in atomicint.__file__, atomicint.__file__
assert importlib.metadata.version("atomicint") == atomicint.__version__
assert importlib.resources.files("atomicint").joinpath("py.typed").is_file()
meta = importlib.metadata.metadata("atomicint")
assert "Programming Language :: Python :: Free Threading :: 3 - Stable" in meta.get_all(
    "Classifier"
)

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
try:
    counter.add(1.5)
except TypeError:
    pass
else:
    raise AssertionError("float accepted")

pool = BoundedAtomicInt(0, minimum=0, maximum=1)
pool.increment()
try:
    pool.increment()
except OverflowError:
    pass
else:
    raise AssertionError("bound not enforced")
wrap = BoundedAtomicInt(255, minimum=0, maximum=255, overflow="wrap")
assert wrap.increment() == 0
twin = pickle.loads(pickle.dumps(wrap))
assert repr(twin) == repr(wrap) and twin is not wrap
assert copy.deepcopy(counter).get() == 2000
print("e2e ok")
"""


def _run(*cmd: str | Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, check=False
    )


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(sys.executable, "-m", "build", "--wheel", "--outdir", dist, ROOT)
    assert built.returncode == 0, built.stderr
    (wheel,) = dist.glob("atomicint-*.whl")

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "e2e ok"
