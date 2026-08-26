"""W-82 §3.6 — the invocation ladder, and the rules that keep it safe.

The defect this closes was live and silent: `fux.agent.md` told an agent to fall
back to ordinary search when `fux` was not found, so **any repo whose fux lives
in an unactivated `.venv/` had an agent quietly using grep** while the engine sat
there and the index sat committed. It did not error. It degraded, and the
degradation read like an honest answer.
"""

from __future__ import annotations

import re
from importlib import resources

import pytest

from fux.config import KNOWN_AGENTS
from fux.setup import AGENT_FILES

#: Every template that is supposed to teach invocation.
LADDER_TEMPLATES = ("USAGE-SKILL.md", "fux-usage.instructions.md", "fux.agent.md")

#: The four rungs, in the order an agent must try them.
RUNGS = ("fux --version", "uv run fux", "./.venv/bin/fux", "python -m fux.cli")


def _template(name: str) -> str:
    return (resources.files("fux") / "templates" / "agents" / name).read_text(encoding="utf-8")


def _all_templates() -> dict[str, str]:
    names = {tpl for entries in AGENT_FILES.values() for _dest, tpl in entries}
    return {name: _template(name) for name in sorted(names)}


# -- the ladder ---------------------------------------------------------------


@pytest.mark.parametrize("name", LADDER_TEMPLATES)
@pytest.mark.parametrize("rung", RUNGS)
def test_every_ladder_template_carries_every_rung(name, rung):
    assert rung in _template(name)


@pytest.mark.parametrize("name", LADDER_TEMPLATES)
def test_the_rungs_are_in_order(name):
    """Order is the content. `python -m fux.cli` first would mask a broken venv;
    `./.venv/bin/fux` first would ignore a perfectly good active environment."""
    text = _template(name)
    positions = [text.index(rung) for rung in RUNGS]
    assert positions == sorted(positions)


@pytest.mark.parametrize("name", LADDER_TEMPLATES)
def test_windows_rung_is_present(name):
    """Windows-first fleets are a design input, and `.venv\\Scripts\\fux.exe` is
    a different path, not a footnote."""
    assert r".venv\Scripts\fux.exe" in _template(name)


@pytest.mark.parametrize("name", LADDER_TEMPLATES)
def test_not_installed_is_never_the_conclusion(name):
    """The exact sentence that caused the silent fallback.

    An unresolvable command means *could not be invoked*, which is diagnosable.
    *Not installed* is a claim about the world that the evidence does not
    support, and it sends the agent to grep.
    """
    text = _template(name)
    assert "could not be invoked" in text
    # The exact sentence that shipped the defect. It is asserted absent as a
    # literal, which is only meaningful because the templates were rewritten to
    # state the counter-example WITHOUT quoting it -- a check that cannot tell
    # an instruction from a prohibition is a check that gets loosened later.
    assert "fux is not installed" not in text


@pytest.mark.parametrize("name", LADDER_TEMPLATES)
def test_which_is_never_the_probe(name):
    """`which` answers *is there a file*, not *does it run* — a stale shim from
    a deleted venv passes it."""
    text = _template(name)
    assert "--version" in text
    assert "which" in text  # named, so the agent knows not to reach for it


# -- the rule worth gating ----------------------------------------------------

#: Phrases that would make an agent mutate the user's environment.
#: Asserted absent as LITERALS. The templates state the prohibition in prose
#: ("do not activate the virtualenv") precisely so these strings never appear,
#: which is what makes the check exact instead of a heuristic about negation.
MUTATIONS = (
    "source .venv/bin/activate",
    "source venv/bin/activate",
    "export path=",
    "pip install fux",
    "pip install -e",
    "uv pip install",
)


@pytest.mark.parametrize("name,text", sorted(_all_templates().items()))
def test_no_rendering_ever_tells_an_agent_to_activate_or_install(name, text):
    """**The failure mode a well-meaning edit introduces**, and the reason this
    is a test rather than a sentence in a record.

    Reaching for `source .venv/bin/activate` is the obvious fix for a
    `command not found`, and it is wrong: mutating the user's shell so a
    read-only query can run is a side effect nobody consented to, and in an
    agent's non-interactive subshell it usually does not even persist.
    """
    lowered = text.lower()
    for phrase in MUTATIONS:
        assert phrase not in lowered, f"{name} tells an agent to run: {phrase}"


# -- one template, two destinations ------------------------------------------


def test_the_usage_skill_is_the_same_bytes_for_claude_and_kiro():
    """Kiro implements the same open Agent Skills standard Claude does, so the
    identical template is valid at both paths.

    **Agreement by construction**, which is strictly stronger than a conformance
    test asserting that two separately-maintained renderings still match.
    """
    claude = [d for d, t in AGENT_FILES["claude"] if t == "USAGE-SKILL.md"]
    kiro = [d for d, t in AGENT_FILES["kiro"] if t == "USAGE-SKILL.md"]
    assert claude == [".claude/skills/fux-usage/SKILL.md"]
    assert kiro == [".kiro/skills/fux-usage/SKILL.md"]


def test_every_vendor_gets_the_ladder():
    """A ladder in one rendering and not the others is exactly the drift
    ADR-AGENT-POLICY decision 2's conformance test exists to catch."""
    for vendor in KNOWN_AGENTS:
        templates = {tpl for _dest, tpl in AGENT_FILES[vendor]}
        assert templates & set(LADDER_TEMPLATES), f"{vendor} has no invocation guidance"


# -- the Agent Skills standard's own constraints ------------------------------


def test_skill_frontmatter_matches_its_folder_name_and_length_limits():
    """Kiro enforces these; Claude does not. A skill that silently fails to load
    on one vendor is the same silent-degradation class this phase is about."""
    for vendor, entries in AGENT_FILES.items():
        for dest, tpl in entries:
            if not dest.endswith("/SKILL.md"):
                continue
            folder = dest.rsplit("/", 2)[-2]
            text = _template(tpl)
            name = re.search(r"^name:\s*(.+)$", text, re.M)
            description = re.search(r"^description:\s*(.+)$", text, re.M)
            assert name and description, f"{tpl} is a SKILL.md with no name/description"
            assert name.group(1).strip() == folder, f"{tpl}: name must equal folder {folder}"
            assert re.fullmatch(r"[a-z0-9-]{1,64}", folder), f"{folder} is not a legal skill name"
            assert len(description.group(1).strip()) <= 1024, f"{tpl}: description over 1024 chars"


def test_the_usage_skill_names_the_kiro_custom_agent_trap():
    """Kiro custom agents load neither skills nor steering by default. Fux
    cannot write someone's agent config, so the skill has to say it — otherwise
    a consumer on a custom agent gets none of this and no error."""
    text = _template("USAGE-SKILL.md")
    assert "custom agent" in text.lower()
    assert "skill://" in text
