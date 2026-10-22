"""The built sdist and wheel hold exactly what they should, with correct metadata.

Runs only with ATOMICINT_E2E=1 (see tests/conftest.py); twine is optional.
"""

from __future__ import annotations

import subprocess
import sys
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path

import pytest

PACKAGE = {"__init__.py", "_atomic.py", "_bounded.py", "_coerce.py", "_state.py", "py.typed"}
FORBIDDEN = ("__pycache__", ".pyc", "IMPROVEMENTS", "CERT-1.0", ".github", "dist/", "venv")


def _metadata(wheel: Path) -> tuple[list[str], dict[str, list[str]]]:
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        info = next(n for n in names if n.endswith(".dist-info/METADATA"))
        message = Parser().parsestr(archive.read(info).decode("utf-8"))
    fields: dict[str, list[str]] = {}
    for key, value in message.items():
        fields.setdefault(key, []).append(value)
    return names, fields


def test_the_wheel_holds_the_package_and_the_licence_only(built_dist: dict[str, Path]) -> None:
    names, _ = _metadata(built_dist["wheel"])
    package = {n.split("/", 1)[1] for n in names if n.startswith("atomicint/")}
    assert package == PACKAGE
    others = {n for n in names if not n.startswith("atomicint/")}
    info = "atomicint-1.0.0.dist-info/"
    assert others == {f"{info}{n}" for n in ("METADATA", "WHEEL", "RECORD", "licenses/LICENSE")}


def test_the_metadata_describes_a_stable_typed_package(built_dist: dict[str, Path]) -> None:
    _, fields = _metadata(built_dist["wheel"])
    assert fields["Name"] == ["atomicint"] and fields["Version"] == ["1.0.0"]
    assert fields["Requires-Python"] == [">=3.10"]
    assert fields["License-Expression"] == ["MIT"]
    assert all("extra ==" in r for r in fields.get("Requires-Dist", [])), "runtime dependency"
    classifiers = set(fields["Classifier"])
    assert "Development Status :: 5 - Production/Stable" in classifiers
    assert "Typing :: Typed" in classifiers
    versions = {
        c.rsplit(" ", 1)[1]
        for c in classifiers
        if c.startswith("Programming Language :: Python :: 3.")
    }
    assert versions == {"3.10", "3.11", "3.12", "3.13", "3.14"}
    urls = {u.split(",", 1)[0] for u in fields["Project-URL"]}
    assert {"Homepage", "Source", "Issues", "Changelog"} <= urls
    assert fields["Description-Content-Type"] == ["text/markdown"]


def test_the_sdist_ships_sources_tests_and_docs_but_no_fetched_files(
    built_dist: dict[str, Path],
) -> None:
    with tarfile.open(built_dist["sdist"]) as archive:
        names = [n.split("/", 1)[1] for n in archive.getnames() if "/" in n]
    for required in ("LICENSE", "README.md", "GUIDE.md", "CHANGELOG.md", "pyproject.toml"):
        assert required in names, required
    assert {f"src/atomicint/{n}" for n in PACKAGE} <= set(names)
    assert "tests/upstream/MANIFEST.json" in names
    assert [n for n in names if n.startswith("tests/upstream/")] == ["tests/upstream/MANIFEST.json"]
    assert "scripts/oracle/AtomicOracle.java" in names
    for name in names:
        assert not any(bad in name for bad in FORBIDDEN), name


def test_twine_accepts_both_files(built_dist: dict[str, Path]) -> None:
    pytest.importorskip("twine")
    files = [str(built_dist["sdist"]), str(built_dist["wheel"])]
    done = subprocess.run(
        [sys.executable, "-m", "twine", "check", "--strict", *files],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    assert done.stdout.count("PASSED") == 2
