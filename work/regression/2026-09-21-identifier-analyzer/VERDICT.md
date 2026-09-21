---
type: Verdict
name: W-205-PART-2-FAMILY-A
verdict: INCONCLUSIVE
prediction: W-205 part 2 family (a)
pre_registration: work/regression/2026-09-21-identifier-analyzer/PRE-REGISTRATION.md
run: 2026-09-21-identifier-analyzer
item: W-205
filed: 2026-09-21
---

# VERDICT — W-205 part 2, family (a): **INCONCLUSIVE. The change does NOT ship.**

**Ruled against [the frozen pre-registration](PRE-REGISTRATION.md)**, whose own
words decide this: *"**INCONCLUSIVE** — every rung's net is in ±5. **The change
does not ship on an inconclusive**, and the arm is reported as not
distinguishable at this N, never as no difference."*

`ANALYZER_VERSION` stays **`v2`**. The branch is not merged.

---

## The endpoint — `rank_primary_bare`, hit@1, paired, per rung

| rung | before | after | fixed | broke | discordant | **net** | the floor at that discordant count |
|---|---:|---:|---:|---:|---:|---:|---|
| `rung-00100` | 32/43 | 33/43 | 1 | **0** | 1 | **+1** | 🔴 impossible — no split clears α |
| `rung-01000` | 30/43 | 33/43 | 3 | **0** | 3 | **+3** | 🔴 impossible |
| `rung-10000` | 29/43 | 33/43 | 4 | **0** | 4 | **+4** | 🔴 impossible |

🔴 **Nets of 1–5 cannot clear α at ANY discordant count**
([SR-RS](../../../records/0133_predictions.md) decision 19). Their best
achievable p-values are `1.00`, `0.50`, `0.25`, `0.125` and `0.0625`. **No
arithmetic on these rows produces a result**, and that is settled without
reference to how good the change looks.

**Headroom, disclosed from the before-arm before any net is quoted** (decision
22): improving **11 · 13 · 14** of 43; degrading **32 · 30 · 29** of 43. 🔴 **The
run was not structurally unable** — the improving direction had 14 misses to
work with at `rung-10000`, well above the floor. **It converted 4.**

## 🔴 The finding that matters more than the verdict: the failing shape did not fail

**Set 3 was authored to give this measurement headroom.** Its whole purpose was
identifiers of the shape that breaks — a shared prefix plus a short number,
siblings differing by one digit.

| family | n | fixed | broke | net | before-arm hit@1 |
|---|---:|---:|---:|---:|---|
| `sibling-rf` — `RF-117/119/120` | 3 | **0** | **0** | **+0** | **3/3 in BOTH arms** |
| `sibling-proj` — `PROJ-123/124/125` | 3 | **0** | **0** | **+0** | **3/3 in BOTH arms** |
| `sibling-tsl` — `TSL-RF-119-A/120-A` | 2 | **0** | **0** | **+0** | **2/2 in BOTH arms** |
| `unique` — `NGP-MNT-731` | 1 | 0 | 0 | +0 | 1/1 both |
| `frontmatter-only` — `QCL-QA-MAP-01` | 1 | **0** | **0** | **+0** | **0/1 in BOTH arms** |
| **`pre-set-3`** — the 33 of 2026-09-18 | 33 | **4** | **0** | **+4** | 23 → 24 |

🔴 **Every one of the eight sibling identifiers already ranked its own document
first, in both arms, at every rung.** The precision defect the item is built on —
*"`RF-118`, `RF-119` and `RF-120` collide on `rf`"* — **does not cost a hit@1 on
this corpus.** Splitting is symmetric, `118` is a rare term in its own right, and
the pair `rf` + `118` is already enough to separate three documents.

⚠ **Every fix came from the OLD 33** — `RF-221`, `GHY-7`, `SANDHU-EXC`,
`WIKI-NGP-DOCK-12` — and none from the ten identifiers set 3 was written to
supply. **The input arrived and the feature did not need it.**

🔴 **This does not make set 3 a waste, and saying so would be the wrong lesson.**
Set 3 also carried the 61 `ref` edges that took the ladder from zero, and it
produced phase A's replication of the authorship gap. What it did *not* do is
create headroom for this particular arm — **because the premise that the shape
fails at hit@1 was never measured before the documents were written for it.**

## The direction is monotone in corpus size, and that is the one thing worth carrying forward

**+1 → +3 → +4** across 100 → 1 000 → 10 000 documents, with **zero regressions
at any rung**. The effect grows as the corpus grows, which is what a
precision fix should do: more documents, more chances for a split prefix to
collide.

⚠ **It cannot be extrapolated into a pass.** **10 000 is the ceiling**
([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)), so the rung where this
might clear 6 is a rung nobody may build or measure. **A trend is not a result**,
and decision 19 does not admit one.

## The two absolute conditions — both hold

| # | condition | result |
|---|---|---|
| 1 | no `ref` or coverage count may move | ✅ **61 `ref` edges, 101 `supersedes`, 1 000 documents — identical in both arms** |
| 2 | the 60-question set-1 control must not degrade | ✅ **2 of 60 moved top-1**, far below the floor |

⚠ **Both control movements went TOWARD a seed document** — `s1-009` from a
generated hard negative to `seed/01-sop-temperature-excursion.md`, and `s1-119`
from the set-3 map to `seed/06-re-fw-telematics-cutover.eml`. **That is not
evidence the change is good.** The control's endpoint is *stability*, it has no
key, and a top-1 that moved to a seed document may still be the wrong seed
document. **It is reported and not counted.**

⚠ **One number moved that is not a coverage count: anchor terms, 245 → 266.**
Anchor text is analyzed link text, so a new analyzer necessarily re-tokenizes it.
Expected, not a finding, and it is why condition 1 was written about `ref` and
coverage counts rather than about "nothing in the census moves".

## What it costs

| | before (`v2`) | after (`v3`) | ratio |
|---|---:|---:|---:|
| analyzed tokens, 28 seed documents | 12 936 | 13 237 | **×1.023** |
| distinct terms, same | 1 641 | 1 960 | **×1.194** |
| accelerator terms, `rung-00100` | 2 258 | 2 794 | ×1.237 |
| accelerator terms, `rung-01000` | 3 769 | 6 009 | ×1.594 |
| accelerator terms, `rung-10000` | 14 033 | 29 489 | **×2.101** |
| postings, `rung-10000` | 849 935 | 896 233 | ×1.054 |
| committed index bytes, `rung-10000` | 24 876 KB | 26 008 KB | **×1.046** |

🔴 **The vocabulary roughly DOUBLES at 10 000 documents while the postings grow
5 %.** That is the signature of adding many rare terms: each whole-form appears
in one or two documents. It is cheap in bytes and expensive in dictionary size,
and **the dictionary is the plane that grows with the corpus**.

⚠ **The cost is not bounded by the identifier count, and the pre-registration
said so before the number existed.** English prose is full of hyphenated
compounds — `one-off`, `cold-chain`, `night-shift` — and each becomes a term.
**The ×2.1 at `rung-10000` is mostly prose, not identifiers.**

**No cost threshold was set**, deliberately, so this number rules nothing on its
own. It is here because a change that doubles the dictionary for a net of +4
should be *seen* to do so.

## What this run may NOT be read as saying

- **Not that the analyzer change is wrong.** It does exactly what it claims:
  **33 of 33 seed identifiers survive whole, from 0 of 33** — W-168's gate A,
  met on both readers, with the moving rows named in
  [`evidence/w202-diff.md`](evidence/w202-diff.md). **The mechanism works and the
  ranking did not care enough to prove it.**
- **Not that identifiers rank badly.** They rank well, in both arms.
- **Not a null.** [SR-RS](../../../records/0133_predictions.md) decision 22d:
  *not distinguishable at this N*, with headroom disclosed.
- **Not a statement about `QCL-IT-ADR-08`.** It is frontmatter-only, absent from
  the index in both arms, and waits on **part 1** — SR-INGEST decision 23d says
  this in advance, and this run confirms it rather than discovering it.

## 🔴 To Arpit, because SR-RS says an ambiguous result is his

**The mechanism is built, tested on both readers, and measured clean — 4 fixed, 0
broken, growing with corpus size — and it cannot be certified on a corpus capped
at 10 000 documents.** Three ways forward, none of which a session may choose:

1. **Ship it anyway on the mechanism**, treating *"whole-and-parts is the
   analyzer's stated promise and v2 keeps it for `_` alone"* as a **correctness**
   argument rather than a ranking one. 🔴 **This is the honest case**, and it is
   the one the fixture supports: SR-RANKING decision 9 asserts a property the code
   does not have. The ranking evidence would then be *no harm at 0 regressions*.
2. **Hold it** until a corpus with genuinely colliding identifiers exists — one
   where the sibling number is *not* itself discriminating (`PROJ-1` … `PROJ-9`,
   or ids that differ only in a letter).
3. **Drop family (a)** and with it family (c), which it is a precondition of.

⚠ **Whichever he picks, the corpus lesson stands: the shape was chosen without
measuring that it failed.** The next data-shaped unblock should measure the
premise before the documents are written, which is decision 23c one step earlier
than it currently reaches.

## Classification

**`informed`.** The id-queries were authored by the measurer's family from the
seed, on Arpit's 2026-09-18 instruction after Codex declined, and this session
rebuilt the corpus. **No golden answer was used, needed or reachable** — an
id-query set carries no answer and never enters `work/golden/`, which is the
property that let this be measured at all.
