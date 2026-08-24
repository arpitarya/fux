"""The accelerator build: determinism, derived-plane hygiene, and the two
invariants that refuse to build an accelerator which could disagree with scan.
"""

from __future__ import annotations

import json

import pytest

from fux.derive import build
from fux.derive import format as fmt
from fux.errors import FuxError
from fux.store import term_hash, write_index
from fux.store.fuxdir import CACHEDIR_SIGNATURE


def _rec(doc_id, title, flen, terms, **extra) -> dict:
    record = {
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
    record.update(extra)
    return record


def _corpus(n=300):
    # tf vectors are `[body, heading]` (v2 order — `store.TF_FIELDS`); `flen`
    # is a single body-token count, so `derive_wlen(flen) == flen[0]`.
    return [
        _rec(
            f"file:doc{i:04d}.md",
            f"Doc {i}",
            [10 + i],
            {term_hash("common"): [1 + i % 5, 0], term_hash(f"t{i % 40}"): [2, 1]},
        )
        for i in range(n)
    ]


def test_build_is_byte_identical_across_runs(tmp_path):
    """Same committed bytes in, same derived bytes out.

    `stamp.json` is excluded by design — it carries filesystem mtimes, which
    are the cheap staleness check and cannot be reproducible.
    """
    write_index(tmp_path, _corpus())
    build(tmp_path)
    first = _snapshot(tmp_path)
    build(tmp_path)
    assert _snapshot(tmp_path) == first


def _snapshot(root):
    directory = fmt.runtime_dir(root)
    out = {}
    for name in fmt.DETERMINISTIC_FILES:
        out[name] = (directory / name).read_bytes()
    for path in sorted((directory / fmt.POSTINGS_DIR).glob("*")):
        out[f"postings/{path.name}"] = path.read_bytes()
    return out


def test_runtime_dir_is_tagged_as_a_cache(tmp_path):
    """ADR-DOTFUX: every derived directory carries CACHEDIR.TAG."""
    write_index(tmp_path, _corpus(20))
    build(tmp_path)
    tag = fmt.runtime_dir(tmp_path) / "CACHEDIR.TAG"
    assert tag.read_text(encoding="ascii").splitlines()[0] == CACHEDIR_SIGNATURE


def test_rebuild_drops_stale_postings_shards(tmp_path):
    """A shrinking corpus must not leave last build's postings behind.

    A stale shard would still be bisectable and would answer with documents
    that no longer exist — a wrong answer that looks like a correct one.
    """
    write_index(tmp_path, _corpus(300))
    build(tmp_path)
    before = {p.name for p in (fmt.runtime_dir(tmp_path) / fmt.POSTINGS_DIR).glob("*.jsonl")}

    assert len(before) > 1

    write_index(tmp_path, [_rec("file:only.md", "Only", [5], {term_hash("solo"): [0, 1]})])
    build(tmp_path)
    after = {p.name for p in (fmt.runtime_dir(tmp_path) / fmt.POSTINGS_DIR).glob("*.jsonl")}

    # Exactly one term survives, so exactly one postings shard may exist. The
    # new shard need not be a member of `before` — term prefixes are hashes, not
    # a subset relation — so the assertion is on the count, not containment.
    assert len(after) == 1


def test_stats_match_the_scan_oracle(tmp_path):
    """`n` and `total_wlen` must be exactly what `query/scan.py` derives."""
    from fux.query.scan import scan_candidates

    write_index(tmp_path, _corpus(50))
    build(tmp_path)
    _, _, corpus = scan_candidates(tmp_path, [term_hash("common")])

    stats = json.loads((fmt.runtime_dir(tmp_path) / fmt.STATS_NAME).read_bytes())
    assert stats["n"] == corpus.n
    assert stats["total_wlen"] == corpus.total_wlen


def test_build_refuses_a_stray_quoted_term_hash(tmp_path):
    """Invariant 1: a 16-hex token outside `terms` makes the two paths disagree.

    `scan.py` counts df from a raw-bytes substring check, so a document whose
    *title* happens to be sixteen hex characters would inflate that term's df on
    the scan side only. The build fails loudly rather than shipping a
    divergence no test would catch.
    """
    stray = "deadbeefdeadbeef"
    write_index(tmp_path, [_rec("file:a.md", stray, [10], {term_hash("x"): [0, 1]})])
    with pytest.raises(FuxError, match="outside `terms`"):
        build(tmp_path)


def test_build_refuses_when_regex_flen_disagrees_with_the_parse(tmp_path):
    """Invariant 2: `scan.py` sums `flen` (via `derive_wlen`) by regex and scores from the parse.

    A record whose serialized bytes present a different `flen` to the regex than
    to `json.loads` would give the two paths different `avg_wlen`, and therefore
    different scores for every document in the corpus.

    Reaching it needs a **nested key**, not a string value: a string containing
    `"flen":` is escaped to `\\"flen\\":` on the way out, so the regex never
    matches it. Canonical keys sort, so `edges` serializes before `flen` and
    the regex finds the nested one first — and it must be an *array* value to
    match `_FLEN_RE`'s `\\[...\\]`, same shape as the real field.
    """
    record = _rec("file:a.md", "A", [10], {term_hash("x"): [0, 1]})
    record["edges"] = [{"dst": "file:b.md", "grade": 8, "kind": "ref", "flen": [999]}]
    write_index(tmp_path, [record])
    with pytest.raises(FuxError, match="byte-level regex reads"):
        build(tmp_path)


def test_offset_entries_are_sorted_by_term(tmp_path):
    """The bisect in `blocks_for` is only correct on a sorted table."""
    write_index(tmp_path, _corpus(200))
    build(tmp_path)
    for path in (fmt.runtime_dir(tmp_path) / fmt.POSTINGS_DIR).glob("*.idx"):
        buf = path.read_bytes()
        keys = [
            fmt.unpack_entry(buf, i)[:2] for i in range(len(buf) // fmt.ENTRY_SIZE)
        ]
        assert keys == sorted(keys)


def test_blocks_hold_at_most_block_size_postings(tmp_path):
    write_index(tmp_path, _corpus(500))
    report = build(tmp_path)
    assert report.docs == 500
    directory = fmt.runtime_dir(tmp_path) / fmt.POSTINGS_DIR
    for path in directory.glob("*.jsonl"):
        for line in path.read_bytes().split(b"\n"):
            if not line:
                continue
            _, postings = json.loads(line)
            assert 0 < len(postings) <= fmt.BLOCK_SIZE
