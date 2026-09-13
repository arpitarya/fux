---
type: OpenItem
id: W-152
title: "W-152 — close archived_weight and recency_half_life_days"
description: "Two of the four ranking priors, ruled closed by Arpit on 2026-09-13 on VERDICT-W143's evidence. Both ship as no-ops, so nothing moves for anyone; what goes is two global multipliers that cannot be set correctly. The archived FACT stays and is already on every hit. Ratified here, not built."
status: open
lane: agent
timestamp: 2026-09-13T00:00:00Z
filed: 2026-09-13
---

# W-152 — close `archived_weight` and `recency_half_life_days`

**Model: Sonnet.** Same shape as W-151, which **landed 2026-09-13**
([IMPLEMENTATION.md](../IMPLEMENTATION.md)) and is the worked example — the
refusal table `tune._REMOVED_KEYS` and its Node twin already exist. ⚠ **Escalate to
Opus if a record needs re-arguing rather than editing.**

## The ruling

**Arpit, 2026-09-13**, on the recommendation in this session: close both.
Option (c) of the three [W-143](../../archive/open/W-143-four-no-op-priors.md) named, now taken for
two more of the four priors.

## The evidence

[VERDICT-W143](../regression/2026-09-12-priors-and-tables/VERDICT-W143.md), 26
intent-split probes across three rungs, truth from the corpus's own
declarations:

| knob | best candidate | net vs floor of **6** | how it fails |
|---|---|---|---|
| `archived_weight` | `0.75`, clears on `rung-01000` | **+2** | breaks `p20` on *both* other rungs |
| `recency_half_life_days` | none | — | **at ≤365 days history-seeking goes to 0/13** |

**The trade, at the shipped defaults:** the system already scores **11–12/13
current-seeking and 8–9/13 history-seeking**. Every value of either knob that
takes current-seeking to 13/13 drags history-seeking to 5/13 or lower. **+1 or
+2 in exchange for −3 to −9.**

⚠ **`archived_weight` was NEVER in W-97's sweep at all** (W-73's law), so no
selection evidence for it exists anywhere outside that verdict. Carried here
from W-97 before it was archived.

## Why closing costs nothing user-facing

- **Both ship as no-ops** — `archived_weight` at `1.0` (identity),
  `recency_half_life_days` at `0.0` (off). `Weighting.of()` returns the same
  float before and after. **This is a cleanup, not a ranking change**, which is
  also the answer to *never ship a ranking change off one synthetic corpus*:
  nothing ships.
- **The archived FACT survives and is already public** — `archived=true` in
  `.fux/sources/dirs`, the flag on the record, `ARCHIVED_MARKER = "[archived]"`
  and a response-level note in prose output, and `archived: bool` on every JSON
  hit, `required: always`, with the schema's own instruction: *"BRANCH ON THIS,
  never on the prose note."* An agent can filter and a human can see.
- ⚠ **Recency is the asymmetric one.** Closing it removes a capability, because
  `mtime` is on every record in the index and appears **nowhere** in
  `query/output.schema.json`. [W-153](W-153-mtime-on-the-hit.md) exposes it and
  is **not a blocker** — it is filed so the gap is named rather than discovered.

## Definition of done

1. **Both keys leave the closed key set** in `src/fux/tune.py`, and their fields
   and branches leave `Weighting`, `Weighting.of()` and the `maximum` bound in
   `src/fux/query/rank.py`. Check `src/fux/query/__init__.py` and
   `src/fux/doctor.py` for the same names.
2. **`recency_multiplier` and its module** — `src/fux/ingest/priors.py` exists
   for this knob. Decide in the change whether it goes or stays for `mtime`
   consumers, and **say which in the commit message**.
3. **The Node twin moves in the same change** — `node/src/config/tune.mjs`,
   `node/test/config.test.mjs`. `tests/test_node_twins.py` will demand it.
4. **Each key is REFUSED BY NAME, not as an unknown key**, exactly as W-151
   does for `superseded_weight`: the error says it was removed on 2026-09-13
   and why. A silent *"unknown key"* on a key fux itself shipped costs somebody
   an afternoon.
5. **`.fux/tune.toml` in this repo drops both keys.**
6. **Records amended in the same change** (Law zero):
   [SR-TUNE](../../records/0135_tuning.md), [SR-RANKING](../../records/0111_ranking.md),
   [SR-ARCHIVED-CONTENT](../../records/0134_archived-content.md) — which must keep
   describing the *flag* while losing the *weight* — plus
   [SR-DOTFUX](../../records/0102_fux-directory.md) and
   [SR-DOCTOR](../../records/0153_doctor.md) wherever they name a key.
   Then `scripts/sr-owns.py --write && scripts/sr-hash.py --write`.
7. **`CONFIG-SKILL.md` template and its three renderings** — `.agents/`,
   `.claude/`, `.kiro/`. Edit the template, copy across.
8. **`tools/quality-controls/priors_sweep.py`** sweeps these knobs. With three
   of four gone it has one subject left; retire it or narrow it, deliberately.
9. **`CHANGELOG.md`**, and **both suites whole** plus `node --test`.

## In scope / out of scope

- **IN:** the two knobs, their keys, plumbing, docs, refusals.
- **OUT — do not touch:** `archived=true` in `.fux/sources/dirs`, the `archived`
  record property, `ARCHIVED_MARKER`, the `archived` field on the hit, every
  `mtime` in the index. **The facts are not the weights.**
- **OUT:** `rerank_weight` — [W-154](W-154-rerank-weight-cost.md), a different
  question on a different plane.
- **OUT:** any query-side flag (`--intent`, `--as-of`, `--no-archived`). Those
  are an unopened fork with no compare doc.

## Key files

`src/fux/tune.py` · `src/fux/query/rank.py` · `src/fux/query/__init__.py` ·
`src/fux/doctor.py` · `src/fux/ingest/priors.py` · `node/src/config/tune.mjs` ·
`.fux/tune.toml` · `src/fux/templates/agents/CONFIG-SKILL.md` ·
`tools/quality-controls/priors_sweep.py`

## Tests

`tests/test_config.py` · `tests/test_tune_boundary.py` · `tests/query/test_priors.py` ·
`tests/test_doctor.py` · `tests/test_node_config_parity.py`, plus a **new** test
per key that the named refusal fires.
