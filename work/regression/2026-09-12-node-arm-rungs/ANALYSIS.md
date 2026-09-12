---
type: Analysis
name: node-arm-on-the-golden-ladder-analysis
description: "What the first ladder run of the Node arm says to change: Node's missing tune reader and reranker (the gap the harness was pointed away from), the OS/Node matrix the run does not cover, and the query set that is a substitute for the golden questions until W-145 lands."
timestamp: 2026-09-12T00:00:00Z
---

# Analysis — the Node arm on the golden ladder

Diagnosis of [`report.md`](report.md), turned into specific improvements. Each
carries a repro command. Unresolved causes are stated as unresolved.

---

## 1 🔴 Node reads no `tune.toml`, so a tuned index gets two different answers

**The defect, precisely.** `node/src/config/` contains `root.mjs` and nothing
else. No file under `node/src/` mentions tune. W-107 R5's fixed read path lists
`.fux/tune.toml   absent = defaults; malformed = hard error`; that row is
unbuilt, and `query/rerank.mjs` — listed in Phase 2 — does not exist.

**Why it matters more than a missing feature.** `fux-engine` is **published on
npm** and `fux setup` **vendors the reader into every consumer's `.fux/`**
(R2). A consumer who runs `fux tune` and then reads with Node gets a different
ranked list from the same index, with nothing saying so — which is the
*"stale reader against a bumped `_format` is a wrong answer, not an old
preference"* argument in R2, arriving through a door R2 does not cover: the
version is identical and the answer still differs.

**Repro:**

```console
$ cp -R ~/my_programs/fux-lab/corpora/golden/rung-00100 /tmp/probe
$ sed -i '' 's/^rerank_weight.*/rerank_weight = 0.3/' /tmp/probe/.fux/tune.toml
$ python tools/differential/node_arm.py /tmp/probe --queries fixed --tops 5
discordant: 20 of 58
$ python tools/differential/node_arm.py /tmp/probe --queries fixed --tops 5 --python-tune off
discordant: 0 of 58
```

**The improvement, and it is two items, not one:**

- **`node/src/config/tune.mjs`** — the twin of `src/fux/tune.py`'s *reader*
  (not its 739 lines of validation): the keys `rank.mjs` and `bm25f.mjs`
  already take as parameters, plus the loud refusal on a malformed file that
  R5 names. The `config/toml.mjs` subset it needs already exists.
- **`node/src/query/rerank.mjs`** — Phase 2, and the harder half: the
  proximity reranker reads document *content*, so it lands with the refer
  plane and not before it.

⚠ **Not fixed in this change, deliberately.** Both are Node ranking code under
[ADR-NODE-SEARCH](../../../docs/adr/0155_node-search.md); transcribing 300
lines of reranker in the session that discovered the gap is how a wrong last
bit ships with a green arm behind it. What this change does is make the gap
**visible and attributable** — see item 2.

## 2 ✅ Done here — the arm compares the path the CLI uses, and says which

`node_arm.py` now calls `run_query`, and carries an explicit axis:

| `--python-tune on` (default) | the **contract** — what `fux find` answers |
| `--python-tune off` | the **transcription** — `--no-tune`, the engine's own answer, which is what Node implements today |

Both numbers are printed with the corpus's tune delta as a run condition, and
the delta is written into the evidence TSV's header. **An evidence file that
does not name the tune cannot be interpreted later**, which is the same
argument as ADR-RS's per-query rule at a smaller scale.

CI runs the **transcription** arm on this repo (`.fux/tune.toml` here sets
`rerank_weight = 0.3`), so a failure there is a Node transcription defect and
nothing else. The **contract** arm runs on the golden rungs, whose tune is
all-defaults — where the two arms are the same run.

## 3 🟠 One machine, one Node, and it is outside the matrix

The run is darwin/arm64, **Node v24.13.0**. [PRE-REG-NODE-2](../../benchmark/PRE-REGISTRATION-NODE-2.md)
§4 names ubuntu (glibc) · macOS arm64 · windows, and Node **20 and 22**.

- **The `ladder` job added to [`node-arm.yml`](../../../.github/workflows/node-arm.yml)
  runs the same commands the moment a runner has the corpora**, via
  `FUX_GOLDEN_CORPORA`; without one it emits a notice and passes, rather than
  reporting a cadence it did not meet.
- 🔴 **Unresolved: a GitHub runner cannot hold the ladder.** The corpus is not
  committed (only its manifests are — `work/golden/README.md`), `rung-10000` is
  120 MB, and `build_golden_rung.py` hard-codes two absolute paths on Arpit's
  machine. So §4's *per-push, full matrix* cadence is met **in fux-lab, on one
  OS**, and nowhere else. **Stated, not silently dropped.** The routes are a
  self-hosted runner, a committed small rung, or a portable builder — each a
  decision, none taken here.
- [`log-probe.yml`](../../../.github/workflows/log-probe.yml) is **still
  unrun**: musl, Windows and Node 20 remain unmeasured for `Math.log`.

## 4 🟠 The query set is a substitute, and says so

N5/N6 read *"over every golden"*. The golden questions are not released to a
Claude session until [W-145](../../open/W-145-codex-regenerates-the-key.md), so
this run used `queryset.py`'s corpus-derived set — built from the documents by
a fixed rule, capped **by position** and never sampled, so it cannot be curated
toward green.

- **Improvement:** when `questions.jsonl` is released, `node_arm.py` gains
  `--goldens <path>`; `queryset.generate` already takes a `goldens=` list and
  has since before this item. Until then **no run may be reported as N5 or
  N6**, and none is.

## 5 ✅ Done here — the manifests became load-bearing

Two things that were asserted in prose are now executable:

- **`rungs.py` verifies a rung against `rung-NNNNN.{index,sha256}` before the
  arm reads a byte** — every document hash and the index root hash. A drifted
  rung refuses the run. **Both readers would agree perfectly on a drifted
  corpus**, so this is the one failure the differential arm structurally cannot
  catch about itself.
- **`ladder_check.py` checks all eight manifests with no corpus at all** —
  counts, duplicate paths, the `seed/`+`ext/`-only rule, and the nesting
  `work/golden/README.md` called *"verified, not asserted"*. It runs in CI.

```console
$ python tools/differential/ladder_check.py
8 rungs, manifests consistent and nesting verified
```

## 6 🟠 Unresolved — `node --test` is unrun against a rung

The Node unit pins (`node/test/`) run against fixtures, not against a rung.
Nothing checks that Node's own tests and the arm agree about the same corpus.
Low value while the arm is green on both ends; recorded so it is not
rediscovered.
