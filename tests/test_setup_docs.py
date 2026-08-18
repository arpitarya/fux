"""`work/setup/` documents the things fux needs but does not contain.

Two working directories sit next to the repo — `fux-playground` (grades) and
`fux-lab` (measures) — and neither can be reconstructed from anything in this
tree. A setup document that does not say *where* its thing lives, or that
describes something actually inside the repo, has stopped being a setup
document.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fux import frontmatter as fm  # noqa: E402

SETUP = ROOT / "work" / "setup"
INDEX = SETUP / "README.md"


def docs() -> list[Path]:
    return sorted(p for p in SETUP.glob("*.md") if p.name != "README.md")


def test_the_directory_has_an_index() -> None:
    assert INDEX.is_file(), "work/setup/README.md states what belongs here and which is which"


@pytest.mark.parametrize("path", docs(), ids=lambda p: p.name)
def test_setup_doc_declares_what_it_is(path: Path) -> None:
    meta = fm.parse(path.read_text(encoding="utf-8")).meta
    assert meta.get("type") == "Setup", (
        f"{path.name}: type must be Setup, got {meta.get('type')!r}. "
        "A setup document is not an ADR — an ADR records a decision someone can supersede."
    )
    for key in ("name", "title", "description", "location"):
        assert str(meta.get(key, "")).strip(), f"{path.name}: missing {key!r} in frontmatter"


@pytest.mark.parametrize("path", docs(), ids=lambda p: p.name)
def test_the_thing_lives_outside_this_repository(path: Path) -> None:
    """Rule 1. If it were inside the repo it would not need a setup document."""
    location = str(fm.parse(path.read_text(encoding="utf-8")).meta["location"]).strip()
    assert location.startswith(("~", "/")), (
        f"{path.name}: location must be an absolute or home-relative path outside "
        f"this repo — got {location!r}"
    )
    resolved = Path(location).expanduser().resolve()
    assert ROOT not in resolved.parents and resolved != ROOT, (
        f"{path.name}: location {location!r} resolves inside this repository. "
        "work/setup/ is for the things fux needs but does not contain."
    )


@pytest.mark.parametrize("path", docs(), ids=lambda p: p.name)
def test_setup_doc_is_listed_in_the_index(path: Path) -> None:
    text = INDEX.read_text(encoding="utf-8")
    assert path.name in text, f"{path.name} is not listed in work/setup/README.md"
