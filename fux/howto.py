"""`fux how "<question>"` — fux explains fux, deterministically (handoff §C).

Dogfoods the engine: builds a tiny corpus from the command registry (`registry.py`)
+ a few bundled self-doc snippets, runs the EXISTING BM25F recall (`recall.rank`,
$0, no model) over it, and returns a short explanation **plus the exact command**
for the task. ``--explain`` is the only path that uses a model — it emits a fenced
prompt for the host agent, never an engine call.
"""
from __future__ import annotations

from pathlib import Path

from fux import recall, registry
from fux.model import Rule

# Key self-documentation facts — recalled alongside the per-command entries so a
# conceptual question ("how does drift detection work") maps to the right command.
_SELF_DOCS = [
    ("drift-detection", "check",
     "drift detection staleness dead refs schema conflicts validate",
     "`fux check` validates schema, dead code_refs, git-staleness and conflicts; "
     "`fux seal` then makes a rule fail when its governed code changes structure."),
    ("constitution-tier", "ratify",
     "constitutional tier ratify binding rule tamper evidence lock apex law",
     "Binding rules live in the constitutional tier; `fux ratify` stamps + seals + "
     "locks them and `fux check` makes any later tampering a blocking finding."),
    ("cost-zero", "savings",
     "cost dollars tokens cheap save money zero budget price",
     "Every maintenance path is $0; `fux savings` measures the token + dollar win "
     "from your real file sizes."),
    ("which-rules-govern-file", "refs",
     "which rules govern this file reverse lookup who owns covers path",
     "`fux refs <path>` is the reverse lookup — the rules that govern a given file."),
    ("web-source-rules", "ingest",
     "scrape ingest website url web page pdf excel image docs draft rule from file or internet source",
     "`/fux ingest <url|file>` has the agent extract a URL, PDF, Excel, TXT, or image "
     "and draft governed rules (status: draft) with provenance; nothing auto-activates."),
]


def _corpus() -> list[Rule]:
    """Synthetic Rules — one per command + the self-doc snippets — for recall."""
    rules: list[Rule] = []
    for c in registry.COMMANDS:
        body = f"{c.desc}\n\n{c.example}"
        fm = {"id": c.name, "type": "command", "keywords": [c.group, *c.desc.split()],
              "aliases": list(c.related)}
        rules.append(Rule(id=c.name, type="command", fm=fm, body=body,
                          path=Path(c.name), layer="registry"))
    for rid, cmd, keywords, expl in _SELF_DOCS:
        fm = {"id": rid, "type": "doc", "keywords": keywords.split(), "related": [cmd]}
        rules.append(Rule(id=rid, type="doc", fm={**fm, "command": cmd},
                          body=f"{expl}\n\n{keywords}", path=Path(rid), layer="registry"))
    return rules


def answer(question: str, top: int = 3) -> dict:
    """Deterministic answer: the best command, a one-line why, and runner-up commands."""
    ranked = recall.rank(_corpus(), question, top=max(top, 3))
    hits: list[dict] = []
    for r, score in ranked:
        cmd = registry.get(r.id) or registry.get(str(r.fm.get("command") or ""))
        if cmd is None:
            continue
        hits.append({"command": cmd.name, "example": cmd.example,
                     "explanation": r.body.split("\n\n")[0] if r.type == "doc" else cmd.desc,
                     "score": score})
        if len(hits) >= top:
            break
    return {"question": question, "hits": hits}


def render(result: dict) -> str:
    hits = result["hits"]
    if not hits:
        return (f'fux how: no command matched "{result["question"]}".\n'
                "Try `fux help` for the grouped command list.")
    best = hits[0]
    lines = [f'How to: {result["question"]}', "",
             f"  → {best['example']}", f"    {best['explanation']}"]
    if len(hits) > 1:
        lines += ["", "Related:"]
        lines += [f"  · {h['example']:<44}  {h['explanation']}" for h in hits[1:]]
    return "\n".join(lines)


def explain_prompt(result: dict) -> str:
    """`--explain`: a fenced prompt the HOST AGENT answers (its tokens, never the engine)."""
    best = result["hits"][0] if result["hits"] else {"command": "?", "example": "fux help"}
    return (
        "```explain (host agent — not the $0 engine path)\n"
        f"Question: {result['question']}\n"
        f"Deterministic match: {best['example']}\n"
        "Write a 2–3 sentence answer grounded ONLY in the command above and the "
        "Fux docs already in context. Do not invent flags. End with the exact command.\n"
        "```")
