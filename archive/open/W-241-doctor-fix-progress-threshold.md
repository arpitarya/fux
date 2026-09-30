---
type: Handoff
name: W-241
description: "fux doctor --fix cannot repair an output.toml that lacks [cli] progress_threshold, because doctor reads that key (for its own progress bar, W-238) before it starts — so the repair verb refuses the one file it exists to fix."
item: W-241
filed: 2026-09-30
ball: agent
---

# W-241 — `doctor --fix` cannot add `progress_threshold`

**Status: closed 2026-09-30 — built as specified.** `doctor` takes any
`output.toml` key the file lacks from the template, per key, so `--fix` starts
and writes it ([SR-OUTPUT](../../records/0143_output-defaults.md) decision 20b,
`cli._apply_output_defaults`). Two tests in `tests/test_output_config.py`
reproduced the refusal first. The audit (3) found one other key read before
`--fix`: `[cli.json] enabled`, which the same fallback covers. PII is exempt for
`doctor`, and `fill_missing`, `Progress` and the fail-open observer read no
repo config. ⚠ The fallback is recorded in SR-OUTPUT, not SR-DOCTOR as step 1
said, because SR-OUTPUT decision 20 already owns `doctor`'s template fallback
(L0: stated once). SR-DOCTOR's L12 note points at it.

~~Status: filed 2026-09-30, not started.~~ Found by the W-237 capture: an
older `fux-lab` rung copy's `.fux/output.toml` had no `[cli] progress_threshold`,
and `fux doctor --fix` stopped with the L12 missing-key error instead of
writing it. The capture added `progress_threshold = 200` (the template's value)
by hand, and [its report](../regression/2026-09-30-rm3-grounded/report.md) says so.

**Model:** Claude Code, **Sonnet**.

## Definition of done

1. `fux doctor --fix` on a tree whose `output.toml` lacks the key writes it from
   the template and exits clean. Doctor's own progress bar must not need the key
   it is about to repair (decide the fallback in [SR-DOCTOR](../../records/0152_doctor.md),
   not in code — L12 forbids a code default).
2. A test that reproduces the refusal first.
3. The same audit for every other key doctor reads before `--fix` runs.
