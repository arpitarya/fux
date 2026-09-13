from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from fux import __version__
from fux.cli import build_parser, main

ROOT = Path(__file__).resolve().parents[1]


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"fux {__version__}"


def test_no_command_prints_help_and_exits_1(capsys):
    assert main([]) == 1
    assert "usage" in capsys.readouterr().out.lower()


def test_module_invocation_spellings_agree():
    """`python -m fux` and `python -m fux.cli` are ONE implementation.

    The ladder's last rung (SR-AGENT-POLICY) exists so a repo with an
    inactive `.venv` still resolves to *the engine is here* rather than
    `command not found`. `fux.cli` always worked; `fux` is the spelling a
    human actually types, and Arpit ruled it supported (2026-08-27, W-82
    §3.6 fork B).

    **This test is the fence around `__main__.py` staying a delegate.** The
    moment that file grows argument handling of its own, the two spellings
    diverge and this fails — which is the point, because a second entry point
    with its own behaviour is a second thing to support forever.
    """
    runs = [
        subprocess.run(
            [sys.executable, "-m", target, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        for target in ("fux", "fux.cli")
    ]
    assert runs[0].returncode == runs[1].returncode == 0
    assert runs[0].stdout == runs[1].stdout == f"fux {__version__}\n"


def test_parser_has_the_verb_surface():
    """The CLI contract, in four groups and no subcommand tree (SR-CLI).

    lifecycle `setup`/`doctor` set the repo up and check it · write
    `ingest`/`build` — one writes the committed plane, one derives from it ·
    sources **`add`/`remove`/`update`** maintain what is indexed (W-63,
    replacing `url`) · read `ask`/`find`/`answer` differ only in how much they
    commit to · **graph `explain`/`graph`/`path` answer with relationships
    rather than with rankings** (M3) · maintenance `hooks` wires the
    repository up to keep its own index in step (M5).

    Seven groups: W-76 Phase 5 added **agent `mcp`**, Phase 8 added
    **enrichment `enrich`** — which plans and validates the text an agent skill
    generates, and has **no `--model` flag**, because fux never calls one.

    Phase 5's `mcp` — the index served to
    coding agents over stdio JSON-RPC ([SR-MCP](../records/0136_mcp.md)). A
    verb rather than a flag on `ask`, because it is a long-running server and
    not a query.

    SR-TUNE added **`tune`**, which prints the tunables file and exits. A verb
    rather than `setup --print-tune` because it answers a question on its own —
    *what can I change?* — and it is the one verb that touches neither the repo
    nor the network, so it works before `fux setup` has ever run.

    SR-OUTPUT added **`output`**, the exact twin of `tune` one boundary
    further in: `tune` prints what changes WHICH documents come back, `output`
    prints what changes how they are SHOWN. Both print and neither writes.

    Six, not four, and the count was never the mental model — which is why
    adding one costs a line here and a line in SR-CLI rather than a redesign.

    **`url` is gone, not deprecated** (W-63). It was four days old, pre-1.0,
    and its whole surface is `fux add <URL>` / `fux remove <URL>`. The flag
    `ingest --refresh-urls` was the opposite call — older, likelier to be in
    someone's CI — and survives one release as a hidden alias for
    `fux update`, which is asserted below.
    """
    parser = build_parser()
    sub_actions = [a for a in parser._subparsers._group_actions if a.dest == "command"]
    assert set(sub_actions[0].choices) == {
        "setup",
        "doctor",
        "ingest",
        "build",
        "add",
        "remove",
        "update",
        "output",
        "ask",
        "find",
        "answer",
        "enrich",
        "mcp",
        "explain",
        "graph",
        "path",
        "hooks",
        "tune",
        # W-82 ruling 10 (Arpit, 2026-08-27). A verb like `mcp`, for the same
        # reason: a long-running process, not a query. `start`/`stop`/`status`
        # are a positional ARGUMENT, not a subparser — `fux daemon start` must
        # not become the first subcommand tree on this surface.
        "daemon",
        # SR-PROVENANCE (2026-08-27). A verb, not a flag on `answer`: it takes
        # a receipt FILE rather than a query, so every flag on the query parser
        # -- `--top`, `--fast`, `--no-tune` -- would be meaningless on it.
        "verify",
    }


def test_no_verb_grows_a_subcommand_tree():
    """Flat verbs, however many there are — that is the constraint that survives."""
    parser = build_parser()
    (command,) = [a for a in parser._subparsers._group_actions if a.dest == "command"]
    for name, sub in command.choices.items():
        nested = [a for a in sub._subparsers._group_actions] if sub._subparsers else []
        assert not nested, f"`fux {name}` grew a subcommand tree"


# -- SR-PII decision 17: no .fux/pii.toml, no command -----------------------


def _verbs():
    import argparse

    parser = build_parser()
    sub = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    return sorted(sub.choices)


def test_every_verb_is_gated_except_the_named_exemptions(tmp_path, monkeypatch):
    """The table in SR-PII decision 17, enforced over the parser as it is.

    A verb added later is gated by default; exempting one means changing the
    record's table and this set together.
    """
    from fux.cli import PII_EXEMPT, _require_pii_rules
    from fux.errors import FuxError

    assert PII_EXEMPT == {"setup", "tune", "output", "doctor"}
    assert PII_EXEMPT <= set(_verbs())
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    for verb in _verbs():
        if verb in PII_EXEMPT:
            _require_pii_rules(verb)
        else:
            with pytest.raises(FuxError, match="pii.toml is missing"):
                _require_pii_rules(verb)


def test_the_gate_checks_the_same_file_pii_loads(tmp_path):
    """Every hand-spelled copy of the path, against the one that loads it.

    ⚠ **Three copies now, not two.** `cli.py` and `api.py` each spell
    `.fux/pii.toml` inline so the gate costs a stat instead of importing
    `fux.ingest` (~50 ms of decoders on a warm `fux.open`), and `node/fux.mjs`
    spells it a third time for the same reason in a runtime that cannot import
    Python at all. The REFUSAL WORDING is not duplicated — it stays in `pii`,
    which is the part that would actually drift.
    """
    from fux.api import _PII_RULES as api_rules
    from fux.cli import _PII_RULES
    from fux.ingest import pii

    assert tmp_path.joinpath(*_PII_RULES) == pii.rules_path(tmp_path)
    assert api_rules == _PII_RULES


def test_the_node_reader_gates_on_the_same_file(tmp_path):
    """W-107 O1, ruled by Arpit 2026-09-12: Node enforces the gate identically.

    A reader that answers where the CLI refuses is a divergence in the
    PRODUCT, not merely in the code — the gate exists so that a redacted index
    is the only index anything reads. `fux.mjs` is read as text rather than
    run, so this costs nothing and still fails if the path is edited there.
    """
    from fux.ingest import pii

    source = (ROOT / "node" / "fux.mjs").read_text(encoding="utf-8")
    assert '".fux", "pii.toml"' in source, (
        "node/fux.mjs no longer spells the gate's path — a Node-only clone "
        "would answer where Python refuses (W-107 O1)"
    )
    assert pii.rules_path(tmp_path) == tmp_path / ".fux" / "pii.toml"

    # 🔴 **And in the artefact a consumer actually runs** (2026-09-12, L10).
    # `.fux/node/fux.mjs` and the npm entry point are the BUNDLE, generated from
    # the source above — so the literal travels by construction. Asserted on the
    # built bytes anyway, because "aimed at the source while the consumer runs
    # something else" is exactly the class of defect SR-NODE-SEARCH decisions
    # 9-12 were all instances of.
    from fux.store import nodebundle

    assert '".fux", "pii.toml"' in nodebundle.bundle(ROOT / "node")


def test_a_gated_verb_stops_before_dispatch_with_exit_1(tmp_path, monkeypatch, capsys):
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    assert main(["find", "anything"]) == 1
    err = capsys.readouterr().err
    assert err.startswith("error: .fux/pii.toml is missing")
    assert "fux setup" in err


def test_the_file_with_no_rules_opens_the_gate(tmp_path, monkeypatch):
    from fux.cli import _require_pii_rules

    (tmp_path / ".git").mkdir()
    (tmp_path / ".fux").mkdir()
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    _require_pii_rules("find")


def test_the_gate_does_not_fire_outside_any_root(tmp_path, monkeypatch):
    from fux.cli import _require_pii_rules
    from fux.config import find_root

    monkeypatch.chdir(tmp_path)
    if find_root() is not None:
        pytest.skip("the temp directory sits inside a repository on this machine")
    _require_pii_rules("find")


def test_the_gate_does_not_import_fux_ingest_when_the_file_exists(tmp_path):
    """~70 ms of decoder imports on every `ask` and `find` is the cost avoided."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".fux").mkdir()
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    code = (
        "import sys; from fux.cli import _require_pii_rules; "
        "_require_pii_rules('find'); print('fux.ingest' in sys.modules)"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", check=True
    )
    assert out.stdout.strip() == "False"


# -- W-140 rows 9 and 10: a rendering default that changed what a verb did ---


def test_hooks_installs_even_when_the_repo_renders_json(tmp_path, monkeypatch, capsys):
    """🔴 `[cli.json] enabled = true` turned `fux hooks` into a status report.

    It selected report-instead-of-install from `args.json`, which the output
    config fills — so in a repo that renders JSON, the command whose whole job
    is to wire the hooks installed nothing and printed a true report of a repo
    nobody had wired. A rendering default may never change what a command does.
    """
    import subprocess

    from fux.maintain import cmd_hooks

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Args:
        command = "hooks"
        json = True           # what the output config resolved
        json_explicit = False  # what the user typed
        status = False

    assert cmd_hooks(Args()) == 0
    assert (tmp_path / ".git" / "hooks" / "post-commit").is_file(), (
        "the hooks were not written — the rendering default selected the mode"
    )
    payload = json.loads(capsys.readouterr().out)
    assert "post-commit" in payload["installed"], "JSON rendering, of the work actually done"


def test_hooks_status_is_still_selected_by_the_typed_flag(tmp_path, monkeypatch, capsys):
    """`fux hooks --json` keeps meaning *report*, for whoever scripted it."""
    import subprocess

    from fux.maintain import cmd_hooks

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    class Args:
        command = "hooks"
        json = True
        json_explicit = True
        status = False

    assert cmd_hooks(Args()) == 0
    assert not (tmp_path / ".git" / "hooks" / "post-commit").exists()
    assert "hooks" in json.loads(capsys.readouterr().out)


def test_a_shard_with_conflict_markers_says_so(tmp_path):
    """It reported *not a fux index shard, or the file is truncated* — a
    sentence that sends a reader looking for corruption while the answer is an
    unresolved merge two commands away."""
    from fux import store
    from fux.errors import FuxError

    index = tmp_path / ".fux" / "index"
    index.mkdir(parents=True)
    (index / "00.jsonl").write_text(
        '{"_format":"fux.index.v2"}\n<<<<<<< ours\n{"id":"a"}\n=======\n{"id":"b"}\n>>>>>>> theirs\n',
        encoding="utf-8",
    )
    with pytest.raises(FuxError, match="unresolved merge conflict markers"):
        store.read_index(tmp_path)
