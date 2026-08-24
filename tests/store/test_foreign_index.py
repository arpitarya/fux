"""The v1 -> v2 migration seam — ADR-INDEX-LIFECYCLE decision 10.

Decision 10 owes a full re-ingest on every index older than the current
analyzer and names `fux ingest --full` as the command that discharges it.
That command read the prior index unconditionally, so **it refused the exact
index it exists to replace**: the documented migration path was unreachable,
and the only way out was to delete `.fux/index/` by hand — which silently
destroys any `url:` record, the one thing in there that cannot be rebuilt.

These tests pin the line the fix draws: **record identity is schema-stable,
record content is not.** Everything here is about `id`; nothing here reads
`terms`, and `read_index` keeps refusing a foreign shard exactly as before.
"""

from __future__ import annotations

import json

import pytest

from fux import store as store_mod
from fux.errors import FuxError
from fux.ingest.run import _existing_index

V1_HEADER = {"_format": "fux.index.v1", "analyzer": "v1", "tf_fields": ["heading", "body"]}


def _write_foreign(root, *records, header=None):
    """A shard as an older fux wrote it — v1 header, v1 field order."""
    directory = store_mod.index_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    by_shard: dict[str, list[dict]] = {}
    for record in records:
        by_shard.setdefault(store_mod.shard_for(record["id"]), []).append(record)
    for shard, group in by_shard.items():
        lines = [json.dumps(header or V1_HEADER, separators=(",", ":"), sort_keys=True)]
        lines += [json.dumps(r, separators=(",", ":"), sort_keys=True) for r in group]
        (directory / f"{shard}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _file_record(loc):
    # `src: "git"` because `write_index` refuses a non-git record with no
    # `meta` (L5) — irrelevant to what these tests are about, required to
    # construct a healthy index at all.
    return {
        "id": f"file:{loc}",
        "loc": loc,
        "sha": "0" * 40,
        "src": "git",
        "terms": {"deadbeefdeadbeef": [1, 0]},
    }


def _url_record(url):
    return {"id": f"url:{url}", "loc": url, "sha": "1" * 40, "terms": {"deadbeefdeadbeef": [1, 0]}}


# -- detection ----------------------------------------------------------------


def test_no_index_is_not_foreign(tmp_path):
    """Absent and foreign want different messages, so they are different states."""
    assert store_mod.index_is_foreign(tmp_path) is False
    assert store_mod.index_header(tmp_path) is None


def test_a_current_index_is_not_foreign(tmp_path):
    store_mod.write_index(tmp_path, [_file_record("docs/a.md")])
    assert store_mod.index_is_foreign(tmp_path) is False


def test_an_older_index_is_foreign(tmp_path):
    _write_foreign(tmp_path, _file_record("docs/a.md"))
    assert store_mod.index_is_foreign(tmp_path) is True
    assert store_mod.index_header(tmp_path)["analyzer"] == "v1"


@pytest.mark.parametrize(
    "field, value",
    [
        ("_format", "fux.index.v1"),
        ("analyzer", "v1"),
        ("tf_fields", ["heading", "body"]),
    ],
)
def test_each_header_field_independently_makes_it_foreign(tmp_path, field, value):
    """A loop over the three, not one example. A check that tests two of three
    passes an example test and lets the third through silently."""
    header = dict(store_mod.HEADER) | {field: value}
    _write_foreign(tmp_path, _file_record("docs/a.md"), header=header)
    assert store_mod.index_is_foreign(tmp_path) is True


def test_read_index_still_refuses_a_foreign_shard(tmp_path):
    """The new seam does not widen the old refusal. This is the whole safety
    argument: only `--full`, which rebuilds from source anyway, may proceed."""
    _write_foreign(tmp_path, _file_record("docs/a.md"))
    with pytest.raises(FuxError, match="_format header"):
        store_mod.read_index(tmp_path)


# -- the url: inventory -------------------------------------------------------


def test_url_ids_are_read_out_of_an_index_the_reader_refuses(tmp_path):
    _write_foreign(
        tmp_path,
        _file_record("docs/a.md"),
        _url_record("https://example.com/one"),
        _url_record("https://example.com/two"),
    )
    assert store_mod.foreign_url_ids(tmp_path) == [
        "url:https://example.com/one",
        "url:https://example.com/two",
    ]


def test_a_file_only_index_strands_nothing(tmp_path):
    _write_foreign(tmp_path, _file_record("docs/a.md"), _file_record("docs/b.md"))
    assert store_mod.foreign_url_ids(tmp_path) == []


def test_a_url_inside_a_file_record_is_not_a_url_record(tmp_path):
    """The scan prefilters on the substring `"url:` for speed, then confirms
    against the parsed `id`. A document that merely CONTAINS the text must not
    be counted, or a corpus of documentation about URLs strands itself."""
    record = _file_record("docs/a.md") | {"title": 'see "url:https://example.com/x" for detail'}
    _write_foreign(tmp_path, record)
    assert store_mod.foreign_url_ids(tmp_path) == []


# -- what --full does with it -------------------------------------------------


def test_full_discards_a_foreign_file_only_index(tmp_path):
    """The migration decision 10 documents, finally reachable."""
    _write_foreign(tmp_path, _file_record("docs/a.md"))
    assert _existing_index(tmp_path, full=True) == {}


def test_full_refuses_rather_than_stranding_url_records(tmp_path):
    """A `file:` record is a pure function of a committed file; a `url:` record
    is the only thing in the index that came from the network. Deleting one
    silently is the failure the whole seam exists to prevent."""
    _write_foreign(tmp_path, _file_record("docs/a.md"), _url_record("https://example.com/one"))
    with pytest.raises(FuxError) as excinfo:
        _existing_index(tmp_path, full=True)
    message = str(excinfo.value)
    assert "url:https://example.com/one" in message, "the stranded record must be NAMED"
    assert "fux update" in message, "the message must name the way forward"
    assert "fux.index.v1" in message, "and what it found"


def test_a_delta_run_still_refuses_a_foreign_index(tmp_path):
    """Carry-forward genuinely cannot proceed against another analyzer, so the
    relaxation is scoped to `--full` and nothing else."""
    _write_foreign(tmp_path, _file_record("docs/a.md"))
    with pytest.raises(FuxError, match="_format header"):
        _existing_index(tmp_path, full=False)


def test_full_on_a_current_index_reads_it_normally(tmp_path):
    """`--full` must not become a blind path on a healthy index — the reuse
    decision belongs to `_reusable`, not to this function."""
    store_mod.write_index(tmp_path, [_file_record("docs/a.md")])
    assert set(_existing_index(tmp_path, full=True)) == {"file:docs/a.md"}
