"""The public API is typed: mypy infers the documented types and rejects wrong ones."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

api = pytest.importorskip("mypy.api")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

SNIPPET = """
from atomicint import AtomicInt, BoundedAtomicInt, Overflow
counter = AtomicInt(3)
reveal_type(counter.get())
reveal_type(counter.compare_and_set(3, 4))
reveal_type(counter.compare_and_exchange(4, 5))
reveal_type(counter.update(lambda v: v * 2))
bounded = BoundedAtomicInt(0, minimum=0, maximum=9, overflow="wrap")
reveal_type(bounded.maximum)
reveal_type(bounded.overflow)
policy: Overflow = "saturate"
counter.add("1")
counter.set(1.5)
BoundedAtomicInt(0, overflow="clamp")
counter.update(lambda v: str(v))
BoundedAtomicInt(0, 0, 9)
"""


@pytest.fixture(scope="module")
def mypy_output(tmp_path_factory: pytest.TempPathFactory) -> str:
    folder = tmp_path_factory.mktemp("typing")
    target = folder / "snippet.py"
    target.write_text(SNIPPET, encoding="utf-8")
    config = folder / "mypy.ini"
    config.write_text(f"[mypy]\nmypy_path = {SRC.as_posix()}\n", encoding="utf-8")
    cache = str(folder / "cache")
    out, err, _ = api.run(
        ["--strict", "--config-file", str(config), "--cache-dir", cache, str(target)]
    )
    return str(out) + str(err)


def test_reads_and_results_are_plain_types(mypy_output: str) -> None:
    assert _revealed(mypy_output, 4) == "int"
    assert _revealed(mypy_output, 5) == "bool"
    assert _revealed(mypy_output, 6) == "int"
    assert _revealed(mypy_output, 7) == "int"


def test_bounds_and_policy_are_typed(mypy_output: str) -> None:
    assert _revealed(mypy_output, 9) == "int | None"
    policy = _revealed(mypy_output, 10)
    assert "Literal[" in policy
    assert re.findall(r"'(\w+)'", policy) == ["raise", "saturate", "wrap"]


def test_the_overflow_alias_accepts_a_policy_name(mypy_output: str) -> None:
    assert not re.search(r"snippet\.py:11: error", mypy_output)


def test_wrong_argument_types_are_rejected(mypy_output: str) -> None:
    for line in (12, 13, 14, 15):
        assert re.search(
            rf"snippet\.py:{line}: error: .*\[(arg-type|return-value)\]", mypy_output
        ), (
            line,
            mypy_output,
        )


def test_bounds_and_policy_are_keyword_only(mypy_output: str) -> None:
    assert re.search(r"snippet\.py:16: error: Too many positional arguments", mypy_output)


def _revealed(output: str, line: int) -> str:
    match = re.search(rf"snippet\.py:{line}: note: Revealed type is \"(.+)\"", output)
    assert match, output
    # Older mypy releases spell builtins with their module prefix.
    return match.group(1).replace("builtins.", "")


def test_the_doc_examples_pass_strict_type_checking(tmp_path: Path) -> None:
    # The README and GUIDE promise mypy --strict; only a refused input, written on purpose
    # as the first line of a try block, may be an error.
    files: list[Path] = []
    for doc in ("README", "GUIDE"):
        text = (ROOT / f"{doc}.md").read_text(encoding="utf-8")
        for number, block in enumerate(re.findall(r"```python\n(.*?)```", text, re.DOTALL)):
            files.append(tmp_path / f"{doc.lower()}_{number}.py")
            files[-1].write_text(block, encoding="utf-8")
    config = tmp_path / "mypy.ini"
    config.write_text(f"[mypy]\nmypy_path = {SRC.as_posix()}\n", encoding="utf-8")
    out, err, _ = api.run(
        ["--strict", "--config-file", str(config), "--cache-dir", str(tmp_path / "cache")]
        + [str(path) for path in files]
    )
    errors = re.findall(r"(\w+)\.py:(\d+): error: (.*)", str(out) + str(err))
    for name, line, message in errors:
        lines = (tmp_path / f"{name}.py").read_text(encoding="utf-8").splitlines()
        assert lines[int(line) - 2].strip() == "try:", (name, lines[int(line) - 1], message)
    # The refused float and the float update result are there, so errors were read.
    assert len(errors) >= 3 and len(files) >= 13, str(out) + str(err)
