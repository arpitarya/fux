from __future__ import annotations

from fux.store.format import HEADER, content_sha, shard_for, term_hash


def test_term_hash_is_16_hex_chars():
    h = term_hash("pruning")
    assert len(h) == 16
    int(h, 16)  # valid hex


def test_term_hash_deterministic():
    assert term_hash("pruning") == term_hash("pruning")


def test_content_sha_is_40_hex_chars():
    h = content_sha(b"hello world")
    assert len(h) == 40
    int(h, 16)


def test_content_sha_deterministic():
    assert content_sha(b"hello") == content_sha(b"hello")
    assert content_sha(b"hello") != content_sha(b"world")


def test_shard_for_is_2_hex_chars():
    s = shard_for("file:docs/foo.md")
    assert len(s) == 2
    int(s, 16)


def test_shard_for_deterministic():
    assert shard_for("file:docs/foo.md") == shard_for("file:docs/foo.md")


def test_shard_distribution_across_many_ids_is_not_degenerate():
    shards = {shard_for(f"file:doc-{i}.md") for i in range(500)}
    # 500 ids into 256 buckets should spread out, not collapse to a handful.
    assert len(shards) > 100


def test_header_carries_format_analyzer_and_tf_fields():
    assert HEADER["_format"] == "fux.index.v2"
    assert HEADER["analyzer"]
    assert HEADER["tf_fields"] == ["body", "heading", "title", "path", "ctx"]


# Golden vectors — pin the exact algorithm (blake2b + digest_size), not just
# "produces a hex string of the right length". CI runs this file's literal
# bytes on ubuntu, macos, and windows: unlike a self-comparison test, a
# hard-coded expected value only passes if all three runners agree with each
# other, which is what R1 is actually supposed to prove.
def test_term_hash_golden_vector():
    assert term_hash("pruning") == "5618d61da2fc0d56"


def test_content_sha_golden_vector():
    assert content_sha(b"hello world") == "70e8ece5e293e1bda064deef6b080edde357010f"


def test_shard_for_golden_vector():
    assert shard_for("file:docs/foo.md") == "2b"


def test_digest_size_is_not_a_manual_slice_of_the_default_digest():
    # blake2b's digest_size is mixed into its parameter block, not truncated
    # after the fact — confirm the two differ so a future refactor can't
    # "simplify" this into slicing a 64-byte hexdigest.
    import hashlib

    full = hashlib.blake2b(b"pruning").hexdigest()
    assert term_hash("pruning") != full[:16]
