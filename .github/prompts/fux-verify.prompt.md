---
name: fux-verify
description: Replay a fux receipt and report whether the answer still reproduces.
argument-hint: [path to receipt json]
tools: ['search', 'runCommands']
---

Verify a previously produced fux answer: **$ARGUMENTS**

1. Run `fux verify` against the receipt.
2. Report the verdict **in its own words**: `reproduced`, `drifted`, or
   `unverifiable`. Do not soften `drifted` into "mostly the same".
3. On `drifted`, say **what** moved — the document's bytes, or the index — and
   name the document. A receipt produced with `--expand` replays that exact
   expansion; without it you are comparing two different queries.
4. `unverifiable` is not a failure of the answer. It means the source can no
   longer be reached, and that is a fact about the world, not the receipt.
