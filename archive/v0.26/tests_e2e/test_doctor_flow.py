"""e2e coverage for `fux doctor` — real CLI, real corpus (handoff 0005 §C)."""

from __future__ import annotations

import json
import shutil

from conftest import CORPUS, run_fux


def test_doctor_healthy_ingested_corpus(ingested):
    proc = run_fux(ingested, "doctor")
    assert proc.returncode == 0
    assert "healthy" in proc.stdout
    assert "FAIL" not in proc.stdout


def test_doctor_no_config(tmp_path):
    proc = run_fux(tmp_path, "doctor", check=False)
    assert proc.returncode == 1
    assert "fux setup" in proc.stdout


def test_doctor_zero_match_source_glob(tmp_path):
    proj = tmp_path / "proj"
    shutil.copytree(CORPUS, proj)
    (proj / "empty_dir").mkdir()
    run_fux(proj, "setup", "-y", "--docs", "docs,empty_dir")
    proc = run_fux(proj, "doctor", check=False)
    assert proc.returncode == 1
    assert "0 files" in proc.stdout
    assert "empty_dir" in proc.stdout


def test_doctor_drift(ingested):
    (ingested / "docs" / "guide.md").write_text("# changed\nnew content\n", encoding="utf-8")
    proc = run_fux(ingested, "doctor", check=False)
    assert proc.returncode == 1
    assert "drift" in proc.stdout.lower()


def test_doctor_json_shape(ingested):
    proc = run_fux(ingested, "doctor", "--json")
    payload = json.loads(proc.stdout)
    assert payload["healthy"] is True
    names = {g["name"] for g in payload["groups"]}
    assert names == {
        "environment", "capabilities", "config", "corpus",
        "consistency", "agent surface", "self-test",
    }


def test_doctor_never_touches_debug_output(ingested):
    """--debug=trace must not change doctor's own stdout (the M1 gate applies here too)."""
    off = run_fux(ingested, "doctor")
    trace = run_fux(ingested, "--debug=trace", "doctor")
    assert trace.stdout == off.stdout
