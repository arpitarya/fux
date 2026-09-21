---
type: Report
run: 2026-09-21-frontmatter-reachable
item: W-205
classification: informed
description: "W-205 part 1 — front-matter identity keys reach the index. PASS: 6 of 6 reachable, 0 broke on the 43 id-queries, 0 of 60 top-1 changes on the set-1 control. The before-arm falsified the pre-registration's own premise: 5 of the 6 were already reachable, and the change fixed exactly one."
filed: 2026-09-21
---

# REPORT — a `doc_id` you can read is now one you can search

**Verdict: [PASS](VERDICT.md)**, with the premise correction the before-arm
forced. The arithmetic and the ruling are there; this is what was run.

**Pre-registration:** [frozen at `51be0ff1`](PRE-REGISTRATION.md), committed with
the build and **before any arm ran** — `git log` shows the pre-registration and
the code in one commit, and the first evidence file written afterwards.

## The arms

| | engine | what differs |
|---|---|---|
| **before** | `88feb927` in an isolated worktree | — |
| **after** | the working tree at `51be0ff1` | `parse.meta_fields()`, `Decoder.meta_fields`, `[meta]`, the values reaching their field |

Each arm on **its own `arm_corpus.py` copy**, ingested end to end by its own
engine, on `rung-00100` and `rung-01000`.

## The endpoint

**6 of 6 reachable, both rungs** — up from **5 of 6**.

| identifier | before | after |
|---|---:|---:|
| `QCL-IT-ADR-08` | 🔴 absent | **1** |
| `QCL-OPS-DOCK-03` | 2 | **1** |
| `QCL-QA-MAP-01` | 2 | **1** |
| `QCL-CS-MTX-02` | 3 | **1** |
| `QCL-CS-MTX-03` | 3 | **1** |
| `QCL-QA-SOP-17` | 3 live / 13 archived | 5 live / **4 archived** |

🔴 **Five of the six were already reachable, and the verdict's §1 is about why.**
The analyzer splits, so `qcl` + `op` + `dock` + `03` matched from body, headings
and path even though the whole identifier appeared nowhere. Only
`QCL-IT-ADR-08` genuinely failed.

## Headroom

🔴 **The endpoint is absolute, not paired, so decision 22's paired headroom does
not apply to it** — *absent* and *present* have no degrees, and the
pre-registration chose that shape because six identifiers is AT decision 19's
floor and a paired test would have needed a total sweep.

**Headroom IS disclosed for the paired no-harm arm**, in decision 22b's terms —
improvement headroom is the queries not right in both arms, regression headroom
the queries not wrong in both:

| endpoint, `rung-01000` | before | after | improvement headroom | regression headroom | net |
|---|---:|---:|---:|---:|---:|
| bare identifier | 30/43 | 35/43 | 13 | 30 | **+5** |
| in a question | 33/43 | 39/43 | 10 | 33 | **+6** |

**0 broke on either form.**

## The two no-harm arms

1. **43 id-queries, `rung-01000`** — bar: a net of ≥ 6 **against** is a FAIL.
   **0 broke.** ⚠ The question form's **+6** arrives in the direction the arm was
   **not** registered to test, and this run does not claim it; see the verdict.
2. **60 set-1 questions, `rung-01000`** — **0 of 60 top-1 changes.** The worry was
   that new `title` terms move `avg_wlen` for every document with front-matter.
   Nothing moved.
3. **Corpus unchanged:** `ref` 61, `supersedes` 101, 1 000 documents, both arms.

## 🔴 What the run found that nobody registered

**The archived revision now outranks the live document** for
`QCL-QA-SOP-17`, which two documents declare: 3 / 13 before, **5 / 4** after.
Both carry the id at `title` weight and the archived file is shorter. It is the
supersession-inversion class the 2026-09-12 ladder run measured, given a new way
to fire. **Recorded, not fixed** — `superseded_weight` was removed on
measurement by W-152 and re-opening it is Arpit's.

## Reproduce

```bash
work/regression/2026-09-21-frontmatter-reachable/evidence/run-arms.sh
```

Four `arm_corpus.py` builds, four `reach.py` probes, two `identifier_probe.py`
runs and two `control_60.py` runs. Every JSON in `evidence/` is one of their
outputs.

## Authorship

| artifact | author | blind? |
|---|---|---|
| the six identifiers and their targets | **Claude Code, this session**, by grep over `seed/` | no |
| the 43 id-queries | Claude (2026-09-18 and this session) | no |
| the 60-question control | set 1 — Codex-authored questions, sampled by rule | the questions are Codex's; the sample is the measurer's |
| the change, the pre-registration, this run | Claude Code | — |

**`classification: informed`.** 🔴 **No golden answer was used, needed or
reachable** — the endpoint asks whether a document comes back at all, which a
ranked list answers.
