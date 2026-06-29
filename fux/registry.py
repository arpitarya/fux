"""The command registry — one source of truth for help, `fux how`, and cli.md.

Each entry: ``name``, ``group`` (authoring · verification · governance · runtime),
a one-line ``desc``, a copy-paste ``example``, and ``related`` command names.
``fux --help`` groups by ``group``; ``fux help <cmd>`` prints the detail; ``fux
how`` recalls over this table; and ``docs/cli.md``'s command table is regenerated
from it so help and docs can never drift (plan §9, §20). Stdlib only, no model.
"""
from __future__ import annotations

from dataclasses import dataclass, field

GROUPS = ["authoring", "verification", "governance", "runtime"]   # display order


@dataclass(frozen=True)
class Command:
    name: str
    group: str
    desc: str
    example: str
    related: tuple[str, ...] = field(default=())


def _c(name, group, desc, example, *related):
    return Command(name, group, desc, example, tuple(related))


COMMANDS: list[Command] = [
    _c("init", "authoring", "scaffold .fux/ + wire hooks in this project",
       "fux init --recall", "build", "hooks"),
    _c("new", "authoring", "scaffold a schema-valid rule stub from a template",
       "fux new formula stcg-equity-rate --domain tax", "build", "lint"),
    _c("build", "authoring", "regenerate INDEX + rules.json + graph ($0)",
       "fux build --full", "check", "stats"),
    _c("self-build", "authoring", "regenerate fux's self-knowledge bundle from its own source ($0, AST-only)",
       "fux self-build", "build", "how"),
    _c("import", "authoring", "import existing markdown as narrative entries",
       "fux import docs/ --type narrative", "import-memory", "parity"),
    _c("import-memory", "authoring", "mirror Claude's home-dir memory into .fux/memory",
       "fux import-memory --scope shared", "import", "capture"),
    _c("ingest", "authoring", "agent batch-ingests URLs/files/globs (+ --follow-links / --connector) → draft review queue (skill)",
       'fux ingest ./docs/*.pdf "https://docs.example.com/api"', "fetch-rules", "check", "ratify"),
    _c("scrape", "authoring", "deprecated alias for 'ingest' — use 'ingest' instead",
       'fux ingest "https://docs.example.com/api"', "ingest"),
    _c("fetch-rules", "authoring", "fetch URL/PDF/txt → extract durable rule entries (skill)",
       'fux fetch-rules "https://example.com/policy" --raw', "ingest", "new"),
    _c("check", "verification", "validate schema/refs/staleness/conflicts; --fix repairs",
       "fux check --fix", "verify", "lint", "gate"),
    _c("verify", "verification", "run invariant/example checks against data",
       "fux verify --fuzz", "check", "seal"),
    _c("lint", "verification", "rule quality: why/code_refs/edges/provenance",
       "fux lint --strict", "check", "stats"),
    _c("seal", "verification", "bind rules to an AST fingerprint of their code",
       "fux seal --all", "verify", "check"),
    _c("coverage", "verification", "% of important files with a governing rule",
       "fux coverage", "stats", "mine"),
    _c("stats", "verification", "knowledge-health dashboard + score",
       "fux stats", "coverage", "lint"),
    _c("mine", "verification", "surface candidate rules latent in the code (drafts)",
       "fux mine --min-sites 3", "new", "coverage"),
    _c("parity", "verification", "decommission readiness vs graphify-out/docs/memory",
       "fux parity", "import", "report"),
    _c("ratify", "governance", "ratify a constitutional rule (stamp + seal + lock)",
       'fux ratify money-never-floats --by "Arpit"', "constitution", "critic", "seal"),
    _c("capture-decision", "governance", "capture a concluded debate/council as a routed, tamper-evident ADR",
       'fux capture-decision use-postgres --route fux --by "Arpit"', "ratify", "constitution"),
    _c("constitution", "governance", "status: what's constitutional + current violations",
       "fux constitution", "ratify", "critic"),
    _c("critic", "governance", "critique a change vs principles (deterministic first)",
       'fux critic "drop the rounding guard"', "constitution", "ratify"),
    _c("gate", "governance", "CI / pre-commit enforcement (exit 2 on blocking)",
       "fux gate --install", "check", "constitution"),
    _c("recall", "runtime", "keyword-retrieve relevant rules (BM25F, $0)",
       'fux recall "how is short-term gain taxed" --top 6', "why", "how", "query"),
    _c("how", "runtime", "fux explains fux: question → the right command ($0)",
       'fux how "which rules govern a file"', "recall", "help", "why"),
    _c("why", "runtime", "explain a rule + rationale + linked code",
       "fux why stcg-equity-rate --history", "recall", "refs"),
    _c("refs", "runtime", "reverse lookup: which rules govern this file",
       "fux refs src/tax.py", "why", "impact"),
    _c("context", "runtime", "emit the compact INDEX (SessionStart hook)",
       "fux context", "recall", "build"),
    _c("query", "runtime", "traverse the graph from rules matching a question",
       'fux query "settlement" --depth 2', "path", "explain", "trace"),
    _c("path", "runtime", "shortest path between two graph nodes",
       "fux path src/a.py src/b.py", "query", "impact"),
    _c("explain", "runtime", "explain a graph node + its neighbours",
       "fux explain settlement", "query", "path"),
    _c("impact", "runtime", "downstream blast radius of changing a file",
       "fux impact src/tax.py", "refs", "query"),
    _c("savings", "runtime", "estimate the token + dollar cost win ($0)",
       'fux savings "how is gain taxed"', "stats", "recall"),
    _c("tour", "runtime", "emit an ordered ONBOARDING.md reading path",
       "fux tour", "stats", "context"),
    _c("serve", "runtime", "local dashboard over the generated views",
       "fux serve --port 8765", "stats", "report"),
    _c("report", "runtime", "write GRAPH_REPORT.md (god nodes + communities)",
       "fux report", "build", "serve"),
    _c("mcp", "runtime", "serve the substrate over MCP (stdio JSON-RPC)",
       "fux mcp", "recall", "why"),
    _c("hooks", "runtime", "install/uninstall/status Fux hooks across surfaces",
       "fux hooks status", "init", "gate"),
    _c("setup", "runtime", "copy bundled assets (schema/hooks/skills) to ~/.claude",
       "fux setup", "init"),
    _c("capture", "runtime", "session observation queue for `fux distill`",
       "fux capture --list", "import-memory", "stats"),
    _c("components", "runtime", "design-system registry + data-binding catalog",
       "fux components --json", "validate-spec", "feedback"),
    _c("validate-spec", "runtime", "validate a generated UISpec against the registry",
       "fux validate-spec spec.json --json", "components", "feedback"),
    _c("feedback", "runtime", "record/summarise on-the-fly generation outcomes",
       "fux feedback --record -", "components", "validate-spec"),
]

_BY_NAME = {c.name: c for c in COMMANDS}


def get(name: str) -> Command | None:
    return _BY_NAME.get(name)


def by_group() -> dict[str, list[Command]]:
    return {g: [c for c in COMMANDS if c.group == g] for g in GROUPS}
