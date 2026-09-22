"""W-168 step 5 — RM3 pseudo-relevance feedback, behind `[ranking] rm3_weight`, default off.

**What is pinned here is the mechanism, never its value.** Whether RM3 improves
ranking is the frozen pre-registration's question
(`work/regression/2026-09-23-rm3/PRE-REGISTRATION.md`), answered on golden data
and not by a unit test. What a unit test can hold is the six properties the
build promised before it existed:

1. **`0.0` is byte-identical** and runs no first pass at all.
2. **Feedback terms are the pre-registration's**: top 10 documents, 10 terms,
   RM1-weighted, the query's own terms excluded, ties by ascending hash.
3. **SR-EXPAND's refusal holds**: a document matching only feedback terms is
   never returned.
4. **A caller's `--expand` wins**, and **`fux lexical` never runs it.**
5. **The scan and the accelerator agree** at every arm value.
6. **The Node reader picks the same terms and the same bytes.**
"""

from __future__ import annotations

import dataclasses
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from fux.derive import build
from fux.query import rm3, run_query
from fux.query.rank import AskResult
from fux.store import term_hash, write_index
from fux.tune import DEFAULT_TUNE

ENGINE = Path(__file__).resolve().parents[2]
ALPHA, BETA, GAMMA, FILLER = (term_hash(w) for w in ("alpha", "beta", "gamma", "filler"))
ARMS = (0.1, 0.2, 0.3, 0.5)


def _rec(doc_id: str, flen, terms) -> dict:
    return {
        "id": doc_id, "src": "git", "loc": doc_id.removeprefix("file:"),
        "mode": "extracted", "title": doc_id, "phrases": [],
        "terms": terms, "flen": flen, "edges": [],
    }


def _corpus() -> list[dict]:
    """`alpha` is the query. The two leaders share `beta`; `lifted.md` carries
    `alpha` weakly and `beta` heavily, so feedback should raise it. `beta-only`
    carries no word the user typed and must never appear."""
    return [
        _rec("file:lead-1.md", [60], {ALPHA: [6], BETA: [5], GAMMA: [1]}),
        _rec("file:lead-2.md", [60], {ALPHA: [5], BETA: [4]}),
        _rec("file:plain.md", [60], {ALPHA: [3], FILLER: [8]}),
        _rec("file:lifted.md", [60], {ALPHA: [2], BETA: [12]}),
        _rec("file:beta-only.md", [30], {BETA: [20]}),
        *[_rec(f"file:pad{i}.md", [80], {FILLER: [2]}) for i in range(30)],
    ]


@pytest.fixture
def built(tmp_path):
    write_index(tmp_path, _corpus())
    build(tmp_path)
    return tmp_path


def _tune(weight: float):
    return dataclasses.replace(DEFAULT_TUNE, rm3_weight=weight)


def _payload(results):
    return [(r.id, repr(r.score)) for r in results]


# -- 1. off is off ------------------------------------------------------------

def test_the_default_is_off():
    assert DEFAULT_TUNE.rm3_weight == 0.0


def test_off_runs_no_first_pass_and_is_byte_identical(built, monkeypatch):
    before = _payload(run_query(built, "alpha", 10, tune=DEFAULT_TUNE)[0])

    def boom(*_a, **_k):
        raise AssertionError("rm3_weight = 0.0 must not compute feedback")

    monkeypatch.setattr(rm3, "feedback_terms", boom)
    assert _payload(run_query(built, "alpha", 10, tune=_tune(0.0))[0]) == before


# -- 2. the feedback terms are the pre-registration's -------------------------

def test_feedback_excludes_the_query_and_weights_by_rm1(built):
    first = run_query(built, "alpha", 10, tune=DEFAULT_TUNE)[0]
    terms = rm3.feedback_terms(built, first, [ALPHA])
    assert ALPHA not in terms
    assert terms[0] == BETA, "beta is in every leading document and weighs most"
    assert set(terms) <= {BETA, GAMMA, FILLER}


def test_feedback_takes_at_most_ten_documents_and_ten_terms(built):
    terms = {term_hash(f"t{i}"): [1] for i in range(15)}
    records = [_rec(f"file:d{i}.md", [15], {ALPHA: [1], **terms}) for i in range(12)]
    root = built.parent / "wide"
    root.mkdir()
    write_index(root, records)
    first = [AskResult(id=r["id"], title="", loc="", score=1.0) for r in records]
    got = rm3.feedback_terms(root, first, [ALPHA])
    assert len(got) == rm3.FB_TERMS == 10
    # Every term ties, so the ten are the ten smallest hashes, ascending.
    assert got == sorted(terms)[:10]


def test_nothing_to_feed_back_is_the_identity(built):
    assert rm3.feedback_terms(built, [], [ALPHA]) == []


# -- 3. the hallucinated-citation guard holds ---------------------------------

@pytest.mark.parametrize("weight", ARMS)
def test_a_document_matching_only_feedback_terms_is_never_returned(built, weight):
    ids = [r.id for r in run_query(built, "alpha", 20, tune=_tune(weight))[0]]
    assert "file:beta-only.md" not in ids


def test_feedback_moves_the_document_that_shares_the_leaders_vocabulary(built):
    off = [r.id for r in run_query(built, "alpha", 10, tune=DEFAULT_TUNE)[0]]
    on = [r.id for r in run_query(built, "alpha", 10, tune=_tune(0.5))[0]]
    assert off.index("file:lifted.md") > on.index("file:lifted.md")


# -- 4. a caller's expansion wins; the baseline verb never runs it ------------

def test_a_callers_expand_wins(built, monkeypatch):
    monkeypatch.setattr(rm3, "feedback_terms", lambda *a, **k: pytest.fail("RM3 ran beside --expand"))
    expanded = _payload(run_query(built, "alpha", 10, tune=_tune(0.3), expand="gamma")[0])
    assert expanded == _payload(run_query(built, "alpha", 10, tune=DEFAULT_TUNE, expand="gamma")[0])


def test_lexical_forces_rm3_off():
    source = (ENGINE / "src" / "fux" / "query" / "__init__.py").read_text(encoding="utf-8")
    assert "ask_boost=False, ask_related=False, rm3_weight=0.0" in source
    node = (ENGINE / "node" / "src" / "query" / "run.mjs").read_text(encoding="utf-8")
    assert "askBoost: false, askRelated: false, rm3Weight: 0.0" in node


# -- 5. the scan and the accelerator agree ------------------------------------

@pytest.mark.parametrize("weight", (0.0, *ARMS))
def test_accelerator_equals_scan_at_every_arm(built, weight):
    scan = _payload(run_query(built, "alpha", 10, tune=_tune(weight), force_scan=True)[0])
    fast, path = run_query(built, "alpha", 10, tune=_tune(weight), force_scan=False)
    assert path == "accelerator"
    assert _payload(fast) == scan


# -- 6. the Node reader -------------------------------------------------------

@pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")
@pytest.mark.parametrize("weight", (0.0, 0.3))
def test_node_reader_ranks_byte_identically(built, weight):
    """Through each reader's own `tune.toml` loader, so the key's parsing is
    under the differential law as well as the mechanism."""
    (built / ".fux").mkdir(exist_ok=True)
    (built / ".fux" / "tune.toml").write_text(f"[ranking]\nrm3_weight = {weight}\n", encoding="utf-8")
    py = [[r.id, r.score] for r in run_query(built, "alpha", 10)[0]]
    script = (
        f'import {{ runQuery }} from {json.dumps(str(ENGINE / "node/src/query/run.mjs"))};'
        f'const out = runQuery({json.dumps(str(built))}, "alpha", 10);'
        'console.log(JSON.stringify(out.results.map((r) => [r.id, r.score])));'
    )
    js = json.loads(subprocess.check_output(["node", "--input-type=module", "-e", script], text=True))
    assert js == py
