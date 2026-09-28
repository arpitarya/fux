---
type: Report
run: 2026-09-28-families-lens-ladder
item: W-228
classification: surface capture
description: "W-228 DoD 11's first half: the `families` inspect lens run on the golden `rung-seed` (68) and `rung-01000` (1 000). At a2ce3fc6 the seed has 8 families and 0 misfits, so it carries no planted misfit. rung-01000 has 32 families and 16 misfits, and 14 of those are a document's own title heading. After the same-session lens change (title heading out, a shared heading required), rung-01000 has 23 families and 1 misfit. The misfit floor stays PROVISIONAL."
filed: 2026-09-28
---

# REPORT — the `families` lens on the golden ladder

**A surface capture.** No arms, no questions, no threshold, no verdict. It
records what `fux inspect --json` prints under `families` on two frozen golden
rungs, so that W-228 DoD 11 has a filed rung. **It does not move `misfit_floor`
off PROVISIONAL.** The reason is below.

## Authorship

One Claude Code session (Opus 5.5) did the whole run. Under `work/golden/` it
read `seed/` (as a directory listing), `ladder/rung-seed.index`,
`ladder/rung-01000.index`, `ladder/rung-seed.coverage`, and `README.md`. It did
not open, list, grep, hash or stat `questions/`, and it touched neither spelling
of the sealed-key directory ([L11](../../../records/0012_LAW-11-sealed-answer-key.md)).
The lens reads headings, front-matter keys and lengths. No question and no score
reaches it.

| artifact | author | could reach |
|---|---|---|
| the lens (`src/fux/inspect/lenses.py`, SR-INSPECT d24) | the W-228 build session, 2026-09-28 | none |
| [`evidence/inspect.toml`](evidence/inspect.toml) | the `fux setup` template, unmodified | none |
| [`evidence/reproduce.sh`](evidence/reproduce.sh), this report, the analysis | this session | none |

## Setup

- **Engine:** `fux 3.0.0-alpha.5`, a clean worktree at `a2ce3fc6`. The main tree
  held another session's uncommitted W-225 change, so it was not used.
- **Corpora:** `fux-lab/corpora/golden/rung-seed` and `rung-01000`, the
  generation-3 ladder (the [2026-09-27 rebuild](../2026-09-27-ladder-gen3-rebuild/report.md)).
  Each was **copied to scratch**. The kept rungs were not modified.
- **Two config gaps on the copies, both filled by the engine's own command.** The
  rungs predate `.fux/inspect.toml` and several keys added since `80495b44`. The
  template's `inspect.toml` was dropped in, and `fux doctor --fix` wrote the rest.
  Nothing was re-ingested; `index_root_sha256` is the rung's own.
- **Thresholds (template defaults):** `skeleton_jaccard = 0.60`,
  `core_share = 0.80`, `misfit_floor = 0.20` (provisional),
  `length_edges = [200, 1000, 5000]`.

## Output

| | `rung-seed` | `rung-01000` |
|---|---:|---:|
| documents | 68 | 1 000 |
| families (≥ 2 members) | 8 | 32 |
| documents in a family | 22 (**32.4 %**) | 911 (**91.1 %**) |
| singletons | 44 | 55 |
| no headings | 2 | 34 |
| misfits | **0** | **16** |
| `misfit_share` | 0.0 % | **1.8 %** |
| flagged (floor 20 %, provisional) | no | no |
| exact heading-set families (the older signature, for comparison) | — | 94, covering 672 |
| `inspect --json` wall time | — | 0.57–0.62 s |

**Determinism:** two runs per rung gave byte-equal `families` sections, and a
third from [`reproduce.sh`](evidence/reproduce.sh) matched the filed evidence on
both rungs.

### The seed's eight families

| members | family (first headings) |
|---:|---|
| 4 | `23`–`26` mapping studies TMS-41…44 |
| 3 | `27`–`29` lane qualifications LQ-51…53 |
| 3 | `16`–`18` reefer asset files RF-118…120 |
| 3 | `40-procedure-dry-ice-handling` + cards `56`, `57` |
| 3 | `43-procedure-ammonia-leak-response` + cards `58`, `59` |
| 2 | `14`, `15` customer notification matrices 2025 / 2026 |
| 2 | `46-procedure-seal-control` + card `60` |
| 2 | `51-reference-gel-pack-conditioning` + sheet `62` |

### rung-01000's sixteen misfits

| missing | count |
|---|---:|
| only the family's **title heading** (`Temperature Excursion Response SOP` ×13, `Release notes` ×1) | **14** |
| the title heading **and** `4. Immediate containment` (`seed/archive/a01-…-rev2.md`) | 1 |
| a section only: `Raipur DC` (`ext/sibling/00673-dockwiki.html`) | 1 |

Full lists: [`families-rung-seed.json`](evidence/families-rung-seed.json),
[`families-rung-01000.json`](evidence/families-rung-01000.json), and the prose
section as printed: [`prose-rung-01000-section-4b.md`](evidence/prose-rung-01000-section-4b.md).

## What this run does not do

- **It does not carry DoD 11's input.** The seed has **no planted misfit**, and
  rung-01000's misfits are the generator's accidents, with no known answer. A
  floor tuned on them would be tuned against noise. [ANALYSIS](ANALYSIS.md) §2.
- **It changes no threshold.** It did change the lens, in the same session. See
  §After the lens change below.

## After the lens change

The same session applied [ANALYSIS](ANALYSIS.md) §3 in `lenses.py`:
- a leading heading equal to the document's title is left out of its shape;
- only a shared heading makes two documents candidates for one family.

It then re-ran both rungs twice, and the output was byte-equal.

| | `rung-seed` before → after | `rung-01000` before → after |
|---|---:|---:|
| families | 8 → **8** | 32 → **23** |
| documents in a family | 22 → 22 | 911 → 913 |
| singletons | 44 → 42 | 55 → 50 |
| no headings | 2 → **4** | 34 → 37 |
| misfits | 0 → 0 | 16 → **1** |

- **rung-01000's one misfit left** is `seed/archive/a01-…-rev2.md`, which lacks
  `4. Immediate containment`. It is an archived older revision, and the
  section is really missing.
- **The four dock-wiki families are now one, of 45.** The two notification
  families (45 + 13) are now one, of 58.
- **The seed's eight families have the same members as before**, now
  named by their sections instead of the first member's title.
- ⚠ **"No headings" now includes title-only documents.** Two seeds,
  `06-re-fw-telematics-cutover.eml` and `33-cold-chain-glossary.md`, have no
  heading besides their title, and rung-01000 adds one ext document. They are
  listed under *no headings*: they have no section skeleton to compare, but they
  do have a heading.

Evidence: [`families-rung-seed-after.json`](evidence/families-rung-seed-after.json),
[`families-rung-01000-after.json`](evidence/families-rung-01000-after.json).

## Reproduce

```bash
git worktree add --detach /tmp/fux-wt a2ce3fc6
FUX_PY=$PWD/.venv/bin/python \
  bash work/regression/2026-09-28-families-lens-ladder/evidence/reproduce.sh /tmp/fux-wt /tmp/fux-families
# rung-seed: reproduces
# rung-01000: reproduces
# with the lens change applied to the worktree, add `-after` as a third argument
```
