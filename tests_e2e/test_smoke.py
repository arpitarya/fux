"""M0 smoke: the real CLI via subprocess, not the in-process API."""

from __future__ import annotations

import os
import subprocess
import sys

from fux import __version__


def test_fux_version_via_subprocess():
    result = subprocess.run(
        [sys.executable, "-m", "fux.cli", "--version"], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == f"fux {__version__}"


def test_fux_doctor_via_subprocess(tmp_path):
    (tmp_path / ".git").mkdir()
    result = subprocess.run(
        [sys.executable, "-m", "fux.cli", "doctor"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0
    assert "python version" in result.stdout


def test_fux_doctor_output_is_ascii_safe(tmp_path):
    """A non-ASCII character (e.g. a Unicode checkmark) crashes Windows'
    default console codepage ('charmap' can't encode U+2714) — the process
    exits 1 with a UnicodeEncodeError instead of printing. Force the
    strictest plausible stdout encoding to catch this on any platform."""
    (tmp_path / ".git").mkdir()
    env = {**os.environ, "PYTHONIOENCODING": "ascii"}
    result = subprocess.run(
        [sys.executable, "-m", "fux.cli", "doctor"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    result.stdout.encode("ascii")  # raises if anything non-ASCII slipped through


def test_fux_doctor_reports_the_w101_checks_as_a_user_sees_them(tmp_path):
    """W-101: the four checks, through the real CLI, on a real ingest.

    The in-process suite drives each branch; this asserts the lines exist at
    all in a repo built the way a consumer builds one — the failure mode a
    unit test cannot see is a check registered in `_layout` and never reached
    because an earlier one raised.
    """
    import json

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "fux.toml").write_text("", encoding="utf-8")
    (tmp_path / "a.md").write_text("# Alpha\n\nsomething findable\n", encoding="utf-8")
    setup = subprocess.run(
        [sys.executable, "-m", "fux.cli", "setup"], capture_output=True, text=True, cwd=tmp_path
    )
    assert setup.returncode == 0, setup.stderr
    ingest = subprocess.run(
        [sys.executable, "-m", "fux.cli", "ingest"], capture_output=True, text=True, cwd=tmp_path
    )
    assert ingest.returncode == 0, ingest.stderr

    result = subprocess.run(
        [sys.executable, "-m", "fux.cli", "doctor"], capture_output=True, text=True, cwd=tmp_path
    )
    for name in ("refusal rules", "decoder bindings", "recency prior", "freshness verdicts"):
        assert name in result.stdout, result.stdout

    # `fux doctor --json`'s `freshness` block is what ADR-ACQUIRED and
    # ADR-URL-FRESHNESS both name as the way to run their veto.
    payload = json.loads(
        subprocess.run(
            [sys.executable, "-m", "fux.cli", "doctor", "--json"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        ).stdout
    )
    assert payload["freshness"] == {}, "no answer has been journalled, so the share is unknown"


def test_a_generated_types_file_leaves_the_binding_check_quiet(tmp_path):
    """The check must not fire on a repo `fux setup` just wrote.

    `setup` writes the whole built-in binding table, so on a markdown corpus
    most bindings match no document — every one of them correct. A check that
    is loud on a fresh healthy repo is one people learn to skip.
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "fux.toml").write_text("", encoding="utf-8")
    (tmp_path / "a.md").write_text("# Alpha\n\nfindable\n", encoding="utf-8")
    subprocess.run([sys.executable, "-m", "fux.cli", "setup"], check=True, cwd=tmp_path,
                   capture_output=True)
    subprocess.run([sys.executable, "-m", "fux.cli", "ingest"], check=True, cwd=tmp_path,
                   capture_output=True)
    line = next(
        ln
        for ln in subprocess.run(
            [sys.executable, "-m", "fux.cli", "doctor"], capture_output=True, text=True,
            cwd=tmp_path,
        ).stdout.splitlines()
        if "decoder bindings" in ln
    )
    assert line.startswith("[OK]"), line
    assert "match no indexed document" not in line
