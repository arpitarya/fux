---
type: OpenItem
id: W-218
title: "W-218 — the scorer cannot score a generation-2 set: `--set` is an int and `just golden-score` does not find a single-rung hand-off"
description: "Found 2026-09-22 while writing Arpit the command to score set-2-u. Two defects in tools/golden-score and the justfile, both of which predate the set-<gen>-<x|u> naming: score.py's --set is type=int so '2-u' is refused, and the golden-score recipe globs evidence/*/rung-*/ and evidence/rung-*/, so a hand-off filed flat at evidence/handoff-set-2-u.jsonl is never found. A workaround exists; the defect is that the workaround mislabels the output."
status: open
lane: build
timestamp: 2026-09-22T00:00:00Z
filed: 2026-09-22
ball: agent
---

# W-218 — the scorer does not know generation-2 set names

**Model: Sonnet.** Two small changes and their tests. **Touches no key**: the
scorer's code, the justfile recipe and a synthetic fixture — never a real key.

## The two defects

1. **`tools/golden-score/score.py` — `--set` is `type=int`.** Generation 2 names
   sets `set-<gen>-<x|u>` ([L11](../../records/0012_LAW-11-sealed-answer-key.md)
   decision 14), so `--set 2-u` exits 2 in argparse before anything is read.
   The value is only a label — it goes into the output's `"set"` field and the
   printed summary — so nothing else depends on it being a number.
2. **`just golden-score` never finds a flat hand-off.** It globs
   `<run>/evidence/*/rung-*/handoff-set-*.jsonl` and
   `<run>/evidence/rung-*/handoff-set-*.jsonl`. The `set-2-u` baseline filed its
   hand-off at `<run>/evidence/handoff-set-2-u.jsonl`, with the rung in the run
   name — so the recipe exits *"no handoff-set-\*.jsonl"* on the one run it now
   needs to score.

## The workaround in use until this lands

Arpit calls `score.py` directly with `--set 2`. **The output file is named
`set-2-u.json`, but its `"set"` field reads `2`** — which is also the name of a
**retired generation-1 set**. ⚠ **Read any score file from that run as `set-2-u`
whatever its `"set"` field says**; that mislabel is the reason this item exists.

## Definition of done

1. `--set` accepts a string matching `^\d+(-[xu])?$`; the output's `"set"` field
   carries it verbatim (`"2-u"`, or `"1"` for a generation-1 set).
2. The recipe also globs `<run>/evidence/handoff-set-*.jsonl`, taking the rung
   from a `--rung` argument or from the run's `PRE-REGISTRATION.md`, and labels
   the arm `single` as it already does for the flat-rung layout.
3. A test on a **synthetic** hand-off and a **synthetic** key under a
   `tmp_path` — never the real directory — for both the new name and the old
   integer, and for the flat layout.
4. `work/golden/README.md` §Phase 6 and prompt 5 name the flat layout if they
   describe the evidence tree.

## Out of scope

Running the scorer — **no agent invokes it, in either state**. Re-labelling the
score file Arpit produced with the workaround: it is his output, and the
reader's note above is the correction.
