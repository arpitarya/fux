# Handoff 01: `fux parity` — head-to-head coverage vs Graphify

**One-liner:** A CLI command that runs Fux and Graphify on the same repo (and your
logged real queries) and scores how much of your actual Graphify usage Fux already
covers — turning "can I remove graphify?" into a number.
**Owner / executor:** Claude Code
**Status:** Ready to build
**Stress-tested:** Challenged the premise — a parity *score* can lie two ways: (a)
counting features Fux will never have (video, LLM extraction) drags the number down
for a use case you don't have; (b) counting only graph rows hides that Fux's value
is the governance layer graphify lacks. **Survived** by scoping the score to *your
logged queries* (`--from-log`) not an abstract feature list, and by reporting two
sub-scores: **graph-parity** (replaceable surface) and **fux-only** (why you keep
fux). **Residual risk:** requires graphify installed + a query log to be meaningful;
without a log it falls back to a static capability manifest (weaker signal — labelled).

## 1. Context & background

Decision driver: [docs/fux-vs-graphify-parity-matrix.md](fux-vs-graphify-parity-matrix.md).
The matrix is a human judgement; this command makes it *measured and repeatable* on
your real repo so the removal decision isn't vibes. Graphify logs every
`query`/`path`/`explain` to `~/.cache/graphify-queries.log` (JSONL) — that log is the
ground truth for "what I actually use graphify for."

## 2. Definition of done

- [ ] `fux parity [PATH]` runs and prints a report with two sub-scores (graph-parity
      %, and a fux-only capability count) + a gap list.
- [ ] `fux parity --from-log [FILE]` replays graphify's query log: for each logged
      question, run the equivalent `fux recall`/`query`/`explain` and score whether
      Fux returns a non-empty, relevant subgraph (coverage %, not correctness-vs-LLM).
- [ ] `fux parity --json` emits machine output for the removal checklist.
- [ ] A static **capability manifest** (committed, versioned) encodes the §2 matrix
      rows so the score is reproducible when no log exists; `--from-log` overrides it.
- [ ] Runs `$0`, deterministic, stdlib-only. Graphify is invoked as an external
      subprocess **only** when present; absence degrades gracefully (manifest-only).
- [ ] Docs updated (README command list, cli.md registry table, §9.5).

## 3. Scope

**In scope:** the `fux parity` command, the capability manifest, log-replay scoring,
`--json`, registry + help wiring.
**Out of scope (explicit):** *installing* or *fixing* graphify; judging graphify
answer quality with a model (no LLM — score is coverage/non-empty, not semantic
correctness); auto-uninstalling graphify. Do not add a runtime dep on graphify.

## 4. Current state

- Read first: `fux/registry.py` (command registration), `fux/cli.py` (dispatch +
  error boundary), `fux/recall.py`/`fux/graphquery.py` (the retrieval fux will score),
  `docs/cli.md` (registry-table regen step), `fux/clihelp.py`.
- Graphify log shape: JSONL, fields incl. `timestamp, question, corpus, nodes_returned,
  duration` (README §Privacy). Graphify CLI: `graphify query "Q"`, `graphify path a b`.

## 5. Technical approach (decided)

1. **New command module** `fux/cliparity.py`, registered in `registry.py` (group
   `runtime`). Follows the existing command pattern; renders via the same help path.
2. **Capability manifest** `fux/data/parity-manifest.json`: the matrix rows (id,
   capability, weight, fux_score, graphify_score, use_case #1/#2). Editable, versioned.
   `fux parity` with no log scores from this.
3. **Log replay** (`--from-log`): parse the JSONL, dedupe questions, and for each run
   `recall.run()` in-process; score = fraction of questions where Fux returns ≥1
   relevant rule/node above a threshold. Report per-question hits/misses so gaps are
   actionable ("these 12 queries fux missed").
4. **Two sub-scores, never one blended number** — graph-parity (use-case #1,
   replaceable) and fux-only (governance rows). Blending them is the lie the debate flagged.
5. **Graphify as optional subprocess:** if `graphify` is on PATH, optionally run the
   same corpus through it for a live node-count delta; else manifest-only, labelled.

## 6. Non-negotiables / constraints

- **Python ≥ 3.11, stdlib-only, `$0`, deterministic.** No LLM to score relevance —
  use lexical/graph overlap, exactly like `recall`.
- **Use:** existing `recall`/`graphquery`; `subprocess` for optional graphify calls.
  **Avoid:** any third-party dep; importing graphify as a library; network calls.
- **Error contract:** honour the CLI boundary (`FuxError` → terse `error:`, exit 1).
- **Do not touch:** engine retrieval internals beyond read; other commands.

## 7. Dependencies & prerequisites

Optional: `graphify` on PATH and a query log for the strongest signal. Neither
required — degrade to manifest-only with a printed caveat.

## 8. Edge cases & risks

- No graphify / no log → manifest-only mode, clearly labelled "static estimate."
- Empty or malformed log line → skip with a counted warning, don't crash.
- Query log contains questions about media/video (use-case #2) → tag them as
  out-of-Fux-scope so they don't unfairly lower graph-parity.
- Huge log → cap replay at `--top N` most recent/frequent.

## 9. Testing & validation

- Unit: manifest parse + scoring math; log replay with a fixture JSONL (hits, misses,
  malformed, out-of-scope). `python -m pytest -q`.
- Integration: run `fux parity` on `fux-lab/`; assert two sub-scores + gap list.
- Verify `--json` shape matches the removal-checklist consumer.

## 9.5 Documentation impact

- [ ] **README** — required: add `fux parity` to the command surface.
- [ ] **docs/cli.md** — required: regenerate the registry table (documented step).
- [ ] **docs/fux-implementation.md** — required: status + test count.
- [ ] **docs/fux-vs-graphify-parity-matrix.md** — required: link the command as the
      runnable realization of §4 checklist.
- [ ] **CLAUDE.md / AGENTS.md** — propose only if a new module convention is introduced.
- [ ] CHANGELOG/ADR — N/A unless you keep a changelog for internal commands.

## 10. Open questions

- OPEN QUESTION: relevance threshold for a log-replay "hit" — top-1 non-empty, or
  score ≥ X? Recommendation: node returned AND overlaps the graphify corpus for that
  query; expose as `--threshold`.
- OPEN QUESTION: should `fux parity` gate the removal (exit non-zero below a target %)
  or report-only? Recommendation: report-only + `--min` flag for CI-style use.
