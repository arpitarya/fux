"""Reduce-before-draft — cut ingestion tokens with NO model and NO binary parsing.

Operates ONLY on the agent's already-extracted text (handoff §4b): per-type
structure slicing, a rule-signal pre-filter (reusing recall.py's tokenizer),
boilerplate stripping, and incremental-diff on re-ingest. `full=True` bypasses
it for high-stakes regulatory precision; before→after tokens are filed via
cage_receipt (fail-open). Deterministic, $0, stdlib — imports no parser/network/
LLM library (guard test enforces this).
"""
from __future__ import annotations

import re
from collections import Counter

from fux import cage_receipt
from fux.recall import _tokens          # shared BM25F tokenizer — the rule lexicon

# Rule-bearing signal terms: a chunk matching these (or its section) is kept.
SIGNAL = {"must", "shall", "required", "require", "mandatory", "deprecated",
          "limit", "rate", "threshold", "constraint", "unique", "null",
          "maximum", "minimum", "max", "min", "forbidden", "prohibited", "only",
          "never", "always", "default", "auth", "scope", "endpoint", "param"}
_PAGE = re.compile(r"^\s*(page\s+)?\d+(\s*(/|of)\s*\d+)?\s*$", re.IGNORECASE)
_HEADING = re.compile(r"^(#{1,6}\s|[A-Z0-9][^\n]{0,58}:\s*$)")  # md head or 'Label:'


def reduce(text: str, source_type: str = "txt", *, full: bool = False,
           tool: str = "fux-ingest") -> tuple[str, dict]:
    before = cage_receipt.toks(text)
    if full:
        return text, _stats(before, before)
    cleaned = _strip_boilerplate(text)
    if source_type == "xlsx":
        out = _slice_grid(cleaned)
    elif source_type in ("json", "yaml", "openapi"):
        out = _slice_contract(cleaned)
    else:
        out = _slice_prose(cleaned)
    after = cage_receipt.toks(out)
    cage_receipt.emit(tool, raw_alternative=before, actual=after,
                      task="ingest-reduce", op=source_type)
    return out, _stats(before, after)


def changed_sections(old: str, new: str) -> str:
    """Incremental re-ingest: blocks present in `new` but not `old` (§4b)."""
    old_keys = {_norm(b) for b in re.split(r"\n\s*\n", old) if _norm(b)}
    out = [b.strip() for b in re.split(r"\n\s*\n", new)
           if _norm(b) and _norm(b) not in old_keys]
    return "\n\n".join(out)


def _slice_prose(text: str) -> str:
    """PDF/Word/TXT: headings + rule-bearing passages + tables (not full pages)."""
    kept = [b.strip() for b in re.split(r"\n\s*\n", text)
            if _is_heading(b) or _has_signal(b)]
    return "\n\n".join(kept) if kept else text.strip()


def _slice_grid(text: str) -> str:
    """Excel: schema (header) + a few sample rows + formula/constraint lines —
    NEVER the full data grid (handoff §4b)."""
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return text.strip()
    picked, seen = [], set()
    for l in [lines[0], *lines[1:4], *[x for x in lines if "=" in x or _has_signal(x)]]:
        if l not in seen:
            seen.add(l)
            picked.append(l)
    return "\n".join(picked)


def _slice_contract(text: str) -> str:
    """JSON/YAML/Swagger: the contract/schema (keys, required, paths) — not the
    example values. Long literal values are trimmed, keys kept."""
    kept = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if re.match(r'["\']?[\w./{}-]+["\']?\s*:', s) or _has_signal(s) or s[-1:] in "{[:":
            kept.append(ln if len(ln) <= 200 else ln[:200] + " …")
    return "\n".join(kept) if kept else text.strip()


def _strip_boilerplate(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", ln).rstrip() for ln in text.splitlines()]
    counts = Counter(l.strip() for l in lines if l.strip())
    many = len(lines) > 30
    out, prev = [], None
    for ln in lines:
        s = ln.strip()
        if _PAGE.match(s) or (s and many and len(s) <= 60 and counts[s] >= 3):
            continue                       # page number / repeated header-footer
        if s == "" and prev == "":
            continue                       # collapse blank runs
        out.append(ln)
        prev = s
    return "\n".join(out).strip()


def _has_signal(text: str) -> bool:
    return bool(set(_tokens(text)) & SIGNAL) or text.count("|") >= 2


def _is_heading(block: str) -> bool:
    first = block.strip().splitlines()[0] if block.strip() else ""
    return bool(_HEADING.match(first)) and len(first) <= 80


def _norm(b: str) -> str:
    return re.sub(r"\s+", " ", b).strip().lower()


def _stats(before: int, after: int) -> dict:
    return {"before_tokens": before, "after_tokens": after,
            "saved_tokens": max(0, before - after)}
