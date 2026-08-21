"""P5: `ask`/`find`/`answer` show a hashed document's real title when the
materialise-first display cache is warm, and a labelled hash when it is
cold — never a bare, indistinguishable-from-working hash (`meta-privacy.
compare.md`, reopened 2026-08-21).

The cache can only go cold *after* a record is committed — `store/writer.py`
refuses to write a `hashed` record with no cache entry for its `sha` — so
every "cold" scenario here writes warm, then clears the cache, matching how
a real cache eviction would leave the index.
"""

from __future__ import annotations

import argparse
import json as json_mod

from fux.query import cmd_answer, cmd_ask, cmd_find
from fux.store import DisplayCache, content_sha, term_hash, title_hash, write_index

DOC_ID = "url:https://x.test/handbook"
SHA = content_sha(DOC_ID.encode("utf-8"))
TITLE = "The Oncall Handbook"


def _record() -> dict:
    return {
        "id": DOC_ID,
        "src": "url",
        "loc": "https://x.test/handbook",
        "mode": "extracted",
        "meta": "hashed",
        "sha": SHA,
        "title_h": title_hash(TITLE),
        "terms": {term_hash("oncall"): [1, 2]},
        "wlen": 12,
        "edges": [],
    }


def _corpus(tmp_path):
    DisplayCache(tmp_path).put(SHA, DOC_ID, TITLE)  # warm — required to write at all
    write_index(tmp_path, [_record()])
    return tmp_path


def _ask_args(**overrides) -> argparse.Namespace:
    base = dict(query="oncall", top=5, json=False, scan=True, explain=False, hybrid=False)
    base.update(overrides)
    return argparse.Namespace(**base)


# -- warm cache: the real title shows -----------------------------------


def test_ask_shows_the_real_title_when_the_cache_is_warm(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path))
    assert cmd_ask(_ask_args()) == 0
    out = capsys.readouterr().out
    assert TITLE in out
    assert "uncached" not in out


def test_ask_json_shows_the_real_title_when_the_cache_is_warm(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path))
    assert cmd_ask(_ask_args(json=True)) == 0
    payload = json_mod.loads(capsys.readouterr().out)
    assert payload["results"][0]["title"] == TITLE


def test_answer_shows_the_real_title_when_the_cache_is_warm(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path))
    args = argparse.Namespace(query="oncall", json=False, scan=True)
    assert cmd_answer(args) == 0
    assert capsys.readouterr().out.startswith(TITLE)


# -- cold cache: a labelled hash shows, never a bare one -----------------


def test_ask_degrades_to_a_labelled_hash_when_the_cache_is_cold(tmp_path, monkeypatch, capsys):
    root = _corpus(tmp_path)
    DisplayCache(root).clear()  # simulate eviction after the record was already committed
    monkeypatch.setattr("fux.query.find_root", lambda: root)

    assert cmd_ask(_ask_args()) == 0
    out = capsys.readouterr().out
    assert TITLE not in out
    assert "uncached — title unavailable" in out


def test_ask_json_degrades_to_a_labelled_hash_when_the_cache_is_cold(tmp_path, monkeypatch, capsys):
    root = _corpus(tmp_path)
    DisplayCache(root).clear()
    monkeypatch.setattr("fux.query.find_root", lambda: root)

    assert cmd_ask(_ask_args(json=True)) == 0
    payload = json_mod.loads(capsys.readouterr().out)
    assert "uncached — title unavailable" in payload["results"][0]["title"]
    assert TITLE not in payload["results"][0]["title"]


def test_find_json_degrades_to_a_labelled_hash_when_the_cache_is_cold(tmp_path, monkeypatch, capsys):
    root = _corpus(tmp_path)
    DisplayCache(root).clear()
    monkeypatch.setattr("fux.query.find_root", lambda: root)

    args = argparse.Namespace(query="oncall", top=5, json=True, scan=True)
    assert cmd_find(args) == 0
    payload = json_mod.loads(capsys.readouterr().out)
    assert "uncached — title unavailable" in payload["results"][0]["title"]


def test_answer_degrades_to_a_labelled_hash_when_the_cache_is_cold(tmp_path, monkeypatch, capsys):
    root = _corpus(tmp_path)
    DisplayCache(root).clear()
    monkeypatch.setattr("fux.query.find_root", lambda: root)

    args = argparse.Namespace(query="oncall", json=False, scan=True)
    assert cmd_answer(args) == 0
    assert "uncached — title unavailable" in capsys.readouterr().out


def test_the_scan_and_accelerator_paths_agree_on_a_cold_hashed_title(tmp_path, monkeypatch, capsys):
    """The differential law's own spirit, applied to the new display step:
    whichever path answers, title resolution must agree — see ADR-ASK's
    P5 consequence for why this can never diverge by construction."""
    from fux.derive import build as build_fn

    root = _corpus(tmp_path)
    build_fn(root)
    DisplayCache(root).clear()
    monkeypatch.setattr("fux.query.find_root", lambda: root)

    scanned = _ask_args(scan=True, json=True)
    accelerated = _ask_args(scan=False, json=True)
    assert cmd_ask(scanned) == 0
    scan_out = capsys.readouterr().out
    assert cmd_ask(accelerated) == 0
    accel_out = capsys.readouterr().out
    assert json_mod.loads(scan_out)["results"] == json_mod.loads(accel_out)["results"]
