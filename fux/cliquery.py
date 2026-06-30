"""Read-only query command handlers (recall/why/refs/new/coverage/verify/tour)."""
from __future__ import annotations
import sys

from fux import (candidates, capture, config, costledger, coverage, explain,
                 feedback, fetchrules, lint, loader, mine, paths, recall,
                 savings, scaffold, seal, stats, tour, verify)
from fux.cliutil import root, scope_root


def cmd_feedback(args) -> int:
    import json
    here = root()
    if getattr(args, "record", None):
        raw = sys.stdin.read() if args.record == "-" else open(args.record).read()
        feedback.record(here, json.loads(raw))
        print("fux feedback: recorded")
        return 0
    print(feedback.render(feedback.load(here)))
    return 0


def cmd_recall(args) -> int:
    hybrid = True if getattr(args, "hybrid", False) else None
    expand = True if getattr(args, "expand", False) else None
    for r, score in recall.run(scope_root(args), args.query, top=args.top, hybrid=hybrid, expand=expand):
        print(f"{score:6.3f}  {r.id} ({r.type}) — {r.title}")
    return 0


def cmd_why(args) -> int:
    here = root()
    r = explain.why(here, args.id)
    if r is None:
        print(f"fux: no rule '{args.id}'")
        return 1
    if getattr(args, "history", False):
        print(explain.render_history(here, r))
        return 0
    print(explain.render_why(r))
    return 0


def cmd_seal(args) -> int:
    here = root()
    cfg = config.load(paths.Footprint(here).config)
    rules = loader.resolve(here, cfg).rules
    if not getattr(args, "all", False):
        wanted = set(args.ids)
        if not wanted:
            print("fux: pass rule ids or --all")
            return 1
        rules = [r for r in rules if r.id in wanted]
        missing = wanted - {r.id for r in rules}
        for m in sorted(missing):
            print(f"fux: no rule '{m}'")
    sealed = seal.stamp(here, rules)
    if sealed:
        print("✔ sealed " + ", ".join(sealed))
    else:
        print("· nothing to seal (no resolvable code_refs, or already current)")
    return 0


def cmd_refs(args) -> int:
    hits = explain.refs(root(), args.file)
    print("\n".join(f"{r.id} ({r.type}) — {r.title}" for r in hits)
          or f"(no rules govern {args.file})")
    return 0


def cmd_new(args) -> int:
    target = scaffold.make(root(), args.type, args.id, domain=args.domain)
    print(f"✔ created {target}")
    return 0


def cmd_coverage(_args) -> int:
    c = coverage.run(root())
    print(f"Documented-logic coverage: {c.pct:.0f}% ({c.governed}/{c.total} important files)")
    for f in c.uncovered[:20]:
        print(f"  ✗ {f}")
    return 0


def cmd_verify(args) -> int:
    results = verify.run(root(), fuzz=getattr(args, "fuzz", False))
    failed = [v for v in results if v.status == "fail"]
    for v in results:
        mark = {"pass": "✔", "fail": "✗", "skip": "·"}[v.status]
        print(f"{mark} {v.rule_id} {v.detail}".rstrip())
    return 1 if failed else 0


def cmd_tour(_args) -> int:
    target = tour.write(root())
    print(f"✔ onboarding path → {target}")
    return 0


def cmd_savings(args) -> int:
    here = root()
    if getattr(args, "reset", False):
        costledger.reset(here)
        print("✔ cost ledger cleared")
        return 0
    rep = savings.build(here, query=getattr(args, "query", None), top=args.top)
    print(savings.render(rep))
    print(costledger.render_summary(costledger.load(here), per_mtok=rep.usd_per_mtok), end="")
    return 0


def cmd_lint(args) -> int:
    issues = lint.run(root())
    for f in issues:
        print(f.line())
    if not issues:
        print("✔ No lint findings — every rule carries its weight.")
    return 1 if (issues and getattr(args, "strict", False)) else 0


def cmd_stats(_args) -> int:
    print(stats.render(stats.build(root())))
    return 0


def cmd_mine(args) -> int:
    print(mine.render(mine.mine(root(), min_sites=getattr(args, "min_sites", 3))))
    return 0


def cmd_propose_rules(args) -> int:
    """Propose draft rules into .fux/CANDIDATES.md — forward (agent --from) or retro ($0).

    The harness never calls an LLM: --retro is pure mine+git; --from just gates/files
    the candidates the host agent drafted. Nothing here auto-activates (§2).
    """
    from fux import proposer
    here = root()
    if getattr(args, "from_file", None):
        import json
        raw = sys.stdin.read() if args.from_file == "-" else open(args.from_file).read()
        added = proposer.from_json(here, json.loads(raw))
    elif getattr(args, "retro", False):
        added = proposer.retro(here)
    else:
        print("fux propose-rules — two-sided (drafts only; nothing auto-activates):\n"
              "  forward (skill): the agent drafts candidates-with-why from the diff +\n"
              "    its rationale, then files them: fux propose-rules --from drafts.json\n"
              "    (see skills/propose-rules/SKILL.md)\n"
              "  retro ($0):      fux propose-rules --retro   (mine + git-history why)\n"
              "  triage:          fux candidates [--pending] · accept|reject <id>")
        return 0
    print(f"✔ {len(added)} draft(s) → {candidates.path_of(here)}" if added
          else "· no new candidates (all dropped by the gate, duplicate, or capped)")
    return 0


def cmd_candidates(args) -> int:
    here = root()
    action, cid = getattr(args, "action", None), getattr(args, "id", None)
    if action in ("accept", "reject"):
        if not cid:
            print(f"fux: `fux candidates {action} <id>` needs a candidate id")
            return 1
        if action == "reject":
            c = candidates.set_state(here, cid, "rejected")
            print(f"✔ rejected {cid}" if c else f"fux: no candidate '{cid}'")
            return 0 if c else 1
        return _accept_candidate(here, cid)
    print(candidates.render(here, pending=getattr(args, "pending", False),
                            why_todo=getattr(args, "why_todo", False)))
    return 0


def _accept_candidate(here, cid) -> int:
    """Human ratification: promote one draft to an active, standard-tier rule."""
    import datetime as _dt

    from fux import fmwrite, schema
    from fux.model import TYPES
    c = next((x for x in candidates.read(here) if x.cid == cid), None)
    if c is None:
        print(f"fux: no candidate '{cid}'")
        return 1
    rid, today = candidates._slug(c.title) or cid, _dt.date.today().isoformat()
    fm = {"id": rid, "type": c.kind if c.kind in TYPES else "rule", "status": "active",
          "tier": "standard", "created": today, "updated": today,
          "code_refs": [r.split(":")[0] for r in c.code_refs], "source": c.source}
    if c.why_source:
        fm["why_source"] = c.why_source
    if errs := schema.validate(fm):
        print("fux: cannot accept — " + "; ".join(errs))
        return 1
    target = paths.Footprint(here).rules / f"{rid}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        print(f"fux: rule '{rid}' already exists — reject the candidate or rename it")
        return 1
    target.write_text(fmwrite.dump(fm, f"**{c.kind.title()}:** {c.title}\n\n**Why:** {c.why}"),
                      encoding="utf-8")
    candidates.set_state(here, cid, "accepted")
    print(f"✔ accepted {cid} → active rule {target}")
    return 0


def cmd_capture(args) -> int:
    here = root()
    if getattr(args, "clear", False):
        capture.clear(here)
        print("✔ capture queue cleared")
        return 0
    if not getattr(args, "list", False):
        capture.observe(here)
    print(capture.summary(capture.pending(here)))
    return 0


def cmd_how(args) -> int:
    """fux explains fux: deterministic recall over the command registry + self-docs.

    Pure $0 — `--explain` only emits a prompt for the host agent (no engine model call).
    """
    from fux import howto
    result = howto.answer(args.question, top=getattr(args, "top", 3))
    print(howto.render(result))
    if getattr(args, "explain", False):
        print("\n" + howto.explain_prompt(result))
    return 0 if result["hits"] else 1


def cmd_ingest(args) -> int:
    """`/fux ingest <sources…>` is a SKILL (the agent fetches/extracts/drafts, from
    URLs, PDF, Excel, Word, TXT, image, JSON/YAML, or Swagger — and, with
    `--follow-links`, the documents a page links). The engine only does the
    deterministic, $0 parts: glob-expand + dedup the source list, show the draft
    review queue (`--queue`), and re-verify a drafted source (`--recheck`, behind
    the network extra) — never on the default `fux check` path, never a model call.
    """
    targets = list(getattr(args, "targets", None) or [])
    if getattr(args, "queue", False):
        from fux import ingestqueue
        print(ingestqueue.render(root()))
        return 0
    if getattr(args, "connector", None):
        from fux import ingestconnector
        try:
            pl = ingestconnector.plan(args.connector, getattr(args, "query", None),
                                      since=getattr(args, "since", None),
                                      max_items=getattr(args, "max", ingestconnector.DEFAULT_MAX))
        except ingestconnector.ConnectorError as e:
            print(f"fux: {e}")
            return 1
        print("fux ingest (connector) is an agent skill — the agent pulls server-side-filtered\n"
              "  structured data (MCP → REST+PAT → export/clone → CDP-JSON → DOM; GitHub first);\n"
              "  fux never builds a client or calls an API ($0). The engine only bounds + governs.\n"
              f"  {pl.describe()}\n"
              "  Run it via Claude: /fux ingest --connector <c> --query \"<filter>\" "
              "(see skills/ingest/SKILL.md)\n"
              "  Low-trust drafts land in the review queue — show it: fux ingest --queue")
        return 0
    if getattr(args, "recheck", False):
        from fux import ingest          # lazy: the only network/file-reading path
        return ingest.recheck_cmd(root(), targets[0] if targets else None)
    if targets:
        from fux import ingestqueue
        srcs = ingestqueue.expand_sources(targets)   # globs expand against cwd
        print(f"fux ingest is an agent skill — fetching/extracting/drafting are the "
              f"host agent's tokens, not the engine.\n  {len(srcs)} source(s) "
              f"(globs expanded, deduped):")
        for s in srcs:
            print(f"    {s}  [{ingestqueue.classify_type(s)}]")
        print("  Run it via Claude: /fux ingest <sources…> [--follow-links] "
              "(see skills/ingest/SKILL.md)\n"
              "  Drafts land in the review queue — show it: fux ingest --queue")
        return 0
    print("fux ingest is an agent skill — fetching/extracting and drafting are the "
          "host agent's tokens, not the engine.\n"
          "  Run it via Claude: /fux ingest <sources…>   (see skills/ingest/SKILL.md)\n"
          "  Queue ($0):        fux ingest --queue        (show the draft review queue)\n"
          "  Recheck ($0):      fux ingest <rule-id> --recheck   "
          "(re-verify a drafted source; needs the [scrape] extra)")
    return 0


def cmd_scrape_deprecated(args) -> int:
    """Deprecated alias for `cmd_ingest` — kept for one release after the rename."""
    print("fux: 'scrape' is deprecated, use 'ingest' instead (same behaviour).",
          file=sys.stderr)
    return cmd_ingest(args)


def cmd_fetch_rules(args) -> int:
    """Fetch and print the plain-text content of a URL / file / PDF.

    This is the $0 extraction half of ``/fux fetch-rules``.  Pass the output
    to the skill (Claude) which analyzes it and authors durable rule entries.
    """
    source = args.source
    try:
        text = fetchrules.fetch_text(source)
    except fetchrules.PDFDependencyError as exc:
        print(f"fux: {exc}", file=sys.stderr)
        return 1
    except fetchrules.FetchError as exc:
        print(f"fux: {exc}", file=sys.stderr)
        return 1
    label = fetchrules.source_label(source)
    if not getattr(args, "raw", False):
        print(f"# Source: {label}  ({len(text):,} chars)\n")
    print(text)
    return 0
