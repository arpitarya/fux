"""`fux setup --agents` — the installer, and the safeguards a default-on install needs.

SR-AGENT-POLICY decision 5 makes this install **by default**, into
`.claude/`, `.agents/` (shared by Codex and Copilot, decision 16), `.github/`
and `.kiro/` — directories Anthropic, OpenAI, GitHub and AWS own. Two things are all that stand between that and a tool quietly editing a
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
#
# ⚠ **A set, then sorted**: Codex and Copilot share `.agents/skills/`
# (decision 16), so the same path appears under two vendors and is ONE file.
ALL_AGENT_PATHS = sorted(
    {rel for files in setup_mod.AGENT_FILES.values() for rel, _ in files} | {setup_mod.AGENTS_FILE}
)


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
    for vendor_dir in (".agents", ".claude", ".codex", ".github", ".kiro"):
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
    guides = [name for name, _tpl in setup_mod.GUIDE_SKILLS]
    assert _agent_files_on_disk(root) == sorted(
        [
            # W-86 P7: the committed-write skills ship to the SKILL surface and to
            # neither ambient one. A Kiro skill is progressive-disclosure; only
            # Kiro *steering* enters every interaction.
            ".kiro/skills/fux-decoder/SKILL.md",
            ".kiro/skills/fux-enrich/SKILL.md",
            ".kiro/skills/fux-usage/SKILL.md",
            ".kiro/steering/fux-archived-results.md",
        ]
        # SR-AGENT-POLICY decision 15: the operating guides, and Kiro's
        # path-scoped and auto-inclusion steering pointers.
        + [f".kiro/skills/{name}/SKILL.md" for name in guides]
        + [f".kiro/steering/fux-{t}-files.md" for t in setup_mod.PATH_SCOPED_TOPICS]
        + [f".kiro/steering/fux-{t}-guide.md" for t in setup_mod.AUTO_GUIDE_TOPICS]
        # SR-AGENT-SURFACES decision 3a: Kiro ships repo-level hooks (12
        # triggers, `PreToolUse` among them) and repo-level custom agents.
        # Derived from the roster rather than retyped, so the two cannot drift.
        + [rel for rel, _tpl in setup_mod.KIRO_SURFACES]
    )


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
    silent convention for everyone else — the derivation SR-DIR-LIST decision
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
    assert (tmp_path / ".agents/skills/fux-usage/SKILL.md").read_bytes() == usage
    assert (tmp_path / ".kiro/skills/fux-usage/SKILL.md").read_bytes() == usage
    assert (tmp_path / ".agents/skills/fux-decoder/SKILL.md").read_bytes() == decoder
    enrich = (tmp_path / ".claude/skills/fux-enrich/SKILL.md").read_bytes()
    for rel in (".agents/skills", ".kiro/skills"):
        assert (tmp_path / rel / "fux-enrich/SKILL.md").read_bytes() == enrich, rel


def test_codex_gets_no_archived_results_skill(tmp_path):
    """Decision 9's test: *does an agent that has never heard of Fux still need
    this sentence to avoid being wrong?* Yes — so it must be ambient, and a
    skill has to be LOADED to apply. Codex's only ambient surface is the
    repo-root `AGENTS.md`, which carries the verbatim block."""
    setup_mod.run(_fresh(tmp_path))
    assert not (tmp_path / ".agents/skills/fux-archived-results").exists()
    assert "fux:policy:begin" in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")


def test_enrich_ships_to_every_skill_surface_and_no_ambient_one():
    """SR-ENRICH decision 10, as amended 2026-09-06. The rule is **never
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
        # twice: one row for Codex, one for Copilot, one shared file (decision 16)
        ".agents/skills/fux-enrich/SKILL.md",
        ".agents/skills/fux-enrich/SKILL.md",
        ".claude/skills/fux-enrich/SKILL.md",
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


#: Every skill surface Fux installs to, **as (vendor, directory) pairs** — four
#: vendors, three directories, because Codex and Copilot share `.agents/skills`
#: (SR-AGENT-POLICY decision 16). **Keyed by vendor on purpose**: a set of bare
#: directories would still pass with Codex's row deleted, since Copilot writes
#: the same paths. **Ambient planes are deliberately absent**: the rule that
#: keeps a committed-write skill off `instructions/` and `steering/` is what
#: these templates are held to (decision 14).
SKILL_SURFACES = {
    ("claude", ".claude/skills"),
    ("codex", ".agents/skills"),
    ("copilot", ".agents/skills"),
    ("kiro", ".kiro/skills"),
}


def _surfaces(template):
    return {
        (vendor, rel.rsplit("/", 2)[0])
        for vendor, files in setup_mod.AGENT_FILES.items()
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
    `fux setup`.** Never the other way round.

    🔴 **`setup_mod.CO_OWNED_SURFACES` is exempt, and the exemption is a
    finding, not a waiver** (SR-AGENT-SURFACES decision 6). `.claude/settings.json`
    is a file the CONSUMER owns and fux only seeds: this repo's own copy carries
    Arpit's golden-answer deny rules and five hooks that have nothing to do with
    fux. Byte equality is the wrong assertion for a surface somebody else also
    writes to — it would fail for every real consumer, and the only way to make
    it pass would be to overwrite their settings, which is precisely what
    decision 6 forbids. What IS asserted for these: the template stays valid
    JSON, and it is never written over an existing file
    (`test_co_owned_surface_is_never_written_over`)."""
    root = Path(__file__).resolve().parents[1]
    pairs = [
        (rel, tpl)
        for files in setup_mod.AGENT_FILES.values()
        for rel, tpl in files
        if rel not in setup_mod.CO_OWNED_SURFACES
    ]
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


def test_every_operating_guide_reaches_every_skill_surface_and_no_ambient_one():
    """SR-AGENT-POLICY decision 15 (Arpit, 2026-09-11). The operating guides are
    decision 14a's roster rule applied once per guide: one template, all four
    skill surfaces, and never an `instructions/` or `steering/` destination --
    four of them (`fux-sources`, `fux-config`, `fux-fetcher`, `fux-pii`) write
    committed files, and decision 9a is a predicate on the surface, not on a
    list of names.

    **Twelve since 2026-09-14** — `fux-inspect` (SR-INSPECT) and `fux-correct`
    (SR-ENRICH decision 19) both joined that day, at the two ends of the
    spectrum this rule covers. `inspect` writes nothing at all; `correct`
    writes committed files and records a claim under somebody's name, and its
    own first section is *propose the command, do not run it* — because the
    moment an agent notices a bad result is exactly when it would be tempted.
    """
    assert len(setup_mod.GUIDE_SKILLS) == 12
    for name, template in setup_mod.GUIDE_SKILLS:
        assert _surfaces(template) == SKILL_SURFACES, template
        for files in setup_mod.AGENT_FILES.values():
            for rel, tpl in files:
                if tpl == template:
                    assert rel.endswith(f"/skills/{name}/SKILL.md"), rel


def test_codex_alone_still_gets_the_root_agents_file(tmp_path):
    """`AGENTS_MD_VENDORS`. The root file is written for a FULL install because
    a partial declaration names what it wants — true for the three vendors that
    have their own ambient plane, and false for Codex, whose ambient plane IS
    this file. Without the clause, `install = ["codex"]` writes two skills and
    no archived-results policy, and nothing says so."""
    root = _fresh(tmp_path)
    (root / "fux.toml").write_text('[sources]\n[agents]\ninstall = ["codex"]\n', encoding="utf-8")
    setup_mod.run(root)
    assert _agent_files_on_disk(root) == sorted(
        [
            # sorted(): "." < "A", so the vendor paths come first
            ".agents/skills/fux-decoder/SKILL.md",
            ".agents/skills/fux-enrich/SKILL.md",
            ".agents/skills/fux-usage/SKILL.md",
            # decision 3a: Codex has documented repo-level hooks and subagents
            ".codex/agents/fux-researcher.md",
            ".codex/hooks.json",
            ".codex/hooks/fux-index-hint.sh",
            "AGENTS.md",
        ]
        # decision 15: the guides reach Codex as skills; Codex has no
        # path-scoped surface, so no pointer is written for it
        + [f".agents/skills/{name}/SKILL.md" for name, _tpl in setup_mod.GUIDE_SKILLS]
    )


# -- codex and copilot share `.agents/skills/` (decision 16) ----------------


def test_codex_and_copilot_write_the_one_directory_codex_reads():
    """W-141, ruled by Arpit 2026-09-12. Codex reads repository skills from
    `.agents/skills` **only**; Copilot reads `.github/skills`, `.claude/skills`
    **and** `.agents/skills`. So both vendors write `.agents/skills`, and neither
    retired directory is written by anyone.

    ⚠ **Veto 3 fired here** — *a shipped rendering no longer loads in its
    vendor's tool*. `.codex/skills` is not a path Codex's docs list."""
    for vendor in ("codex", "copilot"):
        skills = [rel for rel, _tpl in setup_mod.AGENT_FILES[vendor] if rel.endswith("/SKILL.md")]
        assert skills, vendor
        assert all(rel.startswith(".agents/skills/") for rel in skills), vendor
    every = [rel for files in setup_mod.AGENT_FILES.values() for rel, _tpl in files]
    # 🔴 **Narrowed 2026-09-14 from `.codex/` to `.codex/skills/`.** Veto 3 fired
    # on the SKILLS path -- `.codex/skills` is not a path Codex's docs list. It
    # never said anything about `.codex/hooks.json` or `.codex/agents/`, which
    # ARE documented and which fux now writes (SR-AGENT-SURFACES decision 3a).
    # A blanket ban on the vendor's whole directory read as a finding when it
    # was only ever a finding about one path inside it.
    assert not [rel for rel in every if rel.startswith((".codex/skills/", ".github/skills/"))]


def test_codex_and_copilot_skill_rosters_are_identical():
    """One tuple (`setup.SHARED_SKILLS`) in both rows, so the two cannot drift:
    a skill added for one vendor reaches the other by construction."""
    def skills(vendor):
        return sorted(
            (rel, tpl) for rel, tpl in setup_mod.AGENT_FILES[vendor] if rel.endswith("/SKILL.md")
        )

    assert skills("codex") == skills("copilot") == sorted(setup_mod.SHARED_SKILLS)


def test_a_path_two_vendors_share_maps_to_one_template():
    """Two vendors naming one path is legal only if they would write the same
    bytes there — otherwise install order would decide which vendor's file a
    repository gets, silently."""
    templates: dict[str, set[str]] = {}
    for files in setup_mod.AGENT_FILES.values():
        for rel, tpl in files:
            templates.setdefault(rel, set()).add(tpl)
    assert {rel: tpls for rel, tpls in templates.items() if len(tpls) > 1} == {}


def test_a_shared_path_is_written_and_announced_once(tmp_path):
    """`_write_agents` skips a path an earlier vendor wrote in the same run.
    Without that, the second pass reports fux's own fresh file as `kept ...
    (yours; never rewritten)`, and the announcement names it twice."""
    report = setup_mod.run(_fresh(tmp_path))
    assert len(report.outside) == len(set(report.outside))
    assert len(report.written) == len(set(report.written))
    assert not [rel for rel in report.kept if rel.startswith(".agents/")]


def test_copilot_alone_still_gets_every_skill(tmp_path):
    """Decision 14's hole, re-checked after the move: `install = ["copilot"]`
    without `codex` must still write the shared skills."""
    root = _fresh(tmp_path)
    (root / "fux.toml").write_text('[sources]\n[agents]\ninstall = ["copilot"]\n', encoding="utf-8")
    setup_mod.run(root)
    for rel, _tpl in setup_mod.SHARED_SKILLS:
        assert (root / rel).is_file(), rel
    assert not (root / ".github" / "skills").exists()


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
    missing**, and [SR-DOTFUX](../records/0102_fux-directory.md) decision 8
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


def test_co_owned_surface_is_never_written_over(tmp_path):
    """Decision 6. A consumer's `settings.json` survives `fux setup` untouched.

    The failure this prevents is not hypothetical: this repository's own
    `.claude/settings.json` carries deny rules protecting the sealed golden
    answer key. A setup that overwrote it would silently remove the guard that
    keeps an evaluation set out of a model's context.
    """
    import json

    root = _fresh(tmp_path)
    mine = {"permissions": {"deny": ["Read(**/secret/**)"]}}
    for rel in setup_mod.CO_OWNED_SURFACES:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(mine), encoding="utf-8")

    setup_mod.run(root)

    for rel in setup_mod.CO_OWNED_SURFACES:
        assert json.loads((root / rel).read_text(encoding="utf-8")) == mine, rel


def test_co_owned_surface_template_is_valid_json():
    """What replaces byte equality for a co-owned surface: it must still parse."""
    import json

    by_path = {rel: tpl for files in setup_mod.AGENT_FILES.values() for rel, tpl in files}
    for rel in setup_mod.CO_OWNED_SURFACES:
        json.loads(setup_mod.agent_template_bytes(by_path[rel]).decode("utf-8"))


def test_the_hook_surface_is_written_executable(tmp_path):
    """Decision 5. A hook written 0644 fails silently — nothing reports it."""
    root = _fresh(tmp_path)
    setup_mod.run(root)
    for rel in setup_mod.EXECUTABLE_SURFACES:
        assert (root / rel).stat().st_mode & 0o111, f"{rel} is not executable"
