"""Hook entrypoints — read the stdin event JSON, emit guidance (plan §8 I/O contract).

stdin  ← { session_id, cwd, tool_name, tool_input.file_path, … }
stdout → guidance injected as additionalContext
exit 0 → OK · exit 2 → block (only when the project opts into `strict`)
"""
from __future__ import annotations

import os
import sys

from fux import check as checkmod
from fux import (capture, config, context, drift, explain, fix, frontmatter,
                 loader, paths, recall, touch)
from fux.findings import blocking
from fux.hookio import edited_rel, event, mode_of, root_of


def _debug_trace(where: str, exc: Exception) -> None:
    """Fail-open ≠ fail-silent: a hook swallows every error to keep the session
    alive, but under `FUX_DEBUG=1` the swallowed exception is surfaced on stderr so
    a hidden bug is still discoverable (mirrors cage's `CAGE_DEBUG` discipline)."""
    if os.environ.get("FUX_DEBUG") == "1":
        import traceback
        sys.stderr.write(f"fux hook {where}: {type(exc).__name__}: {exc}\n")
        traceback.print_exc()


def session_start() -> int:
    try:
        root = root_of(event())
        if root:
            print(context.run(root))
    except Exception as e:  # noqa: BLE001 — hook fail-open: never break the session
        _debug_trace("session_start", e)
    return 0


def post_tool_use() -> int:
    try:
        return _post_tool_use()
    except Exception as e:  # noqa: BLE001 — hook fail-open: never break the session
        _debug_trace("post_tool_use", e)
        return 0


def _post_tool_use() -> int:
    ev = event()
    root = root_of(ev)
    if not root or mode_of(root) == "off":
        return 0
    rel = edited_rel(ev, root)
    if rel is None:
        return 0
    session = ev.get("session_id", "")
    if touch.is_rule_file(root, rel):
        fm, _ = frontmatter.split((root / rel).read_text(encoding="utf-8"))
        touch.mark_rule_edited(root, session, str(fm.get("id") or rel.rsplit("/", 1)[-1][:-3]))
        return 0
    hits = touch.affected(root, rel, session)
    if hits:
        ids = ", ".join(r.id for r in hits)
        print(f"⚑ Fux: {rel} is governed by rule(s) [{ids}] not updated this session. "
              f"Review with `fux why <id>` and update the rule body if the logic changed.")
    return 0


def stop() -> int:
    """Fail-open wrapper. The deliberate strict-mode `return 2` is computed inside
    `_stop()` and passed straight through — only an *exception* maps to 0, so a
    blocking finding still hard-blocks (the strict path is never swallowed)."""
    try:
        return _stop()
    except Exception as e:  # noqa: BLE001 — hook fail-open: an error never breaks the turn
        _debug_trace("stop", e)
        return 0


def _stop() -> int:
    ev = event()
    root = root_of(ev)
    if not root:
        return 0
    cfg = config.load(paths.Footprint(root).config)
    mode = cfg.get("mode", "fix")
    if mode == "off":
        return 0
    if cfg.get("capture"):
        new = capture.observe(root, cfg)
        if new:
            print(capture.summary(capture.pending(root)))
    findings = checkmod.run(root)
    if not findings:
        return 0
    if mode == "fix":
        _emit_drift_prompts(root, findings)   # semantic drift → scoped prompt first
        for note in fix.apply(root, findings):
            print(f"✔ Fux auto-fixed: {note}")
        findings = checkmod.run(root)  # re-check after mechanical fixes
    for f in findings:
        print(f"⚑ Fux {f.line()}")
    if mode == "strict" and blocking(findings):
        sys.stderr.write("Fux strict: unresolved blocking findings — see above.\n")
        return 2
    return 0


def _emit_drift_prompts(root, findings) -> None:
    """For stale/plan-drift findings, print the scoped edit prompt with the diff."""
    ids = {f.rule_id for f in findings if f.kind in ("stale", "plan-drift")}
    if not ids:
        return
    by_id = loader.resolve(root).by_id()
    for rid in sorted(ids):
        rule = by_id.get(rid)
        if rule:
            print(drift.scoped_prompt(rule, root))


def session_end_propose() -> int:
    """Opt-in (config `propose_forward`) SessionEnd nudge to propose rules-with-why.

    The harness calls no model — it only prompts the host agent to run the
    propose-rules skill, whose drafts land in .fux/CANDIDATES.md for triage. Never
    blocks, never nags when the gate is off (rule-proposer §3A)."""
    try:
        root = root_of(event())
        if not root or not config.load(paths.Footprint(root).config).get("propose_forward"):
            return 0
        print("Fux: consider proposing rules from this session — review the diff + your "
              "rationale, draft candidates-with-why, then `fux propose-rules --from drafts.json` "
              "(skills/propose-rules/SKILL.md). Drafts await triage in .fux/CANDIDATES.md; "
              "nothing auto-activates.")
    except Exception as e:  # noqa: BLE001 — hook fail-open: never break the session
        _debug_trace("session_end_propose", e)
    return 0


def user_prompt_recall() -> int:
    try:
        return _user_prompt_recall()
    except Exception as e:  # noqa: BLE001 — hook fail-open: never break the session
        _debug_trace("user_prompt_recall", e)
        return 0


def _user_prompt_recall() -> int:
    ev = event()
    root = root_of(ev)
    prompt = ev.get("prompt") or ev.get("user_prompt") or ""
    if not root or not prompt:
        return 0
    hits = recall.run(root, prompt, top=4)
    if hits:
        lines = ["Fux — rules relevant to this prompt:"]
        for r, _ in hits:
            lines.append(explain.render_why(r))
            lines.append("---")
        payload = "\n".join(lines)
        print(payload)
        _emit_recall_receipt(root, ev, [r for r, _ in hits], payload)
    return 0


def _emit_recall_receipt(root, ev, rules, payload) -> None:
    """File a token-saving receipt: distilled recall vs the selected rules' whole
    source files (the §5 conservative default). Fail-open — never breaks the hook."""
    try:
        from fux import cage_receipt
        seen, raw = set(), 0
        for r in rules:                       # whole source files fux selected, deduped
            if r.path in seen:
                continue
            seen.add(r.path)
            raw += cage_receipt.toks(r.path.read_text(encoding="utf-8"))
        cage_receipt.emit("fux", raw, cage_receipt.toks(payload),
                          task=ev.get("session_id", ""), op="hook-recall")
    except Exception as e:  # noqa: BLE001 — fail-open: no receipt, no disruption (traced under debug)
        _debug_trace("recall_receipt", e)
