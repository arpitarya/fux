---
type: Verdict
name: W-205-PART-1-META-FIELDS
verdict: PASS
prediction: W-205 part 1 front-matter identity keys
pre_registration: work/regression/2026-09-21-frontmatter-reachable/PRE-REGISTRATION.md
run: 2026-09-21-frontmatter-reachable
item: W-205
filed: 2026-09-21
---

# VERDICT — W-205 part 1: **PASS**, and the pre-registration's premise was wrong

**6 of 6 reachable, both rungs.** Both no-harm arms hold: **0 broke** on the 43
id-queries and **0 of 60** top-1 changes on the set-1 control. The change ships.

🔴 **And the before-arm falsified this document's own premise before the after-arm
ran.** That correction is the first section, not a footnote, because a PASS
reported without it would overstate the result by a factor of six.

---

## 🔴 1 · The premise was wrong: 5 of the 6 were ALREADY reachable

The pre-registration asserted:

> *"Before: each of the six identifiers, as a bare query, returns the document
> that declares it at NO rank in the top 50 — it is absent from the index."*

**Measured, before-arm, both rungs: 5 of the 6 were already reachable.**

| identifier | before (`rung-01000`) | after | what actually changed |
|---|---|---|---|
| `QCL-IT-ADR-08` | 🔴 **ABSENT** | **1** | **reachability** — the only one |
| `QCL-OPS-DOCK-03` | 2 | **1** | rank |
| `QCL-QA-MAP-01` | 2 | **1** | rank |
| `QCL-CS-MTX-02` | 3 | **1** | rank |
| `QCL-CS-MTX-03` | 3 | **1** | rank |
| `QCL-QA-SOP-17` | 3 (live) / 13 (archived) | 5 / **4** | 🔴 **see §4** |

**Why the premise was wrong, and it is the same mechanism part 2 measured.** The
analyzer *splits*: `QCL-OPS-DOCK-03` becomes `qcl`, `op`, `dock`, `03`, and those
parts occur in the document's body, headings and **path** for other reasons. The
whole identifier was absent; **enough of its pieces were not.** Only
`QCL-IT-ADR-08` failed, because `qcl` + `adr` + `08` do not co-occur in the
document that declares it — and its `IT` segment is deleted as a stopword.

⚠ **This is MY error, not the record's.** [SR-INGEST](../../../records/0106_ingest.md)
decision 23 says **`QCL-IT-ADR-08` was absent from the top 50 at every rung** —
one identifier, measured. The pre-registration generalised *"7 declared keys are
front-matter-only"* into *"6 identifiers are absent"* and **froze that without
measuring it.**

🔴 **Twice in one session, and that makes it a pattern rather than a slip.** W-205
part 2 was held, and set 3 was authored, on the premise that sibling identifiers
fail at `hit@1` — **they did not**. Part 1 was pre-registered on the premise that
six identifiers were unreachable — **five were reachable.** In both cases the
defect was *described* accurately by a record and **generalised** into a
population nobody probed. **The cheap fix is one probe run before the freeze**,
and it is put to Arpit in §6.

## 2 · The endpoint, as frozen

**PASS: all 6 of 6 reachable at `rank ≤ 50`, on both rungs.** The rule had no
INCONCLUSIVE — *absent* and *present* are not a matter of degree — and the arm
cleared it.

⚠ **Reachability is not ranking, and this verdict keeps that line.** That five of
six went to **rank 1** is reported in §1 and is **not** what passed; the
pre-registration set no bar on rank, deliberately, and inventing one now would be
a threshold written to be cleared.

## 3 · The two no-harm arms — both hold, and one moved the other way

**Arm 1 — the 43 id-queries, `rung-01000`.** The bar was *a net of ≥ 6 **against**
is a FAIL*.

| endpoint | before | after | fixed | broke | net |
|---|---:|---:|---:|---:|---:|
| bare identifier | 30/43 | 35/43 | 5 | **0** | **+5** |
| in a question | 33/43 | 39/43 | 6 | **0** | **+6** |

**0 broke on either form.** The arm holds with room to spare.

🔴 **The question form's +6 sits exactly at decision 19's floor at 6 discordant —
and this verdict does NOT claim it.** That arm was pre-registered to detect
**harm**, in one direction. A net that arrives in the *other* direction is not
the endpoint it was frozen for, and reporting it as an improvement would be
using an arm for a question it was not registered to answer — the exact move
[SR-RS](../../../records/0133_predictions.md) decision 10b exists to stop.
**If it is worth claiming, it is worth its own pre-registration**, and it would
be a cheap one.

**Arm 2 — 60 set-1 questions, `rung-01000`: 0 of 60 top-1 changes.** The concern
was that new `title` terms move `avg_wlen` for every document with front-matter
and reorder ordinary prose queries. **They did not move one.**

**Condition on the corpus:** `ref` 61, `supersedes` 101, 1 000 documents —
**identical in both arms**.

## 🔴 4 · FOUND: the archived revision now outranks the live document

`QCL-QA-SOP-17` is declared by **two** documents — the live SOP and its archived
revision 2. At `rung-01000`:

| | live `01-sop-…md` | archived `a01-…-rev2.md` |
|---|---:|---:|
| before | **3** | 13 |
| after | 5 | 🔴 **4** |

**The archived document gained nine places and passed the live one.** Both now
carry `QCL-QA-SOP-17` at `title` weight, and the archived file is **shorter**, so
BM25F's length normalisation favours it — at `b = 0.15`, but favours it.

⚠ **This is not a regression against anything this run pre-registered**, and it
is not caught by either no-harm arm: the id-queries target `QCL-QA-SOP-17`'s live
document only through a family the probe counts as a hit either way, and the
control is set-1 prose.

🔴 **It is the supersession-inversion class, seen before.** The
[2026-09-12 ladder run](../2026-09-12-golden-ladder/report.md) measured a declared
supersession landing *"at a coin flip"* — the retired half above its successor in
51–58 % of co-ranked pairs — and W-143 later ruled that **no single global prior
fixes it**. Part 1 did not create that class; **it gave it a new way to fire**,
because a shared `doc_id` is now a strong term on both halves of a superseded
pair.

**Not escalated into a change here.** `superseded_weight` was removed by W-152
after being measured, and re-opening it needs its own pre-registration and
Arpit's ruling. **Recorded so the next reader of a `doc_id` ranking meets it
before a consumer does.**

## 5 · What this run may not claim

- **That six identifiers became findable.** **One** did; five moved up.
- **That ranking improved.** It is not the endpoint, and the +6 is an unregistered
  direction.
- **That an identifier is whole.** `QCL-IT-ADR-08` reaches rank 1 while still
  losing its `IT` to the stopword list — SR-INGEST decision 23d, confirmed rather
  than discovered, and part 2 did not clear its bar.
- **Anything about a person key.** The default excludes them; none was bound.

## 🔴 6 · To Arpit — one rule, because it has now cost two measurements

**SR-RS decision 23c says *where the input is COUNTABLE, count it — before the
run, with a check that can fail*, and `ref_edge_census.py` is that check for
links.** There is no equivalent for *does this input actually exercise the
defect*, and this session hit the gap twice:

- **part 2** — set 3 was authored to supply a failing shape that **did not fail**;
- **part 1** — six identifiers were pre-registered as unreachable and **five were
  reachable**.

**The candidate rule:** *a data-shaped endpoint measures the defect on a handful
of the proposed population before the documents are authored or the threshold is
frozen.* One probe run, minutes.

🔴 **It is a rule about measurement, so it is SR-RS's and a session does not add
one.** Put here rather than taken.

## 7 · Classification

**`informed`.** The six identifiers were found by the measurer by grep over
`work/golden/seed/`, and this session rebuilt the corpus and wrote the change.
🔴 **No golden answer was used, needed or reachable** — the endpoint is *does this
document come back at all*, answerable from a ranked list alone.
