"""Read-only query command handlers (recall/why/refs/new/coverage/verify/tour)."""
from __future__ import annotations

from fux import (capture, coverage, explain, lint, recall, savings, scaffold,
                 stats, tour, verify)
from fux.cliutil import root


def cmd_recall(args) -> int:
    hybrid = True if getattr(args, "hybrid", False) else None
    for r, score in recall.run(root(), args.query, top=args.top, hybrid=hybrid):
        print(f"{score:6.3f}  {r.id} ({r.type}) — {r.title}")
    return 0


def cmd_why(args) -> int:
    r = explain.why(root(), args.id)
    if r is None:
        print(f"fux: no rule '{args.id}'")
        return 1
    print(explain.render_why(r))
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


def cmd_verify(_args) -> int:
    results = verify.run(root())
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
    rep = savings.build(root(), query=getattr(args, "query", None), top=args.top)
    print(savings.render(rep))
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
