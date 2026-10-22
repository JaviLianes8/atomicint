"""Shared fixtures: the wheel and sdist built once for the end-to-end tests.

The build is isolated, exactly as a release build is, so it downloads the build backend
from the package index: the end-to-end mode (ATOMICINT_E2E=1) needs network access.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def built_dist(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Build the sdist, then the wheel from it, exactly as a release does."""
    if os.environ.get("ATOMICINT_E2E") != "1":
        pytest.skip("set ATOMICINT_E2E=1 to build and install the package")
    out = tmp_path_factory.mktemp("dist")
    done = subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(out), str(ROOT)],
        capture_output=True,
        text=True,
        check=False,
    )
    hint = "the isolated build fetches hatchling from the package index; is it reachable?"
    assert done.returncode == 0, f"{hint}\n{done.stdout}{done.stderr}"
    (wheel,) = out.glob("atomicint-*.whl")
    (sdist,) = out.glob("atomicint-*.tar.gz")
    return {"wheel": wheel, "sdist": sdist}
