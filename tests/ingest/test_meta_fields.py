"""W-205 part 1 — which front-matter keys reach the index, and into which field.

🔴 **The defect this closes: `parse()` returned `(meta, body)` and only `body`
reached the postings.** A `doc_id:` a human could read was not one they could
search — true, undocumented, and measured: **7 of the golden seed's 14 declared
identity keys are front-matter-only**, and every one was absent from the index.

**The four properties [SR-INGEST](../../records/0106_ingest.md) decision 23
names**, which are the four this file is built around: a listed key is
retrievable, an unlisted one is not, a `none` binding silences a claim, and two
decoders resolve different dicts.
"""

from __future__ import annotations

import pytest

from fux.decode import Decoder
from fux.ingest.extract import _meta_values, extract_fields
from fux.ingest.parse import DEFAULT_META_FIELDS, ParsedDoc, meta_fields
from fux.ingest.typesfile import META_TARGETS


def doc(**meta) -> ParsedDoc:
    return ParsedDoc(meta=meta, body="Tessaline is the vendor of record.")


def terms_in(field: str, fields) -> set[str]:
    i = ("body", "heading", "title", "path", "ctx").index(field)
    return {t for t, tf in fields.terms.items() if tf[i]}


# --- 1 · a listed key is retrievable ----------------------------------------

def test_a_front_matter_doc_id_reaches_the_title_field() -> None:
    """🔴 The whole point. `QCL-IT-ADR-08` appears NOWHERE in the body of the
    document that declares it, and before this change it was absent from the
    index entirely."""
    fields = extract_fields("seed/11-decision.md", doc(doc_id="QCL-IT-ADR-08"))
    assert {"qcl", "adr", "08"} <= terms_in("title", fields)


def test_identity_keys_reach_title_and_tags_reach_ctx() -> None:
    """Decision 23b: an identifier is how a person NAMES a document, so it
    ranks at `title` weight. `ctx` would make it one body word in ten thousand."""
    fields = extract_fields("a.md", doc(doc_id="KFS-2014", tags=["telematics"]))
    assert "2014" in terms_in("title", fields)
    assert "telemat" in terms_in("ctx", fields)
    assert "telemat" not in terms_in("title", fields)


def test_aliases_takes_a_list_because_that_is_what_aliases_are_for() -> None:
    fields = extract_fields("a.md", doc(aliases=["NGP hub", "Nagpur DC"]))
    assert {"ngp", "hub", "nagpur", "dc"} <= terms_in("title", fields)


# --- 2 · an unlisted key is NOT indexed -------------------------------------

def test_a_key_nobody_listed_is_not_indexed() -> None:
    """The closed list. `status: rushed-review` is in the golden seed today, and
    *everything in `meta` is searchable* would put workflow noise — and names —
    into posting lists without SR-PII's gate ever being asked."""
    fields = extract_fields("a.md", doc(status="rushed-review", review_note="messy"))
    assert "rush" not in terms_in("title", fields)
    assert "messi" not in terms_in("ctx", fields)


def test_no_person_key_is_indexed_by_default() -> None:
    """🔴 Decision 23c, and it is the one a session must not quietly relax.
    `owner`, `author` and `contributors` are names."""
    for key in ("owner", "author", "contributors"):
        assert key not in DEFAULT_META_FIELDS
    fields = extract_fields("a.md", doc(owner="Revathi Iyer", author="Farhan Qureshi"))
    every = set(fields.terms)
    assert not ({"revathi", "iyer", "farhan", "qureshi"} & every)


def test_a_bool_contributes_nothing_and_a_number_does() -> None:
    """`draft: true` would put every draft in the corpus on one posting list.
    A numeric `doc_id` is an identifier a person types."""
    assert _meta_values(True) == []
    assert _meta_values(None) == []
    assert _meta_values(4471) == ["4471"]
    assert _meta_values(["a", 2]) == ["a", "2"]


# --- 3 · `none` silences a claim --------------------------------------------

def decoder(name: str, **claim) -> Decoder:
    return Decoder(name=name, extensions=(".x",), fn=lambda raw, rel: "",
                   wants_path=False, origin=f"<{name}>", meta_fields=claim)


def test_a_none_binding_silences_a_claim(tmp_path) -> None:
    """⚠ The only way to un-index a person key a consumer decoder claims, and
    worth knowing BEFORE the decoder is installed rather than after."""
    fux = tmp_path / ".fux"
    fux.mkdir()
    (fux / "formats.toml").write_text('[meta]\nowner = "none"\n', encoding="utf-8")
    claimed = decoder("mail", owner="title")
    assert "owner" in meta_fields(claimed, None)
    assert "owner" not in meta_fields(claimed, tmp_path)


def test_a_binding_outranks_a_claim_which_outranks_the_default(tmp_path) -> None:
    """Decision 23a's order, asserted as an order rather than as three cases."""
    fux = tmp_path / ".fux"
    fux.mkdir()
    (fux / "formats.toml").write_text('[meta]\ndoc_id = "ctx"\n', encoding="utf-8")
    claimed = decoder("mail", doc_id="heading")
    assert meta_fields(None, None)["doc_id"] == "title"      # 3 · default
    assert meta_fields(claimed, None)["doc_id"] == "heading"  # 2 · claim
    assert meta_fields(claimed, tmp_path)["doc_id"] == "ctx"  # 1 · binding


# --- 4 · two decoders resolve different dicts -------------------------------

def test_an_eml_decoder_and_a_markdown_decoder_resolve_different_keys() -> None:
    """🔴 Why the claim is PER DECODER and not one global list. A YAML
    front-matter decoder's identity key is `doc_id`; an `.eml` decoder's is
    `Message-ID`. One list would be wrong for both."""
    mail = meta_fields(decoder("mail", **{"Message-ID": "title"}), None)
    prose = meta_fields(None, None)
    assert "Message-ID" in mail and "Message-ID" not in prose
    assert mail["doc_id"] == prose["doc_id"] == "title"


# --- the guards on the mechanism itself -------------------------------------

def test_the_resolver_never_returns_none_as_a_target() -> None:
    """`none` is removed rather than mapped, so no caller has to know the word."""
    assert "none" not in set(meta_fields(decoder("d", a="none"), None).values())


def test_every_default_target_is_a_real_index_field() -> None:
    from fux.store import TF_FIELDS

    assert set(DEFAULT_META_FIELDS.values()) <= set(TF_FIELDS)


def test_meta_targets_agrees_with_the_store_field_list() -> None:
    """`META_TARGETS` is a literal in `typesfile` so config validation does not
    import the store. This is what stops the two drifting."""
    from fux.store import TF_FIELDS

    assert tuple(t for t in META_TARGETS if t != "none") == tuple(TF_FIELDS)


def test_a_claim_naming_no_index_field_is_refused() -> None:
    from fux.decode import _meta_fields_of
    from fux.errors import FuxError

    class Mod:
        META_FIELDS = {"doc_id": "nowhere"}

    with pytest.raises(FuxError, match="not an"):
        _meta_fields_of(Mod, "mod", "<mod>")


def test_values_go_in_through_the_analyzer_so_part_2_reaches_them_too() -> None:
    """🔴 Decision 23d, made executable — and the reason part 1 routes values
    **through** the analyzer rather than appending them raw.

    ⚠ **This assertion inverted on 2026-09-22, and the inversion is the point.**
    When part 1 shipped, the analyzer was `v2`: `QCL-IT-ADR-08` reached the index
    and arrived in pieces, so this test pinned *reachable but not whole* and said
    so in its name. W-205 part 2 family (a) made `-` an identifier separator like
    `_`, and because part 1 feeds the analyzer instead of bypassing it, **the
    whole form appeared here with no change to `parse.py` at all**. That is the
    composition the two parts were ordered for; a part 1 that appended raw values
    would have been untouched by part 2 and would still be wrong.

    `IT` still goes to the stopword list, and that is correct: the stopword pass
    runs on the *parts*, never on the whole token, so `qcl-it-adr-08` survives
    beside `qcl`, `adr` and `08`."""
    fields = extract_fields("a.md", doc(doc_id="QCL-IT-ADR-08"))
    title = terms_in("title", fields)
    assert "it" not in title, "the stopword pass still runs over the parts"
    assert "qcl-it-adr-08" in title, (
        "the analyzer is v3 and the whole form must exist beside its parts — "
        "if this is missing, part 1 has stopped routing values through analyze()"
    )
    assert {"qcl", "adr", "08"} <= title, "the parts must survive alongside the whole"
