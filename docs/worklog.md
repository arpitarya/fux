---
type: Log
title: Worklog — the running session handoff
description: Per-exchange rolling record (OKF log.md convention, date-grouped, newest first) so a new chat picks up cold.
timestamp: 2026-07-21T00:00:00Z
---

# Worklog — the running session handoff

*A rolling, per-exchange record so a new chat can pick up cold. Think of each entry
as a mini exit-interview for the conversation that produced it: what was asked, what
was done, what was decided, and the exact next step. **Both Cowork and Claude Code
must append to this** at the end of every substantive exchange (CLAUDE.md binds you
to it). Newest entry on top. Keep entries short and true; this is continuity, not a
diary.*

**Entry format**

```
## YYYY-MM-DD — <one-line title>  ·  <Cowork | Claude Code>
- **Asked:** what the human requested.
- **Did:** what actually changed (files, decisions).
- **Decided / open:** verdicts reached, and what's still awaiting a call.
- **Next:** the single immediate next step.
```

---

## 2026-07-22 — phase 4 complete: knowledge substrate shipped at v0.23.0 · Claude Code
- **Asked:** three rulings (integer token-sums approved as amendment; early-return
  judgment approved; state budget → measure at M8 before optimizing), then
  M6 → M7 → M8 → close-out, with a discipline check first.
- **Did:** discipline check passed (M1–M5 already committed as clean milestone
  commits; tracker rows ✅ with counts) except one reconcile — `fux path`'s
  renderer did not match the format cli-examples had specified first, so the
  **code was changed to follow the doc**, and the multi-path form documented.
  - **M6 PPR-lite:** constants as specced; seed-*rank* personalization; graph
    joins RRF as a fourth list. Guard: fusion skipped for node seeds, since a
    neighbour's passage among a document's own would misattribute it.
  - **M7 profiles:** lean = a Searcher over re-derived candidates with the df
    sidecar injected, so the kernel never learns its profile. Mid-corpus switch
    (full→lean) keeps rankings **and** scores — **mutation-verified non-vacuous**
    (making `lean_searcher` return None fails the test). LRU uses a monotonic
    counter, never a clock. `db pull` sha-verifies and refuses mismatches.
  - **M8:** committed generator + harness; 100k measured. **state 22.96 MB
    (≤30 ✓), df 0.92 MB (≤5 ✓)**, db 1081 MB (77% of §8b), FuxVec scan **54 ms
    < 150 → IVF not built**, ingest 566 s. Relational eval added for
    explain/graph/path.
  - **Close-out:** ADRs 0008–0011 (0010's flagged citations **verified**, not
    asserted); full docs pass; 0004 pair archived; **v0.23.0**.
  - Suites **172+29 → 365 unit + 71 e2e**; eval hit@5 **1.000**; `--lexical-only`
    still exactly 0.762/0.952/0.833.
- **Decided / open:** two behaviour changes recorded in Deviations — a fresh
  clone now answers *exactly* (better than DoD 2's doc-level, so the docs were
  corrected to match), and `auto` gained `lean_threshold` because §G read
  literally would have flipped every small repo to lean silently.
  **The M3a size warning was wrong and is kept next to the measurement that
  corrected it** (351 B/doc projected from this repo's adversarial docs vs
  230 B/doc actual); per the ruling, no zlib change was made.
  **⚠ The honest finding:** at 100k a query takes ~10 s — `postings` is stored
  and indexed but never read at query time, so the whole index still loads into
  memory. Phase 4 solved *storage* at scale, not *query* at scale.
- **Next:** **query-at-scale** — score from `postings` by term instead of
  loading every row (table, index and exact corpus stats already exist).
  Scoped in ADR 0011; it is the head of phase 5. Branch
  `feat/phase4-knowledge-substrate` (10 commits) is ready for PR to main.

## 2026-07-22 — phase 4 M3a–M5: df sidecar, kernel, FuxVec · Claude Code
- **Asked:** Arpit's DoD-7 ruling (Option B — exact df sidecar, guarantee does **not**
  soften), commit M1–M3 first, then continue M4→M8.
- **Did:** committed the backlog as three clean commits (spec docs / M1–M3 / sidecar),
  then landed M3a, M4, M5 — each green, each committed.
  - **M3a df sidecar** (`state/df/`): term hashes sharded by hash low byte,
    delta-encoded + varint df; `_stats.bin` holds total_docs/total_chunks and
    per-field token **sums** (integers round-trip exactly, and `avg_wlen`
    recomputes for any weights without re-ingesting). `Searcher` gained an
    optional `stats` injection — scoring math untouched, only input provenance
    changes. Parity is enforced, not asserted: every term in the vocabulary,
    scored over a strict *subset* (where subset-derived idf would diverge),
    matches full exactly — and **mutation-tested** (removing the injection fails
    both parity tests). Collisions raise rather than silently merging df.
  - **M4 kernel:** `retrieve() -> ResultGraph` is now the only retrieval path;
    ask/find/answer are projections, and explain/graph/path are new ones.
    `explain` = ask seeded by a node (its own `top_terms` become the query), so
    there is genuinely one code path. Edges now persist in the JSON store too.
  - **M5 FuxVec:** full-corpus Hamming prefilter → exact int8 rerank →
    `dense_global` as a third RRF list. **Gate beats v0.22 hybrid:** hit@1
    .762→.810 · hit@5 .952→**1.000** · MRR .833→.873, and ADR 0006's named
    zero-overlap miss is rescued. `--lexical-only` still measures exactly
    .762/.952/.833 with its four goldens byte-identical.
- **Decided / open:** two judgment calls recorded (implementation.md → Decisions,
  → ADR 0010). (1) **dense_global does not fire when BM25F returns zero
  candidates** — removing that early return made "No confident matches"
  unreachable, since a binary prefilter always has a nearest neighbour; measured
  noise scores 0.23–0.26 cosine vs a true rescue's 0.34, so no floor separates
  them as the corpus grows. Re-reading ADR 0006 settled it: "zero lexical
  candidates" meant the correct *document* had no overlap, not the query.
  (2) The two **hybrid goldens were updated deliberately**, with the eval table
  as justification; the four `--lexical-only` goldens were not touched.
  **⚠ Open (size):** early measurement projects the state envelope to ~35 MB
  @100k against Arpit's 30 MB budget — `meta/` + `sigs/` are the risk, not
  `df/` (~2 MB). M8 measures properly; cheap fixes noted if it confirms.
- **Next:** **M6 — PPR-lite expansion** (damping 0.85, 3 iterations, top-10
  ≥0.01, `[engine.graph]` config) + graph list into RRF. Then M7 (profiles +
  `db pull`), M8 (100k benchmark + gate), ADRs 0008–0011, docs pass, v0.23.0.
  Version still 0.22.1.

## 2026-07-21 — phase 4 M1–M3: substrate, state plane, graph · Claude Code
- **Asked:** execute handoff 0004 (knowledge substrate v3) — the full phase, M1 first,
  milestone plan posted before any code.
- **Did:** posted the M1–M8 plan with file-level breakdown, then built and landed
  **M1–M3**, each green before the next.
  - **M1** — `index/sqlstore.py` (schema A, format_version 2, WAL, single-writer
    `.fux/index/.lock`, PK-sorted writes) beside the JSON store, with `[index] format
    = json|sqlite|auto` dispatch; `ingest/lock.py` writes **`fux.lock`** at the repo
    root (format B) and the operational manifest moves to `.fux/index/manifest.jsonl`;
    `--check` is now lock-only and three-way (DRIFT/STALE/STATE-DESYNC); `fux setup`
    writes `.fux/index/` to `.gitignore`. **Parity proven, not asserted:** all six
    v0.22 goldens pass byte-for-byte on the sqlite backend (`tests_e2e/test_sqlite_parity.py`).
  - **M2** — `fux/state/` committed lean plane (format C: 256 buckets ×
    codes/sigs/meta, `FUXSTATE1\0` header, sorted records); Bloom signatures
    (k=4, 9.6 bits/term, 8–128 B — handoff open question 1 **decided**);
    `embed/fuxvec.py` sign-quantizer; bulk/mirror tier (`docs_text` rows, no files
    on disk); `fux cat`; and the **fresh-clone query path** — `rm -rf .fux/index`
    still answers `find`/`ask` at doc level from committed state, and `fux ingest`
    rebuilds the state buckets byte-for-byte.
  - **M3** — `fux/graph/` deterministic extraction: `references`, `cites` (links
    under a citations heading, ranked as evidence), `crawled_from`, `tagged`
    (tag *nodes*, so N docs sharing a tag cost N edges not N²), all EXTRACTED
    grade; node payloads (outline, top_terms) into the `docs` row.
  - Bugs the tests caught and fixed: vectors were hardcoded to the JSON store;
    sqlite corruption escaped past the CLI error boundary; a local-only `fux ingest`
    silently evicted mirror-tier `docs_text`; `fux cat` could not resolve on a
    fresh clone (manifest is in the runtime plane — now falls back to the lock).
  - Suites **172+29 → 262 unit + 55 e2e**, all green. cli-examples.md updated
    *before* each new renderer, per the handoff.
- **Decided / open:** three deviations recorded in implementation.md → Deviations
  (all headed for ADRs 0008/0011): `web:<slug>` ids apply to **all** fetched pages,
  not just bulk (otherwise every curated web doc reads as a permanent
  STATE-DESYNC); the operational manifest survives, relocated, rather than being
  replaced by the lock; `fux answer` has **no** state-only mode — it is extractive
  *and cited*, and citations need line-anchored passages, so it declines with a
  reason rather than citing lines the index never scored. **Open:** profile
  ranking parity (DoD 7) needs corpus-level df to be exact — Bloom-derived df is
  approximate; decide and record honestly at M7/M8.
- **Next:** **M4 — the kernel** (`retrieve()` + `ResultGraph`, re-plumb
  ask/find/answer under it with v0.22 golden byte-parity, then the
  `explain`/`graph`/`path` renderers). M4–M8 + ADRs 0008–0011 + the docs pass +
  the 0.23.0 bump are **not** started; version is still 0.22.1.

## 2026-07-21 — dummy playground repo for dogfooding · Claude Code
- **Asked:** set up a sibling repo with dummy data to play with the fux package.
- **Did:** created `~/my_programs/fux-playground` (git-initialized, initial commit) — fictional
  "Kestrel Coffee" roastery corpus: 3 md docs, 1 txt note, 2 py files, inventory.json,
  suppliers.yaml. Ran `fux setup --docs docs,notes --code src --data data -y` + `fux ingest`
  via fux's own .venv (fux 0.22.1): 8 files → 8 chunks, BM25F + embeddings. Verified
  `ask`/`find`/`answer` all return sensible results; `.fux/` cache committed per convention.
- **Decided / open:** nothing decided; playground is throwaway-adjacent but committed so
  re-ingest determinism can be diffed. `answer` output for the JSON-flattened chunk is noisy
  (dumps the whole flattened lot list) — possible future chunking/answer tuning observation.
- **Next:** play with queries in `fux-playground`; consider it a scratch dogfood corpus.

## 2026-07-21 — Pipeline stages reviewed → full platform matrix (linux/macos/windows) · Claude Code
- **Asked:** review all pipeline stages for necessity; the package must work on
  Python ≥ 3.11 across unix/linux/mac — then "and windows as well".
- **Did:** restructured CI — matrix now linux (3.11–3.14) + macos + windows
  (3.11 + 3.14 boundaries); **"fux gate" became a strict aggregator**
  (`if: always()` + explicit needs-result checks — a skipped required check
  would otherwise count as satisfied), so the wall now transitively requires
  every platform green; **ai-review no longer re-runs the suites** (they ran 3×
  per PR with zero added signal — its value is the separation-of-duties refusal
  + $0-law + credential probes, now ~10 s). Windows product fixes that CI made
  necessary: CLI boundary reconfigures stdout/stderr to UTF-8 on win32 (cp1252
  consoles crash on `·`/`→`), and `.gitattributes` forces LF everywhere with
  explicit binary guards (CRLF checkout would silently break fixture shas +
  goldens per platform; renormalize showed zero drift). pyproject gains the
  3.14 classifier.
- **Decided / open:** publish stages unchanged (pure-py wheel = one build for
  all OS). **Result: all 11 checks green on first run — Windows and macOS
  passed both suites with no further fixes needed.** Merged as PR #36.
- **Bookkeeping note (honest):** the Cowork session's README rewrite was
  uncommitted in the shared working tree and got swept into PR #36's commit
  (`git add --renormalize .` staged it; the unstage didn't hold). The content
  is intact and correct on main — only the commit message is wrong about it.
  Main is protected, so the history stands as-is rather than being rewritten.
- **Next:** Anton dogfood.

## 2026-07-21 — Agent commits now attributed + Verified on GitHub · Claude Code
- **Asked:** commits showed "Unverified" — why, and fix by attributing agent
  commits to Arpit's account.
- **Did:** diagnosed via the commits API: commits were already GPG-signed with
  Arpit's own key (`E38B58D8FDEF7698`), but the committer email
  `claude-code@fux.local` belongs to no GitHub account → `reason: no_user`.
  Fix (empirically converged): the noreply address gave `bad_email` — GitHub
  also requires the committer email to appear in the signing key's identities —
  so repo-local `user.email` is now `arpitarya.dev@gmail.com` (the key's UID,
  verified on the account). Live result on this very commit:
  `verified: true, reason: valid`, attributed to `arpitarya`, author name still
  `Claude (agent)`, `Co-Authored-By: Claude` trailer intact — the agent trail
  survives in metadata while GitHub verifies against Arpit's key.
- **Decided / open:** nothing open — future agent commits in this repo are
  Verified. (Historic commits keep their badge; rewriting history for a badge
  is not worth it.)
- **Next:** merge this PR; Anton dogfood continues.

## 2026-07-21 — v0.22.1 published; scheduled protection audit removed · Claude Code
- **Asked:** (1) what is audit-protection.yml, is it needed? (2) remove it.
- **Did:** explained it (weekly drift alarm comparing live branch protection vs
  `.github/branch-protection.json`; fails loudly, needed an admin PAT secret that
  was never set). **Removed the workflow** at Arpit's call — the wall itself is
  untouched (required checks + enforce_admins verified live); the JSON source of
  truth + `scripts/audit-branch-protection.sh` / `apply-branch-protection.sh`
  stay for manual audits (`./scripts/audit-branch-protection.sh arpitarya fux
  main`). Also this exchange: **v0.22.1 released and verified on PyPI** — wheel
  6.98 MB, sdist now 133 files with zero old-build/CI leaks (the 0.22.0 sdist
  had shipped `archive/`); publish ran with the new tag↔version guard.
- **Decided / open:** no scheduled tamper alarm on the wall anymore — re-add the
  workflow + a `BRANCH_PROTECTION_TOKEN` PAT if that guarantee is ever wanted back.
- **Next:** Anton dogfood.

## 2026-07-21 — M4+M5 reviewed; three rulings for the run-in · Cowork
- **Asked:** agent reported M4 (kernel re-plumb, six goldens byte-parity) + M5
  (FuxVec: hybrid+dense_global **0.810/1.000/0.873** vs v0.22's
  0.762/0.952/0.833; ADR 0006's named zero-overlap miss now retrieved;
  --lexical-only exactly preserved). Asked for the next-step prompt.
- **Rulings (Arpit via Cowork):** (1) **integer token-sums df header approved**
  — better than the spec'd averages (exact round-trip; avg_wlen recomputable
  for any weights without re-ingest); record as approved amendment in ADR 0008.
  (2) **Early-return judgment call approved** — correct reading of ADR 0006
  (rescue = doc-side zero overlap, via the third RRF list; noise floor
  0.23–0.26 vs 0.34 doesn't separate); record in ADR 0010 with those numbers.
  (3) **Budget risk: measure at M8 before optimizing** — if the synthetic 100k
  confirms >30 MB, apply per-bucket zlib first (simpler, no dictionary artifact
  to version), shared dict only if that misses; honest numbers either way.
- **Next:** continuation prompt → M6 (PPR-lite) → M7 → M8 → close-out at 0.23.0.

## 2026-07-21 — M3 escalation resolved: exact df sidecar, guarantee stays provable · Cowork
- **Asked:** the building agent escalated (correctly, per the no-silent-deviation
  rule): lean-profile BM25F can't be *provably* identical to full without exact
  corpus df — soften DoD 7 to eval-top-k, or grow the state plane?
- **Did (Arpit's call, via Cowork):** **grow the state — `state/df/XX.bin`
  sidecar** (delta-encoded term-hashes + varint df + corpus-stats header,
  ~2–5 MB @100k; incremental per-doc maintenance). DoD 7 *strengthened*:
  provably identical by construction (exact df sidecar + exact re-derived tf),
  asserted by full-corpus comparison on fixtures + eval as belt. Rationale:
  "identical rankings" is the brand promise (deterministic/compliance-grade) —
  softening converts a proof into an eval-shaped empirical claim. State
  envelope @100k: ~25–30 MB (still in Arpit's "around 10–20" band). Handoff
  format C + DoD 7 amended; proposal size table noted. Build state per the
  agent: M1–M3 done (uncommitted, suites green), M4–M8 pending, version 0.22.1.
- **Decided / open:** df sidecar in; continuation prompt handed to Arpit.
- **Next:** paste the continuation prompt into the running Claude Code session.

## 2026-07-21 — Milestone tracking law: pre-register + update every milestone · Cowork
- **Asked:** update the implementation file on every milestone, and put that in
  CLAUDE.md so it applies to every plan.
- **Did:** **Phase-4 table pre-registered** in `implementation.md` (M1–M8 +
  close-out, all ⬜, with the pre-registration note); "Now working on" updated.
  CLAUDE.md 4b split into its two binding halves: (1) every plan/handoff
  **pre-registers** its milestone table in implementation.md in the same change;
  (2) building agents update the row **at every single milestone completion**
  (status + tests + note — per milestone, never batched at phase end). The 0004
  prompt aligned: table already pre-registered, per-milestone updates binding.
- **Decided / open:** standing law for all future plans.
- **Next:** paste the 0004 prompt into Claude Code.

## 2026-07-21 — Proposal FINALIZED; plan + handoff 0004 + prompt written · Cowork
- **Asked:** finalize the proposal; create the plan, handoff, and prompt in as
  much detail as possible.
- **Did:** `proposals/knowledge-substrate.md` → **status: accepted** (graduated
  per lifecycle; header links the build spec). fux-plan: 0004 row added to the
  build queue (v3 — substrate; target v0.23.0, ADRs 0008–0011); §8 next-move
  rewritten. Wrote **`handoff/0004-knowledge-substrate-handoff.md`** — the
  build contract with normative specs: fux.db schema v2 (10 tables, WAL,
  single-writer lock, canonical ordering, citation-stable chunk ids), fux.lock
  format + staleness semantics, `.fux/state/` byte layouts (FUXSTATE1 magic,
  256 hash buckets, Bloom k=4 ~1 % FPR ≤128 B), FuxVec algorithm (quantize →
  Hamming top-500 fixed tie-breaks → exact rerank; IVF only if M8 shows
  >150 ms), kernel `retrieve()`/ResultGraph + PPR-lite constants (damping .85,
  3 iters, EXTRACTED 1.0/INFERRED 0.6, decay .8), CLI additions
  (explain/graph/path/cat/db pull), profiles incl. lean LRU; **M1–M8
  milestones** each with scope, plus DoD (8 phase-level criteria incl. v0.22
  golden byte-parity and the eval gate with zero-candidate rescue), 17 edge
  cases, 4 open questions routed to ADRs, close-out contract. Wrote the
  paste-ready **0004 prompt** (explore order, hard rules — parity sacred, math
  untouchable, cli-examples-before-renderers — verify gates, stop-clean
  semantics). Registry bumped.
- **Decided / open:** phase 4 fully specced. Nothing open in design.
- **Next:** paste `handoff/0004-knowledge-substrate-prompt.md` into Claude Code.

## 2026-07-21 — Git carries the state (committed lean plane) · Cowork
- **Asked:** git should carry the state — and it should be maintained.
- **Did:** the lean profile made this viable (~200 B/doc), so `.fux/state/` is
  now **committed, versioned state**: sharded by doc-id hash into 256 buckets
  (codes/sigs/meta, ~80 KB each @100k) so commits touching 50 docs change a few
  buckets, not a 20 MB blob; deterministic bytes = zero diff noise. What it
  buys: `git clone` → **instantly queryable** at doc level; `git log
  .fux/state/` = history of what the corpus knew; `git checkout <rev> && fux
  ask` = time-travel for free. **Maintained, enforced:** ingest rewrites
  state + lock atomically; session-end hook prompts the commit; CI's
  `--check --strict` becomes a **three-way state ↔ lock ↔ sources** gate —
  stale committed state fails the build. Honest limits: binary state (humans
  diff the lock), history growth (sharded deltas; high-churn/100k+ tiers switch
  to db-pull artifacts). §8 table, §8c subsection, §8e summary, appendix tree,
  M2 milestone all updated; gitignore narrows to `.fux/index/`.
- **Decided / open:** state-in-git folded into the ⏳ proposal.
- **Next:** Arpit's verdict → handoff 0004.

## 2026-07-21 — Lean profile: 100k docs in ~20 MB · Cowork
- **Asked:** can 100k docs land at ~10–20 MB total? Be creative; build from
  scratch if needed.
- **Did:** yes — by flipping the storage assumption. Entropy forbids compressing
  600 MB of text to 20 MB, but **determinism means Fux need not store text at
  all: sources are the storage; the index stores find + verify + re-derive**
  (deterministic converters + fux.lock shas reproduce exact bytes on demand).
  New §8c "lean profile" in the substrate proposal: **~200 B/doc persistent
  plane** — 32 B FuxVec code + 96–128 B **Bloom term signature** (validated by
  BitFunnel, Bing's production signature index, SIGIR'17 — fresh citation
  pulled) + ~50 B metadata → **100k ≈ 18–21 MB ✓**, 1M ≈ 200 MB. Query path:
  dense scan + signature prefilter → top ~50 docs → re-derive text → exact
  chunk BM25F/rerank (false positives only add candidates — rankings identical
  to full profile, eval-proven); bounded LRU keeps hot docs warm. Honest
  trades: cold-doc re-conversion latency; source availability at query time
  (web tiers may prefer full profile). Config `[index] profile = full|lean|
  auto`. Section renumbering fixed (8c lean, 8e fresh-clone summary);
  BitFunnel added to references.
- **Decided / open:** lean profile added to the ⏳ proposal; fits M5/M8.
- **Next:** Arpit's verdict on the proposal → handoff 0004.

## 2026-07-21 — Substrate proposal hardened: git contract, fux.lock, sizes, gaps · Cowork
- **Asked:** (1) exact git-committed file set — clone must rebuild from scratch;
  (2) a separate sources file with hash/date for staleness; (3) .fux size
  estimates at 1k/10k/100k/1M docs; (4) graphify as reference, not benchmark;
  (5) review the doc for gaps.
- **Did:** rewrote §8 as **the git contract** — invariant "clone rebuilds from
  scratch"; committed set = fux.toml + **fux.lock** + @lists + agent files;
  `.fux/` fully gitignored (curated-cache commit demoted to opt-in
  `[git] commit_cache` — the invariant outranks the diffs bet). New **§8a
  fux.lock**: committed root-level sorted-JSONL ledger (file kind: sha/bytes/
  converted_at/fidelity; url kind: sha/fetched_at/**max_age_days**) — staleness
  is structural (files by sha, web by age), `--check` works lock-only right
  after clone; replaces manifest.jsonl. New **§8b size envelope** with stated
  assumptions (~15 KB/doc bulk): 1k ≈ 15 MB · 10k ≈ 145 MB · 100k ≈ 1.4 GB ·
  1M ≈ 14 GB (text+postings dominate; vectors+codes <11 % — semantic is nearly
  free; lock sharding option >100k). §2 + references reworded: **graphify =
  prior art to learn from, never a benchmark**. New **§12 gaps review**, each
  resolved or ⚠ flagged: WAL concurrency, corruption=rebuild, chunk-id/citation
  stability, schema versioning, own-postings-vs-FTS5 made explicit, streaming
  ingest, ⚠ multi-corpus fan-out (federation's first requirement),
  ⚠ at-rest encryption deferred, db-pull auth v1, Windows/AV notes, relational
  eval pairs for graph/path. Appendix tree + M1 milestone aligned to the lock.
- **Decided / open:** proposal hardened; still one ⏳ awaiting Arpit's verdict.
- **Next:** Arpit's verdict → handoff 0004.

## 2026-07-21 — One proposal: knowledge-substrate.md (substrate + FuxVec) · Cowork
- **Asked:** merge the knowledge-substrate compare doc and the FuxVec proposal
  into ONE proposal with details on the approach.
- **Did:** created **`proposals/knowledge-substrate.md`** — the single
  consolidated post-v0.22 proposal, 11 sections: context (enterprise litmus),
  break analysis, SQLite store schema (incl. bulk `docs_text` + `codes`), the
  graph (deterministic + semantic edge tiers), the one-kernel/six-projections
  table, **FuxVec as §6 with the four-step approach detailed** (sign-quantize →
  big-int XOR/bit_count full scan → exact int8 rerank → deterministic IVF;
  storage verdicts incl. Parquet-as-export; standalone-package note; honest
  limits), source spec, git tiers + fresh-clone/db-pull story, enterprise
  inputs, the full sample-repo/CLI appendix (ask/answer/cat/explain/path with
  FuxVec + graph lines in --explain), and **§11 build sequencing** (handoff 0004
  milestones M1–M8, eval-gated). Deleted `compare/knowledge-substrate.compare.md`
  + `proposals/fuxvec.md`; repointed all links (compare README, proposals
  README, fux-plan, fux-toml ×2, cli-examples).
- **Decided / open:** one ⏳ document now carries the entire next phase.
- **Next:** Arpit's verdict on `proposals/knowledge-substrate.md` → handoff 0004.

## 2026-07-21 — Fresh-clone story, FuxVec proposal, answer example · Cowork
- **Asked:** (1) gitignored warehouse — what happens on a fresh clone? (2) build
  a vector db from scratch on JSON/Parquet as a package concept — push
  boundaries; (3) add a `fux answer` example.
- **Did:** substrate doc gained **"Fresh clone"** section — curated tier works
  immediately (cache is committed); bulk-local re-ingests to a byte-identical,
  manifest-verified warehouse; bulk-web either re-crawls (drift visible per doc)
  or uses the enterprise path: **warehouse as CI build artifact** + proposed
  `fux db pull` (download + sha-verify vs committed manifest — the lockfile/
  restore pattern). Wrote **`proposals/fuxvec.md`**: vector-db concept from
  scratch — sign-quantize 256-dim int8 → 256-bit codes (32 MB per 1M chunks),
  full-corpus scan via XOR + `int.bit_count()` (C-speed big-int popcount;
  ~tens of ms at 100k), exact int8 rerank of top ~500, deterministic IVF above
  ~100k, storage = packed shards/SQLite BLOBs (JSON for manifest/centroids;
  **Parquet = opt-in export extra** for DuckDB/Spark interop — pyarrow can't be
  a runtime dep); unlocks `dense_global` seeds → rescues ADR 0006's
  zero-candidate miss class; standalone `fuxvec` package noted as its own
  wedge. Substrate §3 vector-DB verdict updated ("adopting closed; building the
  concept proposed"); §8 gained the `fux answer` example (bulk logical-id +
  local file:line citations, graph-hop note). *Web quota blocked fresh cites —
  binary-quantization numbers flagged for build-time verification.*
- **Decided / open:** FuxVec = milestone inside the substrate handoff, eval-
  gated; `db pull` = proposed command. Substrate verdict still awaits Arpit.
- **Next:** Arpit's verdict on knowledge-substrate.compare.md → handoff 0004.

## 2026-07-21 — Litmus change: enterprise mega-project, not Anton · Cowork
- **Asked:** stop thinking of this project in reference to Anton; think from the
  point of a very large-scale project in corporations.
- **Did:** replaced the Anton litmus in CLAUDE.md with the **enterprise
  mega-project litmus** (scale is the default; enterprise realities are design
  inputs; the laws are the sales story: $0 = auditable supply chain, offline =
  no data egress, deterministic = compliance-grade). fux-plan §6a re-scoped
  (substrate = default forward path; standing proposals gain weight).
  knowledge-substrate doc: build trigger re-scoped (corporate corpora *start*
  past the breakpoint — substrate is the next phase, not a contingency) + new
  **"Enterprise design inputs"** section (proxy/SSO ingest, Windows fleets,
  air-gapped installs, corpus-per-boundary access model, audit priority).
  model-handoff-interview: direction-change Q&A added. Anton demoted to
  convenient small-scale testbed.
- **Decided / open:** litmus changed ✅. Substrate verdict still awaits Arpit's
  formal call, but its sequencing is now "next phase by default."
- **Next:** Arpit's verdict on knowledge-substrate.compare.md → handoff → build.

## 2026-07-21 — Documentation-style rule added to CLAUDE.md · Cowork
- **Asked:** add to CLAUDE.md — no large paragraphs in documents; split into
  points; make them roomier.
- **Did:** new **"Documentation style (required)"** section in CLAUDE.md, placed
  before the docs law: short points (one idea each), 3–4-line paragraph cap,
  blank lines between points/sections, tables for comparisons, takeaway-first
  bullets, and a fix-on-contact clause (splitting an existing wall of text is
  part of touching the doc — form is covered by the same staleness law as facts).
- **Decided / open:** binding for all future doc writing in the repo.
- **Next:** Anton dogfood (unchanged).

## 2026-07-21 — Correction accepted: bulk text lives IN the db, not as files · Cowork
- **Asked:** "saving 100k documents in cache is impractical — try to understand."
- **Did:** understood and fixed the real point — the previous tier design still
  put bulk text in a *gitignored file mirror*; but 100k files are impractical
  **as files** (walks, inodes, deletes, Windows/AV/sync), git or no git. Substrate
  doc corrected end to end: storage verdict is now **tier-dependent** — curated
  tier keeps per-file Markdown (review/git value at 10²–10⁴ docs); **bulk tier
  has no file cache at all** — converted text = `docs_text` rows in fux.db (one
  file on disk at any corpus size; SQLite reads small blobs ~35 % faster than
  the filesystem per its own benchmark). New `fux cat <doc>` materializes any
  single doc on demand; bulk citations use logical id + heading (no fabricated
  file paths); break-analysis row corrected (cache breaks at ~10⁴ *as files*);
  §7 tier table + §8 tree/CLI reworked ("never 100k files — your curated files
  plus one database"). CLAUDE.md + fux-plan tier language corrected to match.
- **Decided / open:** correction folded into the ⏳ substrate verdict (still
  awaiting Arpit's overall call on the doc).
- **Next:** Anton dogfood.

## 2026-07-21 — Consolidated into knowledge-substrate.compare.md · Cowork
- **Asked:** merge corpus-at-scale + document-knowledge-graph into ONE doc; show
  sample CLI + folder structure for the implemented substrate.
- **Did:** created **`compare/knowledge-substrate.compare.md`** — the single
  design of record for post-v0.22 architecture: verdict block with four decisions
  (SQLite substrate; doc-index-IS-the-graph; one kernel/six projections; git
  tiers), break analysis, prior-art (graphify/vector-DBs) condensed, source-spec
  extensions, research references, open build items — plus **§8 appendix**: the
  implemented-substrate walkthrough (fux.toml with globs/@lists/mirror tier;
  repo tree showing curated-committed vs mirror-gitignored vs one fux.db;
  worked CLI: resumable `--web` crawl, `ask` rescued via graph hop, `explain`
  node view, `path` with reliability + EXTRACTED tag, the new `--explain` graph
  line). Deleted the two superseded docs; fixed every live link (compare README,
  proposals README — graph marked *graduated*, fux-toml ×2, fux-plan,
  cli-examples). Worklog history left intact.
- **Decided / open:** one doc now carries the whole ⏳ decision; trigger
  unchanged (Anton: scale pain or relational questions).
- **Next:** Anton dogfood.

## 2026-07-21 — One kernel, six projections; sample-repo walkthrough · Cowork
- **Asked:** difference between ask/graph and explain/path — do they need to be
  separate, can one algorithm serve them? Plus: CLI usage + dir-structure examples
  for a sample repo.
- **Did:** researched PathRAG (AAAI'25: node-retrieval → flow-pruned paths with
  reliability scores → answers as ONE pipeline; paths are scored *byproducts*) and
  GraphRAG local search (entity-seeded = query-by-node). Designed the **unified
  kernel**: `retrieve(seed: text|node) → ResultGraph {seeds, expansion, paths,
  passages}`; all six verbs become projections (ask=passages, find=seeds,
  answer=synthesis, explain=node-seeded deep view, graph=nodes+edges, path=paths
  slice). Key insights recorded: `explain` is `ask` seeded by a node; **paths are
  retrieval provenance the PPR expansion already computes** — not a feature, a
  kept trail; `--explain` and `fux path` converge into one trust story. Written
  into corpus-at-scale §"One kernel, six projections" (engine implements one
  kernel + thin renderers; friendly verbs stay). Added **"A sample repo, end to
  end"** to cli-examples.md: acme-payments tree before/after, commit-vs-gitignore
  split per tier, human + agent daily flows, substrate-v2 era marked as proposed.
- **Decided / open:** one-kernel design folded into the substrate-v2 proposal;
  trigger unchanged.
- **Next:** Anton dogfood.

## 2026-07-21 — The merge: graph + corpus-at-scale = one knowledge substrate · Cowork
- **Asked:** is there an opportunity to merge the graph and corpus-at-scale?
  Creative, outside the box, with research.
- **Did:** found the unifying insight — **the level-1 doc index IS the graph's
  node table** (a doc entry's payload = a node's payload; the thin layer was the
  graph unrecognized). Designed "one substrate": single SQLite-v2 file with
  nodes/edges/chunks/postings/vectors; `ask`/`explain`/`graph`/`path` are three
  surfaces over the same tables; retrieval becomes seed (BM25F+dense on docs) →
  **deterministic PPR-lite expansion over edges** (multi-hop recall, zero model
  calls — the natural rescue for ADR 0006's zero-lexical-candidate miss class) →
  per-doc chunk detail → RRF with graph as third signal. Research validation:
  HippoRAG/LightRAG (PPR-from-seeds, 10–30× cheaper multi-hop; *operators beat
  structure* — cheap deterministic edges suffice), LazyGraphRAG (0.1 % indexing
  cost — defer expensive enrichment, exactly our host-session pattern),
  LiteSemRAG (LLM-free graph retrieval is a recognized lane). Bonus surfaces:
  community-detection → auto corpus map (OKF progressive disclosure, generated);
  `--explain` traversal lines; eval-gated. Written into
  `corpus-at-scale.compare.md` §"The merge"; graph proposal updated to point
  there. Two ⏳ items are now one "knowledge substrate v2" phase.
- **Decided / open:** merge proposed + recommended; trigger unchanged (Anton
  dogfood: scale pain *or* relational questions) → then compare verdict →
  handoff → ADR.
- **Next:** Anton dogfood — now the single gate for the substrate phase.

## 2026-07-21 — Document-knowledge-graph proposal parked · Cowork
- **Asked:** "how about creating a knowledge graph on all these documents — just
  a thought."
- **Did:** wrote `proposals/document-knowledge-graph.md` — the sanctioned vehicle,
  since CLAUDE.md bars graph resurrection without sign-off. Shape: a **document
  graph, not a code graph**, strictly a **derived view over the corpus**. Nodes =
  docs/URLs/tags (+ host-session concept nodes); edges in two tiers mirroring
  ingest — deterministic ($0: markdown `references`, citations, web
  `crawled_from` parent/depth, shared tags) and semantic (host-session skill,
  frontmatter-reviewable). Storage = SQLite-v2 rows (never a 512 MiB blob —
  graphify's ceiling). Surface: `fux graph` (neighborhood), `fux path` (how two
  docs connect), `fux explain` gains Links. Parked with a concrete graduation
  trigger: Anton dogfood surfaces a connects/depends/cites-shaped question that
  ask/answer handles poorly → graduates to a compare doc + ADR.
- **Decided / open:** parked, status: proposed. Nothing else open.
- **Next:** Anton dogfood (unchanged — and it's also this proposal's trigger).

## 2026-07-21 — Four course corrections from Arpit (purpose, $0 semantics, tiers, thin index) · Cowork
- **Asked:** (1) host-session LLM pass keeps fux $0; (2) the point is agents
  querying docs/links via Copilot/Claude extensions, not code; (3) vector-DB idea
  reframed — a thin layer over a *document* index with a drill-down command like
  `fux explain`; (4) millions of cache files in git is the wrong approach.
- **Did:** recorded all four in `corpus-at-scale.compare.md` §"Arpit's
  amendments": host-session semantic pass accepted as $0-legal (the old build's
  proven skill-token pattern — authoring may be model-assisted, checking/retrieval
  stay deterministic); docs-not-code focus accepted (sharpens wedge vs graphify;
  new fux-plan §6a); **two-level retrieval proposed + recommended** — compact
  doc-level index (entry + one vector per doc; 100k chunks → ~5k entries,
  brute-force viable forever, no ANN) routing to per-doc chunk loads, plus new
  `fux explain <doc>` drill-down verb; **git-tier correction accepted** — commit
  the *curated* corpus (10²–10⁴ files), gitignore bulk mirrors, commit
  fux.toml+manifest as the reproducible recipe ("git stores the recipe, not the
  warehouse"). CLAUDE.md purpose+tier folds; fux-plan §6a/§6b amended.
- **Decided / open:** 1, 2, 4 accepted; 3 recommended, folds into the SQLite-v2
  build when the scale trigger fires (`fux explain` can ship earlier as UX).
- **Next:** Anton dogfood on the shipped engine; scale work waits for its trigger.

## 2026-07-21 — Prior art: Graphify reviewed in full; vector-DB question closed · Cowork
- **Asked:** research how Graphify's index works; what about vector-DB-alikes?
- **Did:** read the full Graphify README (91.8k★, YC S26): it's a **knowledge
  graph, explicitly not a vector index** — tree-sitter AST locally for code (no
  LLM), an **LLM semantic pass for docs/media** (breaks Fux's $0 law), one
  graph.json (512 MiB cap — same single-blob pattern as our index.json, validating
  the SQLite-v2 proposal), Leiden communities, query/path/explain traversal, MCP,
  query-first hooks, committed graphify-out/ with a union-merge driver. Strategic
  note recorded: graphify ≈ the *archived* Fux build's graph layer, now
  market-validated — if the graph returns it's a view over the corpus. Vector DBs
  (LanceDB/Chroma/FAISS/sqlite-vec/ANN libs): all third-party runtime deps, and
  **ANN solves a problem Fux architected away** (candidates-first = ~200 exact dot
  products; nothing to approximate). Recorded escalation ladder for the
  zero-lexical-candidate miss class: SQLite-v2 brute-force → opt-in ANN extra.
  Both analyses added to `corpus-at-scale.compare.md` with references.
- **Decided / open:** no vector DB (closed with reasoning + reopen path); SQLite-v2
  proposal reinforced. Corpus-at-scale verdicts still ⏳ Arpit.
- **Next:** Arpit calls corpus-at-scale; Anton dogfood continues.

## 2026-07-21 — Scale review: corpus-at-scale compare + fux.toml reference · Cowork
- **Asked:** explain vectors.bin / index.json; is the cache scalable (thousands of
  files, millions of links)?; create + maintain a fux.toml example; sources could
  be folders/files/links at huge scale. Research it.
- **Did:** read the shipped store code (index.json = versioned JSON, full-load,
  postings derived in memory — ADR 0003; vectors.bin = single packed int8
  chunk-vector cache, (sha,fidelity)-keyed — ADR 0006). Researched scale paths:
  **stdlib `sqlite3`** (FTS5 ~3M rows/hr, snappy at 10k–100k docs; sqlite-vec
  brute-force numbers; Fux's dense pass is candidate-only so vectors don't
  bottleneck). Wrote `compare/corpus-at-scale.compare.md`: component-by-component
  break analysis (index.json breaks first ~25–50k chunks; the *cache* itself
  scales with sources and stays per-file Markdown forever — it's the product);
  proposed verdicts — index format v2 = single SQLite db (Fux's scorer unchanged,
  storage only; frontier solves million-link crawls) + `[sources]` globs/excludes,
  first-class files, `@list` files. Created maintained `fux-toml.md` (every
  shipped key + default from config.py; proposed extensions fenced). Registry +
  index + compare README synced.
- **Decided / open:** both scale verdicts ⏳ awaiting Arpit; build trigger = ~25k
  chunks or an outsized crawl.
- **Next:** Arpit reads corpus-at-scale; meanwhile Anton dogfood proceeds on the
  shipped formats (they're right-sized for it).

## 2026-07-21 — README upgraded to the old build's story-first format · Cowork
- **Asked:** review the README and upgrade it, referencing the older README's
  format.
- **Did:** rebuilt README.md on `archive/README.md`'s skeleton — tagline
  blockquote + badges, **The story** (the red-pipe narrative evolved for the
  query engine: the note exists, it's the *finding* that fails), **See it** (real
  as-shipped `fux ask`/`fux answer` output from cli-examples.md), Quickstart,
  ELI5, **Why it's different** (properties: deterministic, cited-or-didn't-happen,
  hybrid-offline, $0, agent-native, corpus-not-index), **How it works** (pipeline
  diagram + two-tier ingest + fenced web/CDP), collapsible full command surface,
  **The $0 guarantee** with honest limits (no synthesis, English-biased model,
  eval tie disclosed w/ ADR 0006 link), **The name** (kept; notes the rule-engine
  vision on hold), Status, closing CTA. Everything claims only shipped v0.22.x
  behaviour. Registry row bumped.
- **Decided / open:** nothing open.
- **Next:** Anton dogfood.

## 2026-07-21 — GLOSSARY.md rename + ALL-CAPS-no-frontmatter convention · Cowork
- **Asked:** rename glossary.md → GLOSSARY.md; ALL-CAPS markdown files need no
  YAML frontmatter.
- **Did:** renamed to [`GLOSSARY.md`](GLOSSARY.md) and stripped its frontmatter;
  stripped DOC-REGISTRY.md's frontmatter too (same rule); recorded the convention
  in CLAUDE.md §OKF (ALL-CAPS docs = entry-point files, exempt from `type` like
  CLAUDE.md/README.md; lowercase docs conform as before) and in the glossary's
  own Frontmatter entry; updated links in bundle index + registry row.
- **Decided / open:** convention adopted. Nothing open.
- **Next:** Anton dogfood (per the completed master run's close-out).

## 2026-07-21 — Pipeline review: sdist hygiene, publish guard, build-check → v0.22.1 · Claude Code
- **Asked:** review the pipeline with the new changes — is everything needed?
- **Did (review findings, all fixed except one):** (1) the 0.22.0 **sdist shipped
  the archived old build** (2.43 MB `archive/`) + `uv.lock` + `.github` — added
  hatch sdist excludes + a CI assertion that the sdist stays clean (root-level
  `archive/` only; `docs/archive/` is intended content); (2) **publish.yml had a
  silent-failure mode** — unbumped `__version__` + `skip-existing: true` = green
  no-op publish — added a tag↔version guard + `twine check --strict`, and scoped
  `id-token: write` to the publish job only; (3) restored the old CI's
  **build-check job** (`python -m build` + `twine check`) so metadata bugs fail
  PRs, not releases; added PR concurrency cancellation; `.DS_Store` gitignored.
  Bumped to **v0.22.1** so the corrected sdist is the published one.
- **Needs Arpit:** the `BRANCH_PROTECTION_TOKEN` secret is **missing** — the
  weekly protection audit will fail loudly (default GITHUB_TOKEN can't read
  protection). Create an admin-scoped PAT and `gh secret set BRANCH_PROTECTION_TOKEN`.
- **Next:** merge via the wall, release v0.22.1, verify the sdist on PyPI.

## 2026-07-21 — Release pipeline restored + v0.22.0 published via the wall · Claude Code
- **Asked:** push and publish the new package; create the pipeline and always
  publish it the right way.
- **Did:** ported the merge wall's CI to the rebuild — `.github/workflows/ci.yml`
  with the two required contexts: **"fux gate"** (both suites: determinism,
  goldens, eval gate, packaging budgets) and **"ai-review"** (new
  `scripts/ai-review.sh`: separation-of-duties refusal, $0-law probe on
  pyproject dependencies, credential probe on the diff, suites on the merge
  result — deterministic, model-free, per the old script's design) + a 3.11–3.13
  matrix job. Restored `publish.yml` (release → OIDC trusted publishing, `pypi`
  environment) and `audit-protection.yml` + `branch-protection.json` (note
  refreshed) + audit/apply scripts unchanged. README install now `pip install
  fux-engine`. Release path: PR through the protected branch → checks green →
  merge → GitHub release v0.22.0 → publish workflow → PyPI.
- **Decided / open:** the rebuild's "fux gate" IS the test suites until the rule
  engine returns; the wall itself (contexts, enforce_admins) is unchanged.
- **Next:** Anton dogfood (`pip install fux-engine` now works there).

## 2026-07-21 — MASTER RUN COMPLETE: all three phases shipped (v0.22.0) · Claude Code
- **Asked:** the 0000 master prompt — 0001 → 0002 → 0003 with hard gates; this is
  the final close-out entry.
- **Did:** all three phases implemented, gated, and archived in one run:
  **v1** query CLI (v0.20.0, ADRs 0001–0004), **v1.1** web/CDP/advanced ingest
  (v0.21.0, ADR 0005), **v2** hybrid engine (v0.22.0, ADRs 0006–0007).
  Full-suite final run: `tests/` **173 passed** · `tests_e2e/` **29 passed +
  1 gated skip** (office-with-extra) · eval gate green. README tells the whole
  story (install → setup → ingest → ask/find/answer → agent integration →
  corpus-in-git); 0000 master prompt archived `status: implemented`;
  DOGFOOD.md live for Anton.
- **Decided / open:** hybrid ships **enabled** (gate passed as a tie on the
  fixture set — honest reading + rank-level rescues in ADR 0006); vectors are
  derived data (gitignore-able; corpus = cache + manifest); every open question
  in the three handoffs is resolved and recorded in its ADR.
- **Next:** dogfood in Anton (DOGFOOD.md): configure, ingest, live with
  `fux ask`, build the private Anton eval pairs — those numbers pick what gets
  built next (reopen triggers live in the compare docs).

## 2026-07-21 — PHASE 3 REPORT: Hybrid engine v2 shipped (v0.22.0) · Claude Code
- **Asked:** master run, phase 3 — execute handoff 0003 (eval-first hybrid v2).
- **Did (shipped):** eval harness (21 committed Q→passage pairs incl. deliberate
  zero-overlap paraphrases; hit@1/hit@5/MRR; `--project/--pairs` for private
  Anton evals); `tools/distill/` (potion-base-8M → int8 per-vector → packed
  7.93 MB `model.bin`, sha-pinned, MIT license-checked, recipe documented);
  `fux.embed` stdlib runtime (BertNormalizer+WordPiece with exact token-id
  parity, mean-pool folded into the scale, exact int8 cosine, lazy 10 ms load);
  `.fux/index/vectors.bin` chunk-vector cache ((sha, fidelity)-keyed reuse);
  RRF fusion (k=60) over BM25F candidates with full per-result hybrid detail;
  `--lexical-only` byte-parity with v1 proven by unchanged pre-v2 goldens;
  answer question-similarity factor; wheel ships the bundle (6.98 MB ≤ 15 MB).
- **Eval (the gate, in ADR 0006):** lexical 0.762/0.952/0.833 vs hybrid
  0.762/0.952/0.833 — a tie satisfies the ≥ gate → hybrid enabled. Rank-level
  paraphrase rescues observed; the one remaining miss has zero lexical
  candidates (the recorded candidate-only trade). Warm hybrid query 0.2 ms.
- **Decided / open (ADRs 0006–0007):** re-packed potion over distill-our-own
  (no in-domain corpus yet — Anton's is the reopen trigger); single vector
  file over shards; vectors gitignore-able as derived data. Open risks:
  English-biased model (non-English degrades toward lexical); zero-candidate
  documents unreachable by dense (by design, measured).
- **Next:** final master close-out (full suites, README story, archive 0000).

## 2026-07-21 — PHASE 2 REPORT: Ingest v1.1 shipped (v0.21.0) · Claude Code
- **Asked:** master run, phase 2 — execute handoff 0002 (web, CDP, advanced tier).
- **Did (shipped):** stdlib `html.parser` HTML→Markdown converter (deterministic;
  link/title extraction); `[sources.web]` config + fenced crawl — urllib fetcher
  (UA/timeouts/retries/size cap/redirect-final-URL), robots.txt obeyed, BFS
  frontier with depth/budget/domain caps + URL and sha dedupe (dual provenance),
  attachments through the 0001 converters, `url`/`parent`/`depth`/`fetched_at`
  provenance, byte-stable re-crawl of unchanged pages, web entries persist across
  local-only runs and are excluded from `--check`; hand-rolled RFC 6455 WebSocket
  client (RFC-vector + fake-server tested) + minimal CDP capture (existing Chrome
  only, settle delay, actionable errors, websocket-client extra as flagged
  fallback) + `manual_cdp_smoke.py`; advanced tier `fux ingest --advanced` —
  Docling/tesseract upgrades, (sha, fidelity)-keyed index reuse, upgrades survive
  re-ingest and reset when the source changes; AGENTS contract + fux-ingest skill
  teach judge-and-upgrade; import-fence test (query/index can never touch network
  modules). ADR 0005; 0002 pair archived; README/plan/registry/cli-examples/
  interview updated; v0.21.0.
- **Test counts:** `tests/` 154 passed · `tests_e2e/` 24 passed + 1 gated skip,
  incl. fixture-site crawl (robots/oversize/off-domain skips surfaced).
- **Decided / open (in ADR 0005):** hand-rolled HTML→MD as the always-present
  default (open Q1); CDP settle = fixed configurable delay, networkIdle deferred
  to dogfood evidence (open Q2); crawl resumability deferred (open Q3).
  **Open risks carried:** rendered capture depends on local Chrome; changed-page
  re-ingests are not byte-reproducible (inherent to network sources); HTML
  converter is good-enough, not pandoc.
- **Next:** Phase 3 — execute `handoff/0003-hybrid-engine-v2-prompt.md`.

## 2026-07-21 — PHASE 1 REPORT: Query CLI v1 shipped (v0.20.0) · Claude Code
- **Asked:** master prompt 0000 — execute handoffs 0001 → 0002 → 0003 in sequence
  with hard phase gates. This entry is the phase-1 gate report.
- **Did (shipped):** the complete v1 surface per handoff 0001 — `fux setup`
  (wizard + full flags + `-y`, idempotent TOML merge), hand-rolled frontmatter
  parser (subset YAML, permissive, unknown keys round-trip), inferred-tier ingest
  (md/txt/code/json/yaml/image-stub; office via the `[ingest]` extra) → OKF cache
  with provenance + per-dir index.md + canonical manifest.jsonl +
  `--check`/`--strict`/`--list-inferred`/`--list-skipped`, heading chunker
  (256–512 words, fences/tables atomic, source line spans), true BM25F
  (weight-then-saturate; JSON index, incremental by sha), `fux ask`/`find`/
  `answer` per the cli-examples.md contract (+ `--json`/`--explain`/`--top`/
  `-C`/`--answer-max`; extractive TextRank answers with `[n]` citations),
  `fux setup --agents --skills --hooks` (AGENTS.md managed block + CLAUDE.md/
  copilot/Kiro pointers, fux-query/fux-ingest SKILL.md, fail-open hooks).
  ADRs 0001–0004; 0001 pair archived (`status: implemented`); README rewritten;
  DOGFOOD.md emitted (master rule 6); version 0.20.0.
- **Test counts:** `tests/` 108 passed · `tests_e2e/` 20 passed + 1 gated skip
  (office-with-extra). Byte-identical determinism proven for double-ingest AND
  fresh re-ingest; goldens normalized (3 dp, volatile keys stripped), updated
  only via `FUX_UPDATE_GOLDENS=1`.
- **Decided / open:** `converted_at` = SOURCE_DATE_EPOCH/source-mtime, never wall
  clock (determinism outranks the spec's letter — Deviations + ADR 0002); index
  format JSON by measurement (16 ms load @5k chunks; postings build 525 ms
  dominates — escape hatch: persist postings); token ≈ whitespace word validated;
  answer noise guards (stopword-free overlap, 35 % keep floor) earned from smoke;
  implementation reworked to match cli-examples.md as the normative UX contract
  (--check advisory + --strict→2, JSON key shapes, [n]+Sources citations).
  **Open risks carried:** postings-build cost at very large corpora; paraphrase
  recall weak until v2 hybrid (by design); Cowork has no hook surface
  (instruction files only).
- **Next:** Phase 2 — execute `handoff/0002-ingest-web-advanced-prompt.md`.

## 2026-07-21 — Glossary created · Cowork
- **Asked:** create a glossary.
- **Did:** created [`glossary.md`](glossary.md) (`type: Glossary`) — ~35
  alphabetical entries covering engine terms (BM25F, RRF, static embeddings,
  chunk/passage, extractive answer, TextRank, eval harness/MRR), ingest terms
  (cache/corpus/manifest/index, fidelity inferred/advanced, Docling, Tesseract,
  CDP, RFC 6455, drift, provenance), process terms (compare doc, proposal,
  handoff, ADR, goldens, worklog, determinism, `$0`), and agent terms (AGENTS.md,
  SKILL.md, fail-open, Anton). Each entry links to its owning doc. Registered in
  DOC-REGISTRY (trigger: new recurring term or meaning change) + bundle index.
- **Decided / open:** nothing open.
- **Next:** Anton dogfooding (DOGFOOD.md) — the build is complete at v0.22.0.

## 2026-07-21 — CLI examples doc: the input/output contract · Cowork
- **Asked:** create examples of CLI input and output, link to necessary documents,
  maintain it.
- **Did:** created [`cli-examples.md`](cli-examples.md) (`type: Reference`) — worked
  input/output for `fux setup` (wizard + flag forms), `fux ingest` (+ `--check`,
  `--list-inferred`, `--advanced`, `--web`), `ask` (incl. honest no-confident-match
  fallback), `find`, `answer` (extractive + citations), `--json` shape, `--explain`
  breakdown (BM25F factors; RRF detail noted for v2), and the error/exit-code
  contract in practice. Declared **normative**: e2e goldens derive from it;
  deviations go through the implementation tracker. Linked from: bundle index,
  cli-surface compare doc, handoff 0001 (formats normative), DOC-REGISTRY (trigger:
  any command/flag/output/exit change — update doc + goldens together).
- **Decided / open:** nothing open.
- **Next:** paste `handoff/0000-master-prompt.md` into Claude Code.

## 2026-07-21 — Implementation tracker created + wired in · Cowork
- **Asked:** an implementation file tracking everything the building agent
  implements, updated at regular intervals / task completion; update the docs.
- **Did:** created [`implementation.md`](implementation.md) (`type: Implementation
  Tracker`): baseline table (✅ pre-build work), milestone tables for phases 1–3
  mirroring the handoffs (all ⬜, with per-row test counts + notes), a "Now working
  on" line the agent keeps current at regular intervals, a Deviations-from-spec
  section, and the binding update contract (flip on completion; never ✅ with
  failing tests). Wired it in: master prompt ground rule 5b + a "track as you go"
  line in all three phase prompts; CLAUDE.md docs-law item 4b + layout; registry
  row; bundle index entry.
- **Decided / open:** nothing open.
- **Next:** paste `handoff/0000-master-prompt.md` into Claude Code.

## 2026-07-21 — docs/ is now an OKF-conformant bundle · Cowork
- **Asked:** update the existing documents with OKF as well.
- **Did:** added OKF frontmatter (`type` + title/description/timestamp) to every
  doc that lacked it — fux-plan (`Plan`), model-handoff-interview (`Succession
  Record`), worklog (`Log`), DOC-REGISTRY (`Registry`), all six compare docs
  (`Compare Doc`, status: accepted), the four directory READMEs (`Index`), ADR
  TEMPLATE (`ADR Template`). Created bundle-root [`index.md`](index.md) declaring
  `okf_version: "0.1"` with progressive-disclosure listing. Verified by script:
  all 26 docs/*.md now start with a frontmatter block. CLAUDE.md OKF section
  updated: bundle scope = `docs/` (+ future ingest cache); root CLAUDE.md/README
  are entry points outside the bundle.
- **Decided / open:** nothing open.
- **Next:** paste `handoff/0000-master-prompt.md` into Claude Code.

## 2026-07-21 — Master prompt: one run for all three phases · Cowork
- **Asked:** one prompt to execute all of it, one by one.
- **Did:** wrote [`handoff/0000-master-prompt.md`](handoff/0000-master-prompt.md) —
  a single paste-ready prompt driving 0001 → 0002 → 0003 strictly in sequence with
  hard phase gates (DoD met + both suites green + ADRs + docs law + archive the
  pair + version bump before the next phase opens), phase reports appended to this
  worklog, stop-clean-on-failure semantics, and versions 0.20 → 0.21 → 0.22. Since
  the original plan gated 0002/0003 on Anton dogfood, the master prompt has Claude
  Code emit a `DOGFOOD.md` quickstart right after phase 1 so dogfooding runs in
  parallel with the remaining phases. Plan updated.
- **Decided / open:** continuous run accepted (dogfood in parallel, not as a gate).
- **Next:** paste `0000-master-prompt.md` into Claude Code and let it run.

## 2026-07-21 — Handoff+prompt pairs for everything finalized (0002, 0003) · Cowork
- **Asked:** create handoff + prompt documents covering *all* finalized work, not
  just v1.
- **Did:** wrote **0002 (Ingest v1.1)** — web crawling (urllib, robots.txt
  non-negotiable, depth/budget caps, HTML→MD via stdlib `html.parser`), CDP
  rendered pages (hand-rolled RFC 6455 client, fake-socket unit tests, Chrome
  optional), advanced tier (Docling/Tesseract extras, fidelity transitions,
  SKILL.md update), fixture HTTP-server e2e (no real network in tests), query-path
  isolation test. And **0003 (Engine v2)** — eval harness *first* (hit@1/5/MRR,
  recorded lexical baseline, the gate + reopen-instrument), distillation pipeline
  in `tools/distill/` (≤10 MB asserted, reproducible recipe, license check),
  stdlib-only inference (`fux.embed`, int8 dot products over BM25F candidates
  only), manifest-invalidated vector cache, RRF fusion + `--lexical-only`, ship
  gate = hybrid beats lexical on eval. Both pairs `blocked_by: 0001`. Plan now has
  the 3-phase build queue table; registry bumped.
- **Decided / open:** build order 0001 → dogfood → 0002/0003 in either order.
  Open question parked in 0003 for Arpit at review: commit vectors vs gitignore.
- **Next:** run the 0001 prompt in Claude Code.

## 2026-07-21 — Ideation (git-corpus bet) + v1 handoff & prompt written · Cowork
- **Asked:** Arpit's seed — the ingested corpus lives in git long-term and
  ultimately feeds product development. Think outside the box (uses, value, what to
  add), then a detailed implementation plan, with research.
- **Did:** researched signals (Knowledge-as-Code pattern Jan 2026; Karpathy LLM-Wiki
  paradigm; competitors semtools/rlama/qmd/llm-search — none version knowledge).
  Product-builder pass: winner = **product-memory corpus** (Arpit's seed, extended)
  — folded into fux-plan §6b + CLAUDE.md (deterministic diff-friendly cache is now a
  hard requirement); parked three proposals with OKF frontmatter:
  `research-to-spec`, `knowledge-diff` (fux diff/log, time-travel), and
  `audit-evidence-trail` (deterministic cited answers as evidence chain; Plane
  seed). Wrote the **detailed v1 implementation plan**:
  `handoff/0001-query-cli-v1-handoff.md` (DoD, in/out scope — web/CDP/OCR pushed to
  v1.1, embeddings v2; module layout; hard constraints; edge cases; both test
  suites; open questions; ADRs 0001–0004) + `0001-query-cli-v1-prompt.md`
  (paste-ready, explore→plan→implement→verify→close-out incl. archiving the pair
  and bumping to 0.20.0). Pre-mortem gate folded into the handoff (scope-drown,
  chunker quality, golden brittleness, parser correctness, cross-platform).
- **Decided / open:** git-corpus bet adopted into plan + CLAUDE.md ✅; v1 scope cut
  ✅ (local inferred-tier only). Nothing open.
- **Next:** run the 0001 prompt in Claude Code; dogfood the result in Anton.

## 2026-07-21 — Proposals dir, doc archiving, OKF conformance · Cowork
- **Asked:** add to CLAUDE.md — (1) proposal docs for later-stage ideas, (2) archive
  implemented docs, (3) follow the OKF pattern for the fux package and features.
- **Did:** identified OKF = **Google's Open Knowledge Format v0.1** (June 2026 open
  spec: markdown + YAML frontmatter bundles, required `type` field, index.md
  progressive disclosure, log.md history, citations; permissive consumption) — read
  the full spec; it's near-identical to Fux's native substrate, so conformance is
  cheap interop. CLAUDE.md: proposals added to lifecycle step 0
  (`docs/proposals/`, `status: proposed`, graduate to compare/plan), archive rule
  (`docs/archive/`, move on completion with `status: implemented` + ADR link), new
  "Follow the OKF pattern" section (type on every knowledge doc, cache = OKF
  bundle, worklog = log.md convention). Created `proposals/` + `archive/` READMEs;
  updated ingest doc (cache is an OKF bundle), DOC-REGISTRY (2 new rows), plan.
- **Decided / open:** all three ✅. Nothing open.
- **Next:** plan → handoff → prompt for query CLI v1 (OKF conformance now in scope).

## 2026-07-21 — Ingest types + e2e suite + doc registry; CLAUDE.md refreshed · Cowork
- **Asked:** ingest images/JSON/txt/YAML too; a thorough, *maintained* e2e test suite
  in a sibling dir; hooks + docs that prompt updating stale documents via a separate
  tracking file; update CLAUDE.md with the useful information. Research it.
- **Did:** researched OCR (Tesseract offline/open-source; Docling OCR stage; OCR
  quality is a first-class retrieval bottleneck → OCR belongs in the judge-able
  advanced tier), doc-freshness practice (last-reviewed signals, owners, docs-in-
  same-change, CI freshness scoring), pytest e2e patterns (per-dir conftest, golden
  files, subprocess CLI runs). Added file-type section to ingest doc (images:
  metadata stub inferred / OCR advanced; JSON stdlib-flattened; YAML fenced text —
  stdlib has no YAML parser; txt native). Created **`docs/DOC-REGISTRY.md`** (trigger
  + last-verified per doc; hook reads it at session end, advisory + fail-open; also
  step 5 of the generated agent contract). CLAUDE.md: replaced the stale
  "decisions pending" scope with the decided design summary, added `tests_e2e/`
  mandate (fixture corpus + goldens, maintained), registry in the docs law, layout
  refresh, and a standing **auto-fold rule** (durable session knowledge → CLAUDE.md
  in the same change). Synced plan + agent-integration doc.
- **Decided / open:** all three additions ✅. Nothing open.
- **Next:** plan → handoff → prompt for query CLI v1 (now includes e2e suite +
  registry hook in scope).

## 2026-07-21 — Sub-decisions resolved with research; `init` → `setup` · Cowork
- **Asked:** research the open sub-decisions (reranker-beyond-RRF; chunking unit;
  BM25F field weights) and rename `fux init` to `fux setup`.
- **Did:** researched chunking (structure-aware heading-based wins — up to ~9-pt
  recall swing, 15-pt accuracy spread across strategies; 256–512-token sweet spot)
  and BM25F (weighted-tf-then-saturate per Lucene `combined_fields`; titles 2–5×
  body is standard; k1=1.2/b=0.75 defaults). Resolved all three in
  `query-engine.compare.md` with references: **no reranker** (cross-attention needs
  ~22 M-param/~80 MB models — 8× over the 10 MB budget; RRF stays), **chunking =
  heading-based**, 256–512 tokens, heading-path context, code/tables atomic,
  `file:line` boundaries; **BM25F = heading 3.0 / path 2.0 / body 1.0**, overridable
  in `fux.toml`. Renamed `fux init` → **`fux setup`** across cli-surface,
  agent-integration, compare README, plan, handoff (worklog history left intact).
- **Decided / open:** all sub-decisions ✅ — **nothing is open**. Reopen-triggers
  recorded (eval-set evidence only).
- **Next:** plan → handoff → prompt for query CLI v1.

## 2026-07-21 — Agent-integration accepted; one-SKILL.md verdict; `fux init` · Cowork
- **Asked:** accept agent-integration; are per-tool skills (Claude/Copilot/Kiro) a
  good idea; single setup command, interactive + flags. Research it.
- **Did:** researched — **Agent Skills is an open standard since Dec 2025**
  (agentskills.io); by Mar 2026, 32+ tools incl. Copilot, Kiro, Codex, Cursor,
  Gemini CLI read the same `SKILL.md`, so **one skill file serves all tools** (the
  old build's per-platform skillgen is obsolete). Added Skills section to
  agent-integration doc (layer cake: AGENTS.md=when, SKILL.md=how, hooks=enforced;
  ship `fux-query` + `fux-ingest` skills). Added `fux init` to cli-surface doc:
  interactive wizard default, flag-per-prompt, `-y`, idempotent (npm init / gh auth
  / clig.dev pattern). Synced plan + compare README.
- **Decided / open:** agent-integration ✅; skills = one SKILL.md ✅; `fux init` ✅.
  **All major forks now decided.** Open sub-decisions only: reranker-vs-RRF (rec:
  RRF), chunking unit, BM25F weights.
- **Next:** plan → handoff → prompt for query CLI v1.

## 2026-07-21 — CLI verbs + CDP accepted; numpy-vendoring disproven; agent-integration proposed · Cowork
- **Asked:** accept cli-surface + ingest verdicts; ingest must also work over Chrome
  DevTools Protocol; could numpy be vendored as internal files and resynced per
  build; new fork — Claude/Copilot/Kiro hooks or md files (or both, or better) so
  agents know to query fux; everything backed by references.
- **Did:** researched CDP (JSON-RPC over WebSocket; stdlib has no WS client → hand-
  rolled RFC 6455 client on `socket`, user's own headless Chrome, `render = "cdp"`
  config), numpy internals (core is platform-compiled C extensions + BLAS — not
  copyable Python; vendoring = per-platform build farm), and the agent-instructions
  landscape (AGENTS.md = Linux Foundation standard read by Copilot/Cursor/Codex/
  Windsurf/Zed, picked up by Kiro + Claude Code; Kiro steering + hooks; Claude Code
  `UserPromptSubmit`). Marked cli-surface accepted; added CDP section to ingest doc;
  added numpy-vendoring resolution with proof to packaged-model doc; wrote
  `agent-integration.compare.md` (proposed: files + hooks from one `fux init-agents`
  generator, MCP deferred). Synced plan + compare README.
- **Decided / open:** CLI verbs ✅; CDP ingestion ✅; numpy vendoring ✗ (stdlib
  stands). Open: agent-integration verdict; reranker-vs-RRF; chunking; BM25F weights.
- **Next:** Arpit calls agent-integration → then plan → handoff → prompt for v1.

## 2026-07-20 — Verdicts confirmed + refinements; numpy resolved out · Cowork
- **Asked:** accept engine/ingest/model verdicts. Refinements: friendlier CLI
  commands than `fux query --flags`; "what if I don't use numpy?"; ingest as a skill
  + usable from other Python scripts; ingest follows links and their attachments
  multiple levels deep; converted docs need metadata for maintenance/traceability.
- **Did:** wrote `cli-surface.compare.md` (proposed `fux ask`/`find`/`answer`, verb
  per intent). Resolved numpy in `packaged-model.compare.md`: **stdlib-only** — with
  candidate-only ranking (BM25F top-200 → dot products) query latency is single-digit
  ms without numpy; chunk vectors precomputed at ingest. Extended
  `ingest-strategy.compare.md`: per-file traceability frontmatter (source, sha256,
  fidelity, converter, origin/url/parent/depth — first dogfood of the hand-rolled
  frontmatter parser), library-first `fux.ingest` API + agent skill, fenced `--web`
  crawling (max_depth, same_domain, robots.txt, attachments). Synced plan + compare
  README.
- **Decided / open:** all four major forks ✅ accepted; numpy ✅ out. Open: CLI naming
  verdict (proposed verbs), reranker-vs-RRF (rec: RRF only), chunking unit, BM25F
  field weights.
- **Next:** Arpit calls the CLI naming → plan → handoff → prompt for query CLI v1.

## 2026-07-20 — Query-CLI decisions locked; researched + 4 compare docs · Cowork
- **Asked:** decide the three forks with additions — two-tier ingest (inferred +
  advanced/agent-triggered) + manifest + config-driven dirs; staged engine v1/v2/v3
  with a look at BM25 alternatives; output option 2 plus non-LLM synthesis via a
  model *built into the package*; hard rule — no external model, but a bundled model
  ≤10 MB is allowed. Research it.
- **Did:** web-researched retrieval (BM25F, SPLADE, cross-encoders, RRF hybrid ~91 %
  recall), tiny packageable models (Model2Vec/Potion ~8 MB, numpy dep), and non-LLM
  synthesis (TextRank/LexRank extractive). Rewrote `query-engine`, `query-output`,
  `ingest-strategy` compare docs with accepted verdicts; added
  `packaged-model.compare.md`. Synced `fux-plan.md` (Decisions §6) + compare README.
- **Decided / open:** engine = BM25F → +bundled static embeddings via RRF → agent
  surface; output = passages default + `--answer` extractive (no LLM); ingest =
  two-tier + manifest + `fux.toml`; model = ≤10 MB static embeddings, stdlib inference
  + optional numpy. **Honest limit recorded:** ≤10 MB can't *generate* prose —
  `--answer` selects/orders source sentences. Open: stdlib-vs-numpy, reranker-vs-RRF,
  chunking unit, BM25F field weights.
- **Next:** resolve the open sub-decisions, then plan → handoff → prompt for query
  CLI v1.

## 2026-07-20 — Pivot to a document-query CLI; three compare docs · Cowork
- **Asked:** hold the rule engine; make the first deliverable a CLI that answers
  natural-language questions over documents in a defined set of folders. Produce a
  compare doc wherever there are multiple options, decide by reading them.
- **Did:** wrote `docs/compare/query-engine.compare.md`, `query-output.compare.md`,
  `ingest-strategy.compare.md` (+ `compare/README.md`). Grounded with references
  (BM25, RAG, sentence-transformers, MarkItDown/Docling). Synced the pivot into
  CLAUDE.md (scope + compare step 0), `fux-plan.md`, `model-handoff-interview.md`.
- **Decided / open:** proposed verdicts recorded in each compare doc; **all three
  forks await Arpit's call.** The engine fork also decides whether `$0`/no-LLM still
  binds this tool.
- **Next:** Arpit reads the compare docs and picks a verdict per fork → then
  plan → handoff → prompt for query CLI v1.

## 2026-07-20 — From-scratch rebuild: CLAUDE.md + package skeleton · Cowork
- **Asked:** review the old (non-working) build for context, then write a fresh
  CLAUDE.md and do basic Python package setup (keep the name, bump the version).
- **Did:** reviewed `archive/`; wrote binding CLAUDE.md (scope, constraints,
  lifecycle, docs-in-sync); scaffolded `src/fux/` (hatchling, v0.19.0, CLI +
  `FuxError`), README, `docs/fux-plan.md`, `docs/model-handoff-interview.md`,
  `docs/adr/TEMPLATE.md`. 4 smoke tests pass.
- **Decided / open:** src/ layout + hatchling; version 0.19.0 (bumped from old
  0.18.0); constraints carried forward from the old build.
- **Next:** (superseded by the pivot entry above).
