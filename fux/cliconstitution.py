"""CLI handlers for the constitution layer — `ratify` + `critic` (deterministic, no LLM)."""
from __future__ import annotations

from datetime import date as _date
from pathlib import Path

from fux import config, constatus, constitution, criticloop, gitutil, loader, paths, provenance
from fux.cliutil import root


def cmd_ratify(args) -> int:
    """Stamp ratification + freeze the seal + update the lock — the only path to the apex."""
    here = root()
    cfg = config.load(paths.Footprint(here).config)
    rules = loader.resolve(here, cfg).rules
    by = args.by or gitutil.user_name(here) or ""
    if not by:
        print("fux: no ratifier — pass --by <name> (or set git user.name)")
        return 1
    when = args.date or _date.today().isoformat()
    dhash = None
    if args.debate:
        dpath = Path(args.debate)
        if not dpath.is_file():
            print(f"fux: debate transcript not found: {args.debate}")
            return 1
        # Pin the transcript as immutable evidence at the canonical path so `check_provenance`
        # can re-verify it. Re-hash from there, so the stamp matches what the check reads.
        canon = provenance.transcript_path(here, args.id)
        canon.parent.mkdir(parents=True, exist_ok=True)
        if dpath.resolve() != canon.resolve():
            canon.write_bytes(dpath.read_bytes())
        dhash = provenance.transcript_hash(canon)
    try:
        r = constitution.ratify(here, rules, args.id, by=by, date=when, debate_hash=dhash)
    except KeyError:
        print(f"fux: no rule with id '{args.id}'")
        return 1
    except ValueError as e:
        print(f"fux: {e}")
        return 1
    print(f"✔ ratified {r.id} → constitutional (by {by}, {when})")
    print(f"  content_seal frozen{f' + debate_hash {dhash}' if dhash else ''} + "
          ".fux/constitution.lock updated — the only path into the apex.")
    return 0


def cmd_constitution(args) -> int:
    """Status view of the apex: what's constitutional, what each governs, current violations."""
    out = constatus.render(root())
    print(out)
    return 2 if "blocking violations" in out else 0


def cmd_critic(args) -> int:
    """Critique a proposed change: deterministic pass first, then list judgment principles the
    host agent must self-critique. $0, no LLM — the agent (or `[critic]` extra) is the judge."""
    here = root()
    result = criticloop.critique(here, args.proposal)
    criticloop.record(here, result)
    for v in result.verdicts:
        mark = {"pass": "✔", "fail": "✗", "needs-judgment": "?"}.get(v.status, "·")
        print(f"  {mark} [{v.status}] {v.principle}: {v.rationale}".rstrip())
    pend = result.pending
    if pend:
        print(f"\n{len(pend)} judgment principle(s) need self-critique — review each against the "
              "proposal, revise, escalate if borderline (skills/critic/SKILL.md).")
    if result.blocked:
        print("\n✗ critic: a deterministic principle is violated — fix before proceeding.")
        return 2
    if not pend:
        print("\n✔ critic: deterministic pass clean.")
    return 0
