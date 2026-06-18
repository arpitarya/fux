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
    return _route_through_pr(here, r, by, when, no_pr=args.no_pr)


def _route_through_pr(here: Path, r, by: str, when: str, no_pr: bool) -> int:
    """Route a ratification through a NEW branch + gated PR (§2g) so the constitution
    can never land except via the required `fux gate`/`ai-review` checks. Deterministic
    git/gh only — no model call. If a PR can't be opened (no remote, gh missing, branch
    exists, --no-pr, or not on the protected branch) the on-disk ratification stands and
    the manual push→PR commands are printed instead of committing to a protected branch."""
    if no_pr or not gitutil.is_repo(here) or not gitutil.has_remote(here):
        return 0
    branch = f"constitution/{r.id}"
    on = gitutil.current_branch(here)
    if on is not None and on != gitutil.default_branch(here):
        # Already on a feature branch — leave the write for the caller to commit/PR.
        return 0
    paths_ = [str(r.path.relative_to(here)), ".fux/constitution.lock"]
    tpath = provenance.transcript_path(here, r.id)
    if tpath.is_file():
        paths_.append(str(tpath.relative_to(here)))
    msg = (f"constitution: ratify {r.id} (by {by}, {when})\n\n"
           f"Routed through a gated PR — a ratification never lands on the protected "
           f"branch directly (§2g).\n\nAgent: claude-code")
    body = (f"Ratifies constitutional rule **{r.id}** (by {by}, {when}).\n\n"
            f"Authored on a new branch and opened as a PR by `fux ratify` so the change "
            f"is routed through the required `fux gate` + `ai-review` checks — the apex can "
            f"never land except via the gate (§2g).")
    ok, info = gitutil.open_pr_branch(here, branch, paths_, msg,
                                      title=f"constitution: ratify {r.id}", body=body)
    if ok:
        print(f"  → opened PR on branch '{branch}': {info}")
        print("  the ratification lands only after the required checks pass (§2g).")
    else:
        print(f"  ⚠ could not auto-open the PR ({info}). The ratification is written on "
              f"disk; route it through the gate manually:")
        print(f"      git switch -c {branch} && git add {' '.join(paths_)}")
        print(f"      git commit -m 'constitution: ratify {r.id}' && git push -u origin {branch}")
        print(f"      gh pr create --base {gitutil.default_branch(here)} --head {branch}")
    return 0


def cmd_constitution(args) -> int:
    """Status view of the apex: what's constitutional, what each governs, current violations."""
    out = constatus.render(root())
    print(out)
    return 2 if "blocking violations" in out else 0


def cmd_critic(args) -> int:
    """Critique a proposed change: deterministic pass first, then list judgment principles the
    host agent must self-critique. $0, no LLM — the agent (or `[critic]` extra) is the judge.

    Advisory-first (F1): deterministic fails block (exit 2); judgment fails are *suggestions*
    by default and do not block unless escalated via `critic_block_judgment`."""
    here = root()
    result = criticloop.critique(here, args.proposal)
    criticloop.record(here, result)
    for v in result.verdicts:
        suffix = " (advisory)" if v.status == "fail" and v.advisory else ""
        mark = {"pass": "✔", "fail": "✗", "needs-judgment": "?"}.get(v.status, "·")
        print(f"  {mark} [{v.status}{suffix}] {v.principle}: {v.rationale}".rstrip())
    sugg = result.suggestions
    if sugg:
        print(f"\n{len(sugg)} judgment suggestion(s) — advisory, not blocking. Escalate a trusted "
              "principle with `critic_block_judgment` in .fux/config.toml to make it block.")
    pend = result.pending
    if pend:
        print(f"\n{len(pend)} judgment principle(s) need self-critique — review each against the "
              "proposal, revise, escalate if borderline (skills/critic/SKILL.md).")
    if result.blocked:
        print("\n✗ critic: a blocking principle is violated — fix before proceeding.")
        return 2
    if not pend:
        print("\n✔ critic: deterministic pass clean."
              + (" Judgment suggestions are advisory." if sugg else ""))
    return 0
