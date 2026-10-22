"""Read the fetched reference files, checked against the manifest, or skip."""

from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

import pytest

FOLDER = Path(__file__).resolve().parent / "upstream"
MANIFEST = json.loads((FOLDER / "MANIFEST.json").read_text(encoding="utf-8"))


def upstream_text(name: str) -> str:
    """The fetched file ``name`` as text; skip when it has not been fetched."""
    path = FOLDER / name
    if not path.is_file():
        pytest.skip(f"run scripts/fetch_upstream.py to fetch {name}")
    body = path.read_bytes()
    assert hashlib.sha256(body).hexdigest() == MANIFEST[name]["sha256"], name
    return body.decode("utf-8")


def plain_text(page: str) -> str:
    """An HTML page as one line of text: tags dropped, entities and spaces normalised."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", page))
    text = re.sub(r"\s+", " ", text.replace("\N{NO-BREAK SPACE}", " "))
    return re.sub(r" ([,.])", r"\1", text)  # a dropped tag leaves a space before punctuation


def javadoc_member(page: str, anchor: str) -> str:
    """The text of one member's detail section of a javadoc page, by its anchor id."""
    match = re.search(
        rf'<section class="detail" id="{re.escape(anchor)}">(.*?)</section>', page, re.S
    )
    assert match, anchor
    return plain_text(match.group(1))
