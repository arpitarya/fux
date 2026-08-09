"""The draft review queue — `fux ingest`'s batch output manifest (handoff §2).

A Markdown table at `.fux/ingest/queue.md`: one row per item, `status: draft`
(or `failed` + reason), deduped by `source_hash`. NOTHING auto-activates — you
triage, then `/fux debate` → `fux ratify` the keepers. The engine writes rows
and expands/dedups the source list (the only deterministic pre-step); the host
agent did the fetching/extracting/drafting. $0, stdlib.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fux import paths

QUEUE_REL = "ingest/queue.md"
_COLS = ["source", "source_type", "status", "trust", "draft_id", "source_hash", "reason"]
_HEADER = "| " + " | ".join(_COLS) + " |"
_SEP = "| " + " | ".join(["---"] * len(_COLS)) + " |"
_EXT_TYPE = {  # file extension / URL hint → schema `source_type` enum value (§4)
    ".pdf": "pdf", ".xlsx": "xlsx", ".xls": "xlsx", ".csv": "xlsx",
    ".docx": "docx", ".txt": "txt", ".md": "txt", ".markdown": "txt",
    ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".png": "image",
    ".jpg": "image", ".jpeg": "image", ".gif": "image", ".webp": "image",
    ".bmp": "image", ".tiff": "image"}


@dataclass
class Item:
    source: str
    source_type: str = "url"
    status: str = "draft"          # draft | failed — never `active`
    trust: str = ""                # "", verify-source, draft-verify
    draft_id: str = ""
    source_hash: str = ""
    reason: str = ""

    def row(self) -> str:
        return "| " + " | ".join(_cell(getattr(self, c)) for c in _COLS) + " |"


def classify_type(source: str) -> str:
    low = source.lower()
    if "openapi" in low or "swagger" in low:
        return "openapi"
    s = low.split("?")[0].split("#")[0]
    return next((t for ext, t in _EXT_TYPE.items() if s.endswith(ext)), "url")


def expand_sources(targets: list[str], root: Path | None = None) -> list[str]:
    """Expand globs deterministically + dedup (first-seen order); URLs pass through."""
    base, out, seen = root or Path("."), [], set()
    for t in targets:
        matches = [t] if _is_url(t) else (
            sorted(str(p) for p in base.glob(t) if p.is_file())
            if any(ch in t for ch in "*?[") else [t])
        for m in matches:
            if m not in seen:
                seen.add(m); out.append(m)
    return out


def path_of(root: Path) -> Path:
    return paths.Footprint(root).base / QUEUE_REL


def read(root: Path) -> list[Item]:
    p = path_of(root)
    if not p.exists():
        return []
    items = []
    for line in (l.strip() for l in p.read_text(encoding="utf-8").splitlines()):
        if not line.startswith("|") or line == _HEADER or set(line) <= set("|- "):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) == len(_COLS):
            items.append(Item(**{c: _uncell(v) for c, v in zip(_COLS, cells)}))
    return items


def upsert(root: Path, new: list[Item]) -> list[Item]:
    """Merge `new` into the queue, deduped by `source_hash` (else `source`) — a
    re-ingested identical doc updates its row rather than duplicating it (§2)."""
    by_key = {(i.source_hash or i.source): i for i in read(root)}
    for it in new:
        by_key[it.source_hash or it.source] = it
    merged = list(by_key.values())
    write(root, merged)
    return merged


def write(root: Path, items: list[Item]) -> None:
    p = path_of(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join([
        "# Fux ingest — draft review queue", "",
        "Every row is `status: draft` until you triage it — nothing here is active.",
        "", _HEADER, _SEP, *[it.row() for it in items]]) + "\n", encoding="utf-8")


def render(root: Path) -> str:
    items = read(root)
    if not items:
        return "Ingest queue empty — run /fux ingest <sources…> to populate it."
    drafts = sum(i.status == "draft" for i in items)
    head = f"Ingest queue: {drafts} draft · {len(items) - drafts} failed  ({path_of(root)})"
    body = [f"  [{i.status:6}] {i.source_type:7} {i.source}"
            f"{('  ⚑ ' + i.trust) if i.trust else ''}"
            f"{('  — ' + i.reason) if i.reason else ''}" for i in items]
    return "\n".join([head, *body])


def _is_url(s: str) -> bool:
    return s.startswith(("http://", "https://"))

def _cell(v: str) -> str:
    return str(v).replace("|", "\\|").replace("\n", " ").strip() or "—"

def _uncell(v: str) -> str:
    return "" if v == "—" else v.replace("\\|", "|")
