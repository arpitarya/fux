"""`fux tour` — ordered onboarding reading path → ONBOARDING.md (plan §10.10)."""
from __future__ import annotations

from pathlib import Path

from fux import config, loader, paths

# A newcomer's reading order: the "why" first, then conventions, then the
# domain rules, then the operational/edge knowledge.
ORDER = ["narrative", "adr", "convention", "glossary", "rule", "formula",
         "invariant", "regulatory", "edge-case", "runbook", "spec", "task", "memory"]


def run(root: Path) -> str:
    cfg = config.load(paths.Footprint(root).config)
    rules = loader.resolve(root, cfg).active()
    rank = {t: i for i, t in enumerate(ORDER)}
    ordered = sorted(rules, key=lambda r: (rank.get(r.type, 99), r.domain, r.id))
    lines = ["# Onboarding — a generated reading path", "",
             "_Read top to bottom. Each entry: `fux why <id>` for the full text._", ""]
    last = None
    for i, r in enumerate(ordered, 1):
        if r.type != last:
            lines.append(f"\n## {r.type}")
            last = r.type
        lines.append(f"{i}. **{r.id}** — {r.title}")
    return "\n".join(lines).strip() + "\n"


def write(root: Path) -> Path:
    fp = paths.Footprint(root)
    target = fp.out_file("ONBOARDING.md")
    target.write_text(run(root), encoding="utf-8")
    return target
