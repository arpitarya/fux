"""SR-AGENT-POLICY decision 2 — every rendering carries the canonical block.

**Exact match on a shared block, not a substring or a similarity test**, and
that shape was forced by a failure. The renderings were first written to *say
the same thing*: "never drop the mark when you summarise" against "never drop
the archived mark when summarising". Same meaning, different bytes — and **no
fuzzy test can separate a legitimate rewording from a dropped rule.** A test
that cannot fail correctly is worse than none, because it certifies agreement
it never checked.

Named by that record's own "How to check it" block, so this file lives at the
path the record points at (veto condition 3).
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "src" / "fux" / "templates" / "agents"

#: The begin marker carries a trailing reminder in the file, so it is matched
#: by PREFIX and the end marker in full — exactly as SR-AGENT-POLICY's own
#: "How to check it" snippet does. The block between them is then compared
#: whole and byte-for-byte, which is the property that matters.
BEGIN = "<!-- fux:policy:begin v1"
END = "<!-- fux:policy:end v1 -->"

#: The two renderings that enter EVERY request in a consumer's repository —
#: Copilot's `applyTo: "**"` and Kiro's `inclusion: always`. Veto condition 5.
# W-82 ruling 16 made mechanical. The repo-root `AGENTS.md` is AMBIENT — Kiro
# loads it on every interaction — so ruling 16's *"it must stay policy-shaped
# and short"* is enforced by the same byte bound as the other two rather than
# left to whoever edits it next. Ruling 15 says ambient files carry policy, not
# manuals; this is that rule holding itself to account.
AMBIENT = (
    "fux-archived-results.instructions.md",
    "steering-fux-archived-results.md",
    "AGENTS.md",
)

#: ~2 KB each today. The bound is deliberately loose — this catches a rendering
#: that doubled, not one that gained a sentence.
AMBIENT_MAX_BYTES = 4096


#: Files in `templates/agents/` that are NOT renderings of the archived-results
#: policy, and must not be checked against its verbatim block.
#:
#: `ENRICH-SKILL.md` (W-76 Phase 8) is a **procedure**, not a policy: it tells
#: an agent how to generate enrichment when a human asks, and carries no claim
#: about how to read fux's output. Holding it to the policy block would force
#: an unrelated eight-rule preamble into an instruction file whose whole job is
#: to be invoked deliberately and rarely.
#:
#: **This list is the escape hatch and it must stay short.** Every name here is
#: a file the agreement check no longer protects, so adding one is a decision,
#: not a convenience -- which is why `test_the_exemptions_are_deliberate` below
#: pins its contents.
#: `USAGE-SKILL.md` and `fux-usage.instructions.md` (W-82 3.6) are an
#: **operating manual**, not a policy: they teach how to resolve and invoke the
#: `fux` command and which verb to reach for, and state no position on how to
#: read an archived result. They point AT `fux-archived-results` for that, which
#: is the correct relationship -- inlining the eight-rule block would duplicate
#: a policy that already has a rendering per vendor, and duplication is exactly
#: what decision 2's byte-for-byte check exists to prevent drifting.
#: `DECODER-SKILL.md` (W-86 P7) is a **build procedure**, not a policy: it
#: tells an agent how to write or edit a decoder when a human asks, and states
#: no position on how to read fux's output. It is the same shape as
#: `ENRICH-SKILL.md` — invoked deliberately, writes into a committed directory,
#: changes ranking — and holding it to the archived-results block would force an
#: eight-rule preamble about interpreting search results into a file about
#: parsing file formats. It points AT `fux-archived-results` for that instead.
NOT_A_POLICY_RENDERING = frozenset(
    {
        "POLICY.md",
        "ENRICH-SKILL.md",
        "USAGE-SKILL.md",
        "fux-usage.instructions.md",
        "DECODER-SKILL.md",
    }
)


#: **The operating guides and their pointers** (SR-AGENT-POLICY decision 15,
#: Arpit 2026-09-11) -- a SECOND exemption, kept separate from the one above so
#: neither list quietly absorbs the other.
#:
#: Ten skills (one per job the CLI supports) and twenty-six short pointers:
#: seven path-scoped topics rendered for Kiro (`fileMatch`), Claude
#: (`.claude/rules/`, `paths:`) and Copilot (`applyTo:` with explicit globs),
#: plus five Kiro `inclusion: auto` guides. **None of them is a rendering of the
#: archived-results policy** -- each points AT `fux-archived-results` instead, for
#: decision 2's reason: a second copy of the block is a second thing to drift.
#:
#: Pinned by name like the list above, because an unlisted file here stops being
#: checked. Their own gates -- a byte bound, one body per topic across vendors,
#: never `"**"` or `inclusion: always` -- live in `test_setup_agents_guides.py`.
OPERATING_GUIDES = frozenset(
    {f"{g}-SKILL.md" for g in (
        "SEARCH", "ANSWER", "GRAPH", "INDEX", "MAINTAIN", "MCP",
        "SOURCES", "CONFIG", "FETCHER", "PII",
        # SR-INSPECT's guide. An operating guide like the ten above, and it
        # points AT `fux-archived-results` rather than carrying the block —
        # `inspect` reports statistics over a whole corpus and never hands a
        # reader a document to act on, so there is no archived result in its
        # output to misread.
        "INSPECT",
        # SR-ENRICH decision 19's guide. An operating guide, and it points at
        # `fux-archived-results` as well as REFUSING to correct an archived
        # document at all — *`supersedes` / `archived=` is the fix* is in its
        # own Don't list, which is a stronger statement than the block's.
        "CORRECT",
    )}
    | {f"steering-fux-{t}-files.md" for t in (
        "sources", "decoder", "enrich", "fetcher", "pii", "config", "index",
    )}
    | {f"rule-fux-{t}-files.md" for t in (
        "sources", "decoder", "enrich", "fetcher", "pii", "config", "index",
    )}
    | {f"fux-{t}-files.instructions.md" for t in (
        "sources", "decoder", "enrich", "fetcher", "pii", "config", "index",
    )}
    | {f"steering-fux-{t}-guide.md" for t in (
        "usage", "search", "answer", "graph", "mcp",
    )}
)


#: **The ACTING surfaces that are procedures or formatting, not policy**
#: (SR-AGENT-SURFACES decision 3). A THIRD exemption, kept separate from the two
#: above so none of them quietly absorbs another.
#:
#: A slash command is a procedure invoked deliberately by name; an output style
#: is formatting. Neither states a position on how to read an archived result,
#: and each points AT `fux-archived-results` — decision 2's reason again: a
#: second copy of the block is a second thing to drift.
#:
#: 🔴 **`subagent-fux-researcher.md` is deliberately NOT here.** It is an agent
#: that returns cited results, so decision 9's test — *does an agent that has
#: never heard of Fux still need this sentence to avoid being wrong?* — answers
#: yes, and it carries the block verbatim like any other rendering. The hook
#: (`.sh`) and the seeded settings (`.json`) are not `*.md` and never reach this
#: glob at all.
ACTING_SURFACES = frozenset(
    {
        "command-fux-search.md",
        "command-fux-answer.md",
        "command-fux-verify.md",
        "output-style-fux-cited.md",
        # Copilot's prompt files are the same procedures with native frontmatter
        # (SR-AGENT-SURFACES decision 3a). Same class, same exemption.
        "copilot-prompt-fux-search.prompt.md",
        "copilot-prompt-fux-answer.prompt.md",
        "copilot-prompt-fux-verify.prompt.md",
    }
)


def test_the_acting_surface_exemptions_are_deliberate():
    """Pin the third escape hatch, the same way as the first two."""
    from fux import setup as setup_mod

    assert len(ACTING_SURFACES) == 7
    assert not ACTING_SURFACES & NOT_A_POLICY_RENDERING
    assert not ACTING_SURFACES & OPERATING_GUIDES
    shipped = {tpl for files in setup_mod.AGENT_FILES.values() for _rel, tpl in files}
    assert ACTING_SURFACES <= shipped, sorted(ACTING_SURFACES - shipped)
    # the subagent is NOT exempt, and that is the point
    assert "subagent-fux-researcher.md" not in ACTING_SURFACES


def renderings() -> list[Path]:
    return sorted(
        p
        for p in AGENTS.glob("*.md")
        if p.name not in NOT_A_POLICY_RENDERING
        and p.name not in OPERATING_GUIDES
        and p.name not in ACTING_SURFACES
    )


def test_the_operating_guides_are_deliberate():
    """The second escape hatch, pinned the same way as the first: every name is a
    file the agreement check no longer reads, so the count is asserted, and every
    name must be a template that actually ships -- a stale entry here would
    exempt a file that does not exist yet from a check it should face."""
    from fux import setup as setup_mod

    assert len(OPERATING_GUIDES) == 38
    assert not OPERATING_GUIDES & NOT_A_POLICY_RENDERING
    shipped = {tpl for files in setup_mod.AGENT_FILES.values() for _rel, tpl in files}
    assert OPERATING_GUIDES <= shipped, sorted(OPERATING_GUIDES - shipped)
    on_disk = {p.name for p in AGENTS.glob("*.md")}
    assert OPERATING_GUIDES <= on_disk, sorted(OPERATING_GUIDES - on_disk)


def test_the_exemptions_are_deliberate():
    """Pin the escape hatch.

    A file added to `NOT_A_POLICY_RENDERING` stops being checked for the
    verbatim policy block. That is occasionally right and always worth
    noticing, so the set is asserted rather than trusted -- otherwise the
    cheapest way to fix a failing agreement test is to add a name to it.
    """
    assert NOT_A_POLICY_RENDERING == {
        "POLICY.md",
        "ENRICH-SKILL.md",
        "USAGE-SKILL.md",
        "fux-usage.instructions.md",
        "DECODER-SKILL.md",
    }


def canonical_block() -> str:
    text = (AGENTS / "POLICY.md").read_text(encoding="utf-8")
    start, end = text.index(BEGIN), text.index(END) + len(END)
    return text[start:end]


def test_the_canonical_policy_has_exactly_one_block():
    text = (AGENTS / "POLICY.md").read_text(encoding="utf-8")
    assert text.count(BEGIN) == 1 and text.count(END) == 1


def test_the_block_is_substantial():
    """Guards the guard: an empty or truncated block would make every
    agreement assertion below pass vacuously."""
    block = canonical_block()
    assert len(block) > 400, f"the canonical block is only {len(block)} B — too small to be the policy"
    assert block.count("\n") >= 8, "the policy is eight numbered rules; this block has too few lines"


def test_there_are_renderings_to_check():
    """A vacuous pass is the failure mode this whole file exists to avoid.

    **Nine since 2026-09-14**, not five — the subagent shipped to all four
    vendors once decision 3a corrected the Claude-only claim: `subagent-fux-researcher.md` is the
    first ACTING surface to carry the policy, and it carries it for the reason
    every other rendering does — it returns cited results, so an agent running
    it can launder a retired design into plain prose exactly as a skill-driven
    one can (SR-AGENT-SURFACES decision 3; SR-AGENT-POLICY decision 9's test).
    """
    assert len(renderings()) == 9, [p.name for p in renderings()]


@pytest.mark.parametrize("path", renderings(), ids=lambda p: p.name)
def test_every_rendering_carries_the_block_byte_for_byte(path: Path):
    block = canonical_block()
    text = path.read_text(encoding="utf-8")
    assert block in text, (
        f"{path.name} does not carry the canonical policy block byte for byte. "
        "Reworded, reordered, partially included or absent — all four are the same "
        "defect (SR-AGENT-POLICY veto 3). Copy the block from POLICY.md verbatim; "
        "format-native framing goes AROUND it, never inside it."
    )


@pytest.mark.parametrize("path", renderings(), ids=lambda p: p.name)
def test_every_rendering_carries_a_policy_version(path: Path):
    """Decision 8: write-if-missing means a stale file is invisible without one."""
    assert "policy-version" in path.read_text(encoding="utf-8"), (
        f"{path.name} carries no `policy-version` — a consumer's copy is never "
        "rewritten, so without this a file three versions behind is undetectable"
    )


@pytest.mark.parametrize("name", AMBIENT)
def test_the_ambient_renderings_have_not_grown(name: str):
    """Veto condition 5. These enter every request in a consumer's repo, for
    every developer, whether or not they are using fux — the cost is paid on
    every prompt, forever. **Growth here is a regression, not an improvement.**"""
    size = (AGENTS / name).stat().st_size
    assert size <= AMBIENT_MAX_BYTES, (
        f"{name} is {size} B, over the {AMBIENT_MAX_BYTES} B bound. This file is "
        "ambient: it is on every prompt in the consumer's repository. If it genuinely "
        "needs to be longer, that is a decision for SR-AGENT-POLICY, not a bound to raise"
    )


# SR-AGENT-POLICY **veto condition 6** — "the policy tells an agent what the
# answer is, rather than how to read the fact" — is deliberately NOT tested
# here. A first attempt flagged `SKILL.md` for naming `archive/v0.26-docs/...`
# in a worked example, which decision 2 explicitly permits ("a skill's worked
# example") and which the record itself prints in its §1. **A check that fires
# on correct content trains people to switch it off**, which is the same
# lesson `tests/test_windows_console_safe.py` already paid for when it flagged
# the code defending against a character. Veto 6 is a prose judgement; the
# record's own "How to check it" says to read the renderings, and that is the
# honest answer.
