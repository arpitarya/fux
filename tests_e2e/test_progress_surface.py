"""The progress plane through the real CLI (W-64, ADR-CLI decision 9).

**The load-bearing test is `test_stdout_is_byte_identical_with_the_bar_on_or
_off`.** Everything else in this file supports it. A bar that leaked into
stdout would corrupt the `--json` contract every agent consumer reads, and
that is the one failure no amount of care in `progress.py` would catch on its
own.

The corpus is deliberately larger than `progress.THRESHOLD`, or the bar would
never engage and every assertion here would pass vacuously.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from fux.progress import THRESHOLD

# Enough documents that `extract`, `edges` and `postings` all clear the count
# threshold. Below it, nothing paints and this file would prove nothing.
CORPUS = THRESHOLD + 50


def _run(cwd: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = tmp_path / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True)
    dirs.write_text("docs\n", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    for i in range(CORPUS):
        (docs / f"doc{i:04d}.md").write_text(
            f"---\ntitle: Document {i}\n---\n# Document {i}\n\n"
            f"term{i % 37} shared body text about pruning and the committed index.\n",
            encoding="utf-8",
        )
    return tmp_path


#: Every verb that constructs a `Progress` — kept in step with `cli.py`'s
#: `_PROGRESS_COMMANDS` by `test_every_progress_verb_is_covered` below, so a
#: verb added to the plane cannot skip the invariant by being forgotten here.
WRITE_VERBS = ["ingest", "build", "add", "remove", "update"]

#: The one argument each verb needs to do real work on the fixture. `update`
#: with no entry re-reads everything; `add`/`remove` need something to act on.
#: **`remove` takes a single document, not `docs`** — removing the whole
#: directory empties the corpus, so every phase total drops under the
#: threshold, nothing paints, and both arms would be silent. That comparison
#: passes while testing nothing, which is the shape of bug this file exists
#: to catch rather than commit.
VERB_ARGS = {"add": ("docs",), "remove": ("docs/doc0000.md",), "update": ()}

#: The contents of `.fux/sources/dirs` each verb needs **before each arm**, so
#: both arms start from the same state. A mutating verb is not idempotent and
#: the two are not each other's inverse: `add` refuses to un-exclude by design
#: (`!` subtracts and nothing adds back), so `remove`'s reset cannot be an
#: `add`. Rewriting the committed list directly is the honest reset.
VERB_PREPARE = {
    "add": "",  # `docs` not listed yet, so `add docs` has real work to do
    "remove": "docs\n",  # listed and nothing excluded, so `!` is a fresh line
}

#: Verbs whose fixture is large enough that a bar **must** appear. Asserting
#: this is what stops the parametrization above from passing vacuously if a
#: verb silently stops inheriting the plane.
VERBS_THAT_MUST_PAINT = {"ingest", "build", "add", "remove", "update"}


def test_every_progress_verb_is_covered():
    """The parametrize list above must not drift from the CLI.

    W-63 added three verbs to `_PROGRESS_COMMANDS`; without this check the
    invariant would silently keep testing only the two it was written for.
    """
    from fux.cli import _PROGRESS_COMMANDS

    assert set(_PROGRESS_COMMANDS) == set(WRITE_VERBS), (
        "cli.py's _PROGRESS_COMMANDS and this file's WRITE_VERBS disagree — a "
        "verb that paints a bar is not being checked for the stdout invariant."
    )


@pytest.mark.parametrize("verb", WRITE_VERBS)
def test_stdout_is_byte_identical_with_the_bar_on_or_off(repo: Path, verb: str):
    """**The invariant.** If only one test in this file survives, it is this one.

    `--progress` forces the bar on even though the test harness gives the
    subprocess a pipe rather than a TTY — without the force, both arms would
    take the same silent path and the comparison would be vacuous.

    A mutating verb is not idempotent, so each arm is put back into the same
    starting state first (`VERB_PREPARE`) — otherwise the two arms would
    compare a success against a refusal and say nothing about the bar.
    """
    args = VERB_ARGS.get(verb, ())

    def prepare() -> None:
        listing = VERB_PREPARE.get(verb)
        if listing is not None:
            (repo / ".fux" / "sources" / "dirs").write_text(listing, encoding="utf-8")
        # ⚠ **`.fuxignore` is a SECOND piece of mutable state `remove` writes**,
        # added by W-93 after this reset was written. Restoring only `dirs` left
        # the first arm's record behind, so the second arm reported *"already
        # recorded in .fux/.fuxignore"* and *"nothing left the index"* while the
        # first reported a real drop — the two arms differed on their own
        # history rather than on the bar, and the invariant became untestable
        # for `remove` **while still failing loudly**, which is the good outcome
        # of the two.
        fuxignore = repo / ".fux" / ".fuxignore"
        if fuxignore.exists():
            fuxignore.unlink()
        _run(repo, "ingest")  # settle the index against that listing

    prepare()
    with_bar = _run(repo, verb, *args, "--progress")
    prepare()
    without = _run(repo, verb, *args, "--no-progress")

    assert with_bar.returncode == without.returncode == 0, (
        f"{verb} did not succeed in both arms:\n"
        f"--- with --progress (rc={with_bar.returncode})\n{with_bar.stderr}\n"
        f"--- with --no-progress (rc={without.returncode})\n{without.stderr}"
    )
    assert with_bar.stdout == without.stdout, (
        "stdout differs with the bar on. This is the one thing the progress "
        "plane may never do — it would corrupt the --json contract.\n"
        f"--- with --progress\n{with_bar.stdout}\n--- with --no-progress\n{without.stdout}"
    )
    assert without.stderr == ""
    if verb in VERBS_THAT_MUST_PAINT:
        assert with_bar.stderr != "", (
            f"`fux {verb} --progress` painted nothing, so the stdout comparison "
            "above compared two silent runs and proved nothing. Either this verb "
            "stopped inheriting the progress plane, or its fixture fell under "
            "the count threshold."
        )


def test_the_bar_is_off_when_stdout_is_piped_and_nothing_is_forced(repo: Path):
    """Today's exact output, with no flag anywhere — the captured-evidence rule."""
    assert _run(repo, "ingest").stderr == ""
    assert _run(repo, "build").stderr == ""


def test_json_still_parses_with_progress_forced_on(repo: Path):
    """`ask --json` has no bar of its own, but the index it reads was built
    with one — a leak upstream would show up here as unparseable output."""
    _run(repo, "ingest", "--progress")
    result = _run(repo, "ask", "pruning", "--json")
    assert json.loads(result.stdout)["results"]


def test_env_var_suppresses_a_forced_bar_is_false_but_no_progress_wins(repo: Path):
    """`--no-progress` is decisive; `FUX_NO_PROGRESS` is decisive over the TTY."""
    _run(repo, "ingest")
    quiet = _run(repo, "build", "--progress", env={"FUX_NO_PROGRESS": "1"})
    assert quiet.stderr != "", "an explicit --progress overrides the environment"

    off = _run(repo, "build", "--no-progress", env={"FUX_NO_PROGRESS": "0"})
    assert off.stderr == "", "--no-progress is decisive over everything"


def test_the_bar_never_writes_an_ansi_escape(repo: Path):
    """`\\r` + trailing spaces, not `\\x1b[2K` — the litmus names Windows fleets."""
    painted = _run(repo, "ingest", "--progress").stderr
    assert "\x1b" not in painted


def test_the_bar_carries_no_clock(repo: Path):
    """Counts, not clocks: no elapsed, no ETA, no rate anywhere on the line."""
    painted = _run(repo, "ingest", "--progress").stderr
    for forbidden in ("elapsed", "ETA", "eta", "docs/s", "/s ", "remaining"):
        assert forbidden not in painted, f"the bar printed a clock: {forbidden!r}"


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "Windows has no SIGINT to deliver to another process — `send_signal(2)` "
        "raises `ValueError: Unsupported signal: 2`, because a console Ctrl-C is "
        "a control event sent to a process *group*, not a signal to a pid. The "
        "behaviour under test (a phase's __exit__ never leaving a half-painted "
        "line) is platform-independent and is covered on every other arm; only "
        "the way to trigger it is missing here."
    ),
)
def test_an_interrupted_ingest_leaves_no_partial_line(repo: Path):
    """Ctrl-C exits 130 and must not leave a half-painted bar on the terminal."""
    process = subprocess.Popen(
        [sys.executable, "-m", "fux.cli", "ingest", "--progress"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        process.send_signal(subprocess.signal.SIGINT)
        _, err = process.communicate(timeout=60)
    finally:
        if process.poll() is None:  # pragma: no cover - only on a hung child
            process.kill()
    # Whatever it managed to paint, it did not stop mid-line: the phase's
    # __exit__ either committed the line with a newline or erased it with \r.
    assert err == "" or err.endswith(("\n", "\r"))
