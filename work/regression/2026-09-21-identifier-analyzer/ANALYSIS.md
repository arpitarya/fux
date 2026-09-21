---
type: Analysis
run: 2026-09-21-identifier-analyzer
description: "Why the arm produced +4 and not +6: the premise that the failing shape fails at hit@1 was never measured before the documents were written for it. Plus the dictionary cost, the two behaviour changes beyond identifiers, and the record that asserts a property the code does not have."
filed: 2026-09-21
---

# ANALYSIS — a data-shaped unblock that unblocked the wrong thing

## 1 · 🔴 The premise was never measured, and that is the diagnosis

**Diagnosis.** W-205 part 2 was held for one stated reason: *"the headroom is
3–4 of 33 on every rung against a floor of 6 — no arm on this corpus can return
a verdict, whatever is built."* The fix was to add identifiers **of the failing
shape** — `RF-118 / RF-119 / RF-120`, `PROJ-123 / PROJ-124` — so that the arm
would have room.

**What was never checked is whether that shape actually fails.** It does not.
All eight sibling identifiers ranked their own document **first, in both arms, at
every rung**. Splitting is symmetric, so `RF-119` as a query produces the same
`rf` + `119` the document wrote — and **`119` is a rare term on its own**. The
prefix collision is real and it costs nothing, because the number is already
discriminating.

**Change, specific.** [SR-RS](../../../records/0133_predictions.md) decision 23c
says *"where the input is COUNTABLE, count it — before the run, with a check that
can fail"*, and `ref_edge_census.py` is that check for links. **There is no
equivalent for *does this input actually exercise the defect*.** Counting that
`RF-118` is present is not the same as measuring that it ranks badly, and the
first is what was done.

```bash
.venv/bin/python tools/quality-controls/identifier_probe.py \
    --queries work/regression/2026-09-21-identifier-analyzer/evidence/id-queries.jsonl \
    --rung rung-10000
```

**Unresolved, and put to Arpit rather than fixed here:** whether decision 23
should gain a clause — *a data-shaped unblock measures the defect on a handful of
the proposed shape before the documents are authored*. It would have cost one
probe run and saved a seed authoring pass, a ladder rebuild and 5 984 re-run
calls. **It is a rule about measurement, so it is SR-RS's, and a session does not
add a rule to that record on its own.**

⚠ **Set 3 is not the loss here.** It bought the ladder's 61 `ref` edges and
phase A's replication of the authorship gap. **What it did not buy is what it was
commissioned for.**

## 2 · Where the four fixes actually came from

**All four are `pre-set-3` identifiers**, and they are instructive:

| identifier | why `v3` fixed it |
|---|---|
| `RF-221` | `rf` + `221`, competing with `RF-203` and `RF-118` in a corpus where `221` also appears as a bare number |
| `GHY-7` | **single-digit tail** — `ghy` + `7`, and `7` is everywhere. The whole form `ghy-7` is the only discriminating token |
| `SANDHU-EXC` | two common-ish words; `sandhu-exc` is unique |
| `WIKI-NGP-DOCK-12` | four segments, each shared with other identifiers |

🔴 **The pattern is the opposite of the one the item predicted.** `v3` helps
where the *parts* are individually common — a short numeric tail, or segments
shared across a family — and does nothing where the number is already rare.
`GHY-7` is the archetype and `RF-119` is the counter-example, **and set 3 was
built entirely out of counter-examples.**

**That is the specification a future corpus needs:** identifiers whose segments
are individually common. `PROJ-1` … `PROJ-9`, or ids differing only by a letter.

## 3 · The dictionary doubles; the postings do not

| | `rung-10000` before | after | ratio |
|---|---:|---:|---:|
| accelerator terms | 14 033 | 29 489 | **×2.101** |
| postings | 849 935 | 896 233 | ×1.054 |
| committed index | 24 876 KB | 26 008 KB | ×1.046 |

**Diagnosis:** each whole form is a term appearing in one or two documents, so
the dictionary grows and the posting lists barely do. ⚠ **And most of it is not
identifiers** — English prose is full of hyphenated compounds, and `one-off`,
`cold-chain` and `night-shift` each become a term. **The v2 measurement of
`camelCase` splitting (×1.03 on a prose corpus) is not a guide to this**, which
the pre-registration said before the number existed.

**Not escalated into a bar.** No cost threshold was pre-registered, deliberately,
so this rules nothing. It is recorded because **a ×2.1 dictionary for a net of +4
is a trade someone should see rather than infer.**

## 4 · 🔴 SR-RANKING decision 9 asserts a property the code does not have

> *"Whole **and** parts are emitted, which keeps an exact-identifier query
> precise while `user name` finds the identifier at all."*

**That is true for `snake_case` and false for `-`, `.` and `/`.** Under `v2`,
`RF-118` has no whole form anywhere. The record and the code disagreed **while
both looked correct**, which is exactly [SR-LAW-0](../../../records/0002_LAW-0-authority.md)'s
restatement test.

**Change, specific, and it does NOT depend on the verdict:** the sentence is
wrong today and stays wrong if family (a) is dropped. 🔴 **It is not amended in
this change**, because the honest amendment depends on what Arpit decides — if
(a) ships, the sentence becomes true; if it does not, the sentence needs a
carve-out naming the separator asymmetry as a known defect. **Filed as part of
the verdict's question 1–3 rather than pre-empted.**

## 5 · Two behaviour changes beyond identifiers, both pinned

Neither was in the item's framing, and both are now tests rather than surprises:

1. **Decimals are one token** — `0.75` was `0` + `75`.
2. 🔴 **A single-character segment `v2` kept is dropped** — `COLD-1` loses its
   bare `1`. **8 of 33 seed identifiers** are affected.

⚠ **The second is a token that existed and does not any more**, and on this
corpus it is invisible: `GHY-7` — which loses its `7` — is one of the four rows
`v3` **fixed**. The whole form more than pays for the lost digit here. **On a
corpus where a bare number is the query, it would not**, and nothing in this run
measures that.

## 6 · The instrument behaved, and one guard had stopped guarding

- **`compare_arms.py` prints decision 19's rule and does not apply it**
  (decision 10b) — the floor lives in the frozen pre-registration.
- **Headroom is printed before any net**, per decision 22, so the ceiling is
  visible before the number.
- 🔴 **The Node fixture's `survives whole` assertion had gone vacuous** under
  `v3` — `out.length === 1` can never hold once the whole form arrives beside its
  parts, so the filter was always empty and the test passed while checking
  nothing. **Caught because the Python twin moved and the Node one did not**,
  which is the differential law earning its keep.
