"""On a free-threaded build, importing and using atomicint keeps the GIL off."""

from __future__ import annotations

import os
import subprocess
import sys
import sysconfig

import pytest

pytestmark = pytest.mark.skipif(
    not sysconfig.get_config_var("Py_GIL_DISABLED"), reason="needs a free-threaded build"
)

PROGRAM = """
import sys, threading
import atomicint
counter = atomicint.BoundedAtomicInt(0, minimum=0, maximum=10**9)
threads = [threading.Thread(target=lambda: [counter.increment() for _ in range(1000)])
           for _ in range(8)]
for t in threads: t.start()
for t in threads: t.join()
assert counter.get() == 8000
print(sys._is_gil_enabled())
"""


SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")


def test_the_gil_stays_disabled_after_importing_and_using_the_package() -> None:
    # A fresh interpreter with no GIL override, so the package itself is what is tested.
    env = {k: v for k, v in os.environ.items() if k != "PYTHON_GIL"}
    env["PYTHONPATH"] = SRC
    result = subprocess.run(
        [sys.executable, "-c", PROGRAM], capture_output=True, text=True, check=False, env=env
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "False"


@pytest.mark.skipif(os.environ.get("PYTHON_GIL") == "1", reason="GIL forced on")
def test_this_test_run_has_the_gil_disabled() -> None:
    assert sys._is_gil_enabled() is False  # type: ignore[attr-defined]
