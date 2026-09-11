---
type: Analysis
name: ANALYSIS-W116-CHUNKING
title: "Analysis — a defect fix that shipped a defect, and the reuse key that hid it"
description: "Why the title regression survived two weeks, the three improvements that follow, and what stays unmeasured."
status: complete
date: 2026-09-11
timestamp: 2026-09-11T00:00:00Z
---

# Analysis — the measurement found a regression the fix introduced

**The diagnosis:** W-115 landed as a **defect fix**, on Arpit's 2026-09-06
ruling that a `# comment` in a bash block was never a heading. The ruling was
right. **The change also introduced a second defect in the same area** — and a
defect fix that skips measurement has no step at which that gets noticed.

**This is not an argument for gating defect fixes on measurements.** It is the
argument for the item that says *measure it afterwards*, which is what W-116 was
and why leaving it open for five days was expensive: the regression shipped in
`v2.0.0-alpha.7` and sat in every index built from it.

## Why the title regression survived

Three independent things each of which would have caught it:

1. **`DECODER-SKILL.md` documented the correct behaviour** — *emit records as
   siblings under a `# <filename>` title*. ⚠ **And that section was missing from
   the shipped template**, added to the committed rendering and never to its
   source (repaired the same day). **So the guidance existed and could not be
   read by anyone who installed fux.**
2. **`fux doctor` has a `decoder bindings` row** — it checks a binding resolves,
   not that what comes out has a title.
3. **A test asserting "decoding succeeded" passes on it.** The skill's own
   verification section names this exact trap — *four defects in the shipped
   decoders produced plausible output rather than an error* — and it happened a
   fifth time.

**The common factor: nothing compares the output to what the document is.** A
title of `Record 1` is *structurally* valid Markdown, decodes without error, and
indexes cleanly.

## Specific improvements

### 1. 🔴 A decoder change must invalidate carried extraction — it does not

**The sharpest finding here, and it is not about titles.** Reuse is keyed on the
document's **content sha**. A decoder fix moves no document's bytes, so
`fux ingest` **carries the old records forward** and the fix reaches nothing.

**Repro** — this bit during this very session:

```bash
cd ~/my_programs/fux   # after fixing jsonl.py
python -m fux.cli ingest        # titles still "Record 1"
python -m fux.cli ingest --full # titles repaired
```

**`pii.toml` and `[index]` each closed this hole with a digest**
(`_pii_ruleset_moved`, `_extract_config_digest`) precisely because *"a rule
change alters what should be indexed for documents whose bytes did not
change"* — **which is a decoder change, word for word.** A decoder digest is
the same shape as the two that exist.

⚠ **Filed, not built.** It belongs to [ADR-INGEST](../../../docs/adr/0106_ingest.md)'s
reuse key, its blast radius is every ingest in every repo, and inventing it
inside a decoder bugfix is the wrong place to decide it. **Until it exists, a
decoder change ships with the instruction `--full` or it does not ship.**

### 2. The third instance of *a fix that does not reach the repo it was fixed in*

Today, in one session:

| what | reached the repo? |
|---|---|
| the chunking section added to `.claude/skills/fux-decoder/SKILL.md` | **not the template** → no user got it |
| the command-resolution ladder added to `fux.agent.md`'s template | **not this repo's copy** |
| the `jsonl`/`json` fix in `src/fux/decode/` | **not `.fux/decoders/`**, which is what runs |

**All three are the same mechanism**: write-if-missing, correct for a consumer,
wrong for fux's own repository — which is the *source* of what it ships.
**Both are now gated**
(`test_this_repos_own_agent_files_still_match_the_templates_that_ship`,
`test_this_repos_own_decoders_still_match_the_package_modules`). ⚠ Neither gate
says anything about a consumer's copies; a consumer's divergence is the feature.

### 3. Compute headroom before naming a corpus, not after

The queue row named the playground as this run's corpus. **It has zero
headroom** — no `#` inside any fence, none of the changed formats present — and
the arms produce a **byte-identical index**.

**Repro:** the ten-line script in the report's *Reproduce* block, which needs no
engine at all.

**This is the third stated instrument in one day that did not reach its
subject** (the other two: `superseded_weight` on a corpus with no `supersedes:`
key, and `archived_weight` on one with no `archived=true`). **The pattern is
that the queue records which corpus to use and never which population it
contains.** A row naming a corpus should name the population and its size.

## What stays unmeasured, and must be described that way

- 🔴 **W-115 is still unmeasured FOR QUALITY.** This run measures *what moved* —
  304 documents, +12 560 term entries — and **not whether ranking got better**.
  The corpus with goldens cannot see the change; the corpus that can has no
  goldens. **No document may cite W-115 as measured**, and the ADRs that record
  it as an unmeasured defect fix stay exactly as they are.
- **The 304 re-ranked documents were not graded.** The 96 titles are the only
  regression a record-field diff can surface. A ranking regression that moved no
  field is invisible to this method.
- **`toml`, `yaml` and `ini` emit no filename title either.** Pre-existing, not
  W-115's, **deliberately unchanged**: widening a measured defect fix into an
  unmeasured improvement is how a repair becomes a ranking change nobody
  measured. **It is now a decision someone takes, rather than a thing someone
  discovers.**
- **Whether `max_phrases = 32` was a good move is untouched.** This run only
  separated it out as a confound; 76 documents and 2 139 heading entries are
  attributable to it and nothing here judges them.
