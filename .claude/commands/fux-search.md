---
description: Search this repo's committed fux index and report ranked documents with confidence.
argument-hint: <question>
allowed-tools: Bash(fux:*), Bash(uv run fux:*), Read
---

Search the committed fux index for: **$ARGUMENTS**

1. Resolve the command once — `fux` → `uv run fux` → `./.venv/bin/fux` → `python -m fux`.
2. Run `fux ask "$ARGUMENTS" --json --band --top 5`.
3. Read `confidence.band` and branch on it, never on the prose:
   - `none` (= `answerable: false`, the only band that refuses) → **abstain.** Say the index has nothing and name `confidence.missing`.
   - `partial` → answer, and name every term in `confidence.missing`.
   - `weak` → **a signal, not a refusal**: the top two are near-tied, so read them and report candidates rather than a conclusion.
   - `grounded` → answer, citing each document's `loc`.
4. If the band is `none` or `partial`, the cause is a **vocabulary gap**. Retry
   **once** with `--expand` and a passage **you write** — 2–3 sentences
   answering the question in the words the document would use, never a keyword
   list. Fux cannot write it: no fux path may call a model.
5. Stop after about three reformulations. An honest *"the index has nothing on
   this"* beats a guessed citation.

For exact line ranges, use `/fux-answer` instead.
