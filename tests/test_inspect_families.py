"""W-228 — the `families` lens: documents grouped by shape, their misfits, their singletons.

A planted corpus, built as an `IndexView` so the lens is exercised exactly and
nothing depends on ingest: three families of five (ADRs, runbooks, dated
release notes), one misfit in each — five, because a heading 4 of 5 members
carry clears `core_share` and 3 of 4 does not — one singleton, and one
document with no headings. The
exact heading-SET families `duplication()` has always reported must come out
of this corpus unchanged — this lens generalises them and replaces nothing.
"""

from __future__ import annotations

import json
import random
from array import array
from types import SimpleNamespace

from fux.inspect import _scan, lenses
from l12_fixtures import inspect_template

ADR = ["Context", "Decision", "Consequences", "Alternatives"]
RUNBOOK = ["Symptoms", "Diagnosis", "Steps", "Rollback"]
RELEASE = ["Release 2026-09-01", "Added", "Changed", "Fixed"]

#: id -> (headings, front-matter key names, body tokens)
PLANT: dict[str, tuple[list[str], list[str], int]] = {
    "file:adr/0001.md": (ADR, ["status", "date"], 900),
    "file:adr/0002.md": (ADR, ["status", "date"], 1200),
    "file:adr/0003.md": (ADR + ["Notes"], ["status", "date"], 800),   # an extra heading still belongs
    "file:adr/0004.md": (ADR, ["status", "date"], 700),
    "file:adr/0005.md": (["Context", "Consequences", "Alternatives"], ["status", "date"], 600),  # MISFIT: no Decision
    "file:ops/disk.md": (RUNBOOK, ["owner"], 300),
    "file:ops/cpu.md": (RUNBOOK, ["owner"], 350),
    "file:ops/net.md": (RUNBOOK, ["owner"], 320),
    "file:ops/io.md": (RUNBOOK, ["owner"], 310),
    "file:ops/mem.md": (["Symptoms", "Diagnosis", "Rollback"], ["owner"], 280),  # MISFIT: no Steps
    "file:notes/r1.md": (RELEASE, [], 150),
    "file:notes/r2.md": (["Release 2026-09-08", "Added", "Changed", "Fixed"], [], 160),  # the date is masked
    "file:notes/r3.md": (["Release 2026-09-15", "Added", "Changed", "Fixed"], [], 170),
    "file:notes/r4.md": (["Release 2026-09-22", "Added", "Fixed"], [], 140),  # MISFIT: no Changed
    "file:notes/r5.md": (["Release 2026-09-29", "Added", "Changed", "Fixed"], [], 155),
    "file:misc/essay.md": (["A long argument", "Why", "So what"], [], 5000),   # SINGLETON
    "file:data/rows.csv": ([], [], 90),                                        # no headings
}


def _view(order: list[str]):
    view = _scan.IndexView(config=inspect_template())
    for doc_id in order:
        headings, _meta, body = PLANT[doc_id]
        view.docs.append(_scan.Doc(
            id=doc_id, loc=doc_id.split(":", 1)[1], title=doc_id, sha="0" * 40, src="git",
            mode="extracted", archived=False, superseded=False, flen=(body, len(headings), 1, 1),
            nterms=0, phrases=tuple(headings), edges_out=0,
        ))
        view.doc_terms.append(array("q"))
    return view


def _facts():
    return SimpleNamespace(by_id={i: {"meta_keys": sorted(m)} for i, (_h, m, _b) in PLANT.items()})


def _run(order=None):
    return lenses.families(_view(order or sorted(PLANT)), _facts(), top_lists=50)


def test_three_families_each_named_by_its_shared_skeleton():
    out = _run()
    by_first = {f["members"][0]: f for f in out.families}
    assert out.family_count == 3
    assert by_first["file:adr/0001.md"]["size"] == 5
    assert by_first["file:ops/cpu.md"]["size"] == 5
    assert by_first["file:notes/r1.md"]["size"] == 5, "a dated template is ONE shape once digits are masked"
    assert by_first["file:adr/0001.md"]["name"].startswith("Context · Decision")
    assert by_first["file:adr/0001.md"]["shared_meta_keys"] == ["date", "status"]
    assert by_first["file:adr/0001.md"]["folders"] == ["adr/"]


def test_one_misfit_per_family_with_the_missing_heading_named():
    out = _run()
    missing = {m["id"]: m["missing"] for m in out.misfits}
    assert missing == {
        "file:adr/0005.md": ["Decision"],
        "file:ops/mem.md": ["Steps"],
        "file:notes/r4.md": ["Changed"],
    }
    assert "file:adr/0003.md" not in missing, "an EXTRA heading is not a missing one"


def test_a_singleton_is_listed_and_a_headingless_document_is_not_a_shape():
    out = _run()
    assert out.singletons == ["file:misc/essay.md"]
    assert out.no_headings == ["file:data/rows.csv"]
    assert out.documents_in_a_family == 15


def test_the_misfit_share_is_flagged_only_above_its_provisional_floor():
    out = _run()
    assert out.misfit_share == 3 / 15
    assert out.misfit_flagged is (3 / 15 > inspect_template().misfit_floor)


def test_the_exact_set_families_are_unchanged():
    """`duplication()`'s heading-SET families are what `--diff` and the Index tab
    have always read (W-228 §6): same names, same members, byte for byte."""
    dup = lenses.duplication(_view(sorted(PLANT)), top_lists=50)
    assert dup.families == [   # largest first, as `duplication()` has always sorted them
        (" · ".join(sorted(RUNBOOK)), ["file:ops/cpu.md", "file:ops/disk.md", "file:ops/io.md", "file:ops/net.md"]),
        (" · ".join(sorted(ADR)), ["file:adr/0001.md", "file:adr/0002.md", "file:adr/0004.md"]),
    ]


def test_the_report_is_a_function_of_the_corpus_not_of_the_order():
    """L4: shuffled input order, byte-equal output."""
    base = json.dumps(_run().__dict__, sort_keys=True, default=str)
    rng = random.Random(0)
    for _ in range(5):
        order = sorted(PLANT)
        rng.shuffle(order)
        assert json.dumps(_run(order).__dict__, sort_keys=True, default=str) == base


def test_diff_names_families_gained_lost_and_renamed():
    """DoD 6: `--diff` reports what moved in the families each report lists."""
    from fux.inspect import diff as diff_mod

    def report(*families):
        return {"documents": [], "corpus": {}, "families": {"families": [
            {"name": name, "members": members} for name, members in families
        ]}}

    a = report(("ADRs", ["a1", "a2"]), ("Runbooks", ["r1", "r2"]), ("Old", ["o1", "o2"]))
    b = report(("ADR · Decision", ["a1", "a2"]), ("Runbooks", ["r1", "r2"]), ("New", ["n1", "n2"]))
    assert diff_mod.compare(a, b)["families"] == {
        "gained": ["New"],
        "lost": ["Old"],
        "renamed": [["ADRs", "ADR · Decision"]],
    }
