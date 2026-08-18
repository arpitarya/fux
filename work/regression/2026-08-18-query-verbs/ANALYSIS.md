# ANALYSIS — 2026-08-18 query-verb capture

No defect of the W-47 class here. The verbs behave as designed; what the
capture surfaced is three **output-contract inconsistencies**, all
caller-visible, all small, and none of them urgent.

---

## Confirmed sound

Recorded because each was checked deliberately, so a later session does not
re-litigate it:

- **The differential law holds on this corpus.** `ask --json` and
  `ask --json --scan` are byte-identical, floats included. The structural
  reason — the accelerator generates candidates and statistics, never scores,
  and both paths call one `rank()` — is doing its job.
- **`find` is a projection, not a second strategy.** `find --json` and
  `ask --json` return the same objects for the same query and `--top`.
- **`answer` states its ceiling in every text response**, and carries
  `"source": "index"` as the machine-readable form of the same claim.
- **All three verbs exit 0 on no match**, consistently, with the same message.

## Finding 1 — `--explain` cannot be read programmatically (minor)

`--explain` appends `[accelerator]` / `[scan]` / `[hybrid]` in **text mode
only**; `cmd_ask` returns before it when `--json` is set. A programmatic caller
therefore cannot log which machine answered.

Harmless for correctness — the paths are byte-identical by law — but it means a
caller cannot record whether a slow query was an unbuilt repo, which is exactly
the thing worth logging.

**Fix direction:** add `"path"` to the `--json` object when `--explain` is set.
Additive, so no existing consumer breaks.

## Finding 2 — `answer --json` omits `"source"` on the no-match path (minor)

```json
{"answer": null, "citation": null}          // no "source" key
{"answer": {...}, "citation": {...}, "source": "index"}
```

A consumer keying on `"source"` — which ADR-ANSWER recommends, as the way to
detect the M4 upgrade — must also handle its absence.

**Fix direction:** emit `"source": "index"` in both branches. It is a contract
change, however small, so it belongs in its own change with a note in
`CHANGELOG.md`.

## Finding 3 — `find`'s no-match line is prose on stdout (minor, arguable)

`No confident matches.` goes to **stdout**, so a pipeline like
`fux find … | xargs grep` receives it as if it were a path.

This is defensible: it is consistent across all three verbs, and `--json`'s
`{"results": []}` is the machine-readable form. Sending it to stderr for `find`
alone would make the verbs behave differently for the same condition.

**Recorded, not recommended.** ADR-FIND names it as the strongest of its
rejected alternatives and ties it to the record's veto condition — if a real
script is observed breaking on it, that is the evidence to reopen.

---

**All three filed together as [W-48](../../open/W-48-query-output-contract.md)**,
explicitly low priority under OPEN-WORK rule 5: the damage is static, not
accruing. Each is a caller-visible contract detail, and contract changes are
cheaper before there are many callers than after — which is the only argument
for doing them soon.

## What this capture does not establish

- **Nothing about ranking quality.** Five documents, hand-written, a handful of
  queries. The graded corpus is `fux-playground`, and the measured verdicts
  live in [`../2026-08-12-m2-accelerator/`](../2026-08-12-m2-accelerator/report.md).
- **Nothing about hybrid fusion.** §4 shows the flag changes the ranking; it is
  not evidence about which ranking is better, and the measured answer is net −6.
- **Nothing about performance.** No timings taken, and cloud-container
  wall-clock is not comparable across surfaces.
