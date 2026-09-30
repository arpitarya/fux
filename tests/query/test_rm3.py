"""W-237 — RM3 behind a `grounded`-only gate, `[ranking] rm3_weight`, default off.

**What is pinned here is the mechanism, never its value.** Whether gated RM3
improves ranking is the frozen pre-registration's question
(`work/regression/2026-09-30-rm3-grounded/PRE-REGISTRATION.md`), answered on
golden data and not by a unit test. What a unit test can hold is what the bar
fixed before the build:

1. **`0.0` is byte-identical** and runs no first pass: no feedback, no band read.
2. 🔴 **The gate**: RM3 expands only when the first pass's band is `grounded`.
   On `partial` or `weak` the answer is the first pass, byte for byte.
3. **Feedback terms are the pre-registration's**: top `FB_DOCS` of the
   **lexical window**, `FB_TERMS` terms, RM1-weighted, the query's own terms
   excluded, ties by ascending hash.
4. **SR-EXPAND's refusal holds**: a document matching only feedback terms is
   never returned.
5. **A caller's `--expand` wins**, and **`fux lexical` never runs it.**
6. **`--why` names the gate when it fires**, and says nothing when it does not.
7. **The scan and the accelerator agree** at every arm value.
8. **The Node reader ranks identically** through its own loader.

Restored from `363a8b8c^:tests/query/test_rm3.py` (W-224 removed it), with the
W-221 "list `ask` shows" tests dropped — this bar feeds back the lexical window —
and the gate tests added.
"""

from __future__ import annotations

from l12_fixtures import scoring, template_tune, tune_text, tuned, write_config, write_tune
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from fux.derive import build
from fux.query import rm3, run_query
from fux.query.rank import AskResult
from fux.store import term_hash, write_index

ENGINE = Path(__file__).resolve().parents[2]
ALPHA, BETA, GAMMA, DELTA, FILLER = (term_hash(w) for w in ("alpha", "beta", "gamma", "delta", "filler"))
ARMS = (0.1, 0.2, 0.3, 0.5)


def _rec(doc_id: str, flen, terms) -> dict:
    return {
        "id": doc_id, "src": "git", "loc": doc_id.removeprefix("file:"),
        "mode": "extracted", "title": doc_id, "phrases": [],
        "terms": terms, "flen": flen, "edges": [],
    }


def _corpus() -> list[dict]:
    """`alpha` is the query, and `lead-1.md` leads it clearly, so its band is
    `grounded`. The leaders share `beta`; `lifted.md` carries `alpha` weakly and
    `beta` heavily, so feedback should raise it. `beta-only.md` carries no word
    the user typed and must never appear. `delta` is carried equally by two
    documents, so its band is `weak`: the gate must stay shut on it."""
    return [
        _rec("file:lead-1.md", [60], {ALPHA: [12], BETA: [5], GAMMA: [1]}),
        _rec("file:lead-2.md", [60], {ALPHA: [4], BETA: [4]}),
        _rec("file:plain.md", [60], {ALPHA: [3], FILLER: [8]}),
        _rec("file:lifted.md", [60], {ALPHA: [2], BETA: [12]}),
        _rec("file:beta-only.md", [30], {BETA: [20]}),
        _rec("file:tie-1.md", [60], {DELTA: [3], BETA: [9]}),
        _rec("file:tie-2.md", [60], {DELTA: [3], BETA: [9]}),
        *[_rec(f"file:pad{i}.md", [80], {FILLER: [2]}) for i in range(30)],
    ]


@pytest.fixture
def built(tmp_path):
    write_index(tmp_path, _corpus())
    # The CLI refuses a repo without one (SR-PII decision 17); empty = no rules.
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    write_config(tmp_path)
    build(tmp_path)
    return tmp_path


def _tune(weight: float):
    return tuned(rm3_weight=weight)


def _run(root, query, weight, *, top=10, force_scan=True, **kw):
    return run_query(root, query, top, force_scan=force_scan, tune=_tune(weight), use_tune=True, **kw)


def _payload(results):
    return [(r.id, repr(r.score)) for r in results]


def _band(root, query, weight) -> str:
    conf: dict = {}
    _run(root, query, weight, confidence_out=conf)
    return conf["confidence"].band


# -- 1. off is off ------------------------------------------------------------

def test_the_default_is_off():
    assert template_tune().rm3_weight == 0.0


@pytest.mark.parametrize("force_scan", (True, False))
def test_off_runs_no_first_pass_and_is_byte_identical(built, monkeypatch, force_scan):
    """🔴 `0.0` is the engine before the key returned — asserted by making the
    feedback function explode, so any first pass at all fails the test."""
    before = {q: _payload(_run(built, q, 0.0, force_scan=force_scan)[0]) for q in ("alpha", "delta", "alpha zzzq")}

    def boom(*_a, **_k):
        raise AssertionError("rm3_weight = 0.0 must not compute feedback")

    monkeypatch.setattr(rm3, "feedback_terms", boom)
    for q, expected in before.items():
        assert _payload(_run(built, q, 0.0, force_scan=force_scan)[0]) == expected


def test_off_is_the_template_path_exactly(built):
    """The `0.0` arm and the shipped template rank with the same bits, on every
    output a caller can ask for — results, band, trace, related."""
    def everything(tune):
        conf, trace, related = {}, {}, []
        res, path = run_query(built, "alpha", 10, force_scan=True, tune=tune, use_tune=True,
                              confidence_out=conf, trace_out=trace, related_out=related)
        return _payload(res), path, conf["confidence"].as_dict(), sorted(trace), related

    assert everything(_tune(0.0)) == everything(template_tune())


# -- 2. the gate --------------------------------------------------------------

def test_the_fixture_has_all_three_bands(built):
    assert _band(built, "alpha", 0.0) == "grounded"
    assert _band(built, "delta", 0.0) == "weak"
    assert _band(built, "alpha zzzq", 0.0) == "partial"


@pytest.mark.parametrize("weight", ARMS)
@pytest.mark.parametrize("query", ("delta", "alpha zzzq"))
def test_the_gate_stays_shut_unless_grounded(built, monkeypatch, weight, query):
    """🔴 G3: on `weak` or `partial` the first pass IS the answer — same bytes,
    same band — and no feedback is computed."""
    conf0: dict = {}
    base = _payload(_run(built, query, 0.0, confidence_out=conf0)[0])
    monkeypatch.setattr(rm3, "feedback_terms", lambda *a, **k: pytest.fail("the gate opened"))
    conf, trace = {}, {}
    got = _payload(_run(built, query, weight, confidence_out=conf, trace_out=trace)[0])
    assert got == base
    assert conf["confidence"].as_dict() == conf0["confidence"].as_dict()
    assert "rm3" not in trace


@pytest.mark.parametrize("weight", ARMS)
def test_the_gate_opens_on_grounded(built, weight):
    trace: dict = {}
    on = _run(built, "alpha", weight, trace_out=trace)[0]
    assert trace["rm3"] == {"gate": "grounded", "weight": weight, "terms": 3}
    assert _payload(on) != _payload(_run(built, "alpha", 0.0)[0])


def test_feedback_moves_the_document_that_shares_the_leaders_vocabulary(built):
    off = [r.id for r in _run(built, "alpha", 0.0)[0]]
    on = [r.id for r in _run(built, "alpha", 0.5)[0]]
    assert off.index("file:lifted.md") > on.index("file:lifted.md")


# -- 3. the feedback terms are the pre-registration's -------------------------

def test_feedback_reads_the_lexical_window(built, monkeypatch):
    """The feedback set is `rank()`'s window, top `FB_DOCS` — before rerank,
    pin and graph tier — which is what the trace records as `window`."""
    trace: dict = {}
    _run(built, "alpha", 0.0, trace_out=trace)
    seen: list[list[str]] = []
    real = rm3.feedback_terms

    def spy(root, first, *a, **k):
        seen.append([r.id for r in first[: rm3.FB_DOCS]])
        return real(root, first, *a, **k)

    monkeypatch.setattr(rm3, "feedback_terms", spy)
    _run(built, "alpha", 0.3)
    assert seen == [[r.id for r in trace["window"][: rm3.FB_DOCS]]]


def test_a_shallow_window_is_widened_to_fb_docs_for_feedback(built, monkeypatch):
    shallow = tuned(rm3_weight=0.3, ask_boost=False, ask_related=False)
    assert rm3.FB_DOCS > 2
    seen: list[int] = []
    real = rm3.feedback_terms
    monkeypatch.setattr(rm3, "feedback_terms", lambda root, first, *a, **k: (seen.append(len(first)), real(root, first, *a, **k))[1])
    run_query(built, "alpha", 2, force_scan=True, tune=shallow, use_tune=True)
    assert seen and seen[0] > 2


def test_feedback_excludes_the_query_and_weights_by_rm1(built):
    first = _run(built, "alpha", 0.0)[0]
    terms = rm3.feedback_terms(built, first, [ALPHA], scoring())
    assert ALPHA not in terms
    assert terms[0] == BETA, "beta is in every leading document and weighs most"
    assert set(terms) <= {BETA, GAMMA, FILLER}


def test_feedback_takes_at_most_fb_docs_documents_and_fb_terms_terms(tmp_path):
    terms = {term_hash(f"t{i}"): [1] for i in range(15)}
    records = [_rec(f"file:d{i}.md", [15], {ALPHA: [1], **terms}) for i in range(12)]
    write_index(tmp_path, records)
    first = [AskResult(id=r["id"], title="", loc="", score=1.0) for r in records]
    got = rm3.feedback_terms(tmp_path, first, [ALPHA], scoring())
    assert (rm3.FB_DOCS, rm3.FB_TERMS) == (10, 10)
    assert len(got) == rm3.FB_TERMS
    # Every term ties, so the ten are the ten smallest hashes, ascending.
    assert got == sorted(terms)[: rm3.FB_TERMS]


def test_nothing_to_feed_back_is_the_identity(built):
    assert rm3.feedback_terms(built, [], [ALPHA], scoring()) == []


# -- 4. the hallucinated-citation guard holds ---------------------------------

@pytest.mark.parametrize("weight", ARMS)
def test_a_document_matching_only_feedback_terms_is_never_returned(built, weight):
    ids = [r.id for r in _run(built, "alpha", weight, top=40)[0]]
    assert "file:beta-only.md" not in ids
    assert "file:tie-1.md" not in ids


# -- 5. a caller's expansion wins; the baseline verb never runs it ------------

def test_a_callers_expand_wins(built, monkeypatch):
    monkeypatch.setattr(rm3, "feedback_terms", lambda *a, **k: pytest.fail("RM3 ran beside --expand"))
    expanded = _payload(_run(built, "alpha", 0.3, expand="gamma")[0])
    assert expanded == _payload(_run(built, "alpha", 0.0, expand="gamma")[0])


def test_lexical_forces_rm3_off():
    source = (ENGINE / "src" / "fux" / "query" / "__init__.py").read_text(encoding="utf-8")
    assert "intent_weight=0.0,\n            rm3_weight=0.0," in source
    node = (ENGINE / "node" / "src" / "query" / "run.mjs").read_text(encoding="utf-8")
    assert "intentWeight: 0.0, rm3Weight: 0.0 }" in node


def _cli(root: Path, *argv: str):
    env = dict(os.environ, PYTHONPATH=str(ENGINE / "src"))
    proc = subprocess.run(
        [sys.executable, "-m", "fux", *argv],
        capture_output=True, text=True, encoding="utf-8", cwd=root, env=env,
    )
    assert proc.returncode == 0, proc.stderr
    return proc


def test_lexical_ranks_the_same_whatever_rm3_weight_says(built):
    off = _cli(built, "lexical", "alpha", "--json", "--top", "10").stdout
    write_tune(built, tune_text(ranking={"rm3_weight": 0.5}))
    assert _cli(built, "lexical", "alpha", "--json", "--top", "10").stdout == off
    assert _cli(built, "ask", "alpha", "--json", "--top", "10").stdout != _cli(
        built, "ask", "alpha", "--json", "--top", "10", "--no-tune").stdout


# -- 6. --why names the gate when it fires ------------------------------------

def test_why_names_the_gate_only_when_it_fires(built):
    write_tune(built, tune_text(ranking={"rm3_weight": 0.3}))
    fired = json.loads(_cli(built, "ask", "alpha", "--json", "--why", "--top", "10").stdout)
    assert fired["derivation"]["rm3"] == {"gate": "grounded", "weight": 0.3, "terms": 3}
    shut = json.loads(_cli(built, "ask", "delta", "--json", "--why", "--top", "10").stdout)
    assert "rm3" not in shut["derivation"]
    text = _cli(built, "ask", "alpha", "--why", "--top", "10")
    assert "[why] rm3: first pass grounded -> 3 feedback term(s) added at weight 0.3" in text.stderr


# -- 7. the scan and the accelerator agree ------------------------------------

@pytest.mark.parametrize("weight", (0.0, *ARMS))
@pytest.mark.parametrize("query", ("alpha", "delta", "alpha zzzq"))
def test_accelerator_equals_scan_at_every_arm(built, weight, query):
    scan = _payload(_run(built, query, weight, force_scan=True)[0])
    fast, path = _run(built, query, weight, force_scan=False)
    assert path == "accelerator"
    assert _payload(fast) == scan


# -- 8. the Node reader -------------------------------------------------------

@pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")
@pytest.mark.parametrize("weight", (0.0, 0.3))
@pytest.mark.parametrize("query", ("alpha", "delta"))
def test_node_reader_ranks_identically(built, weight, query):
    """Through each reader's own `tune.toml` loader, so the key's parsing is
    under the differential law as well as the mechanism. Scores to nine digits:
    an EXPANDED score may differ in the last bit between the readers (W-222),
    as `test_mined.py` allows."""
    write_tune(built, tune_text(ranking={"rm3_weight": weight}))
    py = [[r.id, round(r.score, 9)] for r in run_query(built, query, 10, force_scan=True, tune=None, use_tune=True)[0]]
    script = (
        f'import {{ runQuery }} from {json.dumps((ENGINE / "node/src/query/run.mjs").as_uri())};'
        f'const out = runQuery({json.dumps(str(built))}, {json.dumps(query)}, 10, '
        '{ useTune: true, wantConfidence: false, compose: true });'
        'console.log(JSON.stringify({ r: out.results.map((r) => [r.id, r.score]), rm3: out.rm3 ?? null }));'
    )
    js = json.loads(subprocess.check_output(["node", "--input-type=module", "-e", script], text=True))
    assert [[i, round(s, 9)] for i, s in js["r"]] == py
    fired = weight > 0 and query == "alpha"
    assert (js["rm3"] is not None) == fired
