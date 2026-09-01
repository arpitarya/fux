"""`.fux/acquired/` — the plane that keeps the bytes a fetch returned.

No network here. The plane is pure filesystem, which is what lets these run
anywhere.
"""

from __future__ import annotations

import json

from fux.store import acquired, fuxdir

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
BODY = b"PK\x03\x04" + b"sheet1.xml" * 300


# -- the plane is declared, so `fux doctor` stays quiet ----------------------


def test_acquired_is_a_third_category_not_a_derived_directory():
    # The whole reason it is not under runtime/: runtime means "fux build can
    # rebuild this", and an acquired blob can only be re-acquired.
    assert "acquired" in fuxdir.ACQUIRED
    assert "acquired" not in fuxdir.DERIVED
    assert "acquired" not in fuxdir.COMMITTED


def test_acquired_is_declared():
    # An undeclared child of .fux/ is ADR-DOTFUX veto condition 1 firing.
    assert "acquired" in fuxdir.DECLARED


def test_gitignore_lists_it_by_name_and_never_uses_a_blanket():
    lines = [ln.strip() for ln in fuxdir._GITIGNORE.splitlines()]
    rules = [ln for ln in lines if ln and not ln.startswith("#")]
    assert "acquired/" in rules
    assert "runtime/" in rules
    # A blanket would silently drop the committed planes from git, which is
    # the exact failure `fux doctor`'s check-ignore assertion exists to catch.
    assert "*" not in rules and ".fux/*" not in rules


def test_the_plane_carries_cachedir_tag(tmp_path):
    # ADR-CACHEDIR-TAG. A directory holding retained SOURCE BYTES is the one a
    # consumer least wants swept into a backup without being asked.
    acquired.save(tmp_path, "https://x/a", BODY, XLSX, ".xlsx")
    tag = acquired.plane(tmp_path) / "CACHEDIR.TAG"  # written by save()
    assert tag.is_file()
    assert tag.read_bytes().startswith(fuxdir.CACHEDIR_SIGNATURE.encode("ascii"))


# -- saving -----------------------------------------------------------------


def test_save_writes_a_content_addressed_blob(tmp_path):
    blob = acquired.save(tmp_path, "https://x/a", BODY, XLSX, ".xlsx")
    assert blob.sha == acquired.sha_of(BODY)
    assert blob.bytes == len(BODY)
    path = acquired.blob_path(tmp_path, blob.sha, ".xlsx")
    assert path.is_file()
    assert path.read_bytes() == BODY
    # Sharded like the index rather than one flat directory.
    assert path.parent.name == blob.sha[:2]


def test_identical_bytes_are_written_once(tmp_path):
    a = acquired.save(tmp_path, "https://x/a", BODY, XLSX, ".xlsx")
    before = acquired.blob_path(tmp_path, a.sha, ".xlsx").stat().st_mtime_ns
    b = acquired.save(tmp_path, "https://x/DIFFERENT", BODY, XLSX, ".xlsx")
    after = acquired.blob_path(tmp_path, b.sha, ".xlsx").stat().st_mtime_ns
    assert a.sha == b.sha
    # Content addressing makes a re-fetch of unchanged bytes a no-op: the file
    # is left alone, not rewritten.
    assert before == after


def test_changed_bytes_get_a_new_blob(tmp_path):
    a = acquired.save(tmp_path, "https://x/a", BODY, XLSX, ".xlsx")
    b = acquired.save(tmp_path, "https://x/a", BODY + b"edited", XLSX, ".xlsx")
    assert a.sha != b.sha
    assert acquired.blob_path(tmp_path, a.sha, ".xlsx").is_file()
    assert acquired.blob_path(tmp_path, b.sha, ".xlsx").is_file()


def test_no_partial_files_are_left_behind(tmp_path):
    acquired.save(tmp_path, "https://x/a", BODY, XLSX, ".xlsx")
    leftovers = list(acquired.plane(tmp_path).rglob("*.part"))
    assert leftovers == []


# -- the manifest -----------------------------------------------------------


def test_manifest_round_trips(tmp_path):
    blob = acquired.save(tmp_path, "https://x/a", BODY, XLSX, ".xlsx")
    acquired.write_manifest(tmp_path, {"https://x/a": blob})
    back = acquired.read_manifest(tmp_path)
    assert back["https://x/a"].sha == blob.sha
    assert back["https://x/a"].content_type == XLSX
    assert back["https://x/a"].bytes == len(BODY)


def test_manifest_lives_inside_the_plane(tmp_path):
    # Deleting the directory must delete the whole feature, not orphan a map.
    acquired.write_manifest(
        tmp_path, {"https://x/a": acquired.Blob("https://x/a", "a" * 64, XLSX, 10)}
    )
    assert acquired.manifest_path(tmp_path).parent == acquired.plane(tmp_path)


def test_manifest_is_sorted_and_stable(tmp_path):
    blobs = {
        f"https://x/{n}": acquired.Blob(f"https://x/{n}", f"{i:064x}", XLSX, 1)
        for i, n in enumerate(("c", "a", "b"))
    }
    acquired.write_manifest(tmp_path, blobs)
    data = json.loads(acquired.manifest_path(tmp_path).read_text())
    assert list(data["entries"]) == sorted(data["entries"])
    assert data["schema"] == acquired.SCHEMA


def test_the_manifest_holds_no_wall_clock(tmp_path):
    # `maintain/urlstate.py`'s rule: counters, never clocks. Wall clock lives
    # in refer/fetchcache.py's TTL store and nowhere else.
    acquired.write_manifest(
        tmp_path, {"https://x/a": acquired.Blob("https://x/a", "b" * 64, XLSX, 10)}
    )
    text = acquired.manifest_path(tmp_path).read_text().lower()
    for banned in ("timestamp", "fetched_at", "_at\"", "mtime", "iso"):
        assert banned not in text


# -- advisory, never load-bearing -------------------------------------------


def test_missing_manifest_reads_as_empty(tmp_path):
    assert acquired.read_manifest(tmp_path) == {}


def test_reading_never_creates_the_plane(tmp_path):
    # Asking where the manifest lives must not conjure the plane into a repo
    # that never opted in -- `fux doctor` would then report a directory the
    # consumer never asked for.
    acquired.read_manifest(tmp_path)
    acquired.stored(tmp_path, "https://x/a")
    acquired.manifest_path(tmp_path)
    assert not acquired.plane(tmp_path).exists()


def test_corrupt_manifest_reads_as_empty_rather_than_raising(tmp_path):
    p = acquired.manifest_path(tmp_path)
    p.parent.mkdir(parents=True)
    p.write_text("{ this is not json")
    # The worst a broken manifest may cost is a re-fetch. It must never take
    # down a run.
    assert acquired.read_manifest(tmp_path) == {}


def test_entries_with_a_bad_sha_are_dropped_not_trusted(tmp_path):
    p = acquired.manifest_path(tmp_path)
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"schema": acquired.SCHEMA, "entries": {
        "https://x/good": {"sha": "c" * 64, "content_type": XLSX, "bytes": 5},
        "https://x/short": {"sha": "abc", "content_type": XLSX, "bytes": 5},
        "https://x/nonsense": "not a dict",
    }}))
    back = acquired.read_manifest(tmp_path)
    assert set(back) == {"https://x/good"}


def test_stored_checks_the_file_not_just_the_manifest(tmp_path):
    blob = acquired.save(tmp_path, "https://x/a", BODY, XLSX, ".xlsx")
    acquired.write_manifest(tmp_path, {"https://x/a": blob})
    assert acquired.stored(tmp_path, "https://x/a") is not None
    # A manifest entry whose blob was deleted by hand is a claim the plane
    # cannot honour; a caller that trusted it would read a missing path.
    acquired.blob_path(tmp_path, blob.sha, ".xlsx").unlink()
    assert acquired.stored(tmp_path, "https://x/a") is None


def test_total_bytes_reports_the_store_size(tmp_path):
    assert acquired.total_bytes(tmp_path) == 0
    acquired.save(tmp_path, "https://x/a", BODY, XLSX, ".xlsx")
    assert acquired.total_bytes(tmp_path) == len(BODY)


# -- the bound that makes keep=true defensible ------------------------------


def _blob(url, n, run_seq=None, body=None):
    return url, (body or (b"x" * n))


def test_sweep_removes_only_unreferenced_blobs(tmp_path):
    kept = acquired.save(tmp_path, "https://x/keep", b"a" * 500, XLSX, ".xlsx")
    acquired.save(tmp_path, "https://x/gone", b"b" * 500, XLSX, ".xlsx")
    # Only one is still referenced by a URL.
    gone = acquired.sweep(tmp_path, {"https://x/keep": kept})
    assert gone == 1
    assert acquired.blob_path(tmp_path, kept.sha, ".xlsx").is_file()
    assert acquired.total_bytes(tmp_path) == 500


def test_eviction_is_ordered_by_run_seq_never_by_mtime(tmp_path):
    blobs = {}
    for i, seq in enumerate((7, 1, 4)):
        url = f"https://x/{i}"
        blobs[url] = acquired.save(tmp_path, url, bytes([i]) * 400, XLSX, ".x", run_seq=seq)
    # Cap forces two out; the two lowest run_seq (1, then 4) must go.
    evicted = acquired.evict(tmp_path, blobs, max_bytes=500)
    assert evicted == ["https://x/1", "https://x/2"]  # run_seq 1 then 4


def test_a_blob_whose_url_is_failing_is_never_evicted(tmp_path):
    # THE safety property: an acquired blob is not rebuildable, only
    # re-acquirable. A URL whose last fetch failed cannot be got back, so it
    # is never chosen however old or however large.
    blobs = {}
    for i, seq in enumerate((1, 2, 3)):
        url = f"https://x/{i}"
        blobs[url] = acquired.save(tmp_path, url, bytes([i]) * 400, XLSX, ".x", run_seq=seq)
    evicted = acquired.evict(
        tmp_path, blobs, max_bytes=400, protected={"https://x/0"}
    )
    assert "https://x/0" not in evicted
    assert acquired.blob_path(tmp_path, blobs["https://x/0"].sha, ".x").is_file()


def test_eviction_is_a_no_op_under_the_cap(tmp_path):
    blob = acquired.save(tmp_path, "https://x/a", b"a" * 100, XLSX, ".x", run_seq=1)
    assert acquired.evict(tmp_path, {"https://x/a": blob}, max_bytes=10_000) == []
    assert acquired.blob_path(tmp_path, blob.sha, ".x").is_file()


def test_run_seq_round_trips_and_none_sorts_oldest(tmp_path):
    a = acquired.save(tmp_path, "https://x/a", b"a" * 400, XLSX, ".x", run_seq=None)
    b = acquired.save(tmp_path, "https://x/b", b"b" * 400, XLSX, ".x", run_seq=9)
    acquired.write_manifest(tmp_path, {"https://x/a": a, "https://x/b": b})
    back = acquired.read_manifest(tmp_path)
    assert back["https://x/a"].run_seq is None
    assert back["https://x/b"].run_seq == 9
    # An entry predating the counter is the least evidence of recent use there
    # is, so it goes first.
    assert acquired.evict(tmp_path, back, max_bytes=400) == ["https://x/a"]


def test_the_manifest_still_holds_no_wall_clock_with_run_seq(tmp_path):
    blob = acquired.save(tmp_path, "https://x/a", b"a" * 10, XLSX, ".x", run_seq=3)
    acquired.write_manifest(tmp_path, {"https://x/a": blob})
    text = acquired.manifest_path(tmp_path).read_text().lower()
    assert '"run_seq": 3' in text.replace(" ", " ")
    for banned in ("timestamp", "fetched_at", "mtime", "iso8601"):
        assert banned not in text


def test_emptying_the_manifest_is_written_not_skipped(tmp_path):
    # Removing the last retained URL must not leave its entry on disk. "Nothing
    # to write" and "write nothing" are not the same instruction.
    blob = acquired.save(tmp_path, "https://x/a", BODY, XLSX, ".xlsx")
    acquired.write_manifest(tmp_path, {"https://x/a": blob})
    assert acquired.read_manifest(tmp_path)
    acquired.write_manifest(tmp_path, {})
    assert acquired.read_manifest(tmp_path) == {}


def test_an_empty_manifest_does_not_conjure_the_plane(tmp_path):
    acquired.write_manifest(tmp_path, {})
    assert not acquired.plane(tmp_path).exists()
