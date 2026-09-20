---
type: Report
name: correction-generalisation-informed-iii
description: "Arm (iii) shape, run informed: 11 corrections from real fux ask failures on a 1006-document github/docs corpus, 55 paraphrases authored by a sealed session that saw only the questions. 0 discordant on the top-3 endpoint; the correction's OWN question rose 11/11."
classification: informed
item: W-175
timestamp: 2026-09-18T00:00:00Z
---

# Arm (iii), informed — a correction fixes its own phrasing and almost nothing else

🔴 **This is NOT the blind arm (iii)** the
[pre-registration](../2026-09-15-correction-generalisation/PRE-REGISTRATION.md)
describes, and it does not rule keep/remove. Arpit directed a Claude session to
run it on 2026-09-18 after declining to commission Codex. It is filed as what it
is.

## Why `informed`

[SR-RS](../../../records/0133_predictions.md) decision 11 has two conditions and
this run meets one.

- ✅ **Information.** The paraphrases were authored by a **fresh session that used
  zero tools** and was shown the twelve question strings and nothing else — no
  corpus, no document, no path, no rank, no correction, no example paraphrase, no
  difficulty steer. That is d11's access condition met literally, and it is the
  same mitigation [`BLIND-AUTHOR-BRIEF.md`](../../../tools/quality-controls/BLIND-AUTHOR-BRIEF.md)
  uses: publish the brief so the steer can be audited. The brief is §B of
  [the Codex prompt](../2026-09-15-correction-generalisation/prompt-codex-paraphrases.md),
  verbatim, plus the twelve questions.
- 🔴 **Authorship.** The failures and the paraphrases are both Claude's, and so is
  the runner. Same model family, twice. **Every number here is `informed`
  permanently.**

## The corpus — ungraded, and not fux's own tree

`github/docs` @ `refs/heads/main`, fetched 2026-09-18, `content/` restricted to
nine areas (actions, codespaces, repositories, issues, pull-requests,
authentication, billing, pages, organizations). **1006 documents**, 7840 terms,
132 628 postings. Built and indexed in VM scratch **outside this repo**; the repo
was never ingested, written to by the harness, or left dirty by the run.

⚠ This differs from the [2026-09-18 informed run](../2026-09-18-correction-generalisation-informed/report.md),
which used fux's own `records/` + `docs/`. **Different corpus, different
questions, different paraphrases, same direction** — which is the only thing
that makes a second informed run worth filing.

## How the twelve were found

39 plausible questions authored against a sha-sorted deterministic sample of the
corpus; `fux ask --top 20` run on each; **27 missed top-3**. Twelve were taken
**in sample order** after dropping four whose `should_win` was ambiguous (a
sibling document was arguably the better answer). **Selection never looked at how
far a question missed.** The other 15 misses are unused and are not in evidence.

## The harness was patched — and the patch changed the result

Run against a **scratch copy** of
[`correction_generalisation.py`](../../../tools/quality-controls/correction_generalisation.py)
with W-175's three recorded defects fixed. **The repo's copy is untouched and
still carries all three.**

1. `reingest()`'s return value discarded (`run.py:132`) → **hard stop**.
2. unfiled corrections still emit rows → **excluded from `usable`**.
3. a row with no target skipped, run still exits 0 → **hard stop**.

🔴 **Defect 2 fired on this run.** `fux correct` **refused c-01** — *"that reads
as a negative correction — stop serving this rather than a question somebody
would type"* — because the question was phrased *"…instead of downloading a
csv"*. On the unpatched harness c-01 would have contributed **5 rows with
`before == after` guaranteed**, taking n from 55 to 60 and biasing the paired
count toward the null. **N is therefore 11, not 12**, reported at the N that
actually ran, per the pre-registration.

## The endpoint — top-3 retrieval of the corrected document, before vs after

| arm | n | before | after | better | worse | discordant | net |
|---|---|---|---|---|---|---|---|
| iii (informed) | 55 | 8 | 8 | 0 | 0 | **0** | **+0** |

**`verdict.py`, not a hand comparison:**

```
b=0 c=0 discordant=0 net=0 p=1.0000 (no net difference can clear alpha at this count, alpha=0.05) -> INCONCLUSIVE
```

**Headroom, measured in the BASELINE arm (SR-RS 22b/22f): improvement 47/55,
regression 8/55 — both non-zero.** 22d's INCONCLUSIVE guard is silent. **This is
not a ceiling effect**: 47 of 55 paraphrases had room to enter the top 3 and none
did.

## The diagnostic that says what actually happened

Not the pre-registered endpoint. Rank@20, pristine tree vs corrected tree.

| | n | rose | fell | unchanged |
|---|---|---|---|---|
| the correction's **own** question | 11 | **11** | 0 | 0 |
| the **paraphrases** | 55 | **1** | 0 | 54 |

- **Own question reached top-3 after the correction: 7 of 11.**
- The single paraphrase that moved went **13 → 12** — it did not cross the
  endpoint, and it is c-12's terse search-box phrasing, the one paraphrase in the
  set that shares its topic nouns with the original.

**Every correction worked. Not one of them transferred.**
