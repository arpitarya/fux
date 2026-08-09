min_confidence calibration — evidence index (conformance run 2026-07-23)
=======================================================================

How this was measured
---------------------
- Environment: fux-lab/acme, but with a DELIBERATE deviation from the pinned
  PyPI install. The env venv holds an EDITABLE install of the local checkout
  (`uv pip install -e ~/my_programs/fux`), because the confidence-floor
  mechanism exists only in the uncommitted working tree (targeting v0.25.0);
  no PyPI release has it. Verified: `.venv/bin/fux --version` -> 0.24.0 with
  `fux.__file__` pointing at ~/my_programs/fux/src/fux.
- Corpus: REGENERATED fresh (`make_repo.py --out corpus`, seed 20260722,
  929 docs, 59 eval pairs), then `fux setup` + `fux ingest` (885 chunks,
  hybrid engine live). The old acme corpus dir did not exist; regen was
  required, not a reuse.
- Mechanism smoke-tested BEFORE trusting any number: with
  `[answer] min_confidence = 0.99`, a known-answerable query declined
  (answer=null, 0 sources); at 0.0 it answered. Boundary re-validated against
  the real CLI at floor 0.24 vs 0.25 (see report.md).

Files
-----
- dump_scores.py          The throwaway measurement script. Mirrors
                          `_run_answer` in src/fux/query/api.py EXACTLY
                          (retrieve pool=10 -> build_answer with the live
                          qsim -> best_confidence = max(sentence.score)).
                          No file under src/ was modified. Run from inside
                          the acme corpus dir with that env's python.
- acme-raw-scores.json    Raw output of dump_scores.py: best_confidence for
                          all 59 acme eval questions + the gibberish control.
- acme-unanswerable.json  Gate #1: the 4 typed-unanswerable questions + scores.
- gibberish.json          Gate #2: the control (declines unconditionally).
- acme-answerable-55.json Gate #4: all 55 answerable pairs, sorted ascending
                          by best_confidence (the false-decline order).
- threshold-sweep.json    The combined trade-off curve across candidate floors.

Gates deliberately omitted from evidence/ (genuine no-ops — stated, not skipped)
-------------------------------------------------------------------------------
- Gate #3 (fixture 21-pair, tests_e2e/eval/run_eval.py): the harness queries
  via `ask` (run_eval.py line 81), never `answer`. `min_confidence` gates only
  `answer`. Unaffected by construction. No evidence file.
- Gate #5 (synthetic 1k/5k/10k, fux-lab/shared/regress/run.py): retrieval
  quality is scored via `_score_pairs` using `find` mode; and the synthetic
  generator (make_corpus.py) plants only `overlap`/`zero-overlap` pairs — NO
  `unanswerable` and NO answer-exercising pairs — so `check_unanswerable_pairs`
  is empty on those tiers. The only `answer` call there is the gibberish probe
  (check_honest_decline), which declines at any floor. Unaffected by
  construction. No evidence file; 5k/10k corpora were not regenerated (the
  deterministic generator demonstrably emits no answer pairs).
