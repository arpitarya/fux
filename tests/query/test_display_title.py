"""Every verb shows a `url:` document's real title, because there is only one
kind of title now.

⚠ **REWRITTEN for W-194 (Arpit, 2026-09-20), and what it used to test is worth
stating.** This file was P5's gate: a `meta: hashed` record carried `title_h`
and no readable text, so `ask`/`find`/`answer` showed the real title only while
the materialise-first display cache was warm, and a *labelled* hash — never a
bare one — when it had gone cold. Six scenarios, three verbs, warm and cold.

`meta`, `title_h` and `.fux/runtime/display-cache/` are deleted, `_format` is
`fux.index.v4`, and law L5 is retired. **The cold path cannot be reached**, so
the tests that exercised it are gone rather than reworded into something that
passes trivially.

🔴 **What the deletion gave up, kept here because a test file is where somebody
looks next.** L5 closed an **ACL-mismatch leak**: a document readable by fifty
people inside Confluence became a title readable by everyone with the repo.
That leak is now an **accepted, documented exposure**, not a solved problem —
[SR-LAW-5](../../records/0007_LAW-5-hashed-meta.md) keeps the argument, the
AOL-2006 citation and the reopen trigger. **L5 was right about the leak and
lost on cost.**

What is asserted below is the property that replaced it: a url record is shaped
exactly like a git record, and no verb has a second path for it.
"""

from __future__ import annotations

import argparse
import json as json_mod

from fux.query import cmd_answer, cmd_ask, cmd_find
from fux.query.tokenize import tokenize
from fux.store import content_sha, term_hash, write_index

DOC_ID = "url:https://x.test/handbook"
SHA = content_sha(DOC_ID.encode("utf-8"))
TITLE = "The Oncall Handbook"


def _h(word: str) -> str:
    """Hash the ANALYZED form — the query analyzes before hashing too, so a
    fixture that hashes the raw word would never be found (v2)."""
    return term_hash(tokenize(word)[0])


def _record() -> dict:
    """A url record. Since W-194 this differs from a git record only in `src`,
    `loc` and the shape of the id — no `meta`, no `title_h`."""
    return {
        "id": DOC_ID,
        "src": "url",
        "loc": "https://x.test/handbook",
        "mode": "extracted",
        "sha": SHA,
        "title": TITLE,
        "phrases": ["Escalation path"],
        "terms": {_h("oncall"): [2, 1]},
        "flen": [12],
        "edges": [],
    }


def _corpus(tmp_path):
    write_index(tmp_path, [_record()])
    return tmp_path


def _ask_args(**overrides) -> argparse.Namespace:
    base = dict(query="oncall", top=5, json=False, scan=True, explain=False, hybrid=False)
    base.update(overrides)
    return argparse.Namespace(**base)


# -- the title shows, on every verb, with nothing warmed -----------------


def test_ask_shows_the_real_title(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path))
    assert cmd_ask(_ask_args()) == 0
    out = capsys.readouterr().out
    assert TITLE in out
    assert "uncached" not in out


def test_ask_json_carries_the_real_title(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path))
    assert cmd_ask(_ask_args(json=True)) == 0
    payload = json_mod.loads(capsys.readouterr().out)
    assert payload["results"][0]["title"] == TITLE


def test_answer_shows_the_real_title(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path))
    args = argparse.Namespace(query="oncall", json=False, scan=True)
    assert cmd_answer(args) == 0
    assert capsys.readouterr().out.startswith(TITLE)


def test_find_carries_the_real_title_in_its_json(tmp_path, monkeypatch, capsys):
    """⚠ `find`'s TEXT output prints the `loc` and no title, which is why the
    assertion is on the JSON. Checked against the verb rather than assumed —
    a text assertion here would pass on the URL and prove nothing."""
    monkeypatch.setattr("fux.query.find_root", lambda: _corpus(tmp_path))
    assert cmd_find(argparse.Namespace(query="oncall", top=5, json=True)) == 0
    payload = json_mod.loads(capsys.readouterr().out)
    assert payload["results"][0]["title"] == TITLE


def test_the_scan_and_accelerator_paths_agree_on_the_title(tmp_path, monkeypatch, capsys):
    """The differential law, applied to the display step.

    ⚠ **This test used to be the important one in this file** — it cleared the
    cache first, so it proved the two paths agreed on a COLD hashed title,
    which was the only way they could ever have diverged. There is no cache and
    no hashed title now, so what it asserts is weaker by construction. It is
    kept because `display_title` is still a shared function with two callers
    and SR-ASK's P5 consequence still turns on them not drifting.
    """
    from fux.derive import build as build_fn

    root = _corpus(tmp_path)
    build_fn(root)
    monkeypatch.setattr("fux.query.find_root", lambda: root)

    assert cmd_ask(_ask_args(scan=True, json=True)) == 0
    scan_out = capsys.readouterr().out
    assert cmd_ask(_ask_args(scan=False, json=True)) == 0
    accel_out = capsys.readouterr().out
    assert json_mod.loads(scan_out)["results"] == json_mod.loads(accel_out)["results"]


# -- the property that replaced L5 ---------------------------------------


def test_a_url_record_needs_no_display_field_a_git_record_does_not(tmp_path):
    """The point of W-194, as a shape assertion rather than a claim.

    Before it, this record could not be written at all: `write_index` refused
    a non-git record that carried `title`, and refused a hashed one with no
    warm display-cache entry for its `sha`. Both refusals are gone with the
    rule, and the write below is the proof.
    """
    write_index(tmp_path, [_record()])
    records = [
        json_mod.loads(line)
        for path in sorted((tmp_path / ".fux" / "index").glob("*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()[1:]
    ]
    assert len(records) == 1
    written = records[0]
    assert written["title"] == TITLE
    assert "meta" not in written, "`meta` is deleted (W-194), not defaulted"
    assert "title_h" not in written, "`title_h` is deleted (W-194)"


def test_the_index_header_pins_v4(tmp_path):
    """A v3 index holds records a v4 reader has no rule for, so the bump is
    what turns a silent misread into a named refusal (`store/reader.py`)."""
    write_index(tmp_path, [_record()])
    shard = next((tmp_path / ".fux" / "index").glob("*.jsonl"))
    header = json_mod.loads(shard.read_text(encoding="utf-8").splitlines()[0])
    assert header["_format"] == "fux.index.v4"
