---
type: OpenItem
id: W-153
title: "W-153 — put mtime on the ask hit"
description: "Every record in the index carries a committed mtime and it appears nowhere in the public output shape, so a caller gets no date back. One additive field across three readers. Filed because closing recency_half_life_days removes the only date-awareness fux had. Ratified, not built."
status: open
lane: agent
timestamp: 2026-09-13T00:00:00Z
filed: 2026-09-13
---

# W-153 — `mtime` on the ask hit

**Model: Sonnet** for the field and the three readers. ⚠ **Opus for the
[SR-API](../../records/0155_api.md) amendment** — that record freezes the only
public shape fux has, and what a frozen surface may gain is a judgement, not an
edit.

## Why

**Every record carries an `mtime`** — the committed date, deterministic, already
used by ingest. It appears **nowhere** in
[`src/fux/query/output.schema.json`](../../src/fux/query/output.schema.json). So
a caller cannot sort by recency, filter by age, or see how old an answer is.

This is the asymmetry that made [W-152](W-152-close-archived-and-recency.md)'s
two knobs different from each other:

| closing | what the caller still has |
|---|---|
| `archived_weight` | `archived: bool` on every hit, `required: always`, plus `[archived]` in prose. **Nothing lost** |
| `recency_half_life_days` | **nothing.** No date reaches the caller at all |

**Not a blocker on W-152 and W-152 is not a blocker on this.** They are filed
together so the gap is named rather than discovered by whoever first asks *"how
old is this answer?"*

## Definition of done

1. **`mtime` on the hit** in `query/output.schema.json`, with its `required`
   discipline stated: it is on every record, so `always` is the honest value —
   **confirm that against an index built before the property shipped** before
   writing `always`, because SR-RECORD warns that older indexes lack keys.
2. **Its type and format decided and stated once.** The index's own encoding is
   the default answer; do not invent a second date format in the output.
3. **Three readers agree** — the Python reader, `node/`, and MCP — and
   `scripts/check-version-parity.py` stays green, including `--with-bundle`.
4. **[SR-API](../../records/0155_api.md) amended in the same change**, and
   [SR-RECORD](../../records/0109_index-record.md) if it describes what reaches
   the caller. Then `scripts/sr-owns.py --write && scripts/sr-hash.py --write`.
5. **Prose output is NOT changed** unless Arpit asks — this item buys a field
   for programmatic callers. A date on every CLI line is a separate taste
   decision.
6. **Both suites whole** plus `node --test node/test/*.test.mjs`.

## In scope / out of scope

- **IN:** one additive field, its schema entry, the three readers, the records.
- **OUT:** sorting, filtering or ranking by it. **This item exposes a fact and
  nothing more** — a `--as-of` flag or any recency ordering is the unopened
  query-side fork and needs a compare doc first.
- **OUT:** `superseded` / `superseded_by` on the hit. The same class of change
  and the same argument, but a different subject and not authorised here.

## Hazard

⚠ **Additive is not free.** `output.schema.json` is described in the code as
*"the only PUBLIC shape fux has"*. A consumer that validates strictly against
the old schema sees a new key. Say in the change whether that is a breaking
change under the `_format` version policy, and if it is, say so in
`CHANGELOG.md` rather than letting a minor bump carry it.
