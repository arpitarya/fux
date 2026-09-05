"""W-110 — questions, the self-retrieval filter, and declared supersession.

Enrichment stopped asking for prose on 2026-09-05 because prose was measured
and did not pay: a blind run scored **+1 fixed / −1 broken**, and the break was
context prose carrying currency words into a *superseded* record. A question is
a narrower object — a retrieval claim about one document — and `--check` can
put it to the index and see.

Three properties here, and the second is the one that makes the filter honest
rather than decorative.
"""

from __future__ import annotations

import pytest

from fux.derive import build
from fux.enrich import ENRICH_DIR, SELF_RETRIEVAL_K, enrich_path, is_question, plan, superseded_by
from fux.ingest import run as ingest_run
from fux.store import read_index


def _doc(root, name: str, title: str, body: str) -> None:
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / name).write_text(f"---\ntitle: {title}\n---\n\n# {title}\n\n{body}\n", encoding="utf-8")


def _repo(tmp_path):
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = tmp_path / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    dirs.write_text("docs                enrich=true\n", encoding="utf-8")
    return tmp_path


def _enrich(root, sha: str, source: str, body: str, **extra) -> None:
    meta = {
        "source": source, "source_sha": sha, "chunks": "1",
        "model": "test", "generated": "2026-09-05", "skill": "fux-enrich@1",
        **extra,
    }
    path = enrich_path(root, sha)
    path.parent.mkdir(parents=True, exist_ok=True)
    block = "\n".join(f"{k}: {v}" for k, v in meta.items())
    path.write_text(f"---\n{block}\n---\n{body}\n", encoding="utf-8")


def _sha_of(root, loc: str) -> str:
    return next(r["sha"] for r in read_index(root).values() if r["loc"] == loc)


def _scopes(root):
    from fux.enrich import _scopes as scopes_of

    return scopes_of(root)


# -- 1. what counts as a question --------------------------------------------


@pytest.mark.parametrize("line", [
    "How do I roll back the gateway?",
    "  what breaks if I skip the freeze?  ",
    "- Who approves a tier 1 deploy?",
])
def test_a_question_is_a_line_ending_in_a_question_mark(line):
    assert is_question(line)


@pytest.mark.parametrize("line", [
    "Sets the payment gateway resilience policy.",
    "",
    "?",
    "supersedes: docs/a.md",
])
def test_everything_else_is_not_a_question(line):
    """Deliberately shallow. A cleverer test refuses lines a human wrote on
    purpose, and an older prose body must stay valid — which it does, because
    a body with no `?` line has nothing for the filter to check."""
    assert not is_question(line)


# -- 2. the filter ------------------------------------------------------------


def test_a_question_that_retrieves_its_document_passes(tmp_path):
    root = _repo(tmp_path)
    _doc(root, "rollback.md", "Gateway rollback",
         "Drain the sidecar, then revert the release. The freeze must be lifted first.")
    _doc(root, "catering.md", "Catering", "The espresso beans arrive on Tuesdays.")
    ingest_run.run(root)
    build(root)

    _enrich(root, _sha_of(root, "docs/rollback.md"), "docs/rollback.md",
            "How do I drain the sidecar and revert a release?\n")
    _enrich(root, _sha_of(root, "docs/catering.md"), "docs/catering.md",
            "When do the espresso beans arrive?\n")

    reports = plan(root, _scopes(root), self_retrieval_k=SELF_RETRIEVAL_K)
    assert [r.unretrievable for r in reports] == [[]]
    assert reports[0].ok == 2


def test_a_question_that_retrieves_ANOTHER_document_is_refused(tmp_path):
    """doc2query--'s whole point: such a question is not neutral, it adds terms
    that pull the *other* document up."""
    root = _repo(tmp_path)
    _doc(root, "rollback.md", "Gateway rollback",
         "Drain the sidecar, then revert the release. The freeze must be lifted first.")
    _doc(root, "catering.md", "Catering", "The espresso beans arrive on Tuesdays.")
    ingest_run.run(root)
    build(root)

    # A question about coffee, attached to the rollback runbook.
    _enrich(root, _sha_of(root, "docs/rollback.md"), "docs/rollback.md",
            "When do the espresso beans arrive?\n")

    reports = plan(root, _scopes(root), self_retrieval_k=SELF_RETRIEVAL_K)
    refused = [u for r in reports for u in r.unretrievable]
    assert len(refused) == 1
    path, misses = refused[0]
    assert path.startswith(ENRICH_DIR)
    assert misses[0][0] == "When do the espresso beans arrive?"


def _retrieves(root, question: str, loc: str, weights) -> bool:
    """Does `question` place `loc` in the top `SELF_RETRIEVAL_K` at `weights`?"""
    import dataclasses

    from fux.query import run_query
    from fux.tune import Tune

    tune = dataclasses.replace(Tune(), field_weights=weights)
    results, _ = run_query(root, question, SELF_RETRIEVAL_K, force_scan=True, tune=tune)
    return loc in [r.loc for r in results]


def test_the_title_field_is_what_the_zeroing_removes(tmp_path):
    """🔴 W-110's stated hazard, isolated.

    The question is made **only** of words in the document's `title` — its body
    shares none of them and no other document has them. So it retrieves at the
    engine's own weights and must NOT retrieve at the filter's. Asserting both
    halves is what stops this from passing for an unrelated reason: a test that
    only checked "refused" stays green when the zeroing is deleted.
    """
    from fux.enrich import _FILTER_WEIGHTS
    from fux.query.bm25f import FIELD_WEIGHTS

    root = _repo(tmp_path)
    # No `# {title}` heading echo: the title words must live in the TITLE field
    # alone, or the `heading` field carries them and the zeroing proves nothing.
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "zeta.md").write_text(
        "---\ntitle: Quokka Vandelay Protocol\n---\n\n"
        "Drain the sidecar, then revert the release.\n",
        encoding="utf-8",
    )
    _doc(root, "other.md", "Catering", "The espresso beans arrive on Tuesdays.")
    ingest_run.run(root)

    q = "What is the Quokka Vandelay Protocol?"
    assert _retrieves(root, q, "docs/zeta.md", FIELD_WEIGHTS), (
        "precondition: at the engine's own weights a title echo DOES retrieve"
    )
    assert not _retrieves(root, q, "docs/zeta.md", _FILTER_WEIGHTS), (
        "a question made only of the title still retrieves — `title` is not zeroed"
    )

    _enrich(root, _sha_of(root, "docs/zeta.md"), "docs/zeta.md", q + "\n")
    reports = plan(root, _scopes(root), self_retrieval_k=SELF_RETRIEVAL_K)
    assert [u[0] for r in reports for u in r.unretrievable]


def test_the_ctx_field_is_what_stops_an_enrichment_vouching_for_itself(tmp_path):
    """🔴 The circularity, isolated the same way.

    Enrichment text is indexed **as `ctx`**. After the enrichment is ingested,
    its own question retrieves its own document *through itself* at the
    engine's weights — so the filter would pass on the second run what it
    failed on the first. Both halves are asserted, for the reason above.
    """
    from fux.enrich import _FILTER_WEIGHTS
    from fux.query.bm25f import FIELD_WEIGHTS

    root = _repo(tmp_path)
    _doc(root, "rollback.md", "Gateway rollback",
         "Drain the sidecar, then revert the release.")
    _doc(root, "catering.md", "Catering", "The espresso beans arrive on Tuesdays.")
    ingest_run.run(root)

    q = "When do the espresso beans arrive?"
    sha = _sha_of(root, "docs/rollback.md")
    _enrich(root, sha, "docs/rollback.md", q + "\n")
    ingest_run.run(root)  # the enrichment is now this document's `ctx`

    assert _retrieves(root, q, "docs/rollback.md", FIELD_WEIGHTS), (
        "precondition: with `ctx` scored, the enrichment vouches for itself"
    )
    assert not _retrieves(root, q, "docs/rollback.md", _FILTER_WEIGHTS), (
        "the question still retrieves its document — `ctx` is not zeroed, so the "
        "filter's answer depends on whether it has been run before"
    )

    reports = plan(root, _scopes(root), self_retrieval_k=SELF_RETRIEVAL_K)
    assert [u for r in reports for u in r.unretrievable]


def test_the_filter_does_not_run_without_a_k(tmp_path):
    """`--plan` must not pay for a query per question. `k = 0` is off."""
    root = _repo(tmp_path)
    _doc(root, "rollback.md", "Gateway rollback", "Drain the sidecar, then revert.")
    _doc(root, "catering.md", "Catering", "The espresso beans arrive on Tuesdays.")
    ingest_run.run(root)
    _enrich(root, _sha_of(root, "docs/rollback.md"), "docs/rollback.md",
            "When do the espresso beans arrive?\n")

    reports = plan(root, _scopes(root))  # no k
    assert [r.unretrievable for r in reports] == [[]]
    assert reports[0].ok == 1


def test_a_prose_body_written_under_the_old_skill_still_passes(tmp_path):
    """Back-compatibility, asserted rather than assumed. A body with no
    `?`-terminated line has nothing for the filter to check, so every
    enrichment written before 2026-09-05 stays valid."""
    root = _repo(tmp_path)
    _doc(root, "rollback.md", "Gateway rollback", "Drain the sidecar, then revert.")
    ingest_run.run(root)
    build(root)
    _enrich(root, _sha_of(root, "docs/rollback.md"), "docs/rollback.md",
            "Sets the release rollback policy. Covers the freeze and the drain order.\n")

    reports = plan(root, _scopes(root), self_retrieval_k=SELF_RETRIEVAL_K)
    assert [r.unretrievable for r in reports] == [[]]


# -- 3. declared supersession -------------------------------------------------


def test_superseded_by_is_read_from_the_frontmatter():
    assert superseded_by("---\nsuperseded_by: docs/b.md\n---\nbody\n") == "docs/b.md"
    assert superseded_by("---\nsource: docs/a.md\n---\nbody\n") == ""
    assert superseded_by("no frontmatter") == ""


def test_an_enrichments_superseded_by_retires_its_document(tmp_path):
    """The declared path a retired document cannot take itself: its successor
    did not exist when it was written."""
    root = _repo(tmp_path)
    _doc(root, "old.md", "Helix mesh", "The mesh handles east-west traffic.")
    _doc(root, "new.md", "Calder gateway", "The gateway handles east-west traffic.")
    ingest_run.run(root)

    _enrich(root, _sha_of(root, "docs/old.md"), "docs/old.md",
            "How did east-west traffic work before?\n", superseded_by="docs/new.md")
    ingest_run.run(root)

    records = {r["loc"]: r for r in read_index(root).values()}
    assert records["docs/old.md"].get("superseded") is True
    assert records["docs/new.md"].get("superseded") is not True


def test_a_superseded_by_naming_nothing_retires_nothing(tmp_path):
    """A dangling name would retire a document in favour of nothing, and it
    would then rank lower with no successor for a reader to go to."""
    root = _repo(tmp_path)
    _doc(root, "old.md", "Helix mesh", "The mesh handles east-west traffic.")
    ingest_run.run(root)
    _enrich(root, _sha_of(root, "docs/old.md"), "docs/old.md",
            "How does east-west traffic work?\n", superseded_by="docs/does-not-exist.md")
    ingest_run.run(root)

    records = {r["loc"]: r for r in read_index(root).values()}
    assert records["docs/old.md"].get("superseded") is not True


def test_a_self_reference_retires_nothing(tmp_path):
    root = _repo(tmp_path)
    _doc(root, "old.md", "Helix mesh", "The mesh handles east-west traffic.")
    ingest_run.run(root)
    _enrich(root, _sha_of(root, "docs/old.md"), "docs/old.md",
            "How does east-west traffic work?\n", superseded_by="docs/old.md")
    ingest_run.run(root)

    records = {r["loc"]: r for r in read_index(root).values()}
    assert records["docs/old.md"].get("superseded") is not True


def test_a_malformed_enrichment_retires_nothing(tmp_path):
    """A file fux would not index must not be able to move a ranking either."""
    root = _repo(tmp_path)
    _doc(root, "old.md", "Helix mesh", "The mesh handles east-west traffic.")
    _doc(root, "new.md", "Calder gateway", "The gateway handles east-west traffic.")
    ingest_run.run(root)
    sha = _sha_of(root, "docs/old.md")
    path = enrich_path(root, sha)
    path.parent.mkdir(parents=True, exist_ok=True)
    # `superseded_by` present, but the required keys are not.
    path.write_text(f"---\nsuperseded_by: docs/new.md\n---\nbody\n", encoding="utf-8")
    ingest_run.run(root)

    records = {r["loc"]: r for r in read_index(root).values()}
    assert records["docs/old.md"].get("superseded") is not True


# -- 4. the defect the ctx test uncovered ------------------------------------


def test_a_new_enrichment_is_indexed_on_the_NEXT_ingest(tmp_path):
    """🔴 **A pre-existing defect, found by writing the test above.**

    Reuse was keyed on the *document's* content sha alone, so a newly written
    `.fux/enrich/` file changed nothing until the document itself changed or
    `--full` ran. `fux enrich --check` reported `ok`, the file was committed
    and reviewed, and its vocabulary **never reached the index**. It presented
    as a working feature.
    """
    root = _repo(tmp_path)
    _doc(root, "rollback.md", "Gateway rollback", "Drain the sidecar, then revert.")
    _doc(root, "catering.md", "Catering", "The espresso beans arrive on Tuesdays.")
    ingest_run.run(root)

    sha = _sha_of(root, "docs/rollback.md")
    _enrich(root, sha, "docs/rollback.md", "How do I quiesce the ingress before a cutover?\n")
    ingest_run.run(root)  # the document did NOT change

    from fux.query import run_query

    results, _ = run_query(root, "quiesce the ingress before a cutover", 3, force_scan=True)
    assert "docs/rollback.md" in [r.loc for r in results], (
        "the enrichment was written and never indexed — reuse is keyed on the "
        "document's sha and does not see its enrichment change"
    )


def test_a_DELETED_enrichment_is_removed_from_the_index(tmp_path):
    """The other half, and it matters as much.

    A reuse keyed only on an enrichment's *presence* would leave its vocabulary
    in the index with nothing on disk explaining where it came from.
    """
    root = _repo(tmp_path)
    _doc(root, "rollback.md", "Gateway rollback", "Drain the sidecar, then revert.")
    _doc(root, "catering.md", "Catering", "The espresso beans arrive on Tuesdays.")
    ingest_run.run(root)

    sha = _sha_of(root, "docs/rollback.md")
    _enrich(root, sha, "docs/rollback.md", "How do I quiesce the ingress before a cutover?\n")
    ingest_run.run(root)
    enrich_path(root, sha).unlink()
    ingest_run.run(root)

    from fux.query import run_query

    results, _ = run_query(root, "quiesce the ingress before a cutover", 3, force_scan=True)
    assert "docs/rollback.md" not in [r.loc for r in results], (
        "the deleted enrichment's vocabulary is still indexed"
    )


def test_an_unchanged_enrichment_does_not_force_re_extraction(tmp_path):
    """The invalidation must be keyed on the enrichment's CONTENT, not on its
    existence — or every enriched document re-extracts on every ingest, which
    is the delta-ingest guarantee gone."""
    root = _repo(tmp_path)
    _doc(root, "rollback.md", "Gateway rollback", "Drain the sidecar, then revert.")
    ingest_run.run(root)
    _enrich(root, _sha_of(root, "docs/rollback.md"), "docs/rollback.md",
            "How do I drain the sidecar?\n")
    ingest_run.run(root)

    stats = ingest_run.run(root)  # third run: nothing moved
    assert stats.reused_count >= 1, (
        "an unchanged enrichment forced a re-extraction — the digest is keyed on "
        "presence rather than on content"
    )
