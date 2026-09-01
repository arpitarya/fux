"""`fux doctor` reports the plane; `fux remove` forgets it."""
from __future__ import annotations
import types
from fux import doctor, sources
from fux.ingest import sourcelist
from fux.store import acquired

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _repo(tmp_path):
    (tmp_path / ".fux").mkdir()
    (tmp_path / "fux.toml").write_text("[sources]\n")
    return tmp_path


def test_doctor_is_quiet_when_nothing_is_retained(tmp_path):
    c = doctor._acquired_health(_repo(tmp_path))
    assert c.ok and c.level == "warn" and "nothing retained" in c.detail


def test_doctor_reports_size_and_count(tmp_path):
    root = _repo(tmp_path)
    b = acquired.save(root, "https://x/a", b"z" * 900, XLSX, ".xlsx", run_seq=1)
    acquired.write_manifest(root, {"https://x/a": b})
    c = doctor._acquired_health(root)
    assert c.ok
    assert "1 blob(s)" in c.detail and "900 bytes" in c.detail


def test_doctor_counts_unreferenced_blobs(tmp_path):
    root = _repo(tmp_path)
    b = acquired.save(root, "https://x/a", b"a" * 100, XLSX, ".xlsx", run_seq=1)
    acquired.save(root, "https://x/orphan", b"b" * 100, XLSX, ".xlsx", run_seq=1)
    acquired.write_manifest(root, {"https://x/a": b})
    assert "1 unreferenced" in doctor._acquired_health(root).detail


def test_an_unignored_plane_is_an_ERROR_not_a_warning(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    b = acquired.save(root, "https://x/a", b"a" * 10, XLSX, ".xlsx")
    acquired.write_manifest(root, {"https://x/a": b})
    # This plane holds SOURCE BYTES. Git being able to see them is the one
    # failing case, not a housekeeping note.
    monkeypatch.setattr(doctor, "_is_git_ignored", lambda r, p: False)
    c = doctor._acquired_health(root)
    assert not c.ok
    assert "NOT GITIGNORED" in c.detail


def test_remove_forgets_the_manifest_entry_and_sweeps(tmp_path):
    root = _repo(tmp_path)
    b = acquired.save(root, "https://x/a", b"a" * 100, XLSX, ".xlsx", run_seq=1)
    acquired.write_manifest(root, {"https://x/a": b})
    sources._drop_acquired(root, sourcelist.URLS, "https://x/a")
    assert acquired.read_manifest(root) == {}
    # The blob went too, because nothing else referenced it.
    assert acquired.total_bytes(root) == 0


def test_remove_leaves_a_blob_two_urls_share(tmp_path):
    root = _repo(tmp_path)
    body = b"shared" * 40
    a = acquired.save(root, "https://x/a", body, XLSX, ".xlsx", run_seq=1)
    c = acquired.save(root, "https://x/b", body, XLSX, ".xlsx", run_seq=1)
    assert a.sha == c.sha           # content addressing: ONE file
    acquired.write_manifest(root, {"https://x/a": a, "https://x/b": c})
    sources._drop_acquired(root, sourcelist.URLS, "https://x/a")
    # Deleting it because one URL went would silently break the other.
    assert acquired.stored(root, "https://x/b") is not None


def test_remove_ignores_non_url_lists(tmp_path):
    root = _repo(tmp_path)
    b = acquired.save(root, "https://x/a", b"a" * 10, XLSX, ".xlsx")
    acquired.write_manifest(root, {"https://x/a": b})
    sources._drop_acquired(root, sourcelist.DIRS, "docs")
    assert acquired.read_manifest(root) != {}
