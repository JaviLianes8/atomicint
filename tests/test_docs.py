"""The README and GUIDE examples run and print what their comments say; docs agree."""

from __future__ import annotations

import contextlib
import io
import re
from pathlib import Path

import pytest

import atomicint
from atomicint import AtomicInt, BoundedAtomicInt

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
GUIDE = (ROOT / "GUIDE.md").read_text(encoding="utf-8")
BADGE = (
    "[![Lianes8 Certified](https://lianes8studio.com/certified/lianes8-certified-badge.svg)]"
    "(https://lianes8studio.com/certified)"
)


def _python_blocks(text: str) -> list[str]:
    return re.findall(r"```python\n(.*?)```", text, flags=re.DOTALL)


def _expected_prints(block: str) -> list[str]:
    # Each print line ends in a comment holding the exact output.
    return re.findall(r"^\s*print\(.*\)  # (.+)$", block, flags=re.MULTILINE)


@pytest.mark.parametrize(("name", "minimum"), [("README", 5), ("GUIDE", 8)])
def test_every_example_runs_and_prints_its_comments(name: str, minimum: int) -> None:
    blocks = _python_blocks(README if name == "README" else GUIDE)
    assert len(blocks) >= minimum
    for block in blocks:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(compile(block, f"{name}.md", "exec"), {"__name__": name.lower()})
        expected = _expected_prints(block)
        assert expected, block
        assert out.getvalue().splitlines() == expected


def test_the_readme_api_table_lists_every_public_name_and_method() -> None:
    table = README.split("## API", 1)[1].split("\n## ", 1)[0]
    for name in atomicint.__all__:
        assert f"`{name}" in table, name
    methods = {n for n in vars(AtomicInt) if not n.startswith("_")}
    methods |= {n for n in vars(BoundedAtomicInt) if not n.startswith("_")}
    for method in methods:
        assert re.search(rf"`{method}\b", table), method
        assert f"`{method}" in GUIDE, method


def test_the_readme_carries_the_badge_and_absolute_links_only() -> None:
    assert README.splitlines()[2] == BADGE
    for target in re.findall(r"\]\(([^)]+)\)", README):
        assert target.startswith("https://"), target
    for page in ("GUIDE.md", "CHANGELOG.md", "LICENSE"):
        assert f"https://github.com/JaviLianes8/atomicint/blob/main/{page}" in README, page


def test_version_matches_pyproject() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, flags=re.MULTILINE)
    assert match is not None
    assert match.group(1) == atomicint.__version__


def test_changelog_has_a_dated_entry_for_this_version() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    pattern = rf"^## \[{re.escape(atomicint.__version__)}\] - \d{{4}}-\d{{2}}-\d{{2}}$"
    assert re.search(pattern, text, flags=re.MULTILINE)


def _own_files() -> list[Path]:
    upstream = ROOT / "tests" / "upstream"
    found = [ROOT / name for name in ("README.md", "GUIDE.md", "CHANGELOG.md", "pyproject.toml")]
    for folder in ("src", "tests", "scripts"):
        for path in ROOT.joinpath(folder).rglob("*"):
            if path.is_file() and upstream not in path.parents and "__pycache__" not in path.parts:
                found.append(path)
    return found


def test_no_em_dash_anywhere() -> None:
    for path in _own_files():
        assert chr(0x2014) not in path.read_text(encoding="utf-8"), path


def test_source_files_stay_under_two_hundred_lines() -> None:
    for path in _own_files():
        if path.suffix in (".py", ".js", ".java"):
            assert len(path.read_text(encoding="utf-8").splitlines()) <= 200, path
