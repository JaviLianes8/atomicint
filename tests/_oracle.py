"""Run the reference runtimes in scripts/oracle for the oracle tests."""

from __future__ import annotations

import functools
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ORACLES = Path(__file__).resolve().parents[1] / "scripts" / "oracle"
# Math.clamp arrived in Java 21; Node.js has had Atomics on BigInt arrays since 10.4.
MINIMUM = {"java": 21, "node": 11}


@functools.cache
def _major(program: str) -> int:
    done = subprocess.run(
        [program, "-version" if "java" in program.lower() else "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    match = re.search(r"(\d+)[.\d]*", done.stdout + done.stderr)
    return int(match.group(1)) if match else 0


def run_oracle(tool: str, script: str, stdin: str) -> str:
    """Feed ``stdin`` to the oracle script and return its output; skip without the tool."""
    program = shutil.which(tool)
    if program is None:
        pytest.skip(f"{tool} is not installed")
    if _major(program) < MINIMUM[tool]:
        pytest.skip(f"{tool} {MINIMUM[tool]} or newer is needed")
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
