"""Migration helpers — existing docs → `narrative`, home memory → `memory` (§17.14/16).

Turns the manual, file-by-file migration that blocks decommission into one command.
Stamps schema-shaped frontmatter onto existing markdown while preserving the body;
deterministic and `$0`. Never overwrites without `--force`.
"""
from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

from fux import fmwrite, frontmatter, paths

_SLUG = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    return _SLUG.sub("-", str(name).lower()).strip("-") or "entry"


def _today() -> str:
    return _dt.date.today().isoformat()


def _iter_md(sources):
    for s in sources:
        p = Path(s)
        if p.is_dir():
            yield from sorted(p.rglob("*.md"))
        elif p.is_file() and p.suffix == ".md":
            yield p


def import_docs(root: Path, sources, rtype: str = "narrative", domain: str = "general",
                force: bool = False) -> tuple[list[Path], list[Path]]:
    """Import markdown files/dirs as `rtype` entries. Returns (created, skipped)."""
    target_dir = paths.Footprint(root).rules
    target_dir.mkdir(parents=True, exist_ok=True)
    created, skipped = [], []
    for src in _iter_md(sources):
        fm, body = frontmatter.split(src.read_text(encoding="utf-8"))
        fm = dict(fm)
        fm["id"] = slugify(fm.get("id") or src.stem)
        fm["type"] = rtype
        fm.setdefault("domain", domain)
        fm.setdefault("status", "active")
        fm.setdefault("created", _today())
        fm["updated"] = _today()
        out = target_dir / f"{fm['id']}.md"
        if out.exists() and not force:
            skipped.append(out)
            continue
        out.write_text(fmwrite.dump(fm, body.strip() + "\n"), encoding="utf-8")
        created.append(out)
    return created, skipped


def import_memory(root: Path, scope: str = "shared", force: bool = False
                  ) -> tuple[list[Path], list[Path]]:
    """Import Claude's home-dir memory for this project as `type: memory` entries."""
    src = paths.home_memory_dir(root)
    if not src.is_dir():
        return [], []
    target_dir = paths.Footprint(root).memory / scope
    target_dir.mkdir(parents=True, exist_ok=True)
    created, skipped = [], []
    for f in sorted(src.glob("*.md")):
        if f.name == "MEMORY.md":                       # the index, not a memory
            continue
        fm, body = frontmatter.split(f.read_text(encoding="utf-8"))
        rid = slugify(fm.get("name") or f.stem)
        meta = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
        subtype = meta.get("type") or fm.get("subtype") or "project"
        if subtype not in ("user", "feedback", "project", "reference"):
            subtype = "project"
        out_fm = {"id": rid, "type": "memory", "subtype": subtype, "scope": scope,
                  "domain": str(fm.get("domain", "general")), "status": "active",
                  "created": str(fm.get("created") or _today()), "updated": _today()}
        out = target_dir / f"{rid}.md"
        if out.exists() and not force:
            skipped.append(out)
            continue
        out.write_text(fmwrite.dump(out_fm, body.strip() + "\n"), encoding="utf-8")
        created.append(out)
    return created, skipped
