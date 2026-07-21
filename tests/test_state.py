"""The committed lean plane: record formats, Bloom sizing, sharding, corruption."""

from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.state import DocState, bloom, format as fmt, load_state, write_state

from test_ingest import make_project, run


def a_doc(doc_id: str, terms=("alpha", "beta"), code: bytes | None = None) -> DocState:
    return DocState(
        doc_id=doc_id, sha12="0123456789ab", title=f"Title {doc_id}",
        flags=["inferred"], code=code or bytes(range(32)), sig=bloom.build(terms),
    )


# -- record formats --------------------------------------------------------


def test_codes_round_trip_sorted(tmp_path):
    records = [(5, bytes(32)), (1, bytes(range(32)))]
    blob = fmt.pack_codes(records)
    assert blob.startswith(fmt.MAGIC)
    unpacked = fmt.unpack_codes(blob)
    assert unpacked == {1: bytes(range(32)), 5: bytes(32)}
    # sorted on disk: doc_hash 1 precedes 5 regardless of input order
    assert blob.index((1).to_bytes(8, "little")) < blob.index((5).to_bytes(8, "little"))


def test_sigs_round_trip_variable_length(tmp_path):
    records = [(2, b"\x01\x02\x03"), (1, b"\xff" * 40)]
    assert fmt.unpack_sigs(fmt.pack_sigs(records)) == {1: b"\xff" * 40, 2: b"\x01\x02\x03"}


def test_meta_round_trip_compressed():
    payload = {"id": "docs/a.md", "sha12": "abc", "title": "A", "flags": ["inferred"]}
    assert fmt.unpack_meta(fmt.pack_meta([(7, payload)])) == {7: payload}


def test_meta_packing_is_deterministic():
    payload = {"id": "docs/a.md", "sha12": "abc", "title": "A", "flags": ["inferred"]}
    assert fmt.pack_meta([(7, payload)]) == fmt.pack_meta([(7, dict(reversed(payload.items())))])


def test_bad_magic_names_the_bucket():
    with pytest.raises(FuxError, match="codes/aa.bin is corrupt"):
        fmt.unpack_codes(b"NOTFUXSTATE!" + bytes(40), "codes/aa.bin")


def test_wrong_format_version_asks_for_reingest():
    import struct

    blob = fmt.MAGIC + struct.pack("<H", 99)
    with pytest.raises(FuxError, match="format 99"):
        fmt.unpack_sigs(blob, "sigs/aa.bin")


def test_corrupt_meta_payload_is_reported():
    import struct

    blob = fmt.HEADER + struct.pack("<QH", 1, 4) + b"junk"
    with pytest.raises(FuxError, match="corrupt"):
        fmt.unpack_meta(blob, "meta/aa.bin")


def test_bucket_is_the_low_byte_of_the_doc_hash():
    doc_id = "docs/guide.md"
    assert fmt.bucket_of(doc_id) == f"{fmt.doc_hash(doc_id) & 0xFF:02x}"


def test_code_width_is_enforced():
    with pytest.raises(FuxError, match="32 bytes"):
        fmt.pack_codes([(1, b"short")])


# -- Bloom signatures ------------------------------------------------------


def test_probe_has_no_false_negatives():
    terms = [f"term{i}" for i in range(40)]
    sig = bloom.build(terms)
    for term in terms:  # every present term must probe true, always
        assert bloom.probe(sig, [term])


def test_absent_terms_usually_miss():
    sig = bloom.build([f"term{i}" for i in range(40)])
    misses = sum(not bloom.probe(sig, [f"absent{i}"]) for i in range(500))
    assert misses > 450  # ~1.4 % FPR by design; a loose bound keeps this stable


def test_signature_is_order_independent():
    assert bloom.build(["b", "a", "c"]) == bloom.build(["c", "a", "b", "a"])


def test_sizing_follows_the_documented_table():
    assert bloom.signature_bytes(1) == bloom.MIN_BYTES
    assert bloom.signature_bytes(25) == 30
    assert bloom.signature_bytes(50) == 60
    assert bloom.signature_bytes(100) == 120
    assert bloom.signature_bytes(10_000) == bloom.MAX_BYTES  # capped


def test_documented_fpr_holds_at_the_design_point():
    fpr = bloom.expected_fpr(bloom.signature_bytes(50), 50)
    assert 0.010 < fpr < 0.020  # the ~1.4 % the docstring table claims


def test_match_count_ranks_by_how_many_terms_could_be_present():
    sig = bloom.build(["alpha", "beta", "gamma"])
    assert bloom.match_count(sig, ["alpha", "beta"]) == 2
    assert bloom.match_count(sig, ["alpha", "nowhere-at-all"]) == 1


def test_empty_signature_never_claims_a_match():
    assert not bloom.probe(b"", ["alpha"])
    assert bloom.match_count(b"", ["alpha"]) == 0


# -- the plane ------------------------------------------------------------


def test_write_and_load_round_trip(tmp_path):
    docs = [a_doc("docs/a.md"), a_doc("docs/b.md"), a_doc("web:example.com/x")]
    assert write_state(tmp_path, docs) == 3
    loaded = load_state(tmp_path)
    assert set(loaded) == {"docs/a.md", "docs/b.md", "web:example.com/x"}
    assert loaded["docs/a.md"].title == "Title docs/a.md"
    assert loaded["docs/a.md"].code == bytes(range(32))
    assert bloom.probe(loaded["docs/a.md"].sig, ["alpha"])


def test_writes_are_byte_identical_across_runs(tmp_path):
    docs = [a_doc(f"docs/{i}.md") for i in range(20)]
    write_state(tmp_path, docs)
    first = {p.name: p.read_bytes() for p in (tmp_path / ".fux/state").rglob("*.bin")}
    write_state(tmp_path, list(reversed(docs)))  # input order must not matter
    assert {p.name: p.read_bytes() for p in (tmp_path / ".fux/state").rglob("*.bin")} == first


def test_docs_shard_across_buckets(tmp_path):
    write_state(tmp_path, [a_doc(f"docs/{i}.md") for i in range(60)])
    buckets = {p.name for p in (tmp_path / ".fux/state/meta").glob("*.bin")}
    assert len(buckets) > 20, "sharding must spread docs, or commits touch one huge file"


def test_removed_docs_leave_no_trace(tmp_path):
    write_state(tmp_path, [a_doc(f"docs/{i}.md") for i in range(30)])
    write_state(tmp_path, [a_doc("docs/0.md")])
    assert set(load_state(tmp_path)) == {"docs/0.md"}


def test_doc_without_a_vector_gets_no_code(tmp_path):
    write_state(tmp_path, [DocState("docs/a.md", "aa", "A", [], None, bloom.build(["x"]))])
    assert load_state(tmp_path)["docs/a.md"].code is None  # never a fake all-zero code


def test_unicode_doc_ids_hash_and_round_trip(tmp_path):
    write_state(tmp_path, [a_doc("docs/café-décisions.md")])
    assert set(load_state(tmp_path)) == {"docs/café-décisions.md"}


def test_empty_plane_loads_as_empty(tmp_path):
    assert load_state(tmp_path) == {}


# -- ingest integration ----------------------------------------------------


def test_ingest_writes_the_plane(tmp_path, monkeypatch):
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    loaded = load_state(tmp_path)
    assert set(loaded) == {
        "docs/guide.md", "docs/sub/notes.txt", "src/util.py", "data/cfg.json", "img/logo.png",
    }
    assert loaded["docs/guide.md"].sha12  # verifiable against the lock
    assert bloom.probe(loaded["docs/guide.md"].sig, ["install"])


def test_plane_stays_byte_identical_on_reingest(tmp_path, monkeypatch):
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    first = {p.name: p.read_bytes() for p in (tmp_path / ".fux/state").rglob("*.bin")}
    run(tmp_path, monkeypatch, "ingest")
    assert {p.name: p.read_bytes() for p in (tmp_path / ".fux/state").rglob("*.bin")} == first


def test_state_is_small_per_doc(tmp_path, monkeypatch):
    """The ~200 B/doc budget is what makes committing the plane viable."""
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    total = sum(p.stat().st_size for p in (tmp_path / ".fux/state").rglob("*.bin"))
    headers = 3 * 5 * len(fmt.HEADER)  # 3 families × 5 single-doc buckets
    assert (total - headers) / 5 < 400  # per-doc payload, headers excluded
