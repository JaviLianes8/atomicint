"""Run the reference runtimes in scripts/oracle for the oracle tests."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ORACLES = Path(__file__).resolve().parents[1] / "scripts" / "oracle"


def run_oracle(tool: str, script: str, stdin: str) -> str:
    """Feed ``stdin`` to the oracle script and return its output; skip without the tool."""
    program = shutil.which(tool)
    if program is None:
        pytest.skip(f"{tool} is not installed")
    done = subprocess.run(
        [program, str(ORACLES / script)],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=240,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    return done.stdout


def edges(low: int, high: int) -> list[int]:
    """The values around both ends of a range, and around zero."""
    return [low - 1, low, low + 1, -1, 0, 1, high - 1, high, high + 1]
