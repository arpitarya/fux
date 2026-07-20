"""Deterministic PII content probe — port of dante's BLOCK-tier regexes (no pip dep).

dante guards PII at *commit time* in anton; this is the same hard-identifier scan,
hand-rolled stdlib, wired into the `gate` CI job so a stray PAN / Aadhaar / account
number in a non-plan `.py`/`.md` is caught **in CI**, not just by a bypassable local
hook (`--no-verify`). `$0`, stdlib, deterministic — no LLM, no network.

Plan/spec/handoff docs legitimately *discuss* these identifiers as examples, so they
are exempt by path; any single line may opt out with an inline `pii-allow` marker.
"""
from __future__ import annotations

import re
from pathlib import Path

# Mirror dante's `critic_guard` / sentinel BLOCK tier so CI == runtime == commit-time.
BLOCK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("pan", re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")),
    ("aadhaar", re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")),
    ("account-id",
     re.compile(r"(?i)\b(account|a/c|acct|client[_ -]?(id|code)|folio)\b\W{0,8}\d{6,}")),
]
ALLOW = "pii-allow"          # inline marker: this line is a vetted example, skip it
# Planning/example docs carry identifiers as illustrations — exempt by path substring.
_EXEMPT = ("handoff", "/decisions/", "-plan", "plan.md", "spec", "prompt", "whats-new")


def is_exempt(path: str) -> bool:
    p = path.replace("\\", "/").lower()
    return any(s in p for s in _EXEMPT)


def scan_text(text: str) -> list[tuple[int, str, str]]:
    """(line_no, kind, snippet) for every hard-identifier hit; honors the `pii-allow` marker."""
    out: list[tuple[int, str, str]] = []
    for n, line in enumerate(text.splitlines(), 1):
        if ALLOW in line:
            continue
        for kind, pat in BLOCK_PATTERNS:
            m = pat.search(line)
            if m:
                out.append((n, kind, m.group(0)))
    return out


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    if is_exempt(str(path)):
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return scan_text(text)


def scan(paths: list[Path]) -> list[tuple[str, int, str, str]]:
    """(path, line_no, kind, snippet) across all non-exempt paths. Deterministic order."""
    out: list[tuple[str, int, str, str]] = []
    for p in sorted(paths, key=lambda x: str(x)):
        for line_no, kind, snip in scan_file(p):
            out.append((str(p), line_no, kind, snip))
    return out


def render(hits: list[tuple[str, int, str, str]]) -> str:
    if not hits:
        return "✔ PII probe: no hard identifiers (PAN/Aadhaar/account) in scanned files."
    lines = [f"✗ PII probe: {len(hits)} hard identifier(s) — money/PII must not enter the tree:"]
    lines += [f"  [{kind}] {path}:{ln}  {snip!r}" for path, ln, kind, snip in hits]
    lines.append("  Remove it, or mark a vetted example line with an inline `pii-allow`.")
    return "\n".join(lines)
