"""W-281 — the capture driver template: schedule changes only, frozen gates untouched."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRV = ROOT / "tools" / "quality-controls" / "capture-driver"

FAKE_G3 = '''
import json, sys
TREATMENTS = ("sw-1.0", "sw-0.5")
def main():
    print(json.dumps({"gate": "g", "questions": 2, "sectionless_documents": 3,
                      "arms": {a: {"failures": 0} for a in TREATMENTS}, "verdict": "PASS"}))
    return 0
'''


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(DRV / "g3_one_arm.py"), *args],
                          capture_output=True, text=True)


def test_one_arm_narrows_the_frozen_treatments_without_editing_it(tmp_path):
    g3 = tmp_path / "g3.py"
    g3.write_text(FAKE_G3)
    before = g3.read_bytes()
    r = _run("run", str(g3), "sw-0.5")
    assert r.returncode == 0, r.stderr
    assert list(json.loads(r.stdout)["arms"]) == ["sw-0.5"]
    assert g3.read_bytes() == before


def test_an_unknown_arm_is_refused(tmp_path):
    g3 = tmp_path / "g3.py"
    g3.write_text(FAKE_G3)
    assert _run("run", str(g3), "sw-9.9").returncode != 0


def test_merge_unions_arms_and_fails_if_any_part_fails(tmp_path):
    parts = []
    for arm, verdict in (("sw-1.0", "PASS"), ("sw-0.5", "FAIL")):
        p = tmp_path / f"{arm}.json"
        p.write_text(json.dumps({"gate": "g", "questions": 2, "sectionless_documents": 3,
                                 "arms": {arm: {}}, "verdict": verdict}))
        parts.append(str(p))
    out = json.loads(_run("merge", *parts).stdout)
    assert set(out["arms"]) == {"sw-1.0", "sw-0.5"} and out["verdict"] == "FAIL"


def test_merge_refuses_mismatched_parts(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps({"gate": "g", "questions": 2, "sectionless_documents": 3, "arms": {}, "verdict": "PASS"}))
    b.write_text(json.dumps({"gate": "g", "questions": 3, "sectionless_documents": 3, "arms": {}, "verdict": "PASS"}))
    assert _run("merge", str(a), str(b)).returncode != 0


def test_builder_disables_signing_and_capture_orders_latency_last():
    assert "commit.gpgsign=false" in (DRV / "build_from_worktree.py").read_text()
    sh = (DRV / "capture.sh").read_text(encoding="utf-8")
    assert sh.index('wait "$G1_PID"') < sh.index("step latency python3")
    assert sh.index("step g3_parallel") < sh.index("step latency python3")
    for frozen in ("g0.py", "g3.py", "g4.py", "latency.py", "decide.py"):
        assert not (DRV / frozen).exists()
    # The driver runs on Arpit's Mac; on a Windows runner `bash` may be WSL's,
    # which cannot open a D:\ path. Linux and macOS check the syntax.
    if sys.platform != "win32":
        subprocess.run(["bash", "-n", str(DRV / "capture.sh")], check=True)
