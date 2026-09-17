"""`fux inspect` on a PLANTED corpus — each lens must name its plant and
nothing else.

⚠ **Named `test_inspect_verb.py`, not `test_inspect.py`.** `tests/` already has
a `test_inspect.py` and neither tree carries an `__init__.py`, so two modules
with one basename make `pytest tests tests_e2e` fail at COLLECTION — an error
that reads like a broken import and is a file name.

**Why a planted corpus and not this repository.** A lens that reports plausible
numbers on a real corpus is unfalsifiable: nobody knows what the right answer
is, so every output looks like a finding. Here the answer is known because it
was put there — one plant per lens, each designed so exactly one lens should
name it — and the assertion is *this lens found mine, and did not find
anybody else's*.

**The plants** (`_planted`):

| plant | file(s) | the lens that must name it |
|---|---|---|
| a word on every document | `zqboilerplate` in all of them | boilerplate |
| a document with no distinctive term | `filler.md` — nothing but the shared words | findability |
| two near-identical documents | `twin-a.md`, `twin-b.md` | duplication |
| three documents with one heading SET | `tpl-1/2/3.md` | duplication (families) |
| a document the index knows only by name | `nameonly.md` — stopwords only | analyzer coverage |
| a document with no edge | `lonely.md` | graph |

The corpus is otherwise ordinary prose with links, so the lenses have something
to be right about besides the plants.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

#: On every document. Nonsense on purpose: a real word would collide with the
#: prose below and the plant would stop being the only term at `df == n`.
BOILER = "zqboilerplate"

#: ⚠ **The corpus has to be big enough for *distinctive* to mean anything.**
#: A term is distinctive at `df <= 10 % of n` (SR-INSPECT decision 8), so on a
#: 13-document corpus the bound is 1.3 and *distinctive* collapses to *hapax* —
#: which made both twins come out **unfindable**, correctly and uselessly, on
#: the first version of this fixture. Twenty-four documents puts the bound at
#: 2.4, so a word the two twins share is still distinctive and the two plants
#: stop interfering.
_SUBJECTS = (
    "ranking saturation length normalisation weighted fields",
    "fetching acquisition digests verification owning systems",
    "chunking passages paragraph boundaries rescoring windows",
    "hooks commits merge drivers reconciliation staging",
    "daemon staleness schedules deferred reindexing background",
    "postings dictionaries impacts blocks skipping",
    "ledger fronts coding prefixes suffixes",
    "edges grades extraction ambiguity inference",
    "communities labels propagation neighbourhoods walks",
    "decoders extensions bindings registries consumers",
    "refusals paywalls shells signatures walls",
    "redaction patterns checksums groups replacements",
    "receipts provenance journals consent surfaces",
    "accelerators segments manifests stamps mmap",
    "confidence bands separation coverage abstention",
    "enrichment questions pinning regeneration backlogs",
    "expansion vocabulary synonyms gaps analysts",
    "tunables weights parameters defaults overrides",
)


def _run(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=check,
    )


def _planted(root: Path) -> None:
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = root / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    dirs.write_text("docs\n", encoding="utf-8")
    (root / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    docs = root / "docs"
    docs.mkdir()

    for i, subject in enumerate(_SUBJECTS):
        head = subject.split()[0]
        (docs / f"s{i:02d}-{head}.md").write_text(
            f"# {head.title()}\n\n{BOILER} A passage about {subject} and how they behave.\n",
            encoding="utf-8",
        )

    # PLANT -- findability. Nothing but words that are on every document: the
    # heading, the body and **the file name** are all `BOILER`, so there is no
    # term a query can select it by. ⚠ The file name matters: the first version
    # called this `filler.md`, and `filler` was a hapax path token, which made
    # the document perfectly findable by the name of the plant.
    (docs / f"{BOILER}.md").write_text(f"# {BOILER}\n\n{BOILER} {BOILER} {BOILER}\n", encoding="utf-8")

    # PLANT -- duplication. A long shared body and one short difference, so the
    # exact Jaccard clears 0.80. ⚠ The first version differed by one sentence
    # on a 16-term body and came out at 16/22 = 0.73 -- a true negative for a
    # pair that was meant to be a plant.
    shared = (
        f"{BOILER} Saturation and length normalisation interact through the free parameters "
        "which the tunables file exposes to an operator directly, and the weighting applied "
        "to every field is resolved once at query time rather than stored anywhere in the "
        "committed plane, because a stored number that is a function of a tunable drifts "
        "silently whenever somebody edits the file that decides it.\n"
    )
    (docs / "twin-first.md").write_text(f"# Twin\n\n{shared}", encoding="utf-8")
    (docs / "twin-second.md").write_text(f"# Twin\n\n{shared}\nPlus one closing remark.\n", encoding="utf-8")

    # PLANT -- template family. One heading SET, three fillings.
    for i, filling in enumerate(("alpha", "beta", "gamma"), start=1):
        (docs / f"tpl-{i}.md").write_text(
            f"# Context\n\n{BOILER} {filling} context\n\n"
            f"## Decision\n\n{filling} decision\n\n"
            f"## Consequences\n\n{filling} consequences\n",
            encoding="utf-8",
        )

    # PLANT -- analyzer coverage. Stopwords only, and no heading, so nothing
    # but the path reaches the index.
    (docs / "nameonly.md").write_text("the and or but if in of to\n", encoding="utf-8")

    # PLANT -- graph. Every other document links into the web below; this one
    # is linked from nowhere and links nowhere.
    (docs / "lonely.md").write_text(
        f"# Lonely\n\n{BOILER} An isolated passage about nothing in particular whatsoever.\n",
        encoding="utf-8",
    )
    (docs / "web.md").write_text(
        f"# Web\n\n{BOILER} see [ranking](s00-ranking.md), [fetching](s01-fetching.md) and "
        "[chunking](s02-chunking.md)\n",
        encoding="utf-8",
    )


@pytest.fixture()
def planted(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    _planted(tmp_path)
    setup = _run(tmp_path, "setup", "--no-agents", check=False)
    assert setup.returncode == 0, setup.stderr
    # `fux setup` writes `.fux/sources/dirs` write-if-missing; the plant above
    # already wrote it, so the value under test is the planted one.
    ingest = _run(tmp_path, "ingest", check=False)
    assert ingest.returncode == 0, ingest.stderr
    return tmp_path


def _report(root: Path) -> dict:
    result = _run(root, "inspect", "--json", "--retrieval-sample", "0", check=False)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


# --------------------------------------------------------------------------
# each lens names its plant


def test_the_boilerplate_lens_names_the_word_that_is_on_everything(planted):
    payload = _report(planted)
    top = payload["boilerplate"]["top"]
    assert top, payload["boilerplate"]
    # ⚠ **Two things this deliberately does NOT assert.**
    #
    # *That the plant sorts first.* `docs` and `md` are path tokens on every
    # single document, so their `df` is `n` and the plant's is `n - 1` -- the
    # one document without it is `nameonly.md`, which has to stay content-free
    # to be its own lens's plant. Two terms at the same `df` are ordered by
    # their hash, deliberately, so the report is a function of the corpus and
    # not of dict order.
    #
    # *That the share is exactly 1.0.* It is 26 of 27, and a fixture bent to
    # make it 27 of 27 would have broken the coverage plant.
    rows = {row["word"].lower(): row["share"] for row in top[:3]}
    assert BOILER in rows, [(row["word"], row["share"]) for row in top[:6]]
    assert rows[BOILER] > 0.95, rows


def test_the_findability_lens_names_the_document_with_no_distinctive_term(planted):
    payload = _report(planted)
    unfindable = payload["findability"]["unfindable"]
    assert f"file:docs/{BOILER}.md" in unfindable, unfindable
    # And nobody else's plant: the twins, the template family and the orphan
    # all carry distinctive vocabulary, which is what makes this a plant for
    # ONE lens rather than a property of the whole fixture.
    for other in ("twin-first", "twin-second", "tpl-1", "lonely", "s00-ranking"):
        assert f"file:docs/{other}.md" not in unfindable, (other, unfindable)


def test_the_duplication_lens_names_the_twins_and_only_the_twins(planted):
    payload = _report(planted)
    pairs = {frozenset((row["a"], row["b"])) for row in payload["duplication"]["near_duplicates"]}
    assert frozenset(("file:docs/twin-first.md", "file:docs/twin-second.md")) in pairs, pairs
    # The three template documents share a heading set and differ in body, so
    # they are a FAMILY and must not also be reported as near duplicates —
    # that is the distinction the two halves of this lens exist to draw.
    for i in (1, 2, 3):
        for j in (1, 2, 3):
            if i < j:
                assert frozenset((f"file:docs/tpl-{i}.md", f"file:docs/tpl-{j}.md")) not in pairs


def test_the_duplication_lens_names_the_template_family(planted):
    payload = _report(planted)
    families = payload["duplication"]["families"]
    members = [set(f["members"]) for f in families]
    wanted = {"file:docs/tpl-1.md", "file:docs/tpl-2.md", "file:docs/tpl-3.md"}
    assert wanted in members, families


def test_the_coverage_lens_names_the_document_the_index_knows_only_by_name(planted):
    payload = _report(planted)
    assert payload["coverage"]["no_content"] == ["file:docs/nameonly.md"], payload["coverage"]


def test_the_graph_lens_names_the_document_with_no_edge(planted):
    payload = _report(planted)
    orphans = payload["graph"]["orphans"]
    assert "file:docs/lonely.md" in orphans, orphans
    assert "file:docs/web.md" not in orphans, orphans


def test_the_length_lens_reports_a_percentile_for_every_field(planted):
    payload = _report(planted)
    assert set(payload["lengths"]["fields"]) == {"body", "heading", "title", "path", "ctx"}
    assert set(payload["lengths"]["body_tokens"]) == {"min", "p10", "p50", "p90", "max"}


# --------------------------------------------------------------------------
# the contracts: nothing committed, deterministic, every lever real


def test_inspect_leaves_git_status_clean(planted):
    """Decision 15's whole claim. `inspect` reads the index and adds nothing a
    consumer would have to decide whether to commit."""
    _run(planted, "add", "-A", check=False)  # no-op: `fux add` is the SOURCES verb
    subprocess.run(["git", "add", "-A"], cwd=planted, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "planted"],
        cwd=planted,
        check=True,
        capture_output=True,
    )
    before = subprocess.run(
        ["git", "status", "--porcelain"], cwd=planted, capture_output=True, text=True, check=True
    ).stdout
    assert before == "", before

    _report(planted)

    after = subprocess.run(
        ["git", "status", "--porcelain"], cwd=planted, capture_output=True, text=True, check=True
    ).stdout
    assert after == "", f"`fux inspect` dirtied the tree:\n{after}"


def test_the_report_is_byte_identical_twice(planted):
    """L3. A wall-clock line would break this, which is why there is none."""
    first = _run(planted, "inspect", "--retrieval-sample", "0", check=False)
    assert first.returncode == 0, first.stderr
    second = _run(planted, "inspect", "--retrieval-sample", "0", check=False)
    assert second.returncode == 0, second.stderr
    assert first.stdout == second.stdout

    written = (planted / ".fux" / "runtime" / "inspect" / "report.md").read_text(encoding="utf-8")
    assert written in first.stdout


def test_a_rebuilt_dictionary_produces_the_same_report(planted):
    """The cached dictionary and a freshly built one must agree, or the cache
    is a second source of truth about the corpus's vocabulary."""
    cached = _run(planted, "inspect", "--retrieval-sample", "0", check=False).stdout
    rebuilt = _run(
        planted, "inspect", "--retrieval-sample", "0", "--rebuild-dictionary", check=False
    ).stdout
    assert cached == rebuilt


def test_every_finding_printed_carries_a_lever(planted):
    from fux.inspect.lenses import LEVERS

    payload = _report(planted)
    for section in ("boilerplate", "findability", "duplication", "coverage", "graph"):
        assert payload[section]["lever"] in LEVERS.values(), section
    assert payload["levers"] == dict(sorted(LEVERS.items()))


def test_inspect_exits_zero_even_when_a_check_is_flagged(planted):
    """Decision 10. A flag is *attention*; the planted corpus is deliberately
    bad and the command still succeeds."""
    result = _run(planted, "inspect", "--retrieval-sample", "0", check=False)
    assert result.returncode == 0, result.stderr
    payload = _report(planted)
    assert any(check["flagged"] for check in payload["checks"]), payload["checks"]


def test_the_floors_print_the_word_provisional(planted):
    result = _run(planted, "inspect", "--retrieval-sample", "0", check=False)
    assert "provisional" in result.stdout


def test_inspect_refuses_nothing_and_reports_when_there_is_no_index(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".fux").mkdir()
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    result = _run(tmp_path, "inspect", check=False)
    assert result.returncode == 1
    assert "fux ingest" in result.stderr


# --------------------------------------------------------------------------
# PII — the dictionary is built from REDACTED text, like the index


def test_the_dictionary_never_names_a_value_pii_toml_redacts(tmp_path):
    """🔴 **The one way this verb could leak.**

    The dictionary exists because the committed index holds hashes rather than
    words, and it is built by re-tokenising the sources. Built from RAW bytes it
    would name exactly the values `pii.toml` exists to remove — in a report, on
    disk, under a hash the index does not even carry, because `[PII:name]` is
    what ingest hashed. So the redaction phase is imported and applied first,
    to the body and to the frontmatter title both.
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    sources = tmp_path / ".fux" / "sources"
    sources.mkdir(parents=True)
    (sources / "dirs").write_text("docs\n", encoding="utf-8")
    (tmp_path / ".fux" / "pii.toml").write_text(
        '[[rule]]\nname = "secret"\npattern = "hunter2zzz"\n', encoding="utf-8"
    )
    docs = tmp_path / "docs"
    docs.mkdir()
    # In the body, and in the frontmatter title -- the third source of
    # committed vocabulary, and the one that was unredacted until W-140 row 2.
    (docs / "leaky.md").write_text(
        "---\ntitle: the hunter2zzz runbook\n---\n# Leaky\n\nThe password is hunter2zzz today.\n",
        encoding="utf-8",
    )
    setup = _run(tmp_path, "setup", "--no-agents", check=False)
    assert setup.returncode == 0, setup.stderr
    (sources / "dirs").write_text("docs\n", encoding="utf-8")
    ingest = _run(tmp_path, "ingest", check=False)
    assert ingest.returncode == 0, ingest.stderr
    report = _run(tmp_path, "inspect", "--retrieval-sample", "0", check=False)
    assert report.returncode == 0, report.stderr

    dictionary = (tmp_path / ".fux" / "runtime" / "inspect" / "dictionary.json").read_text(
        encoding="utf-8"
    )
    assert "hunter2zzz" not in dictionary, "the local dictionary named a redacted value"
    assert "hunter2zzz" not in report.stdout, "the report printed a redacted value"
    # And the placeholder's own terms ARE named, which is the proof that the
    # dictionary was built from the same text the index was.
    assert "pii" in dictionary.lower()
