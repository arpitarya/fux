"""ADR-PROVENANCE — the derivation, the receipt, the journal, and `verify`.

**What these tests are asserting, and what they deliberately are not.**

They assert *rules*, never numbers: that a verdict is one of four states and
that the fourth is reachable; that a receipt keyed on the committed shards
reproduces on a byte-identical tree and drifts on an edited one; that the
journal stays bounded and local. No test here pins a score, because a test that
pins a score fails on every legitimate ranking change and teaches the next
session to edit the test.

⚠ **The `unverifiable` cases carry the most weight.** Three of this repo's
recorded defects were a field reporting confidently on something it no longer
knew. A green suite that never exercised "we did not look" would be the fourth.
"""

from __future__ import annotations

import json

from fux.query import provenance
from fux.query.rank import AskResult
from fux.query.scan import ask
from fux.query.tokenize import tokenize
from fux.store import term_hash, write_index


def _h(word: str) -> str:
    return term_hash(tokenize(word)[0])


def _rec(doc_id, title, flen, terms) -> dict:
    return {
        "id": doc_id,
        "src": "git",
        "loc": doc_id.removeprefix("file:"),
        "mode": "extracted",
        "meta": "plain",
        "title": title,
        "phrases": [],
        "terms": terms,
        "flen": flen,
        "edges": [],
    }


def _corpus(tmp_path):
    write_index(
        tmp_path,
        [
            _rec("file:mesh.md", "Mesh", [10, 2], {_h("rollback"): [3, 1]}),
            _rec("file:other.md", "Other", [10, 2], {_h("rollback"): [1, 0]}),
        ],
    )


# -- identity ------------------------------------------------------------------


def test_index_digest_is_empty_without_an_index(tmp_path):
    """An absent index is `""`, never a hash of nothing.

    A digest of the empty string would be a stable, plausible-looking value
    that `verify` could match against another empty tree — two different
    repositories agreeing that an answer reproduced.
    """
    assert provenance.index_digest(tmp_path) == ""


def test_index_digest_is_stable_and_moves_with_content(tmp_path):
    _corpus(tmp_path)
    first = provenance.index_digest(tmp_path)
    assert first and provenance.index_digest(tmp_path) == first

    write_index(tmp_path, [_rec("file:mesh.md", "Mesh", [10, 2], {_h("rollback"): [9, 1]})])
    assert provenance.index_digest(tmp_path) != first


def test_tune_digest_says_none_rather_than_hashing_absence(tmp_path):
    """`"none"` is a state, not a missing value.

    An answer that changed because somebody *added* a tune file has drifted on
    config exactly as much as one whose weights were edited, and `verify` can
    only say so if absence has its own token.
    """
    assert provenance.tune_digest(tmp_path) == "none"
    (tmp_path / ".fux").mkdir(exist_ok=True)
    (tmp_path / ".fux" / "tune.toml").write_text("[bm25f]\nk1 = 1.2\n")
    assert provenance.tune_digest(tmp_path) not in ("", "none")


# -- the derivation ------------------------------------------------------------


def test_derivation_reports_the_four_gates(tmp_path):
    _corpus(tmp_path)
    results = ask(tmp_path, "rollback")
    why = provenance.derive(
        tmp_path, "rollback", results[:1], path="scan",
        stats={"df": {_h("rollback"): 2}, "n": 2}, window=results,
    )
    assert why.gates.reachable == 2
    assert why.gates.in_window == 2
    assert why.gates.placed == 1
    assert why.gates.answered == 1


def test_the_cut_line_is_the_window_not_the_placed_set(tmp_path):
    """The negative space is the point.

    `cut_score` must come from the last document the retrieval window held —
    not the last one shown. Reading it off the truncated list would make it a
    restatement of the lowest score already printed, which is exactly the
    number a reader can already see.
    """
    _corpus(tmp_path)
    results = ask(tmp_path, "rollback")
    assert len(results) == 2
    why = provenance.derive(
        tmp_path, "rollback", results[:1], path="scan", window=results
    )
    assert why.gates.cut_score == results[-1].score
    assert why.gates.cut_score != results[0].score


def test_matched_terms_carry_the_committed_per_field_counts(tmp_path):
    _corpus(tmp_path)
    records = {"file:mesh.md": _rec("file:mesh.md", "Mesh", [10, 2], {_h("rollback"): [3, 1]})}
    why = provenance.derive(
        tmp_path,
        "rollback",
        [AskResult(id="file:mesh.md", title="Mesh", loc="mesh.md", score=1.0)],
        path="scan",
        stats={"df": {_h("rollback"): 2}, "n": 2},
        records=records.get,
    )
    (doc,) = why.documents
    (hit,) = doc.matched
    assert hit.term == "rollback"
    assert hit.fields == (3, 1)
    assert hit.df == 2
    assert doc.missing == ()


def test_a_repeated_query_word_does_not_misalign_the_terms(tmp_path):
    """⚠ The trap this module nearly shipped.

    `query_term_hashes` DEDUPES on the hash; `analyze_pairs` does not. A `zip`
    of the two silently misaligns every term after a repeated word — the same
    hazard `confidence.py` names, one plane over. A query that repeats a word
    must still report that word against its own frequency.
    """
    _corpus(tmp_path)
    records = {"file:mesh.md": _rec("file:mesh.md", "Mesh", [10, 2], {_h("rollback"): [3, 1]})}
    why = provenance.derive(
        tmp_path,
        "rollback rollback rollback",
        [AskResult(id="file:mesh.md", title="Mesh", loc="mesh.md", score=1.0)],
        path="scan",
        stats={"df": {_h("rollback"): 2}, "n": 2},
        records=records.get,
    )
    (doc,) = why.documents
    assert len(doc.matched) == 1
    assert doc.matched[0].term == "rollback"
    assert doc.matched[0].df == 2


def test_absent_query_terms_are_named_in_the_users_own_spelling(tmp_path):
    """`mTLS` analyzes to `mtl`, and reporting `mtl` is worse than silence."""
    _corpus(tmp_path)
    records = {"file:mesh.md": _rec("file:mesh.md", "Mesh", [10, 2], {_h("rollback"): [3, 1]})}
    why = provenance.derive(
        tmp_path,
        "rollback mTLS",
        [AskResult(id="file:mesh.md", title="Mesh", loc="mesh.md", score=1.0)],
        path="scan",
        records=records.get,
    )
    (doc,) = why.documents
    assert "mTLS" in doc.missing


def test_rank_deltas_are_absent_rather_than_equal_when_not_measured(tmp_path):
    """Absent means *not computed*. Present-and-equal means *unchanged*.

    Emitting `rank_before_rerank == rank` on a tree with reranking off would
    look like a measurement and be a copy of the number beside it.
    """
    _corpus(tmp_path)
    why = provenance.derive(
        tmp_path,
        "rollback",
        [AskResult(id="file:mesh.md", title="Mesh", loc="mesh.md", score=1.0)],
        path="scan",
    )
    assert "rank_before_rerank" not in why.documents[0].as_dict()
    assert "rank_untuned" not in why.documents[0].as_dict()


def test_derive_never_raises_on_a_broken_record_reader(tmp_path):
    """A diagnostic that can fail a query is worse than no diagnostic."""

    def boom(_doc_id):
        raise RuntimeError("record store on fire")

    why = provenance.derive(
        tmp_path,
        "rollback",
        [AskResult(id="file:mesh.md", title="Mesh", loc="mesh.md", score=1.0)],
        path="scan",
        records=boom,
    )
    assert why.documents[0].matched == ()


# -- the receipt ---------------------------------------------------------------


def test_a_receipt_carries_no_wall_clock(tmp_path):
    """Two receipts for the same answer must be byte-identical.

    A timestamp would make every receipt unique, which defeats a re-runnable
    claim and breaks L3 on a deterministic path.
    """
    _corpus(tmp_path)
    subject = [{"id": "file:mesh.md", "loc": "mesh.md:L1-L2", "sha": "abc123"}]
    one = provenance.receipt(tmp_path, "rollback", path="refer", subject=subject)
    two = provenance.receipt(tmp_path, "rollback", path="refer", subject=subject)
    assert one == two
    assert provenance.receipt_sha(one) == provenance.receipt_sha(two)
    blob = json.dumps(one)
    for word in ("time", "date", "stamp", "clock"):
        assert word not in blob.lower()


def test_a_receipt_records_the_question_in_plaintext(tmp_path):
    """L8 as reverted (Arpit, 2026-08-27) permits this; before it, it was illegal."""
    _corpus(tmp_path)
    payload = provenance.receipt(tmp_path, "how do I roll back", path="refer", subject=[])
    assert payload["predicate"]["inputs"]["query"] == "how do I roll back"


# -- the journal ---------------------------------------------------------------


def test_the_journal_is_local_and_gitignored_by_its_directory(tmp_path):
    _corpus(tmp_path)
    payload = provenance.receipt(tmp_path, "rollback", path="refer", subject=[])
    provenance.remember(tmp_path, payload)
    path = provenance.journal_path(tmp_path)
    assert path.exists()
    assert path.parent.name == "runtime"
    assert ".fux" in path.parts


def test_the_journal_is_bounded_and_drops_the_oldest(tmp_path):
    _corpus(tmp_path)
    for i in range(6):
        provenance.remember(
            tmp_path,
            provenance.receipt(tmp_path, f"q{i}", path="refer", subject=[]),
            max_entries=3,
        )
    entries = provenance.read_journal(tmp_path)
    assert len(entries) == 3
    assert [e["predicate"]["inputs"]["query"] for e in entries] == ["q3", "q4", "q5"]


def test_a_zero_bound_writes_nothing(tmp_path):
    """`journal_max = 0` is *off*, not *unbounded*."""
    _corpus(tmp_path)
    provenance.remember(
        tmp_path, provenance.receipt(tmp_path, "q", path="refer", subject=[]), max_entries=0
    )
    assert not provenance.journal_path(tmp_path).exists()


def test_reading_a_corrupt_journal_line_skips_it(tmp_path):
    _corpus(tmp_path)
    provenance.remember(tmp_path, provenance.receipt(tmp_path, "q", path="refer", subject=[]))
    path = provenance.journal_path(tmp_path)
    path.write_text(path.read_text() + "{not json\n")
    assert len(provenance.read_journal(tmp_path)) == 1


# -- verification --------------------------------------------------------------


def test_every_verdict_is_one_of_the_declared_four():
    assert set(provenance.VERDICTS) == {
        provenance.REPRODUCED,
        provenance.DRIFTED_CORPUS,
        provenance.DRIFTED_CONFIG,
        provenance.UNVERIFIABLE,
    }


def test_matching_inputs_without_a_rerun_is_unverifiable_not_reproduced(tmp_path):
    """⚠ The single most important assertion in this file.

    Inputs matching is not an answer reproducing. Returning `reproduced` here
    would be the fourth instance of this repo's recurring defect: a confident
    verdict about something nobody checked.
    """
    _corpus(tmp_path)
    payload = provenance.receipt(tmp_path, "rollback", path="refer", subject=[])
    result = provenance.verify(tmp_path, payload)
    assert result.verdict == provenance.UNVERIFIABLE
    assert "not re-run" in result.note


def test_a_rerun_that_returns_the_same_shas_reproduces(tmp_path):
    _corpus(tmp_path)
    subject = [{"id": "file:mesh.md", "loc": "mesh.md:L1-L2", "sha": "abc123"}]
    payload = provenance.receipt(tmp_path, "rollback", path="refer", subject=subject)
    result = provenance.verify(tmp_path, payload, rerun=lambda q: [{"id": "file:mesh.md", "sha": "abc123"}])
    assert result.verdict == provenance.REPRODUCED


def test_changed_bytes_drift_on_the_corpus(tmp_path):
    _corpus(tmp_path)
    subject = [{"id": "file:mesh.md", "loc": "mesh.md:L1-L2", "sha": "abc123"}]
    payload = provenance.receipt(tmp_path, "rollback", path="refer", subject=subject)
    result = provenance.verify(tmp_path, payload, rerun=lambda q: [{"id": "file:mesh.md", "sha": "def456"}])
    assert result.verdict == provenance.DRIFTED_CORPUS
    assert result.expected == ("abc123",)
    assert result.actual == ("def456",)


def test_an_edited_index_drifts_on_the_corpus(tmp_path):
    _corpus(tmp_path)
    payload = provenance.receipt(tmp_path, "rollback", path="refer", subject=[])
    write_index(tmp_path, [_rec("file:mesh.md", "Mesh", [99, 2], {_h("rollback"): [3, 1]})])
    assert provenance.verify(tmp_path, payload).verdict == provenance.DRIFTED_CORPUS


def test_a_new_tune_file_drifts_on_CONFIG_not_on_corpus(tmp_path):
    """⚠ Naming the wrong cause is how an audit trail becomes worse than none.

    A tune edit changes the answer without changing one indexed byte. Config is
    therefore checked *before* corpus, so the verdict names the thing that
    actually moved.
    """
    _corpus(tmp_path)
    payload = provenance.receipt(tmp_path, "rollback", path="refer", subject=[])
    (tmp_path / ".fux").mkdir(exist_ok=True)
    (tmp_path / ".fux" / "tune.toml").write_text("[bm25f]\nk1 = 9.9\n")
    result = provenance.verify(tmp_path, payload)
    assert result.verdict == provenance.DRIFTED_CONFIG
    assert "tune" in result.note


def test_a_different_engine_version_drifts_on_config(tmp_path):
    _corpus(tmp_path)
    payload = provenance.receipt(tmp_path, "rollback", path="refer", subject=[])
    payload["predicate"]["engine"]["version"] = "0.0.0-not-this-one"
    result = provenance.verify(tmp_path, payload)
    assert result.verdict == provenance.DRIFTED_CONFIG


def test_a_tree_with_no_index_is_unverifiable(tmp_path, tmp_path_factory):
    """Not `drifted`. Nothing was compared, so nothing may be reported."""
    _corpus(tmp_path)
    payload = provenance.receipt(tmp_path, "rollback", path="refer", subject=[])
    elsewhere = tmp_path_factory.mktemp("empty")
    assert provenance.verify(elsewhere, payload).verdict == provenance.UNVERIFIABLE


def test_a_foreign_object_is_unverifiable_rather_than_an_exception(tmp_path):
    assert provenance.verify(tmp_path, {"schema": "something.else"}).verdict == (
        provenance.UNVERIFIABLE
    )
    assert provenance.verify(tmp_path, {}).verdict == provenance.UNVERIFIABLE


# -- the surface ---------------------------------------------------------------
#
# ⚠ **These exist because of a defect that shipped for one run.** The receipt
# was built from the PRE-upgrade confidence block, so it reported
# `verified: unverified` beside its own `verdicts` saying `current` — one
# answer, two disagreeing statements about it, which is precisely what a
# provenance plane exists to make impossible. It was caught by running the
# command, not by a test. Per CLAUDE.md's two-strikes rule the class is gated
# here rather than re-learned.


class _Args:
    def __init__(self, **kw):
        self.query = kw.pop("query", "rollback")
        self.json = kw.pop("json", True)
        self.top = kw.pop("top", 5)
        self.fast = False
        self.scan = True
        self.no_tune = False
        self.no_refer = False
        self.audit = False
        self.receipt = False
        self.journal = False
        self.why = False
        # ADR-CONFIDENCE decision 11 gates the CLI's confidence block behind
        # `--band`. On by default HERE because this file's subject is the
        # receipt and the derivation, both of which quote the block — a test
        # about provenance must not silently become a test about the gate.
        self.band = kw.pop("band", True)
        for k, v in kw.items():
            setattr(self, k, v)


def test_the_receipt_survives_without_band(tmp_path, monkeypatch, capsys):
    """A receipt is a record of the run, not a rendering of the answer.

    ⚠ Gating `confidence` behind `--band` must not gate what the RECEIPT
    carries. The receipt has to be re-runnable on its own, so its own copy of
    the block stays regardless of whether the answer printed one — otherwise
    `fux verify` would silently depend on a display flag.
    """
    from fux import query as query_mod

    root = _answerable_repo(tmp_path)
    monkeypatch.setattr(query_mod, "_root", lambda: root)
    query_mod.cmd_answer(_Args(query="rollback", receipt=True, band=False))
    payload = json.loads(capsys.readouterr().out)

    assert "confidence" not in payload, "the answer's own block is gated"
    assert payload["receipt"]["predicate"]["confidence"], "the receipt's is not"


def _answerable_repo(tmp_path):
    """A tree the refer plane can actually fetch from: an index AND the file."""
    (tmp_path / "fux.toml").write_text("[fux]\nversion = 1\n")
    docs = tmp_path / "docs"
    docs.mkdir()
    body = "# Mesh\n\n## Rollback procedure\n\nDrain the sidecar and fail open.\n"
    (docs / "mesh.md").write_text(body)
    import hashlib

    sha = hashlib.sha1(body.encode()).hexdigest()
    rec = _rec("file:docs/mesh.md", "Mesh", [10, 2], {_h("rollback"): [3, 1]})
    rec["sha"] = sha
    write_index(tmp_path, [rec])
    return tmp_path


def test_the_receipt_agrees_with_the_answer_about_freshness(tmp_path, monkeypatch, capsys):
    from fux import query as query_mod

    root = _answerable_repo(tmp_path)
    monkeypatch.setattr(query_mod, "_root", lambda: root)
    query_mod.cmd_answer(_Args(query="rollback", receipt=True))
    payload = json.loads(capsys.readouterr().out)

    receipt = payload["receipt"]
    assert receipt["predicate"]["confidence"]["verified"] == payload["confidence"]["verified"]
    if receipt["predicate"]["verdicts"]:
        assert receipt["predicate"]["confidence"]["verified"] == receipt["predicate"]["verdicts"][0]["freshness"]


def test_no_provenance_key_appears_unless_a_flag_asked_for_it(tmp_path, monkeypatch, capsys):
    """W-48: an additive key is safe; a key that appears unasked is a trap."""
    from fux import query as query_mod

    root = _answerable_repo(tmp_path)
    monkeypatch.setattr(query_mod, "_root", lambda: root)
    query_mod.cmd_answer(_Args(query="rollback"))
    payload = json.loads(capsys.readouterr().out)
    assert "receipt" not in payload
    assert "audit" not in payload


def test_the_journal_stays_empty_without_the_journal_flag(tmp_path, monkeypatch, capsys):
    """⚠ `--receipt` EMITS; only `--journal` WRITES.

    A tool whose pitch is *nothing leaves your machine* may not quietly begin
    recording questions because a law was relaxed. The flag is the consent.
    """
    from fux import query as query_mod

    root = _answerable_repo(tmp_path)
    monkeypatch.setattr(query_mod, "_root", lambda: root)
    query_mod.cmd_answer(_Args(query="rollback", receipt=True))
    capsys.readouterr()
    assert not provenance.journal_path(root).exists()

    query_mod.cmd_answer(_Args(query="rollback", journal=True))
    capsys.readouterr()
    assert provenance.journal_path(root).exists()


def test_every_answer_branch_validates_against_the_output_contract(tmp_path, monkeypatch, capsys):
    """⚠ The declaration claimed this and only one branch did it.

    `output.schema.json` says *"`fux answer --json` is validated against this
    before it is printed"*. Until ADR-PROVENANCE only the no-match branch went
    through `_emit`; the refer and index branches printed unvalidated. Same
    defect class as W-84's MCP tool descriptions — a promise in a machine-facing
    declaration that nothing enforced.
    """
    from fux import query as query_mod

    root = _answerable_repo(tmp_path)
    monkeypatch.setattr(query_mod, "_root", lambda: root)

    # refer branch, index branch, and no-match branch — all three must emit
    # JSON their own contract accepts, or `_emit` raises.
    for args in (
        _Args(query="rollback", receipt=True, audit=True),
        _Args(query="rollback", no_refer=True, receipt=True),
        _Args(query="zzznomatchanywhere"),
    ):
        query_mod.cmd_answer(args)
        json.loads(capsys.readouterr().out)


# --------------------------------------------------------------------------
# the in-toto shape (Arpit, 2026-08-27: adopt the standard shape, sign nothing)


def _statement(tmp_path):
    from fux.query import provenance

    return provenance.receipt(
        tmp_path,
        "how do I roll back",
        path="refer",
        subject=[{"id": "file:docs/mesh.md", "loc": "docs/mesh.md:L10-L13", "sha": "a" * 40}],
        confidence={"band": "grounded"},
    )


def test_the_receipt_is_an_in_toto_statement(tmp_path):
    from fux.query import provenance

    st = _statement(tmp_path)
    assert st["_type"] == "https://in-toto.io/Statement/v1"
    assert st["predicateType"] == provenance.PREDICATE_TYPE
    assert set(st) == {"_type", "subject", "predicateType", "predicate"}, (
        "a Statement is exactly four fields; anything else belongs in `predicate`"
    )


def test_the_subject_is_a_resource_descriptor(tmp_path):
    """`{id, loc, sha}` -> `{name, digest.sha256, annotations}`.

    **A rename, not a reshape** — fux already cited by digest, which is the
    whole reason the standard shape fits at all.
    """
    entry = _statement(tmp_path)["subject"][0]
    assert entry["name"] == "file:docs/mesh.md"
    assert entry["digest"] == {"sha256": "a" * 40}


def test_loc_lives_in_namespaced_annotations(tmp_path):
    """⚠ A ResourceDescriptor has no field for a line range.

    `annotations` is the spec's own extension point, and the key is namespaced
    because an unnamespaced key in a shared schema is how two tools collide.
    """
    entry = _statement(tmp_path)["subject"][0]
    assert entry["annotations"] == {"fux.dev/loc": "docs/mesh.md:L10-L13"}


def test_a_citation_without_a_loc_carries_no_annotations(tmp_path):
    from fux.query import provenance

    st = provenance.receipt(
        tmp_path, "q", path="index", subject=[{"id": "x", "sha": "b" * 40}]
    )
    assert "annotations" not in st["subject"][0], "an empty extension point is noise"


def test_the_predicate_carries_everything_else(tmp_path):
    predicate = _statement(tmp_path)["predicate"]
    assert set(predicate) == {"engine", "inputs", "confidence", "derivation", "verdicts"}
    assert predicate["inputs"]["query"] == "how do I roll back"


def test_nothing_signs_the_statement(tmp_path):
    """⚠ Ruled 2026-08-27: adopt the shape, sign NOTHING.

    A Statement is valid on its own; the DSSE envelope that carries a
    signature is a separate layer. stdlib `hmac` was refused because it gives
    integrity and authenticity but **not non-repudiation** — verifying needs
    the same secret that signs, so with a repo-shared key every developer and
    the CI runner can produce any receipt and each can deny it.
    """
    st = _statement(tmp_path)
    for forbidden in ("signature", "signatures", "sig", "keyid", "payloadType"):
        assert forbidden not in st, f"a Statement must not carry {forbidden!r}"


def test_the_module_imports_no_crypto():
    """L1, and the refusal above. If `hmac` ever appears here, decision 5 moved
    without its record."""
    import inspect

    from fux.query import provenance

    body = "\n".join(
        line
        for line in inspect.getsource(provenance).splitlines()
        if line.startswith(("import ", "from ")) or line.strip().startswith(("import ", "from "))
    )
    for banned in ("hmac", "hashlib.pbkdf2", "cryptography", "nacl"):
        assert banned not in body, f"provenance imports {banned}"


def test_a_v1_receipt_is_named_as_old_not_as_corrupt(tmp_path):
    """⚠ Precision the holder needs.

    Telling someone a `fux.receipt.v1` payload is *"not a fux receipt"* sends
    them looking for damage in a file that is merely from before the reshape.
    """
    from fux.query import provenance

    result = provenance.verify(tmp_path, {"schema": "fux.receipt.v1"})
    assert result.verdict == provenance.UNVERIFIABLE
    assert "predates" in result.note


def test_someone_elses_attestation_is_named_precisely(tmp_path):
    """A well-formed in-toto Statement carrying another tool's predicate is a
    valid attestation — just not ours, and the note should say which."""
    from fux.query import provenance

    result = provenance.verify(
        tmp_path,
        {
            "_type": "https://in-toto.io/Statement/v1",
            "predicateType": "https://slsa.dev/provenance/v1",
            "subject": [],
            "predicate": {},
        },
    )
    assert result.verdict == provenance.UNVERIFIABLE
    assert "slsa.dev" in result.note


def test_two_missing_digests_never_compare_equal(tmp_path):
    """⚠ The trap `_sha_of` exists for.

    A missing key degrading to `""` on both sides compares EQUAL — which would
    report `reproduced` for a receipt that verified nothing at all.
    """
    from fux.query import provenance

    assert provenance._sha_of({}) == ""
    assert provenance._sha_of({"digest": {}}) == ""
    assert provenance._sha_of({"digest": {"sha256": "c" * 40}}) == "c" * 40
    assert provenance._sha_of({"sha": "d" * 40}) == "d" * 40, "the rerun callback's shape"


def test_verify_never_reaches_the_network(tmp_path):
    """⚠ ADR-PROVENANCE decision 14 / veto 3, made mechanical.

    `verify` answers *does this reproduce from what is committed* — a question
    with the same answer on every machine. A fetching `verify` would make one
    receipt verify differently on a laptop with the VPN up and on a CI runner
    without it, which is the opposite of a re-runnable claim.
    """
    import inspect
    import io
    import tokenize

    from fux.query import provenance

    def code_only(text):
        out = []
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            out.append(tok.string)
        return " ".join(out)

    body = code_only(inspect.getsource(provenance.verify))
    for banned in ("urllib", "socket", "requests", "fetch", "urlsrc", "refer"):
        assert banned not in body, (
            f"verify mentions {banned!r} — its verdict must not depend on the "
            "verifier's network (decision 14)"
        )


def test_the_receipt_shape_does_not_vary_by_config(tmp_path, monkeypatch):
    """⚠ ADR-PROVENANCE decision 15's refusal, made mechanical.

    `.fux/output.toml` may change what is EMITTED; it may not make one artifact
    two shapes. Two receipts of the same answer must be identical, which is the
    same reason decision 8 forbids a timestamp.
    """
    from fux.output_config import CLI_VERBS, MCP_KEYS

    # ⚠ This read `SCHEMA` until 2026-08-28 and had been an ImportError since
    # ADR-OUTPUT decision 19 split that one dict into `CLI_VERBS` (the
    # `[cli]`/`[cli.json]` side, per verb) and `MCP_KEYS` (the `[mcp]` side).
    # An assertion that cannot import is an assertion that never ran, so this
    # walks BOTH key sets now — the guarantee is about every configurable key,
    # and `[mcp]` is exactly the surface decision 15 was written about.
    for verb, keys in CLI_VERBS.items():
        for key in keys:
            assert "receipt" not in key, (
                f"[cli.{verb}] {key} lets a config change the receipt's shape — "
                "two receipts of one answer would then differ"
            )
    for key in MCP_KEYS:
        assert "receipt" not in key, (
            f"[mcp] {key} lets a config change the receipt's shape — "
            "two receipts of one answer would then differ"
        )


def test_an_uncomputed_derivation_is_empty_not_absent(tmp_path):
    """`{}` says *not asked for*. An absent key would be a claim about the run
    rather than about the request — the W-48 trap."""
    from fux.query import provenance

    st = provenance.receipt(tmp_path, "q", path="index", subject=[])
    assert st["predicate"]["derivation"] == {}
    assert "derivation" in st["predicate"]
