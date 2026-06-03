"""Hook entrypoints — read the stdin event JSON, emit guidance (plan §8 I/O contract).

stdin  ← { session_id, cwd, tool_name, tool_input.file_path, … }
stdout → guidance injected as additionalContext
exit 0 → OK · exit 2 → block (only when the project opts into `strict`)
"""
from __future__ import annotations

import sys

from fux import check as checkmod
from fux import (capture, config, context, drift, explain, fix, frontmatter,
                 loader, paths, recall, touch)
from fux.findings import blocking
from fux.hookio import edited_rel, event, mode_of, root_of


def session_start() -> int:
    root = root_of(event())
    if root:
        print(context.run(root))
    return 0


def post_tool_use() -> int:
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


def user_prompt_recall() -> int:
    ev = event()
    root = root_of(ev)
    prompt = ev.get("prompt") or ev.get("user_prompt") or ""
    if not root or not prompt:
        return 0
    hits = recall.run(root, prompt, top=4)
    if hits:
        print("Fux — rules relevant to this prompt:")
        for r, _ in hits:
            print(explain.render_why(r))
            print("---")
    return 0
