"""W-233 end to end through the real CLI: propose, write, ingest, ask.

A planted corpus where the answer is known: `RF-118` lives in one document and a
sibling shares its parts (`RF-119`, and `118` as a quantity). Before families the
question `RF 118` puts the sibling first; after `fux identifiers --write` and one
ingest, the exact document is first for every spelling — and `fux doctor` and
`fux ingest --check` both see an index built under other families.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SPELLINGS = ("RF-118", "RF 118", "rf118", "RF–118")


def _fux(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "fux.cli", *args], cwd=root,
                          capture_output=True, text=True, encoding="utf-8")


def _first(root: Path, query: str) -> str:
    out = _fux(root, "ask", "--json", "--no-related", query)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)["results"][0]["loc"]


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "fryer.md").write_text("# Fryer recalibration\n\nRF-118 covers the fryer oil recalibration.\n", "utf-8")
    (docs / "rota.md").write_text("# Fryer rota\n\nRF-119 replaces RF-117 and RF-120. The RF team logged 118 checks "
                                  "and 118 oil changes; RF-119 is weekly.\n", "utf-8")
    for i in range(6):
        (docs / f"note-{i}.md").write_text(f"# Note {i}\n\nshift ledger audit delivery {i}.\n", "utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "c"],
                   cwd=tmp_path, check=True)
    assert _fux(tmp_path, "setup").returncode == 0
    assert (tmp_path / ".fux" / "identifiers.toml").is_file(), "setup writes the file (L12)"
    assert _fux(tmp_path, "ingest").returncode == 0
    return tmp_path


def test_families_put_the_exact_document_first_for_every_spelling(repo):
    assert _first(repo, "RF 118") == "docs/rota.md", "the planted defect: parts alone favour the sibling"

    proposed = json.loads(_fux(repo, "identifiers", "--json").stdout)
    assert [f["template"] for f in proposed["families"]] == ["RF-{n}"]
    assert proposed["written"] is False

    path = repo / ".fux" / "identifiers.toml"
    user_before = path.read_text("utf-8").split("[detected]")[0]
    wrote = _fux(repo, "identifiers", "--write")
    assert wrote.returncode == 0, wrote.stderr
    text = path.read_text("utf-8")
    assert '"RF-{n}",' in text
    assert text.split("[detected]")[0] == user_before, "everything before [detected] is kept byte for byte"

    check = _fux(repo, "ingest", "--check")
    assert "families" in check.stdout, "ingest --check sees the index built under other families"
    doctor = _fux(repo, "doctor").stdout
    assert "[FAIL] identifier families indexed" in doctor

    assert _fux(repo, "ingest").returncode == 0
    for spelling in SPELLINGS:
        assert _first(repo, spelling) == "docs/fryer.md", spelling
    assert "nothing has drifted" in _fux(repo, "ingest", "--check").stdout
    assert "[OK] identifier families indexed" in _fux(repo, "doctor").stdout


def test_a_refused_regex_stops_ingest_by_name(repo):
    path = repo / ".fux" / "identifiers.toml"
    path.write_text(path.read_text("utf-8").replace("regex = []", 'regex = ["(a+)+"]'), "utf-8")
    out = _fux(repo, "ingest")
    assert out.returncode != 0
    assert "quantifier on a group" in out.stderr


def test_a_missing_file_is_named(repo):
    (repo / ".fux" / "identifiers.toml").unlink()
    out = _fux(repo, "ask", "RF 118")
    assert out.returncode != 0 and "identifiers.toml is missing" in out.stderr
    assert _fux(repo, "doctor", "--fix").returncode in (0, 1)
    assert (repo / ".fux" / "identifiers.toml").is_file(), "`doctor --fix` restores it"
