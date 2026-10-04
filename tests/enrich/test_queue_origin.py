"""W-248 — `fux enrich` consumes the decoder queue.

SR-ENRICH decision 4: the worklist is declared scope UNION the queue rows whose
reason is *a model is needed*. A row saying *no decoder for X* is not enrichment
work -- it is a `fux doctor` line. Two origins, never one count.
"""

from __future__ import annotations

from types import SimpleNamespace

from l12_fixtures import write_config

from fux import decode as decode_mod
from fux import doctor
from fux.enrich import QUEUE_SCOPE, cmd_enrich
from fux.ingest import queue as queue_mod
from fux.ingest import run as ingest_run

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50


def _planted(tmp_path):
    """One undecodable binary (via a real ingest) and one unknown extension."""
    root = tmp_path
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (root / ".fux" / "sources").mkdir(parents=True)
    (root / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (root / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    write_config(root)
    docs = root / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# A\n\nhello world\n", encoding="utf-8")
    (docs / "scan.png").write_bytes(PNG)
    ingest_run.run(root, refresh_urls=False, full=False)
    # Ingest leaves a plain-text unknown extension to the prose path, so the
    # "no decoder" row is written through the queue's own writer, with the
    # reason the decoder plane itself spells.
    rows = queue_mod.read(root)
    rows.append(queue_mod.QueueEntry(
        doc_id="file:docs/clip.zzz", sha="f" * 40,
        reason=decode_mod.reason("docs/clip.zzz", root),
    ))
    queue_mod.write(root, rows)
    return root


def _run(root, monkeypatch, capsys, check=False):
    monkeypatch.chdir(root)
    args = SimpleNamespace(target=None, check=check, progress=None)
    code = cmd_enrich(args)
    return code, capsys.readouterr().out


def test_the_binary_is_in_the_worklist_and_the_unknown_extension_is_not(tmp_path, monkeypatch, capsys):
    root = _planted(tmp_path)
    _code, out = _run(root, monkeypatch, capsys)
    assert "docs/scan.png" in out and "MISSING" in out
    assert "queued: a model is needed" in out
    assert "clip.zzz" not in out


def test_the_unknown_extension_is_a_doctor_line_and_the_binary_is_not(tmp_path):
    root = _planted(tmp_path)
    check = doctor._queue_no_decoder(root)
    assert not check.ok and check.level == "warn"
    assert check.name == "queue: no decoder"
    assert ".zzz" in check.detail and "fux-decoder" in check.detail
    assert ".png" not in check.detail


def test_check_reports_the_two_origins_apart(tmp_path, monkeypatch, capsys):
    root = _planted(tmp_path)
    _code, out = _run(root, monkeypatch, capsys, check=True)
    assert "1 queued by ingest (a model is needed)" in out
    assert QUEUE_SCOPE in out
    assert "clip.zzz" not in out


def test_an_absent_queue_is_no_queued_rows_never_an_error(tmp_path, monkeypatch, capsys):
    root = _planted(tmp_path)
    (root / queue_mod.QUEUE_REL).unlink()
    code, out = _run(root, monkeypatch, capsys, check=True)
    assert code == 0 and "queued by ingest" not in out
    assert doctor._queue_no_decoder(root).ok


def test_a_queue_alone_is_a_worklist(tmp_path, monkeypatch, capsys):
    """No `enrich=true` anywhere: the queue still yields work."""
    root = _planted(tmp_path)
    _code, out = _run(root, monkeypatch, capsys)
    assert "no enrichment scopes declared" not in out


def test_a_no_decoder_only_queue_is_not_a_worklist(tmp_path, monkeypatch, capsys):
    root = _planted(tmp_path)
    queue_mod.write(root, [e for e in queue_mod.read(root) if queue_mod.no_decoder(e)])
    _code, out = _run(root, monkeypatch, capsys)
    assert "no enrichment scopes declared" in out
