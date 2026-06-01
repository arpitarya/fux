"""Read-only query command handlers (recall/why/refs/new/coverage/verify/tour)."""
from __future__ import annotations

from fux import coverage, explain, recall, scaffold, tour, verify
from fux.cliutil import root


def cmd_recall(args) -> int:
    for r, score in recall.run(root(), args.query, top=args.top):
        print(f"{score:6.2f}  {r.id} ({r.type}) — {r.title}")
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
