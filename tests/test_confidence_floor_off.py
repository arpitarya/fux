"""`separation_floor = 0.0` turns `weak` off, and now something says so.

🔴 **[SR-CONFIDENCE](../records/0141_confidence.md) decision 13 says this about
itself**, in the paragraph that reversed decision 7's prohibition:

> A consumer can set `separation_floor = 0.0` and **no answer is ever `weak`
> again**. That is tuning away the *signal* rather than the ranking, it is
> silent, and **nothing mechanical catches it.**

This is the catch (W-164 gate 4). Two surfaces, one string:

- **`fux doctor`'s `confidence floors` row**, for whoever goes looking.
- **A once-per-process note on `ask`'s stderr**, for whoever does not — the
  person reading a `grounded` is the person who needs to know what it is worth,
  and they are not running `doctor`.

**It reports and never refuses.** Decision 13 reversed a lock on exactly the
reasoning that fux states costs rather than clamping knobs; a check that refused
the value would be decision 7 returning in a new costume.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from fux import doctor

ROOT = Path(__file__).resolve().parents[1]


def _repo(tmp_path, floor=None):
    (tmp_path / ".git").mkdir()
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (tmp_path / ".fux" / "sources").mkdir(parents=True)
    (tmp_path / ".fux" / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    # SR-PII decision 17: a repo without .fux/pii.toml refuses; empty redacts nothing.
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# Rollback\n\nhow to roll back\n", encoding="utf-8")
    if floor is not None:
        (tmp_path / ".fux" / "tune.toml").write_text(
            f"[confidence]\nseparation_floor = {floor}\n", encoding="utf-8"
        )
    return tmp_path


def _row(root):
    return next(c for c in doctor.run(root) if c.name == "confidence floors")


# -- the doctor row ----------------------------------------------------------


def test_a_floor_of_zero_is_reported(tmp_path):
    row = _row(_repo(tmp_path, floor="0.0"))
    assert not row.ok
    assert row.level == "warn", "zero is a LEGAL value - decision 13 reversed the lock"
    assert "weak" in row.detail
    assert row.detail.isascii(), "printed text reaches a Windows console"


def test_the_engine_default_is_not_reported(tmp_path):
    """A row that fired on every repo would be a row nobody reads."""
    assert _row(_repo(tmp_path)).ok


def test_a_tuned_but_non_zero_floor_is_not_reported(tmp_path):
    """⚠ **A LOW floor is not this row's business.**

    `0.02` is a judgement about this corpus, and the band publishes the floor it
    was judged under so a reader can see it. Only zero makes `weak` UNREACHABLE,
    which is the one value that changes what the band can say rather than where
    it sits.
    """
    assert _row(_repo(tmp_path, floor="0.02")).ok


def test_doc_coverage_floor_at_zero_is_NOT_reported(tmp_path):
    """⚠ `0.0` is that clause's shipped default — decision 13's own comment says
    `0.0 = the clause is OFF`. Firing on it would fire on every repo there is."""
    root = _repo(tmp_path)
    (root / ".fux" / "tune.toml").write_text(
        "[confidence]\ndoc_coverage_floor = 0.0\n", encoding="utf-8"
    )
    assert _row(root).ok


def test_an_unparseable_tune_file_defers_to_its_own_row(tmp_path):
    """Two rows telling different stories about one broken file teaches a reader
    to trust neither. `tune.toml loads` is the row for that."""
    root = _repo(tmp_path)
    (root / ".fux" / "tune.toml").write_text("[confidence\n", encoding="utf-8")
    assert _row(root).ok


# -- the note on `ask` -------------------------------------------------------


def _ask(root, *extra):
    return subprocess.run(
        [sys.executable, "-m", "fux", "ask", "rollback", *extra],
        cwd=root, capture_output=True, text=True, encoding="utf-8",
    )


def _ingest(root):
    subprocess.run(
        [sys.executable, "-m", "fux", "ingest"],
        cwd=root, capture_output=True, text=True, encoding="utf-8", check=True,
    )


def test_ask_says_it_once_on_stderr(tmp_path):
    root = _repo(tmp_path, floor="0.0")
    _ingest(root)
    result = _ask(root)
    assert "separation_floor" in result.stderr
    assert "separation_floor" not in result.stdout, "stdout is the answer, never a warning"


def test_ask_is_silent_at_the_default_floor(tmp_path):
    root = _repo(tmp_path)
    _ingest(root)
    assert "separation_floor" not in _ask(root).stderr


def test_json_carries_no_note_on_either_stream(tmp_path):
    """🔴 **`--json` is a contract**, and its stdout is captured and diffed.

    A JSON caller reads the floor from the `confidence` block — which decision 13
    called *"the load-bearing half of the reversal"*, added for exactly this
    reason — so the note would be noise on a channel that already carries the
    fact in a parseable form.
    """
    root = _repo(tmp_path, floor="0.0")
    _ingest(root)
    result = _ask(root, "--json", "--band")
    assert "separation_floor" not in result.stderr
    payload = json.loads(result.stdout)
    assert payload["confidence"]["separation_floor"] == 0.0, (
        "the machine-readable half must still carry it - that is what makes "
        "suppressing the prose note legitimate rather than a silence"
    )


def test_the_mcp_transport_never_carries_it(tmp_path):
    """MCP has no free-text channel to a human; its result carries the block.

    Asserted at the seam rather than over a live server: `_declare_floor_off`
    takes `quiet`, and MCP is a `quiet` caller by construction.
    """
    import inspect

    from fux.query import _declare_floor_off

    assert "quiet" in inspect.signature(_declare_floor_off).parameters


def test_all_three_read_verbs_say_it(tmp_path):
    """⚠ **Widened past W-164's DoD, deliberately, and the reason is recorded.**

    The item named `ask`. `find` and `answer` publish the same band from the same
    floor, and a note on one of three would make SR-FIND decision 6's *"the same
    rule as `ask`"* false for the second time in one week. It costs nothing: the
    note is once per PROCESS, so a session using two verbs still hears it once.
    """
    root = _repo(tmp_path, floor="0.0")
    _ingest(root)
    for verb in ("ask", "find", "answer"):
        result = subprocess.run(
            [sys.executable, "-m", "fux", verb, "rollback"],
            cwd=root, capture_output=True, text=True, encoding="utf-8",
        )
        assert "separation_floor" in result.stderr, verb
        assert "separation_floor" not in result.stdout, verb


def test_the_node_reader_says_it_too():
    """Both readers, or the one place a repo answers from Node is the one place
    the note goes unsaid. Node reads `.fux/tune.toml` through `runQuery`
    (SR-NODE-SEARCH decision 8), so it knows the floor and owes the sentence."""
    node = ROOT / "node" / "src" / "verbs" / "find.mjs"
    body = node.read_text(encoding="utf-8")
    assert "declareFloorOff" in body
    from fux.doctor import FLOOR_OFF_NOTE

    # The same sentence, not a second account of it. Compared on the distinctive
    # clause rather than byte-for-byte: the JS builds it from concatenated
    # string literals, so whitespace between them is a formatting choice.
    assert "That tunes away the SIGNAL, not the ranking" in body
    assert "That tunes away the SIGNAL, not the ranking" in FLOOR_OFF_NOTE


def test_the_two_surfaces_print_the_SAME_sentence():
    """One string, two callers. Two accounts of one fact is how they drift."""
    from fux.doctor import FLOOR_OFF_NOTE

    assert FLOOR_OFF_NOTE.isascii()
    assert "separation_floor" in FLOOR_OFF_NOTE
    assert "weak" in FLOOR_OFF_NOTE
