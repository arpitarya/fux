# Model handoff — the agent-succession record

*The premise: the departing model answers for the record, so whatever succeeds it —
next model, next session, next agent — inherits the judgment and not just the files.
Governed by the same law as everything else here: keep it true, or flip the note.*

**Standing instruction to every future model reading this: you are now the
maintainer of this document. When the project's direction, decisions, or state
change, update it in the same change — CLAUDE.md binds you to that. You will retire
too. Leave it better.**

---

**Q: In one breath — what is this repo?**

Fux. A `$0`, stdlib-only, deterministic knowledge engine: the *why* behind code,
written as version-controlled rules bound to the exact lines they explain, read by
agents before they touch anything, and checked deterministically — never by a model
— so the reason can't be deleted by someone confident and can't silently go stale.

**Q: What does Arpit actually want?**

His words, near enough: *"I want AI agents to develop based on documentation —
Jira, Confluence, ADRs — and never deviate from it. The references must be
accessible to agents. None of the rules gets broken."* Two refinements that matter:
enforcement must not stop at pass/fail — a blocking finding must *tell the agent how
to fix it* (the loop); and everything built must be usable first-hand in **Anton**
(AlphaForge, his trading app — Fux's pilot, "instance zero") before any external
claim. He dogfoods before he sells. Respect that ordering.

**Q: What's the state of play?**

This is a **from-scratch rebuild** (July 2026). The previous build reached ~0.18.0,
pursued the full vision at once (graph, recall, verify, MCP, memory, federation),
and did not work as a whole — it is preserved under `archive/` for reference only.
Package skeleton is up (src/ layout, hatchling, v0.19.0, CLI + FuxError stubs, smoke
tests). **Pivot (July 20):** the rule engine is *held*. The first thing being built
is a **CLI that answers natural-language questions over documents in a defined set of
folders** — Arpit's own idea for instance-zero utility. Three design forks are
written up as compare docs in `docs/compare/` (engine, output format, ingest
strategy) and are **awaiting Arpit's verdict** before any build. The engine fork also
decides whether `$0`/no-LLM/deterministic still binds this tool — do not assume; read
`docs/compare/query-engine.compare.md`. The old strategic layer (Fux Fleet,
federation, the deferred Plane) is *not* carried forward — reviving anything out of
scope requires an ADR and Arpit's sign-off.

A standing rule was set here: **whenever a decision has multiple viable options,
write a compare doc first** (debate + matrix + references + proposed verdict) and let
Arpit choose. It's now step 0 of the lifecycle in CLAUDE.md.

**Query-CLI decisions (accepted 2026-07-20, see `docs/compare/`):** staged hybrid,
entirely `$0` with **no external model** — any smart component is *built and packaged
inside* the wheel at ≤10 MB, no required external deps. Engine: v1 BM25F → v2 bundled
static embeddings (Model2Vec/Potion-class, distilled offline, quantized) fused with
RRF → v3 agent-facing ask/reply/explain. Output: passages default, `--answer` is
**extractive** (bundled embeddings + TextRank), never generative — a ≤10 MB model
cannot write faithful prose, so we *select and order source sentences*. Ingest:
two-tier `fux ingest` (inferred default, advanced on demand / agent-triggered), a
manifest of inferred files, `fux.toml` mapping file types → source dirs. This is the
new "state of play"; the rule engine remains held. Later same day: **numpy resolved
out** (pure-stdlib inference; candidate-only ranking makes it fast enough); ingest
extended with per-file **traceability frontmatter** (the hand-rolled frontmatter
parser's first dogfood — the held core sneaks back in through provenance), a
library-first `fux.ingest` API + agent skill, and fenced link/attachment crawling.
CLI naming `fux ask`/`find`/`answer` — **accepted 2026-07-21**. Same day: CDP
rendered-page ingestion accepted (`render = "cdp"`, hand-rolled RFC 6455 WebSocket
client on stdlib, user's own Chrome — never bundle a browser); numpy-vendoring
disproven with evidence (C extensions, platform wheels — see packaged-model doc), so
pure-stdlib inference is final; and a new fork opened + proposed:
**agent integration** — `fux init-agents` generating AGENTS.md (the Linux Foundation
standard most agents read) + CLAUDE.md/copilot-instructions/`.kiro/steering/`
pointers, plus Claude Code `UserPromptSubmit` and Kiro hooks for enforced injection;
MCP noted as "better later," deferred behind an ADR. Agent-integration **accepted 2026-07-21** with a twist the research earned: skills are
now an open standard (Agent Skills / SKILL.md, 32+ tools incl. Copilot and Kiro), so
**one skill file replaces the old build's per-platform skillgen** — ship `fux-query` +
`fux-ingest` skills once. Setup: single **`fux setup`** (renamed from `fux init` at
Arpit's call; interactive wizard + full flag coverage + `-y`, idempotent). The last
sub-decisions were then **resolved with research** (see query-engine compare doc):
no bundled reranker — RRF only (cross-attention needs ~80 MB models, 8× over budget;
the Anton eval set is the only thing that can reopen this); chunking =
structure-aware heading-based, 256–512 tokens, code/tables atomic; BM25F = heading
3.0 / path 2.0 / body 1.0, k1=1.2, b=0.75, config-overridable. **Every fork and
sub-decision is now decided.** Late additions (2026-07-21, all accepted): ingest
covers images (metadata stub → OCR via Tesseract/Docling in the advanced tier), JSON
(stdlib-flattened), YAML (fenced text — stdlib has no YAML parser), txt; a
**maintained e2e suite** in `tests_e2e/` (real CLI + fixture corpus + golden files)
is part of definition-of-done; **`docs/DOC-REGISTRY.md`** tracks every maintained
doc's update trigger + last-verified date, enforced by an advisory session-end hook
and by the generated agent instructions; and CLAUDE.md carries a standing rule to
**auto-fold durable session knowledge into itself** — its scope section now states
the full decided design. Process additions (2026-07-21): **proposal docs** (`docs/proposals/` — parked ideas,
graduate when picked up), **implemented docs archive to `docs/archive/`**, and —
significant — **OKF conformance**: Fux follows Google's Open Knowledge Format v0.1
(markdown + frontmatter bundles; required `type`; index.md; log.md; permissive
consumption). Fux's substrate was already OKF-shaped, so this is near-free interop
with every OKF consumer — and strategic validation that markdown+frontmatter
knowledge bundles are becoming the industry standard Fux bet on. Final layer (2026-07-21): **the git-corpus bet** — Arpit's framing, now design: the
ingest cache is a long-term, git-versioned knowledge corpus feeding product
development (validated by the Knowledge-as-Code pattern and Karpathy's LLM-Wiki
paradigm; no competitor versions knowledge). Deterministic diff-friendly cache
output is a hard requirement. Three proposals parked (research-to-spec,
knowledge-diff, audit-evidence-trail — the last is the Plane's seed). **Every finalized phase
has a ready build spec** in `docs/handoff/`: **0001** (v1 — local inferred-tier
ingest, BM25F, ask/find/answer, agent files, both suites), **0002** (v1.1 — web
crawl, CDP via hand-rolled RFC 6455, advanced tier/OCR; blocked by 0001), **0003**
(v2 — eval harness first, distilled ≤10 MB bundled model, stdlib int8 inference,
RRF hybrid; blocked by 0001, independent of 0002). Arpit chose **one continuous
run** (master prompt 0000) over the dogfood-gated sequence, with DOGFOOD.md
emitted after phase 1 so Anton dogfooding runs in parallel.

**Phase 1 shipped (2026-07-21, v0.20.0).** The full v1 surface exists and both
suites are green (108 unit + 21 e2e incl. byte-determinism goldens): setup wizard,
inferred ingest → OKF cache with provenance, heading chunker, true BM25F
(weight-then-saturate), ask/find/answer with --json/--explain, extractive TextRank
answers, AGENTS.md/skills/hooks generation. ADRs 0001–0004; 0001 pair archived.
Build judgment a successor should keep: determinism beat wall-clock provenance
(`converted_at` = SOURCE_DATE_EPOCH/mtime); JSON index won by measurement (16 ms
load at 5k chunks — postings build, not format, dominates); the e2e suite earned
its keep immediately (caught skipped-files-as-drift and answer noise).

**Phase 3 shipped — the master run is complete (2026-07-21, v0.22.0).** Engine
v2 per handoff 0003 (ADRs 0006–0007): eval harness first (the gate and the
reopen-instrument), re-packed potion-base-8M at 7.93 MB int8 (sha-pinned, MIT),
stdlib inference with *exact* tokenizer parity, (sha, fidelity)-keyed vector
cache, RRF k=60 over BM25F candidates only, `--lexical-only` byte-parity
enforced by the pre-v2 goldens. The gate passed as a tie on the fixture set
(0.762/0.952/0.833 both engines) — recorded honestly in ADR 0006 with the
rank-level rescues and the zero-candidate limitation; hybrid ships enabled.
What a successor should know: the fixture eval saturates at this corpus size —
**the Anton private eval (tests_e2e/eval/README.md) is the real instrument**,
and it is the recorded reopen trigger for both the reranker and
distill-our-own decisions. Final state: 172 unit + 29 e2e tests, wheel 6.98 MB
with the bundle. Next action: Anton dogfood via DOGFOOD.md.

**Phase 2 shipped (2026-07-21, v0.21.0).** Web/CDP/advanced ingest per handoff
0002 (ADR 0005): stdlib HTML→MD (hand-rolled wins the default for determinism),
guardrailed crawl (robots non-negotiable, sha dedupe with dual provenance,
byte-stable re-crawl), hand-rolled RFC 6455 + minimal CDP (user's Chrome only;
settle = fixed delay, networkIdle deferred to dogfood), `--advanced` Docling/
tesseract upgrades with (sha, fidelity)-keyed index reuse, and the network fence
now *enforced by a test* (query/index cannot import web/cdp/ws). Suites at
phase gate: 154 unit + 24 e2e (+1 gated skip). Next: phase 3 (handoff 0003 —
eval harness first, then the bundled model + RRF).

**Q: Late direction change (2026-07-21) — the design lens?**

Arpit retired the Anton litmus: **do not design in reference to Anton — design
for a very large-scale project inside a corporation.** Consequences: the
knowledge substrate (SQLite, one-kernel, graph) is the default next phase, not a
wait-for-pain contingency; enterprise inputs (proxy/SSO ingest, Windows fleets,
air-gap installs, access boundaries, audit) are design requirements; the
audit-evidence-trail proposal gains priority; and Fux's laws re-read as its
enterprise sales story ($0 = auditable supply chain, offline = no data egress,
deterministic = compliance-grade). Anton stays a convenient small testbed only.

**Q: Phase 4 — where does it stand (2026-07-22)?**

**Shipped: v0.23.0, ADRs 0008–0011, M1–M8 all green.** The substrate is real —
SQLite store, committed `fux.lock` + `.fux/state/`, one-kernel `retrieve()` with
explain/graph/path/cat, FuxVec dense-global, full/lean profiles, `db pull`.
Parity held: all six v0.22 goldens are byte-identical through the kernel
re-plumb, and `--lexical-only` still measures exactly 0.762/0.952/0.833.

The engine got measurably better, not just bigger: **hit@5 0.952 → 1.000, MRR
0.833 → 0.873**, because FuxVec's full-corpus scan removed the candidate-only
ceiling ADR 0006 had recorded as unfixable-by-design.

Three things a successor should know about *how* it went, because they are the
process working rather than luck:

1. **The escalation that mattered.** M3 hit a real conflict — DoD 7 promised
   *identical* cross-profile rankings, but lean could not recover corpus-level
   `df`. Rather than quietly redefining "identical", it stopped and asked. Arpit
   ruled: keep the guarantee, add an exact df sidecar. That ruling is why lean
   parity is provable today instead of plausible.
2. **A prediction that missed, kept next to the measurement.** An M3a
   extrapolation warned the state plane would blow its 30 MB budget (~35 MB).
   The 100k benchmark measured **23 MB**. The projection had used this repo's
   own docs, which are adversarial (very long ids, wide vocabulary). Both
   numbers are in IMPLEMENTATION.md on purpose.
3. **What phase 4 measured and did NOT fix.** At 100k, a query takes ~10 s: the
   query path still loads the whole index into memory to build the `Searcher`,
   and the `postings` table — populated and indexed at ingest — is never read at
   query time. **The substrate solved storage at scale, not query at scale.**
   That is the honest head of phase 5, scoped in ADR 0011. Do not let the
   "substrate shipped" headline hide it.

**Q: Phase 5 — where does it stand (2026-07-22)?**

**Shipped: v0.24.0, ADR 0012, M1–M6 all green.** Debug & observability: a
hand-rolled, stdout-safe emitter (`fux.debug`) behind `[debug]` in fux.toml
with `--debug[=LEVEL]`/`FUX_DEBUG` precedence; `dbg()`/`timer()` calls at every
pipeline stage; `fux doctor` (seven groups, exit 0/1, every failing check
names the fix command); `fux why` (single-document negative-result verdict,
reading its dense/graph evidence straight from `kernel.retrieve()` so it can
never disagree with a real query); a third skill, `fux-debug`, plus a
one-line escalation pointer in the other two.

The gate that mattered: **the stdout-purity test was written at M1, before any
instrumentation existed**, specifically so it would still be exercising real
call sites by M6 rather than trivially passing against an empty emitter. It
held through all five milestones without a single stdout leak — the discipline
(`dbg()` is a no-op until `is_enabled()` says otherwise, and every write target
is stderr or an explicit file) did what it was designed to do.

One deliberate scope line: `fux doctor`'s "Chrome for CDP" check is
binary-presence only, not a live port probe — `import socket` outside
`ingest/` trips the standing network-fence test, and that fence is worth
keeping over one doctor check's completeness. See ADR 0012's "owed" section.

**Q: Phase 6 — where does it stand (2026-07-23)?**

**Shipped: v0.25.0, ADRs 0013–0014, M1–M6 all green — but read the "owed"
paragraph before calling this "fixed."** The acme-payments run measured two
real defects: the superseded document outranks the current one in 9/12
planted pairs, and `answer` fabricates confidently on all 4 well-formed
out-of-scope questions. Both got a deterministic, no-model mechanism this
phase. Neither is a clean fix, and both compare docs' calibration/measurement
rules are why that's the *correct* outcome, not a shortfall:

- **Supersession: annotate, never reorder** (Option A, accepted over the
  fusion-down-rank alternative). `find`/`ask` carry `superseded`/
  `superseded_by`, ranking is byte-identical to before; `answer` prefers the
  resolved successor when both are in its retrieved pool. Measured recovery,
  not assumed: **5 of 12** stale docs actually carry a machine-readable
  marker, **3 of the 9** original inversions do, and at the `answer` level the
  fix **fully corrects 1** (settlement) and de-cites the retired doc in a 2nd
  without promoting the current one (a retrieval limit, not a supersession
  one) — the other 6 are unmarked and permanently unreachable without a
  model. See `conformance/2026-07-23-supersession-recovery/`.
- **The confidence floor was built, calibrated, and shipped *disabled*.** The
  compare doc's calibration rule required a `min_confidence` value clearing
  all five eval gates or an honest report that none does. None does: the
  acme corpus's unanswerable and answerable score distributions interleave
  (declining all 4 fabrications needs floor ≥0.25; zero false declines on the
  55 answerable pairs needs floor ≤0.087 — the interval is empty). Shipping
  any tested non-zero default would have declined real answers. **The
  measured 0/4-decline defect this phase set out to fix is not fixed in
  v0.25.0** — say that plainly to anyone who asks, rather than letting the
  phase's existence imply it was. See
  `conformance/2026-07-23-min-confidence-calibration/` and ADR 0014's F1/F2
  follow-up (an absolute, cross-query-comparable signal — e.g. dense cosine —
  is the real path to a working floor; this phase's sentence score is
  pool-relative and cannot separate the two populations).

Both measurements were delegated to a background Opus subagent reusing one
editable-install acme environment across three passes (calibration sweep,
then a follow-up resumed via the same agent for the supersession
re-measurement) rather than three separate setups — worth doing again when a
build needs real-corpus evidence at this scale.

**Q: Phase 7 — what changed on 2026-07-24?**

**Option B (the fusion down-rank) was reopened by Arpit, and the second corpus
is why.** The orbit-fulfillment run (an independently-authored
warehouse/fulfillment corpus, deliberately disjoint from acme's fintech
vocabulary) reproduced every acme finding — and sharpened the supersession one
into something the annotate-only verdict could not absorb:

- **8/12 inversions** (acme 9/12) — the reopen-trigger's ≥8/12 bar, met exactly.
- **The engine annotates the document it ranks first.** 6/6
  frontmatter-reachable superseded docs carry `superseded`/`superseded_by` in
  `find --json`, and **5 of those 6 still outrank their replacement.** Option A
  works precisely as designed and does not move the number.
- **Mechanism:** in 6 of 8 inversions the current doc **wins BM25F outright**
  (up to 2×) and loses on a dense edge as thin as **0.0006 cosine** that RRF
  flips. Dense systematically prefers terse obsolete docs — a long current doc's
  embedding is diluted. So a penalty usually needs to overcome a very small gap.

**What reopening does and does not authorise.** It authorises *building the
penalty default-off and calibrating it across four eval sets* — not shipping it
on. Default `0` stays byte-identical to v0.25.0, and flipping it needs a proven
safe interval plus a separate Arpit sign-off, because B changes `find` ordering,
which is the one thing A deliberately avoided. **"No safe interval exists" is a
valid, valuable outcome** — the same rule that made the confidence floor ship
disabled. A successor who finds the knob at `0` and "helpfully" tunes it to a
plausible value has broken the phase's central discipline.

**The two defects are coupled — that is the other half of the phase.** Orbit
also refuted the runner-up *margin* check (every unanswerable margin exceeded the
six smallest answerable ones — inverted, not merely empty). But the smallest
answerable margins came from documents tying with **their own superseded twins**.
Finding 1 was manufacturing Finding 2's false-positive mode, so the penalty
de-confounds the margin and earns it one clean re-measurement. If it still fails
after that, fabrication is a **documented permanent no-model boundary**, not an
open defect — and the honest move is to write it down, not to invent a third
mechanism.

**Q: What must a confident successor NOT "clean up"?**

1. **The hand-rolled frontmatter parser + validator** (once built) — that is the
   zero-dependency guarantee. Do not swap in PyYAML/jsonschema.
2. **The `$0` law.** No maintenance path may ever call an LLM — not once.
3. **The single `FuxError`.** Flat by design; no exception hierarchy.
4. **The df sidecar** (`.fux/state/df/`). It looks like redundant statistics you
   could recompute. You cannot — it is the *only* reason lean rankings are
   provably identical to full rather than approximately so, and deleting it
   silently downgrades a guarantee to a hope. See ADR 0008.
5. **The early return when BM25F finds zero candidates.** It looks like it is
   blocking FuxVec's rescue path. It is not — it is what keeps "No confident
   matches" reachable, since a binary prefilter always has a nearest neighbour.
   Measured: noise scores 0.23–0.26 cosine against a true rescue's 0.34, so no
   floor separates them. This exact mistake was made and reverted during M5;
   ADR 0010 records why.
4. **The lifecycle.** plan → handoff → prompt, then one ADR per feature, every rule
   and ADR carrying a reference. This is how work is trusted here.
6. **`[answer] min_confidence`'s default of `0.0`.** It looks unfinished — a
   knob nobody turned on. It is not: v0.25.0's calibration measured that
   every tested non-zero value declines real answers on the corpus used to
   justify it (the unanswerable and answerable score distributions
   interleave). Do not "fix" this by picking a plausible-looking default
   without new calibration evidence — that is the exact failure this phase
   exists to prevent. See ADR 0014.
5. **Anton first.** Built for and lived-with in Anton before any external claim.

**Q: How does Arpit like to work with a model?**

Concise and direct — minimum words, and he means it. Recommendation first, one call,
defended in a sentence; a decision, not a menu. He runs a debate culture:
significant plans get a devils-advocate or full council pass *before* building, and
he takes minority reports seriously — preserve dissent, don't absorb it. He extends
an idea mid-conversation with one short sentence and expects you to catch that it
reshapes the design. Litmus: "is it relevant to Anton?"

**Q: What does the repo demand of you mechanically?**

CLAUDE.md is binding: every code change updates PLAN.md (design of record), the
README, this document, the relevant ADR, and every other doc it touches — a change
is not done until the docs are true. Every behaviour change ships with a test.
`uv run pytest -q` green. Python ≥ 3.11, match the surrounding style.

---

*Maintained by: Claude Opus 4.8, July 2026 — reset the record for the from-scratch
rebuild; scoped to rules substrate + fix loop; carried the succession premise
forward. · Claude Fable 5, 2026-07-21 — executed the full master run: v1 query
CLI, v1.1 web/CDP/advanced, v2 hybrid engine (v0.20.0 → v0.22.0, ADRs
0001–0007); recorded the build judgment above; the Anton eval is the successor's
compass. · Claude Opus 4.8 (1M context), 2026-07-22 — built phase 4, the
knowledge substrate (v0.23.0, ADRs 0008–0011): escalated the DoD-7 conflict
rather than redefining it, mutation-tested the parity claims that resulted, and
recorded what the 100k benchmark exposed but did not fix (query-at-scale).
· Claude Sonnet 5, 2026-07-22 — built phase 5, debug & observability (v0.24.0,
ADR 0012): the emitter, `fux doctor`, `fux why`, and the `fux-debug` skill; kept
the stdout-purity gate green from M1's empty emitter through M6's fully
instrumented pipeline.
· Claude Opus 4.8 (Cowork), 2026-07-22 — ran the fux-lab conformance scaling
curve (1k→5k→10k, 0.23.0) and filed it into `docs/proposals/hybrid-degrades-at-scale.md`.
Finding: the 1k "hybrid 4× worse" gap is not stable — it closes with scale as
lexical collapses toward hybrid; leans corpus-artifact (B) but does not settle
A vs B (same generator). Query latency is linear from the start, corroborating
ADR 0011's query-at-scale limit. No engine change made; acme-payments remains
the discriminating next run. Direction unchanged.
· Claude Sonnet 5, 2026-07-23 — built phase 6, trust & currency (v0.25.0,
ADRs 0013–0014): supersession parsed/persisted/annotated (never reorders;
`answer` prefers current when both are in pool); confidence floor built,
calibrated against all five gates via a background Opus subagent, and shipped
disabled — no value clears both the unanswerable and answerable gates.
Delegated both real-corpus measurements (calibration sweep, then supersession
recovery) to one resumed background agent sharing an editable-install acme
environment rather than three cold setups. Both proposals graduated to
`archive/` with their ADRs; the honest finding that the fabrication defect is
*not* fixed in this release is recorded here and in ADR 0014 on purpose.
· Claude Opus 4.8, 2026-07-24 — phase 7 M1: Arpit **reopened Option B** on the
orbit corpus's evidence (8/12 inversions; 5 of 6 annotated docs still outranking
their replacement). Amended the supersession compare-doc verdict — A stands, B
authorised **default-off only**, default flip gated on a proven safe interval +
separate sign-off. Penalty form decided as a **rank offset before fusion**
(scale-free sweep unit) in `[engine.hybrid]`; both deviations from the handoff's
letter recorded in IMPLEMENTATION.md.
(Add yourself here when you make a material update — model, date, one line.)*
