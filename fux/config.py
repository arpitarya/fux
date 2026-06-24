"""Per-project config (.fux/config.toml) — strictness, packs, globs (plan §8)."""
from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover  (Python <3.11)
    tomllib = None

MODES = ["off", "warn", "fix", "strict"]
DEFAULTS = {
    "mode": "fix",
    "packs": [],
    "important_globs": ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.go", "**/*.rs"],
    # What `fux build` graphs — broader than important_globs (the coverage target),
    # so the graph can match a whole-repo scan (plan §17.13). `fux build --full`
    # widens this to every non-ignored file.
    "graph_globs": ["**/*.py", "**/*.pyi", "**/*.ts", "**/*.tsx", "**/*.js",
                    "**/*.jsx", "**/*.mjs", "**/*.go", "**/*.rs", "**/*.java",
                    "**/*.rb", "**/*.php", "**/*.c", "**/*.h", "**/*.cc",
                    "**/*.cpp", "**/*.hpp", "**/*.cs", "**/*.kt", "**/*.swift",
                    "**/*.scala", "**/*.sh"],
    "ignore_globs": ["**/node_modules/**", "**/.venv/**", "**/dist/**", "**/build/**"],
    "use_global": True,
    "recall_rerank": False,   # phase-2 opt-in local embeddings (recall-engine.compare.md)
    "recall_hybrid": False,   # opt-in RRF fusion of lexical ⊕ semantic ⊕ graph (§17.1)
    "recall_expand": False,   # opt-in deterministic query expansion (glossary+graph, §17.18b)
    "capture": False,         # opt-in Stop-hook session capture for distill (§17.2)
    "memory_ttl_days": 180,   # type: memory decays after this many untouched days (§17.3)
    "usage_tracking": False,   # opt-in: record served rules → usage-weighted decay (§17.20c)
    "cost_tracking": False,    # opt-in: record each lookup's savings → cumulative cost.json (§12)
    "usd_per_mtok": 5.0,       # $/million input tokens for `fux savings` dollar figures (§12);
                               # default = Claude Opus 4.8 input price. Model-agnostic — override per project.
    "parity_stay": [],        # docs that stay/are out-of-scope for `fux parity` (§17.17)
    "context_budget_tokens": 0,  # >0 ⇒ knapsack-pack the SessionStart INDEX (§17.25)
    "graph_editor": "vscode",  # editor URI scheme for clickable graph.html node links:
                               # vscode | vscode-insiders | cursor | windsurf (§7)
    "critic_block_judgment": False,  # advisory-first critic (§7d, F1): judgment principles
                               # SUGGEST by default. `true` ⇒ all block; a list of ids ⇒ only
                               # those block. Deterministic principles always block regardless.
    "cdp_host": "127.0.0.1",   # CDP endpoint for the `/fux ingest` render escalation (§B).
    "cdp_port": 9299,          # Overridden by --cdp-host/--cdp-port flags or FUX_CDP_HOST/PORT env.
}


def load(config_path: Path) -> dict:
    """Read config.toml, merged over DEFAULTS. Tolerant of a missing file."""
    cfg = dict(DEFAULTS)
    if config_path.exists() and tomllib is not None:
        with config_path.open("rb") as fh:
            data = tomllib.load(fh)
        cfg.update(data.get("fux", data))
    if cfg.get("mode") not in MODES:
        cfg["mode"] = "fix"
    return cfg


def default_toml() -> str:
    """The config.toml `fux init` writes."""
    return (
        "[fux]\n"
        '# Enforcement: off | warn | fix (default) | strict  — see fux-plan.md §8\n'
        'mode = "fix"\n\n'
        "# Opt-in rule packs from ~/.claude/fux/packs/ (plan §5)\n"
        "packs = []\n\n"
        "# Inherit ~/.claude/fux/global/ best practices\n"
        "use_global = true\n\n"
        "# Files that should ideally have a governing rule (fux coverage)\n"
        'important_globs = ["**/*.py", "**/*.ts", "**/*.tsx"]\n'
        "# What `fux build` graphs — broaden toward a whole-repo scan (plan §17.13);\n"
        "# `fux build --full` graphs every non-ignored file. Empty = use important_globs.\n"
        'graph_globs = ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", '
        '"**/*.go", "**/*.rs"]\n'
        'ignore_globs = ["**/node_modules/**", "**/.venv/**", "**/dist/**"]\n\n'
        "# Phase-2 local embedding re-rank for recall (no API). Off by default.\n"
        "recall_rerank = false\n\n"
        "# RRF hybrid recall: fuse lexical + local-semantic + graph proximity ($0).\n"
        "recall_hybrid = false\n\n"
        "# Opt-in Stop-hook session capture → queue observations for `fux distill`.\n"
        "capture = false\n\n"
        "# type: memory entries decay (excluded from `fux context`) after N days.\n"
        "memory_ttl_days = 180\n\n"
        "# Opt-in: record which rules recall/why serve → usage-weighted decay ($0).\n"
        "usage_tracking = false\n\n"
        "# Opt-in: accumulate each lookup's token savings into .fux/cost.json ($0).\n"
        "cost_tracking = false\n\n"
        "# $/million input tokens used to price `fux savings` in dollars (model-agnostic).\n"
        "# Default = Claude Opus 4.8 input price; set to your model's rate.\n"
        "usd_per_mtok = 5.0\n\n"
        "# Docs that stay / are out-of-scope for `fux parity` (beyond conventions,\n"
        "# guardrails) — e.g. process docs that get deleted, not migrated to narrative.\n"
        "parity_stay = []\n\n"
        "# Token budget for the SessionStart INDEX. 0 = inject everything; >0 picks\n"
        "# the optimal (knapsack) rule subset that fits — for very large corpora.\n"
        "context_budget_tokens = 0\n\n"
        "# Editor for clickable file:line node links in graph.html.\n"
        "# vscode | vscode-insiders | cursor | windsurf\n"
        'graph_editor = "vscode"\n\n'
        "# Advisory-first critic (fux critic): judgment principles SUGGEST, not block, by\n"
        "# default. Escalate trusted ones to blocking — true = all, or a list of rule ids.\n"
        "# Deterministic (money/PII/numbers/audit) principles always block regardless.\n"
        "critic_block_judgment = false\n\n"
        "# CDP endpoint for the `/fux ingest` skill's render escalation (client-rendered\n"
        "# pages). Precedence: --cdp-host/--cdp-port flags > FUX_CDP_HOST/PORT env > these.\n"
        'cdp_host = "127.0.0.1"\n'
        "cdp_port = 9299\n"
    )
