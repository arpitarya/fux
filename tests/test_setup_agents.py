"""`fux setup --agents` — the installer, and the safeguards a default-on install needs.

ADR-AGENT-POLICY decision 5 makes this install **by default**, into
`.claude/`, `.codex/`, `.github/` and `.kiro/` — directories Anthropic,
OpenAI, GitHub and AWS own. Two things are all that stand between that and a tool quietly editing a
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

# W-82 ruling 16: the repo-root `AGENTS.md` is vendor-NEUTRAL, so it lives
# outside `AGENT_FILES` (which is keyed by vendor) and has to be added here by
# hand. It is still an agent file for every purpose these tests check —
# `--no-agents` must not write it, and `report.outside` must list it.
ALL_AGENT_PATHS = [rel for files in setup_mod.AGENT_FILES.values() for rel, _ in files] + [
    setup_mod.AGENTS_FILE
]


def _fresh(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    return tmp_path


def _agent_files_on_disk(root: Path) -> list[str]:
    return sorted(rel for rel in ALL_AGENT_PATHS if (root / rel).exists())


# -- the default: every known vendor installs -------------------------------


def test_setup_installs_every_known_vendor_by_default(tmp_path):
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
    assert 'install = ["claude", "codex", "copilot", "kiro"]' in text


# -- optout (veto condition 1a) --------------------------------------------


def test_optout_flag_writes_no_agent_file(tmp_path):
    setup_mod.run(_fresh(tmp_path), agents=False)
    assert _agent_files_on_disk(tmp_path) == []


def test_optout_flag_leaves_no_vendor_directory_behind(tmp_path):
    """Not just the files: a bare `.github/` fux created and then did not fill
    is still fux having written into GitHub's namespace."""
    setup_mod.run(_fresh(tmp_path), agents=False)
    for vendor_dir in (".claude", ".codex", ".github", ".kiro"):
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
    assert _agent_files_on_disk(root) == [
        # W-86 P7: the committed-write skills ship to the SKILL surface and to
        # neither ambient one. A Kiro skill is progressive-disclosure; only
        # Kiro *steering* enters every interaction.
        ".kiro/skills/fux-decoder/SKILL.md",
        ".kiro/skills/fux-enrich/SKILL.md",
        ".kiro/skills/fux-usage/SKILL.md",
        ".kiro/steering/fux-archived-results.md",
    ]


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
    import io
    import tokenize

    def _code_only(text: str) -> str:
        """Strip comments and string literals before sniffing.

        ⚠ **The same defect the daemon build hit and caught** (W-82 ruling 10):
        a bare substring check punishes a module for DOCUMENTING the constraint
        it obeys — `_write_root_agents` explains in a comment why it does not
        call `.exists()`, and an unfiltered sniff reads that as a violation.
        The tempting fix is to delete the explanation; strip the tokens instead.
        """
        out = []
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            out.append(tok.string)
        return " ".join(out)

    source = inspect.getsource(setup_mod)
    routing = _code_only(source[source.index("def _agents_to_install") : source.index("def run(")])
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


# -- codex: decision 3 exercised -------------------------------------------


def test_every_known_agent_has_a_rendering():
    """The two lists are edited in different files. A vendor named in
    `KNOWN_AGENTS` with no row in `AGENT_FILES` is accepted by `fux.toml`
    validation and then writes nothing — the silent failure `KNOWN_AGENTS`
    exists to prevent, arriving through the door it guards."""
    from fux.config import KNOWN_AGENTS

    assert sorted(setup_mod.AGENT_FILES) == sorted(KNOWN_AGENTS)


def test_codex_reuses_the_claude_and_kiro_skill_bytes(tmp_path):
    """Decision 10, a third and fourth time: Codex CLI implements the same open
    Agent Skills standard, so agreement is BY CONSTRUCTION — one template, three
    destinations — not by a conformance test asserting three files still match."""
    setup_mod.run(_fresh(tmp_path))
    usage = (tmp_path / ".claude/skills/fux-usage/SKILL.md").read_bytes()
    decoder = (tmp_path / ".claude/skills/fux-decoder/SKILL.md").read_bytes()
    assert (tmp_path / ".codex/skills/fux-usage/SKILL.md").read_bytes() == usage
    assert (tmp_path / ".kiro/skills/fux-usage/SKILL.md").read_bytes() == usage
    assert (tmp_path / ".codex/skills/fux-decoder/SKILL.md").read_bytes() == decoder
    enrich = (tmp_path / ".claude/skills/fux-enrich/SKILL.md").read_bytes()
    for rel in (".codex/skills", ".kiro/skills", ".github/skills"):
        assert (tmp_path / rel / "fux-enrich/SKILL.md").read_bytes() == enrich, rel


def test_codex_gets_no_archived_results_skill(tmp_path):
    """Decision 9's test: *does an agent that has never heard of Fux still need
    this sentence to avoid being wrong?* Yes — so it must be ambient, and a
    skill has to be LOADED to apply. Codex's only ambient surface is the
    repo-root `AGENTS.md`, which carries the verbatim block."""
    setup_mod.run(_fresh(tmp_path))
    assert not (tmp_path / ".codex/skills/fux-archived-results").exists()
    assert "fux:policy:begin" in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")


def test_enrich_ships_to_every_skill_surface_and_no_ambient_one():
    """ADR-ENRICH decision 10, as amended 2026-09-06. The rule is **never
    ambient** — it was never *claude only*, and shipping to Claude alone was an
    omission the record had already flagged against itself.

    What this asserts is the rule, not the roster: `ENRICH-SKILL.md` reaches
    every `skills/` destination and **no** ambient one. Add a fifth vendor with
    a skill surface and this test tells you the row is missing; add one with an
    ambient rendering and it tells you the row is illegal."""
    dests = [
        rel for files in setup_mod.AGENT_FILES.values() for rel, tpl in files
        if tpl == "ENRICH-SKILL.md"
    ]
    assert sorted(dests) == [
        ".claude/skills/fux-enrich/SKILL.md",
        ".codex/skills/fux-enrich/SKILL.md",
        ".github/skills/fux-enrich/SKILL.md",
        ".kiro/skills/fux-enrich/SKILL.md",
    ]
    # the rule, stated mechanically: no ambient surface, on any vendor
    for rel in dests:
        assert "/skills/" in rel, rel
        assert "instructions" not in rel and "steering" not in rel, rel


def test_no_committed_write_skill_reaches_an_ambient_surface():
    """The rule both committed-write skills actually live under, asserted once
    over both of them rather than per-roster.

    `fux-decoder` and `fux-enrich` are named in ONE sentence as ONE risk class:
    they write into a committed directory and change ranking, so **neither may
    ever be ambient on any vendor**. A skill folder is progressive-disclosure
    everywhere; `instructions/` (`applyTo: "**"`) and `steering/`
    (`inclusion: always`) are not."""
    for template in ("ENRICH-SKILL.md", "DECODER-SKILL.md"):
        dests = [
            rel for files in setup_mod.AGENT_FILES.values() for rel, tpl in files
            if tpl == template
        ]
        assert dests, template
        for rel in dests:
            assert "/skills/" in rel, f"{template} -> {rel}"


#: Every skill surface Fux installs to — the four progressive-disclosure
#: planes, one per vendor. **Ambient planes are deliberately absent**: the rule
#: that keeps a committed-write skill off `instructions/` and `steering/` is
#: what these three templates are held to (ADR-AGENT-POLICY decision 14).
SKILL_SURFACES = {".claude/skills", ".github/skills", ".kiro/skills", ".codex/skills"}


def _surfaces(template):
    return {
        rel.rsplit("/", 2)[0]
        for files in setup_mod.AGENT_FILES.values()
        for rel, tpl in files
        if tpl == template
    }


def test_the_three_rosters_no_longer_differ_at_all():
    """**The exception is GONE, and that is the assertion.** This test was
    written while `fux-enrich` reached `.github/skills/` and `fux-decoder` did
    not — a recorded asymmetry, because Arpit's 2026-09-06 ruling had named only
    one of them. He ruled the other way on **2026-09-11**: `fux-decoder` and
    `fux-usage` go to Copilot too.

    **It exists so a gap cannot go quiet the way the last one did** —
    `fux-enrich` shipped to one surface while its twin shipped to three, and
    nothing failed. Now any divergence at all fails, in either direction."""
    assert _surfaces("ENRICH-SKILL.md") == _surfaces("DECODER-SKILL.md")
    assert _surfaces("ENRICH-SKILL.md") == _surfaces("USAGE-SKILL.md")


def test_this_repos_own_agent_files_still_match_the_templates_that_ship():
    """🔴 **The drift this catches has already happened, in `fa47760`.**

    `_write_if_missing` never rewrites a file that is already there, so this
    repo's own renderings are writable by hand and a hand edit reaches **no
    user**. `fa47760` added the chunking contract, corrected the decoder count
    and renamed the worked example — all three to
    `.claude/skills/fux-decoder/SKILL.md` and **none of them to the template**.
    Every `fux setup` between then and 2026-09-11 shipped a decoder guide
    missing the section that tells a decoder author how their headings become
    passages. Nothing failed, because nothing compared them.

    ⚠ **This is the exact claim `setup.py` makes about itself** — *"agreement by
    construction -- one template, N destinations"* — asserted rather than
    trusted. Two strikes (CLAUDE.md): the first was `fux-enrich` reaching one
    surface while its twin reached three, which
    `test_the_three_rosters_no_longer_differ_at_all` now gates; this is the
    second, in a different shape, so it is gated in the change that records it.

    **If this fails: edit the TEMPLATE, delete the rendering, re-run
    `fux setup`.** Never the other way round."""
    root = Path(__file__).resolve().parents[1]
    pairs = [(rel, tpl) for files in setup_mod.AGENT_FILES.values() for rel, tpl in files]
    # the vendor-neutral root file lives outside `AGENT_FILES` (W-82 ruling 16)
    # and drifts by exactly the same mechanism, so it is added by hand here too.
    pairs.append((setup_mod.AGENTS_FILE, setup_mod.AGENTS_TEMPLATE))
    stale = []
    for rel, template in pairs:
        committed = root / rel
        if not committed.exists():  # not installed in this repo
            continue
        if committed.read_bytes() != setup_mod.agent_template_bytes(template):
            stale.append(f"{rel}  !=  templates/agents/{template}")
    assert not stale, (
        "this repo's committed agent files have drifted from the templates that "
        "ship to users:\n  " + "\n  ".join(sorted(stale))
    )


def test_every_committed_write_skill_reaches_every_skill_surface():
    """Arpit, 2026-09-11: *yes* — all four vendors, all three skills. Asserted
    against the surface set by name rather than against each other, so deleting
    a vendor from `AGENT_FILES` fails here instead of silently making three
    equally-empty rosters agree.

    ⚠ `fux-archived-results` is **ambient policy, not a committed-write skill**
    — Codex gets it through the repo-root `AGENTS.md` and Copilot through
    `instructions/` — so it is deliberately out of this assertion."""
    for template in ("DECODER-SKILL.md", "USAGE-SKILL.md", "ENRICH-SKILL.md"):
        assert _surfaces(template) == SKILL_SURFACES, template


def test_codex_alone_still_gets_the_root_agents_file(tmp_path):
    """`AGENTS_MD_VENDORS`. The root file is written for a FULL install because
    a partial declaration names what it wants — true for the three vendors that
    have their own ambient plane, and false for Codex, whose ambient plane IS
    this file. Without the clause, `install = ["codex"]` writes two skills and
    no archived-results policy, and nothing says so."""
    root = _fresh(tmp_path)
    (root / "fux.toml").write_text('[sources]\n[agents]\ninstall = ["codex"]\n', encoding="utf-8")
    setup_mod.run(root)
    assert _agent_files_on_disk(root) == [
        # sorted(): "." < "A", so the vendor paths come first
        ".codex/skills/fux-decoder/SKILL.md",
        ".codex/skills/fux-enrich/SKILL.md",
        ".codex/skills/fux-usage/SKILL.md",
        "AGENTS.md",
    ]


def test_a_partial_declaration_without_codex_writes_no_root_agents_file(tmp_path):
    """The other half of the clause: it must widen the gate for Codex only, not
    turn a partial declaration into a full one."""
    root = _fresh(tmp_path)
    (root / "fux.toml").write_text('[sources]\n[agents]\ninstall = ["claude"]\n', encoding="utf-8")
    setup_mod.run(root)
    assert not (root / setup_mod.AGENTS_FILE).exists()


def test_this_repos_own_decoders_still_match_the_package_modules():
    """🔴 **The same drift, a third time, in `.fux/decoders/`.**

    `fux setup` writes the built-in decoders into `.fux/decoders/` **write-if-
    missing**, and [ADR-DOTFUX](../docs/adr/0102_fux-directory.md) decision 8
    makes those copies *what actually run* — the package modules are not
    consulted while a copy exists. So a fix to `src/fux/decode/` reaches **this
    repository not at all**, silently, exactly as a template fix did not reach
    `.claude/skills/`.

    **That is correct for a CONSUMER**, whose overrides must survive an upgrade.
    It is wrong here: fux's own repo is where these modules come from, so its
    copies are a rendering and must equal their source.

    ⚠ **The gate is scoped to THIS repository and asserts nothing about
    anyone else's** — a consumer's divergent decoder is the feature.

    **If this fails: fix `src/fux/decode/<name>.py`, then copy it over.**
    Never the other way round."""
    root = Path(__file__).resolve().parents[1]
    package, committed = root / "src" / "fux" / "decode", root / ".fux" / "decoders"
    if not committed.is_dir():  # pragma: no cover - a checkout without `fux setup`
        pytest.skip("no .fux/decoders/ in this checkout")
    drift = []
    for copy in sorted(committed.glob("*.py")):
        source = package / copy.name
        if not source.is_file():
            drift.append(f"{copy.name}: no module at src/fux/decode/{copy.name}")
        elif copy.read_bytes() != source.read_bytes():
            drift.append(f".fux/decoders/{copy.name}  !=  src/fux/decode/{copy.name}")
    assert not drift, (
        "this repo's committed decoders have drifted from the package modules they "
        "were copied from, so a fix in src/fux/decode/ is not what runs here:\n  "
        + "\n  ".join(drift)
    )
