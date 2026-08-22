"""`fux setup --agents` — the installer, and the safeguards a default-on install needs.

ADR-AGENT-POLICY decision 5 makes this install **by default**, into
`.claude/`, `.github/` and `.kiro/` — directories Anthropic, GitHub and AWS
own. Two things are all that stand between that and a tool quietly editing a
shared repository, and both are veto conditions rather than niceties:

- **the announcement** (veto 1) — every agent file written is named in
  `setup`'s output, together with how to turn it off;
- **the opt-out** (veto 1a) — `--no-agents` and `install = []` write none of
  them.

Test names carry `announces` and `optout` because the record's own "How to
check it" runs this file with `-k "announces or optout"`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fux import setup as setup_mod
from fux.cli import main
from fux.errors import FuxError

ALL_AGENT_PATHS = [rel for files in setup_mod.AGENT_FILES.values() for rel, _ in files]


def _fresh(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    return tmp_path


def _agent_files_on_disk(root: Path) -> list[str]:
    return sorted(rel for rel in ALL_AGENT_PATHS if (root / rel).exists())


# -- the default: all three install ----------------------------------------


def test_setup_installs_all_three_by_default(tmp_path):
    setup_mod.run(_fresh(tmp_path))
    assert _agent_files_on_disk(tmp_path) == sorted(ALL_AGENT_PATHS)


def test_copilot_gets_both_files_not_one(tmp_path):
    """Decision 4: the agent fires when routed to, the instructions fire on
    every request. The gap between them — output pasted into a chat the agent
    never saw — is the dangerous case, so they are not alternatives."""
    setup_mod.run(_fresh(tmp_path))
    assert (tmp_path / ".github" / "agents" / "fux.agent.md").exists()
    assert (tmp_path / ".github" / "instructions" / "fux-archived-results.instructions.md").exists()


def test_the_written_files_are_the_shipped_renderings_byte_for_byte(tmp_path):
    setup_mod.run(_fresh(tmp_path))
    for vendor, files in setup_mod.AGENT_FILES.items():
        for rel, template in files:
            assert (tmp_path / rel).read_bytes() == setup_mod.agent_template_bytes(template), rel


def test_fux_toml_spells_the_default_out_in_full(tmp_path):
    """Decision 5: a default a user can read and edit in a file they own is a
    different thing from a default buried in the engine."""
    setup_mod.run(_fresh(tmp_path))
    text = (tmp_path / "fux.toml").read_text(encoding="utf-8")
    assert "[agents]" in text
    assert 'install = ["claude", "copilot", "kiro"]' in text


# -- optout (veto condition 1a) --------------------------------------------


def test_optout_flag_writes_no_agent_file(tmp_path):
    setup_mod.run(_fresh(tmp_path), agents=False)
    assert _agent_files_on_disk(tmp_path) == []


def test_optout_flag_leaves_no_vendor_directory_behind(tmp_path):
    """Not just the files: a bare `.github/` fux created and then did not fill
    is still fux having written into GitHub's namespace."""
    setup_mod.run(_fresh(tmp_path), agents=False)
    for vendor_dir in (".claude", ".github", ".kiro"):
        assert not (tmp_path / vendor_dir).exists(), f"{vendor_dir} was created under --no-agents"


def test_optout_declaration_writes_no_agent_file(tmp_path):
    """`install = []` is the durable form of the flag."""
    root = _fresh(tmp_path)
    (root / "fux.toml").write_text("[sources]\n[agents]\ninstall = []\n", encoding="utf-8")
    setup_mod.run(root)
    assert _agent_files_on_disk(root) == []


def test_optout_declaration_survives_a_second_setup(tmp_path):
    """The failure this guards: a re-run that ignores the declaration and
    reinstalls what the consumer removed."""
    root = _fresh(tmp_path)
    (root / "fux.toml").write_text("[sources]\n[agents]\ninstall = []\n", encoding="utf-8")
    setup_mod.run(root)
    setup_mod.run(root)
    assert _agent_files_on_disk(root) == []


def test_a_partial_declaration_installs_exactly_what_it_names(tmp_path):
    root = _fresh(tmp_path)
    (root / "fux.toml").write_text('[sources]\n[agents]\ninstall = ["kiro"]\n', encoding="utf-8")
    setup_mod.run(root)
    assert _agent_files_on_disk(root) == [".kiro/steering/fux-archived-results.md"]


def test_optout_through_the_real_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(_fresh(tmp_path))
    assert main(["setup", "--no-agents"]) == 0
    capsys.readouterr()
    assert _agent_files_on_disk(tmp_path) == []


# -- announces (veto condition 1) ------------------------------------------


def test_setup_announces_every_agent_file_it_wrote(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(_fresh(tmp_path))
    main(["setup"])
    out = capsys.readouterr().out
    for rel in ALL_AGENT_PATHS:
        assert rel in out, f"{rel} was written and never named in setup's output (veto 1)"


def test_setup_announces_how_to_turn_them_off(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(_fresh(tmp_path))
    main(["setup"])
    out = capsys.readouterr().out
    assert "install = []" in out and "--no-agents" in out, (
        "naming the files without naming the escape is half a safeguard (veto 1)"
    )


def test_setup_announces_that_they_are_outside_fux(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(_fresh(tmp_path))
    main(["setup"])
    assert "OUTSIDE .fux/" in capsys.readouterr().out


def test_the_report_lists_every_outside_path_it_wrote(tmp_path):
    """The announcement renders `report.outside`; if that list can drift from
    what was written, the announcement can too."""
    report = setup_mod.run(_fresh(tmp_path))
    assert sorted(report.outside) == sorted(ALL_AGENT_PATHS)
    assert set(report.outside) <= set(report.written)


def test_nothing_outside_fux_is_announced_when_nothing_was_written(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(_fresh(tmp_path))
    main(["setup", "--no-agents"])
    assert "OUTSIDE .fux/" not in capsys.readouterr().out


def test_a_second_run_announces_nothing_it_did_not_write(tmp_path, monkeypatch, capsys):
    """Write-if-missing: the second run keeps the files, so it must not claim
    to have written them."""
    root = _fresh(tmp_path)
    monkeypatch.chdir(root)
    main(["setup"])
    capsys.readouterr()
    main(["setup"])
    out = capsys.readouterr().out
    assert "OUTSIDE .fux/" not in out
    report = setup_mod.run(root)
    assert report.outside == []


# -- write-if-missing (decision 7) -----------------------------------------


def test_a_consumer_edit_survives_a_later_setup(tmp_path):
    root = _fresh(tmp_path)
    setup_mod.run(root)
    target = root / ".kiro" / "steering" / "fux-archived-results.md"
    target.write_text("mine now\n", encoding="utf-8")
    setup_mod.run(root)
    assert target.read_text(encoding="utf-8") == "mine now\n"


# -- declared, never derived (veto condition 4) ----------------------------


def test_the_installer_never_branches_on_a_vendor_directory_existing(tmp_path):
    """Veto 4. A heuristic is exact for the repo it was written against and a
    silent convention for everyone else — the derivation ADR-DIR-LIST decision
    4 already refused for `archived`."""
    import inspect

    source = inspect.getsource(setup_mod)
    routing = source[source.index("def _agents_to_install") : source.index("def run(")]
    for sniff in (".exists()", ".is_dir()", "glob("):
        assert sniff not in routing, (
            f"the agent routing calls {sniff} — which agents install is DECLARED, never sniffed"
        )


def test_a_pre_existing_vendor_directory_changes_nothing(tmp_path):
    """The observable half of veto 4: `.github/` already being there must not
    make fux install more, and its absence must not make it install less."""
    root = _fresh(tmp_path)
    (root / ".github").mkdir()
    setup_mod.run(root)
    assert _agent_files_on_disk(root) == sorted(ALL_AGENT_PATHS)


# -- the declaration is validated ------------------------------------------


def test_an_unknown_agent_name_is_a_loud_error(tmp_path):
    """A typo must not silently install nothing."""
    from fux.config import load

    root = _fresh(tmp_path)
    (root / "fux.toml").write_text('[sources]\n[agents]\ninstall = ["copilto"]\n', encoding="utf-8")
    with pytest.raises(FuxError, match="unknown agent"):
        load(root)


def test_install_must_be_a_list(tmp_path):
    from fux.config import load

    root = _fresh(tmp_path)
    (root / "fux.toml").write_text('[sources]\n[agents]\ninstall = "claude"\n', encoding="utf-8")
    with pytest.raises(FuxError, match="must be a list"):
        load(root)


def test_absent_and_empty_are_different(tmp_path):
    """Absent is a repo that never expressed a preference; `[]` is a consumer
    who said no. Collapsing them would make the opt-out unwritable."""
    from fux.config import KNOWN_AGENTS, load

    root = _fresh(tmp_path)
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    assert load(root).agents == KNOWN_AGENTS
    (root / "fux.toml").write_text("[sources]\n[agents]\ninstall = []\n", encoding="utf-8")
    assert load(root).agents == ()


def test_the_install_order_does_not_depend_on_the_file(tmp_path):
    """What gets written must not depend on the order someone happened to type."""
    from fux.config import load

    root = _fresh(tmp_path)
    (root / "fux.toml").write_text(
        '[sources]\n[agents]\ninstall = ["kiro", "claude", "kiro"]\n', encoding="utf-8"
    )
    assert load(root).agents == ("claude", "kiro")
