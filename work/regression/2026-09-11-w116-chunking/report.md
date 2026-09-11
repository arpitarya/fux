---
type: Run Report
run: 2026-09-11-w116-chunking
classification: informed
date: 2026-09-11
---

# W-115 moved 304 of 954 documents — and cost 96 of them their title

**W-116's question:** W-115 re-ranked the corpus and nothing was measured. What
actually moved?

**The answer, in two parts, because the two corpora give opposite ones:**

| corpus | result |
|---|---|
| **the hand-graded playground** (10 docs, 50 goldens) | 🔴 **ZERO headroom — the index is BYTE-IDENTICAL between the arms**, and so are all 50 golden rows |
| **fux's own repo** (954 docs) | ✅ **304 records changed (31.9 %)**, +12 560 term entries — **and 96 documents lost a real title to a generic one** |

🔴 **The headline is a regression, and it was found rather than looked for.**
`decoys.jsonl` was titled `decoys.jsonl` and became **`Record 1`**.
`queries.jsonl` became **`Record 1`**. 86 `.jsonl` and 10 `.json` documents, in
a **heavily-weighted field**, and **not one went the other way.** Fixed in the
same change ([ADR-DECODE](../../../docs/adr/0049_decode.md) decision 11a).

## Headroom, computed before the arms were run

[ADR-RS](../../../docs/adr/0043_predictions.md) decision 22.

| corpus | direction | headroom | status |
|---|---|---:|---|
| playground | improvement | **0** | 🔴 **proven** — 0 `#` lines inside fenced blocks in all 10 documents, and none of the formats whose decoders changed (`pdf`/`rtf`/`csv`/`jsonl`/`mbox`) is present |
| playground | regression | **0** | 🔴 proven, same reason |
| fux's repo | improvement | **146 documents** | ✅ proven — 146 documents contain 856 `#` lines inside fenced blocks |
| fux's repo | regression | **146 documents** | ✅ proven, same population |

🔴 **So the playground result is INCONCLUSIVE in both directions, not "no
detected change"** (decision 22d). It is stronger than a null: the two arms
produce a **byte-identical index**, which is the absence of a measurement rather
than the presence of a negative one.

⚠ **The queue row named the playground as this run's corpus.** It was wrong, and
computing headroom first is what caught it — the third time in one day that a
stated instrument turned out not to reach the thing it was pointed at.

## The arms

| arm | engine | index |
|---|---|---|
| **before** | fux at `94231b2` — the commit immediately before W-115 | rebuilt from source |
| **after** | fux at `fdbf58d` (HEAD) | rebuilt from source |
| **after-12** | HEAD with `max_phrases = 12` | **the de-confounded arm** |

🔴 **The third arm exists because the naive comparison is CONFOUNDED**, and
reporting it would have overstated the change:

- `[index] max_phrases` went 12 → 32 in `fa47760`, **after** the before-arm's
  commit, so the before engine hard-codes 12 and reads no key.
- Naive (before-12 vs after-32): **380 of 954 changed**, phrases `+2292`.
- De-confounded (both at 12): **304 of 954 changed**, phrases **`+153`**.
- **So 76 documents and 2 139 heading entries belong to `max_phrases`, not to
  W-115.** Every number below is the de-confounded arm.

**Two confounds were removed, not just one.** Both arms use an **empty**
`.fux/pii.toml`: the committed starter uses a `validate` key the before-arm's
engine refuses, and a differing ruleset changes redaction and therefore the
index. The corpus contains no PII (`fux doctor`: *"redacted NOTHING across
10 document(s)"*), so an empty ruleset costs nothing and removes the variable.

## What W-115 actually did, on the corpus it actually touched

| | before | after | delta |
|---|---:|---:|---:|
| documents | 954 | 954 | 0 |
| **records changed** | — | — | **304 (31.9 %)** |
| per-doc term entries | 348 299 | 360 859 | **+12 560** |
| heading entries | 6 006 | 6 159 | +153 |

**Fields that moved, per document:** `terms` 303 · `flen` 303 · `phrases` 295 ·
`title` **96**.

**The `+12 560` term entries are entirely W-115** — the figure is identical in
the naive and de-confounded arms, so `max_phrases` contributes none of it. That
is the fence fix and the heading skeletons putting real content where it
belongs.

### 🔴 The 96 titles

| extension | documents | direction |
|---|---:|---|
| `.jsonl` | 86 | **all** became `Record N` |
| `.json` | 10 | **all** became `Item N` |
| anything else | 0 | — |

**Cause.** The `## Record N` / `## Item N` per-record heading landed on
2026-09-06 so `refer/_chunk.py` had a boundary to split on — correct, and it
emitted **no document title at all**. `extract.py` takes the **shallowest**
heading, so the first record's heading became the document's title.

⚠ **The shipped decoder was violating the contract its own skill documents.**
`DECODER-SKILL.md` says: *if your format's unit is a slide, message, page or
record, emit them as SIBLINGS at one level under a `# <filename>` title.* The
guidance was right and the built-in ignored it. **That section had itself gone
missing from the shipped template** — repaired earlier the same day, which is
how the sentence was in front of a reader at all.

**Fixed here**, both decoders, with the committed `.fux/decoders/` copies synced
and a test gating the drift. `fux ingest --full` applies it; a plain
`fux ingest` does **not**, because reuse is keyed on the document's content sha
and a decoder change moves no document's bytes.

## Authorship — classification `informed`

| artifact | author | could reach |
|---|---|---|
| the two engine builds | fux's own history, `94231b2` and `fdbf58d` | — |
| the corpora | fux's own repo; `fux-playground` `fece5a3` | — |
| the harness, this report, the fix | Claude Code (Opus), 2026-09-11 | **everything** |

⚠ **`informed`, so no number here may be compared with a blind arm.** The
document-count deltas are not effect estimates — they are a diff of two indexes,
checkable by anyone who rebuilds both. **No golden score is claimed for fux's
own corpus, because it has no goldens.**

## What this run does NOT establish

- **That the change was good.** It measures *what moved*, not *whether ranking
  improved* — fux's own repo has no goldens, and the corpus that has them has
  zero headroom. **W-115 remains unmeasured for quality**, and no doc may say
  otherwise.
- **That the 96 titles were the only regression.** They are the only one visible
  in a record-field diff. A re-ranking of 304 documents was not graded.
- **That `toml`/`yaml`/`ini` are correct.** They emit no filename title either —
  **pre-existing, not part of this regression, and deliberately not changed.**

## Evidence

- [`evidence/fux-corpus-per-document.jsonl`](evidence/fux-corpus-per-document.jsonl)
  — **954 rows, one per document**: whether it changed, which fields moved, and
  its title and term/phrase counts in each arm.
- [`evidence/playground-before.jsonl`](evidence/playground-before.jsonl) ·
  [`evidence/playground-after.jsonl`](evidence/playground-after.jsonl) — the 50
  golden rows per arm. **They are identical**, which is the zero-headroom
  finding in the form anyone can `cmp`.

## Environment

| | |
|---|---|
| before | fux `94231b2` via `PYTHONPATH`, run by the same interpreter |
| after | fux `fdbf58d` |
| corpora | fux's own repo at `fdbf58d` (954 indexed); `fux-playground` `fece5a3`, corpus sha256 `871c492f…` |
| where | `~/my_programs/fux-lab/2026-09-11-w116-chunking` — copies; neither source repo was ingested in place |
| python | 3.14.3 · **os** Darwin arm64 |

## Reproduce

```bash
# the zero-headroom finding on the playground, in one command
cd ~/my_programs/fux-playground
python3 - <<'EOF'
from pathlib import Path
n = 0
for f in sorted(Path("docs").glob("*.md")):
    inside = False
    for line in f.read_text().splitlines():
        if line.lstrip().startswith("```"): inside = not inside; continue
        if inside and line.lstrip().startswith("#"): n += 1
print("'#' lines inside fenced blocks:", n)   # 0
EOF

# the two arms over fux's own corpus
git -C ~/my_programs/fux worktree add --detach /tmp/fux-pre-w115 94231b2
LAB=~/my_programs/fux-lab/2026-09-11-w116-chunking
# ... extract HEAD into $LAB/fux-before and $LAB/fux-after-12, empty .fux/pii.toml
# ... set max_phrases = 12 in BOTH, then:
PYTHONPATH=/tmp/fux-pre-w115/src python -m fux.cli ingest --full    # in fux-before
python -m fux.cli ingest --full                                     # in fux-after-12
```
