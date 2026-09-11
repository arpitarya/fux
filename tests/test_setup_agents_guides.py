"""ADR-AGENT-POLICY decision 15 — the operating guides and their pointers.

Arpit, 2026-09-11: skills for every job the CLI supports, **and** steering-style
pointers, for Claude, Codex, Copilot and Kiro. Decision 9 had said a manual
ships as a skill and only policy ships as steering; decision 15 admits pointers
on the conditions this file makes mechanical, because every one of them is a
file that can enter a request its reader never asked for:

1. **A pointer is short.** On a Kiro CLI without inclusion-mode support every
   file in `.kiro/steering/` is ambient, so a pointer that grows into a manual is
   veto 6's regression arriving through a new door. Byte-bounded.
2. **A pointer is path-scoped or description-scoped, never `"**"` or
   `inclusion: always`.** The only always-on renderings stay the three policy
   files decision 9 already names.
3. **A committed-write topic is path-scoped only.** It loads when an agent is
   already editing that plane's files — never on a description match, and never
   for a request that does not touch them (decision 9a, as far as a vendor's
   scoping reaches).
4. **One body per topic.** The three renderings of a path-scoped pointer differ
   only in frontmatter, so a rule edited for one vendor and not the others fails
   here — decision 2's device, applied to prose that has no verbatim block.
5. **Every pointer names a skill that ships** to the same vendor.
"""

from __future__ import annotations

import re
from importlib import resources

import pytest

from fux import setup as setup_mod

#: A pointer holds rules and a skill name, never a procedure. ~0.9 KB each at
#: introduction; the bound catches one that doubled.
POINTER_MAX_BYTES = 1200

#: The planes whose files a committed-write skill edits -- each gets a
#: path-scoped pointer.
COMMITTED_WRITE_PLANES = {"sources", "decoder", "enrich", "fetcher", "pii", "config"}

#: Every job that writes something committed: the planes above, plus `index`
#: (`fux setup`, `fux ingest`) and `maintain` (`fux hooks` edits `.gitattributes`).
WRITES_COMMITTED = COMMITTED_WRITE_PLANES | {"index", "maintain"}


def _text(name: str) -> str:
    return (resources.files("fux") / "templates" / "agents" / name).read_text(encoding="utf-8")


def _split(text: str) -> tuple[str, str]:
    assert text.startswith("---\n"), "a pointer must open with frontmatter"
    end = text.index("\n---\n", 4)
    return text[4:end], text[end + len("\n---\n") :]


def _pointers() -> dict[str, tuple[str, str]]:
    """template name -> (vendor, destination), for every pointer setup writes."""
    out = {}
    for vendor, files in setup_mod.AGENT_FILES.items():
        for rel, tpl in files:
            if tpl.startswith(("steering-fux-", "rule-fux-")) and tpl != "steering-fux-archived-results.md":
                out[tpl] = (vendor, rel)
            elif tpl.endswith("-files.instructions.md"):
                out[tpl] = (vendor, rel)
    return out


def test_the_pointer_roster_is_exactly_the_declared_topics():
    names = set(_pointers())
    expected = (
        {f"steering-fux-{t}-files.md" for t in setup_mod.PATH_SCOPED_TOPICS}
        | {f"rule-fux-{t}-files.md" for t in setup_mod.PATH_SCOPED_TOPICS}
        | {f"fux-{t}-files.instructions.md" for t in setup_mod.PATH_SCOPED_TOPICS}
        | {f"steering-fux-{t}-guide.md" for t in setup_mod.AUTO_GUIDE_TOPICS}
    )
    assert names == expected
    assert len(names) == 26


@pytest.mark.parametrize("name", sorted(_pointers()))
def test_a_pointer_stays_short(name):
    size = len(_text(name).encode("utf-8"))
    assert size <= POINTER_MAX_BYTES, (
        f"{name} is {size} B (bound {POINTER_MAX_BYTES}). On a Kiro CLI without "
        "inclusion modes this enters every request. Move the detail into the skill "
        "the pointer names."
    )


@pytest.mark.parametrize("name", sorted(_pointers()))
def test_a_pointer_is_never_always_on(name):
    front, _body = _split(_text(name))
    assert "inclusion: always" not in front, name
    assert not re.search(r'applyTo:\s*"\*\*"', front), name
    if name.startswith("steering-fux-"):
        assert re.search(r"^inclusion: (fileMatch|auto)$", front, re.M), name
    elif name.startswith("rule-fux-"):
        assert re.search(r"^paths:\n(  - \".+\"\n?)+", front + "\n", re.M), (
            f"{name}: a Claude rule with no `paths:` loads at launch, every session"
        )
    else:
        match = re.search(r'^applyTo: "(.+)"$', front, re.M)
        assert match, name
        for glob in match.group(1).split(","):
            assert glob.startswith((".fux/", "fux.toml")), f"{name}: {glob} is not scoped to fux's files"


def test_a_committed_write_topic_is_never_description_triggered():
    """Condition 3. A description match can fire on a request that edits nothing;
    a path match fires only while the agent is already in that plane's files."""
    assert not WRITES_COMMITTED & set(setup_mod.AUTO_GUIDE_TOPICS)
    assert COMMITTED_WRITE_PLANES <= set(setup_mod.PATH_SCOPED_TOPICS)


@pytest.mark.parametrize("topic", setup_mod.PATH_SCOPED_TOPICS)
def test_one_body_per_path_scoped_topic_across_vendors(topic):
    bodies = {
        name: _split(_text(name))[1]
        for name in (
            f"steering-fux-{topic}-files.md",
            f"rule-fux-{topic}-files.md",
            f"fux-{topic}-files.instructions.md",
        )
    }
    assert len(set(bodies.values())) == 1, (
        f"the three renderings of the {topic!r} pointer have drifted apart: "
        + ", ".join(sorted(bodies))
    )


@pytest.mark.parametrize("topic", setup_mod.PATH_SCOPED_TOPICS)
def test_one_glob_set_per_path_scoped_topic_across_vendors(topic):
    kiro, _ = _split(_text(f"steering-fux-{topic}-files.md"))
    claude, _ = _split(_text(f"rule-fux-{topic}-files.md"))
    copilot, _ = _split(_text(f"fux-{topic}-files.instructions.md"))
    kiro_globs = re.findall(r'"([^"]+)"', re.search(r"^fileMatchPattern: (.+)$", kiro, re.M).group(1))
    claude_globs = re.findall(r'^  - "([^"]+)"$', claude, re.M)
    copilot_globs = re.search(r'^applyTo: "(.+)"$', copilot, re.M).group(1).split(",")
    assert kiro_globs == claude_globs == copilot_globs, topic


@pytest.mark.parametrize("topic", setup_mod.AUTO_GUIDE_TOPICS)
def test_an_auto_guide_carries_the_name_and_description_kiro_requires(topic):
    front, _ = _split(_text(f"steering-fux-{topic}-guide.md"))
    assert re.search(rf"^name: fux-{topic}-guide$", front, re.M), topic
    description = re.search(r"^description: (.+)$", front, re.M)
    assert description and ": " not in description.group(1), (
        f"{topic}: the description must be one plain YAML scalar"
    )


@pytest.mark.parametrize("name", sorted(_pointers()))
def test_a_pointer_names_a_skill_its_vendor_actually_gets(name):
    vendor, _rel = _pointers()[name]
    named = re.findall(r"Full procedure: the `([a-z0-9-]+)` skill\.", _text(name))
    assert len(named) == 1, f"{name} must end by naming exactly one skill"
    skills = {rel.rsplit("/", 2)[-2] for rel, _tpl in setup_mod.AGENT_FILES[vendor] if rel.endswith("/SKILL.md")}
    assert named[0] in skills, f"{name} points at {named[0]}, which {vendor} does not get"


#: Codex lists every installed skill's description inside a budget of about
#: 8,000 characters and shortens descriptions first when it overflows. Thirteen
#: fux skills at <= 500 characters stay under it with room for the consumer's own.
SKILL_DESCRIPTION_MAX = 500


def test_every_shipped_skill_description_fits_the_listing_budget_and_parses():
    templates = {tpl for files in setup_mod.AGENT_FILES.values() for rel, tpl in files if rel.endswith("/SKILL.md")}
    for tpl in sorted(templates):
        description = re.search(r"^description: (.+)$", _text(tpl), re.M).group(1)
        assert len(description) <= SKILL_DESCRIPTION_MAX, f"{tpl}: {len(description)} chars"
        # a plain YAML scalar: `: ` or ` #` would end or break it on a strict parser
        assert ": " not in description and " #" not in description, tpl
