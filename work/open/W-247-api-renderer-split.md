---
type: Handoff
name: W-247
description: "The renderer split SR-API staged and W-148 closed without landing: `cmd_ask`, `cmd_find`, `cmd_answer` render the payload `fux.api` builds, so a payload change has one place to change. Pure refactor, stdout byte-identical. Ratified 2026-10-03 by delegation, NOT built."
item: W-247
filed: 2026-10-03
ball: agent
---

# W-247 — one payload, one place: the CLI renders what `fux.api` builds

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
  ruled (W-251 §3 #4 / [`cli-library-parity`](../compare/cli-library-parity.compare.md)).
  **This item does not change key order**; byte-equality is the gate precisely so
  the two changes stay separable.
- The library surface is frozen (SR-API d1). The refactor moves the CLI onto it;
  it does not move the library.
