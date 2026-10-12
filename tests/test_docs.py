"""The README examples run and print what their comments say; versions agree."""

from __future__ import annotations

import contextlib
import io
import re
from pathlib import Path

import atomicint
from atomicint import AtomicInt, BoundedAtomicInt

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def _python_blocks() -> list[str]:
    return re.findall(r"```python\n(.*?)```", README, flags=re.DOTALL)


def _expected_prints(block: str) -> list[str]:
    # Each print line ends in a comment holding the exact output.
    return re.findall(r"^\s*print\(.*\)  # (.+)$", block, flags=re.MULTILINE)


def test_the_readme_has_examples() -> None:
    assert len(_python_blocks()) >= 7


def test_every_readme_example_runs_and_prints_its_comment() -> None:
    checked = 0
    for block in _python_blocks():
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(compile(block, "README.md", "exec"), {"__name__": "readme"})
        expected = _expected_prints(block)
        assert expected, block
        assert out.getvalue().splitlines() == expected
        checked += len(expected)
    assert checked >= 25


def test_the_readme_api_table_lists_every_public_name_and_method() -> None:
    table = README.split("## API", 1)[1].split("\n## ", 1)[0]
    for name in atomicint.__all__:
        assert f"`{name}" in table, name
    methods = {n for n in vars(AtomicInt) if not n.startswith("_")}
    methods |= {n for n in vars(BoundedAtomicInt) if not n.startswith("_")}
    for method in methods:
        assert re.search(rf"`{method}\b", table), method


def test_version_matches_pyproject() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, flags=re.MULTILINE)
    assert match is not None
    assert match.group(1) == atomicint.__version__


def test_changelog_has_an_entry_for_this_version() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{atomicint.__version__}]" in text


def test_no_em_dash_in_shipped_text() -> None:
    paths = [ROOT / "README.md", ROOT / "CHANGELOG.md", *ROOT.joinpath("src").rglob("*.py")]
    for path in paths:
        assert chr(0x2014) not in path.read_text(encoding="utf-8"), path


def test_source_files_stay_under_two_hundred_lines() -> None:
    for path in [*ROOT.joinpath("src").rglob("*.py"), *ROOT.joinpath("tests").rglob("*.py")]:
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 200, path
