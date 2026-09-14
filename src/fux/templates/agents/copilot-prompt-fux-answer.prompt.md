---
name: fux-answer
description: Get a cited answer with exact line ranges from the fux index, and verify it.
argument-hint: <question>
tools: ['search', 'runCommands']
---

Answer from the committed fux index, with citations: **$ARGUMENTS**

1. Run `fux answer "$ARGUMENTS" --json --band --receipt`.
2. **Quote the cited spans. Do not paraphrase them into a claim they do not make.**
3. Report each citation's freshness verdict — `current`, `stale`, `as-ingested`,
   `cached`, `unverified`. A `stale` citation is still evidence, but say so.
4. If `answerable` is false, **abstain and say why**. A confident wrong answer
   is the expensive failure this verb exists to avoid.
5. `--expand "<a passage you write>"` applies here exactly as on `ask` —
   expanding a question is not asking a second one.

To check an answer someone already has, run `fux verify` on its receipt.
