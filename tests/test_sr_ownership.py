"""Ownership is a table, not a judgement call — and this test is its twin.

`records/README.md` carries the ownership table: which decision record owns
which component of `src/` and `tools/`. This test fails when the table and the
tree disagree, so a module cannot be added without someone deciding which
record it belongs to.

**Edit both in the same change.** The table and this file drift silently
otherwise, which is the failure mode the check exists to prevent.

A component with no decision yet is claimed by an open work item (`W-nn`)
instead of an SR name. That id is resolved against `work/OPEN-WORK.md`, so a
`W-nn` that closes without rehoming its component fails this test.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from sr_lib import SR_DIR, RECORD_DIRS, ROOT, open_work_ids, ownership_table, register_names

# Roots whose components must every one be claimed.
CLAIMED_ROOTS = (ROOT / "src" / "fux", ROOT / "tools")

# Not components: caches, dotdirs, and the test trees of the tools themselves.
_IGNORED_DIR_NAMES = {"__pycache__", ".pytest_cache", "tests", "pruning"}


def _has_source(directory: Path) -> bool:
    """Is there any `.py` under here, or is it just abandoned bytecode?

    🔴 **A branch switch leaves the DIRECTORY behind.** `git checkout` removes
    the tracked files of a module that does not exist on the other branch, but
    it cannot remove the directory while `__pycache__/` — untracked, and git
    therefore not git's business — is still sitting in it. What is left is a
    component name with no component under it, and this check reported it as
    **unclaimed by any record**, which reads as a missing ownership row rather
    than as a stale `.pyc`.

    ⚠ **The failure is worse than noise, because the remedy it names is wrong.**
    It says *add a row to the ownership table*, and a row added for a module
    that exists on another branch is a claim that outlives the confusion and
    has to be found again later.

    Recorded twice in the WORKLOG on 2026-09-14 (`src/fux/inspect` both times,
    left by `main` <-> `release/3.0.0-alpha.0`), so it becomes a check rather
    than a third cleanup — [SR-WORK-SESSION](../records/0060_WORK-session.md)
    decision 13. A directory holding real modules still has to be claimed;
    nothing is loosened.
    """
    return any(directory.rglob("*.py"))


def _rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


# --------------------------------------------------------------------------
# parsing


def records_on_disk() -> set[Path]:
    found: set[Path] = set()
    for d in RECORD_DIRS:
        found |= set(d.glob("[0-9][0-9][0-9][0-9]_*.md"))
    return found


# --------------------------------------------------------------------------
# the components that must be claimed


def components() -> set[str]:
    found: set[str] = set()
    for root in CLAIMED_ROOTS:
        if not root.exists():  # pragma: no cover - tree not built yet
            continue
        for child in sorted(root.iterdir()):
            if child.name.startswith("."):
                continue
            if child.is_dir():
                if child.name in _IGNORED_DIR_NAMES:
                    continue
                if not _has_source(child):
                    continue
                found.add(_rel(child))
            elif child.suffix == ".py":
                found.add(_rel(child))
    return found


# --------------------------------------------------------------------------
# the checks


def test_every_component_is_claimed_by_a_record() -> None:
    table = ownership_table()
    unclaimed = sorted(components() - set(table))
    assert not unclaimed, (
        "these components are claimed by no SR and by no open work item:\n  "
        + "\n  ".join(unclaimed)
        + "\n\nAdd a row to the ownership table in records/README.md (and keep "
        "this test in the same change)."
    )


def test_every_ownership_row_points_at_something_real() -> None:
    missing = sorted(c for c in ownership_table() if not (ROOT / c).exists())
    assert not missing, (
        "the ownership table claims components that do not exist:\n  " + "\n  ".join(missing)
    )


def test_every_owner_resolves() -> None:
    names, ids = register_names(), open_work_ids()
    bad = []
    for component, owner in sorted(ownership_table().items()):
        if owner.startswith("SR-"):
            if owner not in names:
                bad.append(f"{component}: {owner} is not in the SR register")
        elif re.fullmatch(r"W-\d{2}", owner):
            if owner not in ids:
                bad.append(
                    f"{component}: {owner} is not an open item in work/OPEN-WORK.md — "
                    "the item closed without rehoming this component"
                )
        else:
            bad.append(f"{component}: {owner!r} is neither an SR name nor a W-nn id")
    assert not bad, "\n".join(bad)


def test_register_covers_every_record_on_disk() -> None:
    listed = {p.resolve() for p in register_names().values()}
    on_disk = {p.resolve() for p in records_on_disk()}
    missing = sorted(_rel(p) for p in on_disk - listed)
    phantom = sorted(str(p) for p in listed - on_disk)
    assert not missing and not phantom, (
        f"records on disk but not in the register: {missing}\n"
        f"records in the register but not on disk: {phantom}"
    )


def test_register_links_match_each_record_state() -> None:
    """A record's directory is its state — the register must point at the real one."""
    wrong = []
    for name, path in sorted(register_names().items()):
        if not path.exists():
            wrong.append(f"{name}: register points at {path}, which does not exist")
    assert not wrong, "\n".join(wrong)


def test_record_numbers_are_unique_within_a_directory() -> None:
    """Numbers are ordinals scoped to a directory and a generation.

    They restart when a record set is replaced, so `0001` may exist in more
    than one directory at once — nothing identifies a record by number. What
    must never happen is two records sharing a number in the SAME directory.
    """
    for d in RECORD_DIRS:
        seen: dict[str, str] = {}
        for path in sorted(d.glob("[0-9][0-9][0-9][0-9]_*.md")):
            num = path.name[:4]
            assert num not in seen, (
                f"{_rel(d)}: {path.name} and {seen[num]} both claim number {num}"
            )
            seen[num] = path.name


@pytest.mark.parametrize("name", sorted(register_names()))
def test_record_declares_its_own_name(name: str) -> None:
    """The register and the record must agree on the record's name.

    The record states it once, in frontmatter. It used to state it twice — a
    `name:` key and a `- **Name:**` bullet, written by hand at different times
    — and this test compared the register to the bullet, which is the copy that
    could drift from the key without anything noticing.
    """
    path = register_names()[name]
    m = re.search(r"^name:\s*(SR-[A-Z0-9-]+)\s*$", path.read_text(encoding="utf-8"), re.M)
    assert m, f"{path.name} has no `name:` in its frontmatter — records are cited by name"
    assert m.group(1) == name, f"{path.name} declares {m.group(1)}, register says {name}"


def test_records_do_not_restate_the_laws() -> None:
    """A record that restates a cross-cutting principle is a bug (SR-LAWS)."""
    handles = [
        "stdlib-only runtime",
        "no model in the maintenance path",
        # L8, added with the law on 2026-08-27. It caught a real paraphrase the
        # same day: SR-WORK-QUALITY decision 11 was written as "bound by L8 —
        # hashed, bounded, local, off every committed and networked path", which
        # is the drift this test exists to stop. Cite the number, not the words.
        "hashed, bounded, and local",
    ]
    offenders = []
    for path in sorted(records_on_disk()):
        if path.name.endswith("_LAWS.md"):
            continue
        # SR-LAW-0: the nine law records ARE the law's text, not a second
        # statement of it. This test guards every OTHER record against
        # paraphrasing a law; a law record carrying its own words is the point.
        if "_LAW-" in path.name:
            continue
        text = path.read_text(encoding="utf-8")
        for handle in handles:
            if handle in text:
                offenders.append(f"{path.name}: restates a law verbatim ({handle!r})")
    assert not offenders, (
        "\n".join(offenders)
        + "\n\nCite SR-LAWS and the law number instead; the laws have one home."
    )


def test_mermaid_diagrams_carry_a_collapsed_ascii_twin() -> None:
    """§1's diagram is a Mermaid block plus a hand-paired ASCII twin.

    The twin is mandatory (a renderer is not always available) and collapsed
    (§1 is capped at one screen). Both halves are cheap to enforce and easy to
    forget, which is exactly what a check is for.

    ⚠ **This check used to read EVERY ```text fence as an ASCII twin, and that
    was wrong.** A record legitimately uses ```text for captured example output
    — `0144_fuxignore.md` has one twin and three output blocks — so the old
    rule reported three violations against a record that was correctly written,
    and the only way to "fix" it was to stop using ```text for examples.
    **Found 2026-08-27 by running the gate for the first time in a session that
    could run it**; the record was right and the test was not.

    The rule now PAIRS them positionally, which is what *"hand-paired twin"*
    always meant: for each Mermaid block, the **next** ```text fence after it is
    its twin, and that one must be collapsed. Fences that are not the next one
    after a diagram are examples, and none of this applies to them.
    """
    problems = []
    for path in sorted(records_on_disk()) + [SR_DIR / "TEMPLATE.md"]:
        text = path.read_text(encoding="utf-8")
        if "```mermaid" not in text:
            continue
        for diagram in re.finditer(r"```mermaid\n.*?\n```", text, re.S):
            twin = re.search(r"```text\n.*?\n```", text[diagram.end():], re.S)
            if twin is None:
                problems.append(f"{path.name}: has a Mermaid block but no ASCII twin")
                continue
            start = diagram.end() + twin.start()
            end = diagram.end() + twin.end()
            before, after = text[:start], text[end:]
            open_tag = before.rfind("<details>")
            inside = open_tag != -1 and open_tag > before.rfind("</details>")
            if not (inside and after.lstrip().startswith("</details>")):
                problems.append(
                    f"{path.name}: the ASCII twin is not wrapped in a <details> block"
                )
            elif "\n\n```text" not in text[open_tag:end]:
                problems.append(
                    f"{path.name}: needs a blank line after </summary>, or the fence will not render"
                )
    assert not problems, "\n".join(problems)


def test_charts_name_the_source_of_their_numbers() -> None:
    """A chart's numbers are measured or computed, and the record says which.

    §1's Charts section is optional — most records should have none. When one
    is present, every number in it has to be traceable, or the chart is a
    drawing rather than evidence. The cheap enforceable form of that rule is a
    `source:` line inside the ASCII twin.
    """
    problems = []
    for path in sorted(records_on_disk()):
        text = path.read_text(encoding="utf-8")
        if "### Charts" not in text:
            continue
        charts = text.split("### Charts", 1)[1].split("\n## ", 1)[0]
        if "source:" not in charts:
            problems.append(
                f"{path.name}: has a Charts section with no 'source:' line — "
                "say which run or which constants the numbers come from"
            )
    assert not problems, "\n".join(problems)


# --------------------------------------------------------------------------
# describes — the second, additive relation (SR-WORK-OWNERSHIP)


def test_every_described_component_also_has_an_owner() -> None:
    """Veto condition 1. `describes` must never become a way to avoid deciding
    an owner — a component with no owner fails whatever describes it."""
    from sr_lib import describes_table

    owners = ownership_table()
    owned = set(owners)
    orphans = [
        c
        for c in describes_table()
        if c not in owned and not any(c.startswith(p + "/") for p in owned)
    ]
    assert not orphans, (
        f"described but unowned: {sorted(orphans)} — `describes` is additive, "
        "never a substitute for `owns`"
    )


def test_no_record_describes_what_it_already_owns() -> None:
    """Veto condition 2. The row would be noise, and noise in a hand-maintained
    table is how the table stops being trusted."""
    from sr_lib import describes_table, owner_of

    owners = ownership_table()
    redundant = [
        f"{component} -> {record}"
        for component, records in describes_table().items()
        for record in records
        if owner_of(component, owners) == record
    ]
    assert not redundant, f"already owned, so the describes row is noise: {redundant}"


def test_every_describing_record_is_a_real_record() -> None:
    """A typo here is invisible: the gate would demand a record that cannot be
    resolved, and `owning_records` skips unresolvable owners by design."""
    from sr_lib import describes_table

    known = set(register_names())
    unknown = sorted(
        {r for records in describes_table().values() for r in records} - known
    )
    assert not unknown, f"describes names records that are not in the register: {unknown}"


def test_every_describes_row_states_a_reason() -> None:
    """Veto condition 4. A bare pair is unauditable — a later reader cannot tell
    a real relation from a defensive one."""
    import re as _re

    from sr_lib import REGISTER

    body = REGISTER.read_text(encoding="utf-8")
    body = body.split("<!-- DESCRIBES-TABLE-START -->", 1)[1]
    body = body.split("<!-- DESCRIBES-TABLE-END -->", 1)[0]
    thin = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|- :"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells[0].lower() == "component":
            continue
        assert len(cells) >= 3, f"a describes row needs a reason cell: {line}"
        if len(cells[2]) < 40:
            thin.append(cells[0])
    assert not thin, f"describes rows with no real reason given: {thin}"


def test_the_describes_table_is_parsed_not_hard_coded() -> None:
    """The markers are the contract between the register and both tests.

    If they vanish, `describes_table()` raises rather than silently returning
    an empty relation — which would turn the widened gate back off with every
    test still green (veto condition 3, in its quietest form).
    """
    from sr_lib import REGISTER

    text = REGISTER.read_text(encoding="utf-8")
    assert "<!-- DESCRIBES-TABLE-START -->" in text
    assert "<!-- DESCRIBES-TABLE-END -->" in text


def test_the_freshness_gate_actually_consults_describers() -> None:
    """⚠ Veto condition 3, made mechanical.

    The widening is one line in `owning_records`. Deleting it leaves every
    other test in this suite green while the gate silently narrows back to
    owner-only — so assert the behaviour, not the line.
    """
    import test_sr_freshness as freshness

    table = ownership_table()
    touched = freshness.owning_records(["src/fux/query/__init__.py"], table)
    assert "SR-ASK" in touched, "the owner must still be demanded"
    assert "SR-CONFIDENCE" in touched, "a describer must be demanded too"
    assert "SR-OUTPUT" in touched


# -- which records the freshness gate can never open (measured 2026-09-11) ---

#: Records that own and describe **no `src/` component at all**, so
#: `test_sr_freshness` can never demand them: no code change can open them.
#:
#: ⚠ **This is an INVENTORY, not an approval.** It was measured on 2026-09-11
#: while W-126 amended [SR-ARCHIVED-CONTENT], which was on this list — the
#: record the change was ABOUT could not be demanded, and the gate asked for
#: seven others instead. Four `describes` rows fixed that one; the other 27 are
#: recorded rather than fixed, because deciding whether each *should* own
#: something is a per-record judgement and doing 27 of them silently is how a
#: register stops meaning anything.
#:
#: **Two legitimate reasons appear on this list and they are not the same:**
#:
#: 1. **Process records with no code** — the nine `SR-LAW-*`, `SR-WORK-OWNERSHIP`,
#:    `SR-PORT-LIST`, `SR-DOCS-TABLE`, `SR-RS`, `SR-WORK-QUALITY`. Nothing is
#:    owed; there is no component to own.
#:    ⚠ **`SR-WORK-OPEN-QUEUE` is here for a different reason and must not be
#:    read as the same case.** It is `kind: process` and it DOES own its
#:    enforcement — `tests/test_open_work_rows_are_short.py`,
#:    `tests/test_open_work_is_not_stale.py` and
#:    `tests/test_no_work_item_is_lost.py` — so a change to any opens it.
#:    It is unreachable only by THIS set's definition, which asks whether a
#:    change under `src/` can demand a record. A process record's subject is
#:    not code, so that question does not apply to it; widening the definition
#:    to `tests/` would quietly re-classify every record in case 1 as covered.
#:    ⚠ **`SR-WORK-ENVIRONMENTS` and `SR-WORK-BENCHMARK` are the same case** —
#:    both `kind: process`, both owning their enforcement
#:    (`tests/test_work_environments.py`, `tests/test_benchmark_capture.py`),
#:    and both unreachable only under this set's `src/`-shaped question.
#: 2. 🔴 **Records whose subject IS code, sitting inside a directory another
#:    record claims** — `SR-FIND`, `SR-RECORD`, `SR-POSTINGS`,
#:    `SR-DIR-LIST`, `SR-CDP-FETCHER`, `SR-URL-INGEST` and the three
#:    `SR-RUNTIME-*`. **These are the SR-ANSWER shape**, which the register's
#:    own describes-table note already records as a defect that shipped.
#:    ⚠ `SR-TYPES` left this list on 2026-09-11: decision 12 gave it
#:    `ingest/typesfile.py`, so a change to the types file's shape can now open it.
#:
#: The pin is deliberate: a record that GAINS coverage, or a new record that
#: arrives with none, lands as one failing assertion naming itself.
_UNREACHABLE_BY_THE_GATE = {
    # Case 1, and a third shape worth naming: **SR-AGENT-SURFACES owns no
    # component because its subject is a TAXONOMY** -- what an agent surface is,
    # and which class each kind belongs to. The rosters it classifies
    # (`CLAUDE_SURFACES`, `CO_OWNED_SURFACES`, `EXECUTABLE_SURFACES`) live in
    # `src/fux/setup.py`, which SR-AGENT-POLICY owns and must keep owning: one
    # component, one owner. A change to that file opens SR-AGENT-POLICY, which
    # is correct -- the roster is policy; the word for it is this record.
    "SR-AGENT-SURFACES",
    # ⚠ **SR-CDP-FETCHER, SR-HTTP-FETCHER and SR-RECORD left this set on
    # 2026-09-21** (W-208). Each gained a `src/` component it had always been
    # the record for -- the two fetcher templates, carved out of SR-FETCHER's
    # `templates/` claim, and `store/index-record.schema.json`, carved out of
    # SR-INDEX-LIFECYCLE's `store/` claim. **Newly reachable is good news**, and
    # deleting a name from here is how it is recorded.
    # ⚠ **Nine more left this set on 2026-09-21** (W-208): SR-CACHEDIR-TAG,
    # SR-DIR-LIST, SR-DOCS-TABLE, SR-FIND, SR-LOCKS, SR-RUNTIME-MANIFEST,
    # SR-RUNTIME-STAMP, SR-RUNTIME-STATS, SR-URL-INGEST and SR-POSTINGS
    # (`store/collisions.py`). **None of them
    # gained an owner** -- each gained `describes` rows on the `src/` files its
    # subject already lived in, which is what this set actually asks about:
    # whether a change under `src/` can demand the record. They still own
    # nothing, and the four runtime-plane records and SR-LOCKS now say in their
    # own bodies which of decision 7's two honest cases that is.
    "SR-LAW-0", "SR-LAW-1", "SR-LAW-2",
    "SR-LAW-3", "SR-LAW-4", "SR-LAW-5", "SR-LAW-6", "SR-LAW-7",
    "SR-LAW-8", "SR-WORK-ENVIRONMENTS", "SR-LAW-10", "SR-WORK-OWNERSHIP",
    "SR-PORT-LIST",
    "SR-WORK-QUALITY", "SR-RS",
    "SR-WORK-BENCHMARK", "SR-WORK-OPEN-QUEUE",
    # SR-WORK-BACKLOG (2026-09-13) owns no `src/` component and never will:
    # it governs `work/BACKLOG.md`, a list of work nobody is doing. No change
    # to the engine can make a backlog row true or false, so the freshness
    # gate cannot reach it — by design, like its sibling SR-WORK-OPEN-QUEUE.
    "SR-WORK-BACKLOG",
    # The eight WORK records the 2026-09-14 `CLAUDE.md` extraction filled,
    # `0057`–`0064`. Every one of them is here for SR-WORK-OPEN-QUEUE's reason
    # and not SR-ANSWER's: **their subject is how work is done**, so no change
    # under `src/` can make any of them true or false. Four are not ungated —
    # they own their enforcement outside `src/`, and each of those tests had no
    # owner at all before this change: SR-WORK-DOCS (`test_doc_registry.py`,
    # `test_doc_links.py`), SR-WORK-OKF (`test_okf_bundle.py`),
    # SR-WORK-ARCHIVE (`test_archive_law.py`), SR-WORK-RELEASE
    # (`check-version-parity.py`, `test_version_parity.py`), and
    # SR-WORK-BLOCKERS (the three `.claude/hooks/` scripts).
    # ⚠ The remaining three own nothing and say so in their own decisions —
    # SR-WORK-SCALE 15, SR-WORK-LIFECYCLE 12, SR-WORK-SESSION 13 — under
    # SR-WORK-OWNERSHIP decision 7: each names the case rather than inventing a
    # component, because a checker for *what a sentence may claim*, *the order
    # work happens in*, or *whether a handoff is true* would grade the wrong
    # thing and read as authority while doing it.
    "SR-WORK-SCALE", "SR-WORK-LIFECYCLE", "SR-WORK-DOCS", "SR-WORK-SESSION",
    "SR-WORK-OKF", "SR-WORK-ARCHIVE", "SR-WORK-RELEASE", "SR-WORK-BLOCKERS",
    # SR-WORK-GOVERNANCE (2026-09-14) owns no component and never will: it is
    # the MAP of what governs what, converted from `work/governance.md`. Its
    # subject is the inventory of governing files, so no change under `src/`
    # can make a row of it true or false. It owns no test either, and says so
    # under SR-WORK-OWNERSHIP decision 7: the only check worth having would be
    # *"is this map complete"*, and completeness against an open-ended set of
    # future steering files is exactly the thing a checker cannot grade —
    # which is why it is decision 8's obligation and the record's veto
    # condition instead.
    "SR-WORK-GOVERNANCE",
    # SR-WORK-REGISTRY (2026-09-22, W-211) owns `tests/test_doc_registry.py`
    # and no code, exactly like SR-WORK-DOCS above. Its subject is **what a
    # registry row owes** — a trigger, a last-verified date, a live target —
    # which is a claim about documents, so no change under `src/` can make a
    # row of it true or false. ⚠ It is also the record that ATE the file it
    # governs: `work/DOC-REGISTRY.md` was retired into its own §3 (Arpit,
    # 2026-09-22), so the rules and the data are now one document and the test
    # reads a section of a record rather than a file of its own.
    "SR-WORK-REGISTRY",
    # SR-WORK-TESTDATA (2026-09-22) owns `tests/test_test_data_prompts.py` and
    # no code. Its subject is **what test data must contain**, which is a claim
    # about seed documents and question sets, so no change under `src/` can
    # make it true or false -- the same reason as SR-WORK-REGISTRY above.
    "SR-WORK-TESTDATA",
    # SR-WORK-GOLDEN (2026-09-15) owns three components and not one of them
    # is under `src/`: the PreToolUse hook that guards the sealed answer key,
    # the generator behind `CLAUDE.md`'s view of the prohibition, and the test
    # that binds the two. Its subject is **who may read a file**, so no change
    # to the engine can make it true or false — the SR-WORK-OPEN-QUEUE case,
    # not the SR-ANSWER one. It is unreachable only by THIS set's question,
    # which asks whether a change under `src/` can demand a record.
    "SR-WORK-GOLDEN",
    # SR-LAW-11 (2026-09-15) is the sealed-answer-key prohibition, and it owns
    # no `src/` component for the same reason its process record SR-WORK-GOLDEN
    # owns none: its subject is **who may read a directory**, enforced outside
    # the engine by a PreToolUse hook, a deny rule, `.gitignore` and the
    # generated law block. No change under `src/` can make the law true or
    # false, so the freshness gate cannot reach it — the SR-WORK-OPEN-QUEUE
    # case, not the SR-ANSWER one.
    "SR-LAW-11",
}


def _records_with_no_src_component() -> set[str]:
    from sr_lib import describes_table, ownership_table

    covered: dict[str, set[str]] = {}
    for component, record in ownership_table().items():
        covered.setdefault(record, set()).add(component)
    for component, records in describes_table().items():
        for record in records:
            covered.setdefault(record, set()).add(component)
    return {
        name
        for name in _record_names()
        if not any(c.startswith("src/") for c in covered.get(name, ()))
    }


def _record_names() -> set[str]:
    names = set()
    for path in sorted(SR_DIR.glob("0*.md")):
        for line in path.read_text(encoding="utf-8").splitlines()[:12]:
            if line.startswith("name:"):
                names.add(line.split(":", 1)[1].strip().strip('"'))
                break
    return names


def test_the_set_of_gate_unreachable_records_is_exactly_this() -> None:
    """A record gaining or losing gate coverage must be seen, not inferred."""
    actual = _records_with_no_src_component()
    assert actual == _UNREACHABLE_BY_THE_GATE, (
        "the set of records no code change can open has moved.\n"
        f"  newly unreachable: {sorted(actual - _UNREACHABLE_BY_THE_GATE)}\n"
        f"  newly reachable:   {sorted(_UNREACHABLE_BY_THE_GATE - actual)}\n\n"
        "Newly reachable is good news — delete it from the pin. Newly "
        "unreachable means a record arrived that no change to src/ can ever "
        "demand, which is the SR-ANSWER defect: give it a describes row, or "
        "add it here with the reason it genuinely owns no code."
    )


def test_archived_content_is_reachable_now() -> None:
    """W-126's own fix, asserted rather than assumed.

    The record was unreachable while the change amending it was being written.
    """
    assert "SR-ARCHIVED-CONTENT" not in _records_with_no_src_component()
