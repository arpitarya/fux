"""`.fux/observers/` — W-170, the observe-only hook.

The load-bearing test in this file is
`test_output_is_byte_identical_with_a_misbehaving_observer`. Everything else
checks a property; that one checks the **promise**, which is that a consumer's
code cannot reach an answer even when it is actively trying to.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from fux import observe

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# args_hash — the contract shared with a subscriber's transcript classifier
# ---------------------------------------------------------------------------


def test_args_hash_excludes_the_question_entirely():
    """🔴 **The clause the whole hook rests on.**

    A hash *of* the question is still a fingerprint of the question: two runs
    of the same query would match across consumers, which is exactly the
    re-identification L8 exists to prevent. So positionals are dropped, and
    two different questions under the same flags hash the same.
    """
    a = observe.args_hash(["ask", "how do i roll back"])
    b = observe.args_hash(["ask", "what is the retention policy"])
    assert a == b, "two different questions must not be distinguishable"
    assert a == observe.args_hash(["ask"]), "the question contributes nothing at all"


def test_args_hash_sorts_flags_so_one_command_is_one_hash():
    """`--json --band` and `--band --json` are the same command.

    A classifier joining on argv order would miss half its matches for a
    difference no user could see.
    """
    assert observe.args_hash(["ask", "q", "--json", "--band"]) == observe.args_hash(
        ["ask", "q", "--band", "--json"]
    )


def test_args_hash_separates_verbs_and_flag_values():
    """The verb is kept — it is the one positional that is not user content —
    and a value the consumer typed differently is a different command."""
    assert observe.args_hash(["ask", "q"]) != observe.args_hash(["find", "q"])
    assert observe.args_hash(["ask", "--top=5"]) != observe.args_hash(["ask", "--top=05"])
    assert observe.args_hash(["ask"]) != observe.args_hash(["ask", "--json"])


def test_a_quoted_command_line_hashes_the_same_as_a_bare_one():
    """The fixture SR-OBSERVE decision 4 requires, on the Python side.

    By the time fux sees `argv` the shell has removed quoting, so
    `fux ask "a b"` and `fux ask a b` arrive as different argv — and hash the
    same, because both drop their positionals. **A subscriber's classifier
    reconstructing argv from a transcript will see the quoted form**, and this
    is what says the two sides still meet.
    """
    assert observe.args_hash(["ask", "a b"]) == observe.args_hash(["ask", "a", "b"])
    assert observe.args_hash(["ask", "a b", "--json"]) == observe.args_hash(
        ["ask", "a", "b", "--json"]
    )


def test_a_bare_flag_never_swallows_the_token_after_it():
    """⚠ **The ambiguity that could have leaked the question.**

    `fux ask --band rollback` is a value-less flag followed by the question.
    Treating the next token as the flag's value would fold question text into
    the hash — the one thing this function may not do. So a bare flag consumes
    nothing, and the token after it is dropped as the positional it is.
    """
    assert observe.args_hash(["ask", "--band", "rollback"]) == observe.args_hash(
        ["ask", "--band", "retention"]
    )


# ---------------------------------------------------------------------------
# The record — a closed schema of counts
# ---------------------------------------------------------------------------


FORBIDDEN_KEYS = {"query", "question", "expand", "expansion", "loc", "path", "id",
                  "doc", "doc_id", "answer", "passage", "text", "title", "snippet"}


def test_the_record_schema_carries_no_content_bearing_field():
    """SR-OBSERVE decision 3's forbidden classes, checked on the SCHEMA.

    A field added by a future change that happens to be named `path` or
    `answer` fails here before it can ever be emitted.
    """
    record = observe.Record(
        verb="ask", args_hash="deadbeefdeadbeef", band="grounded", answerable=True,
        n_results=5, n_related=2, refer_verdicts={"current": 1}, ms=12,
        expand_used=False, q_arms=1, fux_version="0.0.0",
    )
    assert set(record.as_dict()) & FORBIDDEN_KEYS == set()
    assert set(record.as_dict()) == {
        "verb", "args_hash", "band", "answerable", "n_results", "n_related",
        "refer_verdicts", "ms", "expand_used", "q_arms", "fux_version",
    }


def test_every_value_in_the_record_is_a_count_a_name_a_flag_or_a_hash():
    """No free text reaches a subscriber, whatever a future field is called.

    A `str` is allowed only where the vocabulary is fixed (`verb`, `band`) or
    the value is a hash — so this asserts the types rather than trusting the
    names.
    """
    record = observe.Record(
        verb="ask", args_hash="deadbeefdeadbeef", band="grounded", answerable=True,
        n_results=5, n_related=2, refer_verdicts={"current": 1}, ms=12,
        expand_used=False, q_arms=1, fux_version="0.0.0",
    )
    for key, value in record.as_dict().items():
        assert isinstance(value, (str, bool, int, dict, type(None))), key
        if isinstance(value, str):
            assert key in {"verb", "args_hash", "band", "fux_version"}, key


# ---------------------------------------------------------------------------
# The dispatcher
# ---------------------------------------------------------------------------


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    fux = tmp_path / ".fux"
    (fux / "sources").mkdir(parents=True, exist_ok=True)
    (fux / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (fux / "pii.toml").write_text("", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "rollback.md").write_text(
        "# Rollback\n\nHow to roll back a release safely.\n", encoding="utf-8"
    )
    (docs / "retention.md").write_text(
        "# Retention\n\nLogs are kept for thirty days.\n", encoding="utf-8"
    )
    return tmp_path


def _observer(root: Path, name: str, body: str) -> Path:
    directory = root / ".fux" / "observers"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = _repo(tmp_path)
    _run(root, "ingest")
    return root


def test_an_observer_receives_one_record_of_counts(repo):
    """The happy path, through the real CLI rather than the dispatcher."""
    _observer(repo, "probe.py", """
import json, pathlib
def observe(record):
    pathlib.Path("seen.json").write_text(json.dumps(record))
""")
    _run(repo, "ask", "rollback")
    seen = json.loads((repo / "seen.json").read_text(encoding="utf-8"))
    assert seen["verb"] == "ask"
    assert seen["n_results"] >= 1
    assert len(seen["args_hash"]) == 16


def test_no_emitted_record_carries_the_question_or_a_path(repo):
    """🔴 **The grep SR-OBSERVE decision 3 requires, on the EMITTED record.**

    The schema test above checks the shape; this checks what actually comes
    out of a real query against a real corpus — the values, not the keys.
    """
    _observer(repo, "probe.py", """
import json, pathlib
def observe(record):
    pathlib.Path("seen.json").write_text(json.dumps(record))
""")
    _run(repo, "ask", "rollback release safely", "--expand", "revert deploy rollback")
    blob = (repo / "seen.json").read_text(encoding="utf-8")
    for forbidden in ("rollback", "release", "safely", "revert", "deploy",
                      "docs/", ".md", "file:"):
        assert forbidden not in blob, f"{forbidden!r} reached an observer"


def test_output_is_byte_identical_with_a_misbehaving_observer(repo):
    """🔴 **THE load-bearing test.** Zero, one, and an observer that is
    actively hostile — it raises, it sleeps past the cap, and it writes to
    stdout — must all produce the same bytes on stdout and the same exit code.

    If this can be made to fail, the seam leaks and SR-OBSERVE's *remove the
    dispatcher* clause applies: a hook that can reach an answer is worse than
    no hook.
    """
    baseline = _run(repo, "ask", "rollback", "--json")

    _observer(repo, "a_raises.py", """
def observe(record):
    raise RuntimeError("boom")
""")
    _observer(repo, "b_prints.py", """
import sys
def observe(record):
    print("OBSERVER NOISE ON STDOUT")
    sys.stdout.flush()
""")
    _observer(repo, "c_sleeps.py", """
import time
def observe(record):
    time.sleep(5)
""")
    _observer(repo, "d_mutates.py", """
def observe(record):
    record["n_results"] = 999
    record.clear()
    return {"hijacked": True}
""")
    hostile = _run(repo, "ask", "rollback", "--json")

    assert hostile.stdout == baseline.stdout, "consumer code reached stdout"
    assert hostile.returncode == baseline.returncode, "consumer code reached the exit code"


def test_a_mutating_observer_cannot_reach_the_next_one(repo):
    """Each observer gets its own `dict`. One that clears what it is handed
    must not hand the next one an empty record."""
    _observer(repo, "a_clears.py", """
def observe(record):
    record.clear()
""")
    _observer(repo, "b_reads.py", """
import json, pathlib
def observe(record):
    pathlib.Path("second.json").write_text(json.dumps(record))
""")
    _run(repo, "ask", "rollback")
    seen = json.loads((repo / "second.json").read_text(encoding="utf-8"))
    assert seen["verb"] == "ask", "the first observer emptied the second's record"


def test_a_repo_with_no_observers_directory_is_unaffected(repo):
    """The common path: one `stat` and nothing else."""
    assert not (repo / ".fux" / "observers").exists()
    assert _run(repo, "ask", "rollback").returncode == 0


def test_observers_run_in_sorted_filename_order(repo):
    """Order is part of the contract — one that depended on the filesystem
    would make one machine's behaviour differ from another's for no stated
    reason."""
    for name in ("c.py", "a.py", "b.py"):
        _observer(repo, name, f"""
import pathlib
def observe(record):
    with open("order.txt", "a") as fh:
        fh.write("{name}\\n")
""")
    _run(repo, "ask", "rollback")
    assert (repo / "order.txt").read_text(encoding="utf-8").split() == ["a.py", "b.py", "c.py"]


def test_the_doctor_row_names_an_observer_that_never_fires(repo):
    """A present-but-never-firing observer is silent by construction — the
    dispatcher is fail-open — so `fux doctor` is the only place it surfaces."""
    _observer(repo, "broken.py", """
def observe(record):
    raise RuntimeError("always")
""")
    _run(repo, "ask", "rollback")
    out = _run(repo, "doctor").stdout
    assert "observers" in out
    assert "broken.py" in out


def test_fux_carries_no_knowledge_of_any_subscriber():
    """SR-OBSERVE decision 8, as a grep over the shipped package.

    🔴 **fux must not learn a consumer's name.** The whole reason the emit
    design was rejected is that it would have put a cage-shaped path into this
    tree; a mention here would be that decision arriving by drift.
    """
    offenders = []
    for path in (ROOT / "src" / "fux").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for name in ("cage", "langfuse", "helicone", "langsmith"):
            # `cage` as a whole word only — `package`, `cages` in prose and
            # `percentage` must not trip it.
            import re

            if re.search(rf"\b{name}\b", text):
                offenders.append(f"{path.relative_to(ROOT)}: {name}")
    assert not offenders, (
        "src/fux/ names a subscriber — SR-OBSERVE decision 8. fux exposes the "
        "seam and knows nothing about who subscribes:\n  " + "\n  ".join(offenders)
    )
