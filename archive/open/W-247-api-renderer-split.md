---
type: Handoff
name: W-247
description: "The renderer split SR-API staged and W-148 closed without landing: `cmd_ask`, `cmd_find`, `cmd_answer` render the payload `fux.api` builds, so a payload change has one place to change. Pure refactor, stdout byte-identical. Ratified 2026-10-03 by delegation, NOT built."
item: W-247
filed: 2026-10-03
ball: agent
---

# W-247 — one payload, one place: the CLI renders what `fux.api` builds

**✅ CLOSED 2026-10-04 — built, byte-identical** (Claude Code; Sonnet built, Opus 5.5 reviewed):
- `query.build_ask / build_find / build_answer` compute each payload once; `cmd_ask`, `cmd_lexical`, `cmd_find`, `cmd_answer` render it and `fux.api`'s `Index.ask / find / answer` read the same builders. The `redirect_stdout` capture is gone; the library's signatures, return shapes and key order are unchanged (SR-API d1).
- **Gate:** 537 of 537 CLI invocations byte-identical (stdout, stderr, exit) before and after — 291 on a copy of this repo, 246 on a rebuilt copy of fux-lab rung-01000 (its committed v5 index is refused by this engine; the copy was migrated and re-ingested, the lab untouched) — plus 93 library calls equal. Differential arm 0 of 225. Evidence: [`regression/2026-10-04-api-renderer-split`](../../work/regression/2026-10-04-api-renderer-split/report.md).
- ⚠ Kept, not ruled: `build_answer` still prints the stderr notes the library reached through `cmd_answer` before (floor note, pin, "since you last asked"). Whether the library should print them is a ruling, not a refactor.
- Live successor: [SR-API](../../records/0154_api.md) Consequences.

**Model:** Claude Code, **Sonnet** — a refactor against a byte-equality gate.

**From** backlog B-040. [SR-API](../../records/0154_api.md) Consequences: *"`cmd_ask`
and friends do not call into it yet … a deliberate staging"*, and the staging's
closer was *W-148's third leg*. W-148 closed 2026-09-15 with the split
unlanded, so the record pointed at nothing; the debt is real — today
`api.py` wraps `cmd_answer` through `redirect_stdout`, and `query/__init__.py`'s
`cmd_ask` never imports `api`. Two places build one payload.

## Definition of done

1. `fux.api.ask / find / answer` build the payload; `cmd_ask / cmd_find /
   cmd_answer` are `print(render(api.x(...)))` and nothing else. The
   `redirect_stdout` capture in `api.py` is gone.
2. **Stdout byte-identical** for every verb × every output mode (`--json`, prose,
   `--band`, `--why`, `--receipt`) on this repo's index and on fux-lab
   rung-01000 — captured before and after, filed under `work/regression/`.
3. Node parity unchanged: the differential arm reports 0 discordant.
4. SR-API Consequences rewritten: the staging is over; W-148's name becomes
   history in prose. `sr-hash` restamped.
5. Both suites whole.

## Hazards

- `--json` key order is a documented surface in two verbs and is *about to be*
  ruled (W-251 §3 #4 / [`cli-library-parity`](../../work/compare/cli-library-parity.compare.md)).
  **This item does not change key order**; byte-equality is the gate precisely so
  the two changes stay separable.
- The library surface is frozen (SR-API d1). The refactor moves the CLI onto it;
  it does not move the library.
