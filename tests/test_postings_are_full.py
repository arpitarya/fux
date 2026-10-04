"""Every analyzer term of every document has a posting -- the law P1 closed on.

**What this enforces:** [SR-POSTINGS](../records/0112_postings.md) Consequences --
*pruning work is forbidden*; P1 measured the best pruned arm 35.9 points below
unpruned recall@20, so the index carries **full postings, permanently**. Nothing
mechanical stopped a pruning change from arriving as "a size win"; this does,
independently of the code that writes postings. W-246 (B-072).

**How it is independent.** A fixture corpus is ingested by the REAL pipeline in a
temp directory, then judged against the analyzer run on the fixture's own text
(`tokenize`, the same pipeline the query side uses -- not the extractor's
output). Two layers:

1. **Committed.** Every analyzer term of every field (title, headings, body, path)
   of every document has its hash in that document's committed `terms`, with a
   non-zero tf. Extra terms are allowed (front-matter identity values, identifier
   families); a MISSING term is the pruning defect.
2. **Runtime.** After `fux build`, every distinct term, asked as a one-word query on
   BOTH read paths (scan, and the accelerator), returns every document that
   carries it. A posting that exists in the shard but not in the derived plane is
   the same defect one layer down.

**What it cannot do.** It proves the fixture's terms survive, not that a differently
shaped corpus (very long documents, decoders) does; the fixture is deliberately
small so a failure names one term. It also fixes no size, and says nothing about
whether full postings are the *right* design -- that was P1's, and is closed.
"""

from __future__ import annotations

import pytest

from fux import store
from fux.derive import build
from fux.ingest.run import run
from fux.query import run_query
from fux.query.tokenize import tokenize, tokenize_pairs
from fux.store import term_hash
from l12_fixtures import write_config

DOCS = {
    "docs/retry.md": (
        "# Retry policy\n\n## Backoff schedule\n\nThe gateway retries failed requests "
        "with exponential backoff. getUserName and ERR_2031 are logged; see RF-118.\n"
    ),
    "docs/rollback.md": (
        "# Rollback procedure\n\nTo roll back a deployment, drain traffic, restore the "
        "previous release, and verify the health checks before reopening.\n\n"
        "## Verification\n\nRun the smoke tests twice.\n"
    ),
    "docs/runbooks/onboarding-checklist.md": (
        "# Onboarding checklist\n\nNew engineers receive access, a laptop, and a buddy. "
        "Quarterly reviews cover ownership, escalation paths, and pager rotation.\n"
    ),
}


def _fields(rel: str, text: str) -> list[str]:
    """The analyzer's input per field, read off the fixture text and nothing else."""
    lines = text.splitlines()
    headings = [l.lstrip("# ").strip() for l in lines if l.startswith("#")]
    body = " ".join(l for l in lines if not l.startswith("#"))
    return [*headings, body, rel.replace("/", " ").replace(".", " ")]


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    root = tmp_path_factory.mktemp("full-postings")
    (root / ".fux" / "sources").mkdir(parents=True)
    (root / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (root / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    write_config(root)
    for rel, text in DOCS.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    run(root, refresh_urls=False, full=False)
    build(root)
    return root


def _expected() -> dict[str, set[str]]:
    return {
        f"file:{rel}": {t for chunk in _fields(rel, text) for t in tokenize(chunk)}
        for rel, text in DOCS.items()
    }


def test_the_fixture_is_not_trivial():
    expected = _expected()
    assert all(len(terms) >= 10 for terms in expected.values())
    # an identifier, a stemmed word and a stopword-adjacent phrase are in play
    assert "getusernam" in expected["file:docs/retry.md"]


def test_every_analyzer_term_has_a_committed_posting(repo):
    """SR-POSTINGS: a term the analyzer yields and the record omits is pruning."""
    index = store.read_index(repo)
    missing = {}
    for doc_id, terms in _expected().items():
        have = {h for h, tf in index[doc_id]["terms"].items() if any(tf)}
        lost = sorted(t for t in terms if term_hash(t) not in have)
        if lost:
            missing[doc_id] = lost
    assert not missing, f"analyzer terms with no committed posting (pruning?): {missing}"


@pytest.mark.parametrize("force_scan", [True, False], ids=["scan", "accelerator"])
def test_every_term_finds_every_document_that_carries_it(repo, force_scan):
    """SR-POSTINGS: the derived plane answers a one-word query with every carrier."""
    expected = _expected()
    # A query is analyzed again, so it must be typed as a SURFACE word: the
    # analyzed form of `deployment` (`deploy`) would be stemmed a second time.
    surface = {
        analyzed: word
        for rel, text in DOCS.items()
        for chunk in _fields(rel, text)
        for word, analyzed in tokenize_pairs(chunk)
    }
    wrong = {}
    for term in sorted(set().union(*expected.values())):
        carriers = {d for d, terms in expected.items() if term in terms}
        results, _ = run_query(
            repo, surface[term], 50, force_scan=force_scan, use_tune=False, confidence_out={}
        )
        got = {r.id for r in results}
        if not carriers <= got:
            wrong[term] = sorted(carriers - got)
    assert not wrong, f"terms whose postings do not reach the query path: {wrong}"
