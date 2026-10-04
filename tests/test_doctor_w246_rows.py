"""W-246 section C - five `fux doctor` rows, each fired on a planted bad case.

Every test builds a throwaway repo, so no row is judged against this checkout.
Each row has a firing case and a quiet case: a row that cannot be quiet is
ignored, and one that cannot fire is decoration.
"""

from __future__ import annotations

import subprocess

import pytest

from fux import doctor
from fux.query import provenance
from l12_fixtures import write_config


def _repo(tmp_path):
    try:
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        pytest.skip("git unavailable")
    write_config(tmp_path)
    return tmp_path


def _row(root, name):
    return next(c for c in doctor.run(root) if c.name == name)


def _dirs(root, text):
    path = root / ".fux" / "sources" / "dirs"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _tune_entries(root, table, entries):
    """Put `entries` under the template's own `[table]` header (a second header is a TOML error)."""
    path = root / ".fux" / "tune.toml"
    text = path.read_text(encoding="utf-8")
    assert f"\n[{table}]\n" in text
    path.write_text(text.replace(f"\n[{table}]\n", f"\n[{table}]\n{entries}", 1), encoding="utf-8")


# -- B-020 priority keys -------------------------------------------------------


def test_priority_keys_quiet_without_any(tmp_path):
    assert _row(_repo(tmp_path), "priority keys").ok


def test_priority_key_matching_a_source_is_ok(tmp_path):
    root = _repo(tmp_path)
    _dirs(root, "docs\nhandbook/runbooks\n")
    _tune_entries(root, "priority", '"docs" = 2.0\n"handbook" = 1.5\n"docs/api" = 0.5\n')
    row = _row(root, "priority keys")
    assert row.ok, row.detail  # exact, ancestor of an entry, and narrower than an entry


def test_priority_key_matching_no_source_is_named(tmp_path):
    root = _repo(tmp_path)
    _dirs(root, "docs\n")
    _tune_entries(root, "priority", '"doc" = 2.0\n"archive" = 0.5\n')
    row = _row(root, "priority keys")
    assert not row.ok and row.level == "warn"
    # `doc` is a string prefix of `docs` but not at a `/` boundary (W-253).
    assert "`doc`" in row.detail and "`archive`" in row.detail


# -- B-074 fuxignore reachable -------------------------------------------------


def _ignore(root, text):
    path = root / ".fux" / ".fuxignore"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_a_rule_overridden_by_an_identical_later_one_warns(tmp_path):
    root = _repo(tmp_path)
    _ignore(root, "build\n*.log\n!build\n")
    row = _row(root, "fuxignore reachable")
    assert not row.ok and row.level == "warn"
    assert ":1 `build`" in row.detail and ":3 `!build`" in row.detail


def test_a_dir_only_rule_is_shadowed_by_the_same_pattern_without_the_slash(tmp_path):
    root = _repo(tmp_path)
    _ignore(root, "build/\nbuild\n")
    assert not _row(root, "fuxignore reachable").ok


def test_the_narrower_later_rule_does_not_shadow(tmp_path):
    """`build` (files and dirs) then `build/` (dirs only): the first still decides files."""
    root = _repo(tmp_path)
    _ignore(root, "build\nbuild/\n/build\n*.log\n")
    row = _row(root, "fuxignore reachable")
    assert row.ok, row.detail


def test_the_row_is_quiet_without_a_fuxignore(tmp_path):
    assert _row(_repo(tmp_path), "fuxignore reachable").ok


# -- B-080 decoder imports -----------------------------------------------------


def _decoder(root, name, body):
    path = root / ".fux" / "decoders" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


@pytest.mark.parametrize(
    "line",
    [
        "import urllib.request",
        "from urllib import request",
        "import socket",
        "import http.client",
        "from http.client import HTTPSConnection",
        "import requests",
        "import ssl",
    ],
)
def test_a_decoder_importing_a_network_module_warns(tmp_path, line):
    root = _repo(tmp_path)
    _decoder(root, "bad.py", f"{line}\n")
    row = _row(root, "decoder imports")
    assert not row.ok and row.level == "warn"
    assert "bad.py" in row.detail and "tripwire" in row.detail


def test_an_offline_decoder_is_quiet(tmp_path):
    root = _repo(tmp_path)
    _decoder(root, "ok.py", "from urllib.parse import unquote\nimport json\n")
    assert _row(root, "decoder imports").ok


def test_a_dynamic_import_passes_which_is_why_it_is_a_tripwire(tmp_path):
    root = _repo(tmp_path)
    _decoder(root, "sneaky.py", "import importlib\nm = importlib.import_module('soc' + 'ket')\n")
    assert _row(root, "decoder imports").ok


# -- B-168 ranking priors: intent_weight ----------------------------------------


def test_intent_weight_is_reported_with_a_zero_count_and_the_nothing_clause(tmp_path):
    from fux.store import write_index

    root = _repo(tmp_path)
    write_index(root, [])
    row = _row(root, "ranking priors")
    assert "intent_weight=" in row.detail and "0 document(s) of a preferred type" in row.detail
    assert "would change NOTHING in this repository" in row.detail


def test_intent_weight_counts_documents_of_each_type(tmp_path):
    from fux.store import write_index

    root = _repo(tmp_path)
    _tune_entries(root, "doctype", '"runbooks/*" = "procedure"\n')
    base = {"src": "git", "mode": "extracted", "title": "T", "phrases": [], "terms": {}, "wlen": 4, "edges": []}
    write_index(
        root,
        [
            {**base, "id": "file:runbooks/a.md", "loc": "runbooks/a.md"},
            {**base, "id": "file:runbooks/b.md", "loc": "runbooks/b.md"},
            {**base, "id": "file:other.md", "loc": "other.md"},
        ],
    )
    row = _row(root, "ranking priors")
    assert "2 document(s) of a preferred type" in row.detail and "procedure=2" in row.detail
    assert "intent_weight=0.1 (2" in row.detail and "NOTHING" not in row.detail.split("Also:")[-1]


def test_a_declared_doctype_that_reaches_nothing_makes_intent_a_dead_prior(tmp_path):
    from fux.store import write_index

    root = _repo(tmp_path)
    _tune_entries(root, "doctype", '"nowhere/*" = "procedure"\n')
    write_index(root, [])
    row = _row(root, "ranking priors")
    assert not row.ok
    assert "SWITCHED OFF at these values" in row.detail and "intent_weight=0.1 (0" in row.detail
    for nudge in ("try ", "set it to", "recommended", "should be"):
        assert nudge not in row.detail


# -- B-161 journal size ----------------------------------------------------------


def test_no_journal_is_ok(tmp_path):
    row = _row(_repo(tmp_path), "journal size")
    assert row.ok and "opt-in" in row.detail


def test_a_journal_above_the_limit_warns(tmp_path):
    root = _repo(tmp_path)
    out = root / ".fux" / "output.toml"
    out.write_text(
        out.read_text(encoding="utf-8").replace("journal_max_bytes = 4194304", "journal_max_bytes = 100"),
        encoding="utf-8",
    )
    path = provenance.journal_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x" * 500, encoding="utf-8")
    row = _row(root, "journal size")
    assert not row.ok and row.level == "warn"
    assert "journal_max_bytes=100" in row.detail and "500 bytes" in row.detail


def test_a_journal_within_the_limit_is_ok(tmp_path):
    root = _repo(tmp_path)
    path = provenance.journal_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x" * 500, encoding="utf-8")
    assert _row(root, "journal size").ok


def test_doctor_fix_writes_the_new_key_into_an_older_output_toml(tmp_path):
    from fux import setup as setup_mod

    root = _repo(tmp_path)
    out = root / ".fux" / "output.toml"
    out.write_text(
        "\n".join(ln for ln in out.read_text(encoding="utf-8").splitlines() if "journal_max_bytes" not in ln) + "\n",
        encoding="utf-8",
    )
    assert "journal_max_bytes" not in out.read_text(encoding="utf-8")
    changed = setup_mod.fill_missing(root)
    assert any("journal_max_bytes" in line for line in changed), changed
    assert "journal_max_bytes" in out.read_text(encoding="utf-8")
