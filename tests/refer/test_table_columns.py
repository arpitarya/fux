"""W-287 stages B and C — a table answers by row AND by column.

`[ranking] table_column_weight` above zero scores a ROW passage on three fields
(B2), lets a query term that names a column select that column's cell (B3),
folds the row's key value into its heading (B4) and reads `Field | Value`
tables as records (B5). At zero — the template's value until its pre-registered
run decides otherwise — none of it runs, and **G0** below is that claim.
"""

from __future__ import annotations

import dataclasses

from l12_fixtures import chunk_bounds, scoring, template_tune

from fux.refer._assemble import assemble
from fux.refer._rescore import rescore
from fux.text.chunk import chunk

TICKETS = (
    "# Tickets\n\n"
    "| Ticket | Owner | Status | Notes |\n|---|---|---|---|\n"
    "| INC1 | Alice | closed | reopened once, still open questions |\n"
    "| INC2 | Bob | open | none |\n"
    "| INC3 | Carol | closed | see INC2 |\n"
    "| INC4 | Dan | closed | open source dependency |\n"
)
PROPS = "# Service\n\n| Field | Value |\n|---|---|\n| Owner | Erin |\n| Pager | sre-oncall |\n| Tier | gold |\n"
PROSE = "# Notes\n\nThe owner of INC2 is Bob, and its status is open.\n"


def _passages(text: str, generated: bool = False):
    return chunk(text, **chunk_bounds(), line_numbers=not generated, frontmatter=False)


def _scored(query: str, docs: dict[str, str], column_weight: float):
    candidates = [
        (f"file:{loc}", loc, "sha", _passages(text, generated=loc.endswith(".xlsx")))
        for loc, text in docs.items()
    ]
    return rescore(
        query,
        candidates,
        scoring=scoring(),
        weight=0.0,
        proximity=template_tune().proximity,
        column_weight=column_weight,
    )


def _top(query: str, docs: dict[str, str], column_weight: float):
    return _scored(query, docs, column_weight)[0]


def test_the_template_ships_the_mechanism_off():
    """It is a ranking change, so it ships only through its standing bar (L13)."""
    assert template_tune().table_column_weight == 0.0


def test_g0_at_zero_a_row_scores_exactly_as_a_passage_without_a_row():
    """**G0** of the pre-registration. With the key at zero, the row metadata a
    passage now carries moves no score, no order and no locator: every result is
    byte-identical to scoring the same passages with `row` stripped — which is
    the pre-W-287 passage, field for field."""
    docs = {"tickets.md": TICKETS, "props.md": PROPS, "notes.md": PROSE}
    for query in ("status open", "owner of INC2", "INC2", "pager", "gold tier"):
        with_rows = _scored(query, docs, 0.0)
        stripped = rescore(
            query,
            [
                (f"file:{loc}", loc, "sha", [dataclasses.replace(p, row=None) for p in _passages(text)])
                for loc, text in docs.items()
            ],
            scoring=scoring(),
            weight=0.0,
            proximity=template_tune().proximity,
            column_weight=0.0,
        )
        assert [(s.locator, s.score) for s in with_rows] == [(s.locator, s.score) for s in stripped], query
        assert all(s.columns_matched == () for s in with_rows), "the selector ran with the mechanism off"


def test_b2_a_non_row_passage_scores_the_same_at_any_column_weight():
    """Column names ride in the `ctx` slot, which a non-row passage never fills,
    so only `avg_wlen` can move under it — and with no row in the set, nothing."""
    off = _scored("owner status open", {"notes.md": PROSE}, 0.0)
    on = _scored("owner status open", {"notes.md": PROSE}, 2.5)
    assert [(s.locator, s.score) for s in off] == [(s.locator, s.score) for s in on]


def test_b3_a_query_that_names_a_column_prefers_the_row_whose_cell_says_it():
    """*"status open"*: `INC2`'s Status cell says `open`; `INC1` and `INC4` say it
    only in their notes. Off, the three are within a few hundredths."""
    top = _top("status open", {"tickets.md": TICKETS}, 1.0)
    assert dict(top.passage.cells)["Ticket"] == "INC2"
    assert top.columns_matched == ("Status",)


def test_b4_the_key_column_names_its_row_above_a_row_that_mentions_it():
    """`INC3`'s notes say *see INC2*. Off, the two rows are nearly tied; the key
    value in the heading field separates them."""
    off = _scored("INC2", {"tickets.md": TICKETS}, 0.0)
    on = _scored("INC2", {"tickets.md": TICKETS}, 1.0)
    assert dict(on[0].passage.cells)["Ticket"] == "INC2"
    margin_off = off[0].score - off[1].score
    margin_on = on[0].score - on[1].score
    assert margin_on > 10 * margin_off


def test_b4_the_key_is_the_leftmost_column_distinct_in_every_row():
    rows = [p.row for p in _passages(TICKETS) if p.row is not None]
    assert {r.key for r in rows} == {0}
    dup = "# T\n\n| Team | Host |\n|---|---|\n| sre | web-1 |\n| sre | web-2 |\n| db | db-1 |\n"
    assert {p.row.key for p in _passages(dup) if p.row is not None} == {1}


def test_b5_a_field_value_table_is_a_record_and_its_rows_name_their_field():
    top = _top("pager", {"props.md": PROPS}, 1.0)
    assert top.passage.row.record
    assert top.passage.cells == (("Pager", "sre-oncall"),)
    assert top.columns_matched == ("Pager",)
    assert top.passage.row.key == 0, "a record's distinct field names are its key"


def test_b5_a_record_row_named_by_the_query_beats_a_row_whose_value_repeats_it():
    """*"payments pager"* — the `Escalation` row says `pager` twice in its value;
    the `Pager` row names the field once. Off, the repeat wins; on, the field
    name is the row's key and is scored as its heading."""
    props = (
        "# payments\n\n| Field | Value |\n|---|---|\n| Owner | Erin |\n"
        "| Pager | pay-oncall |\n| Escalation | page the pager rota, pager first |\n"
    )
    off = _top("payments pager", {"payments.md": props}, 0.0)
    on = _top("payments pager", {"payments.md": props}, 1.0)
    assert off.passage.cells == (("Escalation", "page the pager rota, pager first"),)
    assert on.passage.cells == (("Pager", "pay-oncall"),)


def test_b5_a_two_column_table_of_records_is_not_a_property_sheet():
    """`Ticket | Owner` is a list of tickets: reading it as a property sheet would
    drop both column names. Only a generic header (`Field | Value`) is a record."""
    two = "# T\n\n| Ticket | Owner |\n|---|---|\n| INC1 | Alice |\n| INC2 | Bob |\n"
    rows = [p.row for p in _passages(two) if p.row is not None]
    assert not any(r.record for r in rows)
    assert rows[0].cells == (("Ticket", "INC1"), ("Owner", "Alice"))


def test_c2_the_asked_cell_prints_first():
    scored = _scored("owner of INC2", {"tickets.md": TICKETS}, 1.0)
    bundle = assemble(scored, budget=4000, source="fetched", per_doc_fraction=0.5, citation_overhead=0)
    c = bundle.citations[0]
    assert c.record()[0] == ("Owner", "Bob", True)
    assert [col for col, _v, _a in c.record()] == ["Owner", "Ticket", "Status", "Notes"]


def test_c3_a_spreadsheet_row_is_cited_by_sheet_and_row():
    sheet = "## Owners\n\n| Ticket | Owner |\n|---|---|\n| INC7 | Gail |\n| INC8 | Hana |\n"
    top = _top("Hana", {"book.xlsx": sheet}, 0.0)
    assert top.locator == "book.xlsx#Owners!R2"


def test_c3_a_csv_row_keeps_its_line_range():
    csv = "# owners.csv\n\n| Ticket | Owner |\n|---|---|\n| INC7 | Gail |\n| INC8 | Hana |\n"
    assert _top("Hana", {"owners.csv": csv}, 0.0).locator == "owners.csv:L6-L6"


def test_c3_a_sheet_locator_moves_no_order_among_tied_rows():
    """🔴 The run's G0 gate found it: rescore and assemble broke equal scores on
    the DISPLAYED locator, so C3's `book.xlsx#Sheet!R12` reordered identically
    scored rows — and changed which one the budget seated — with the key off.
    Ties now break on the positional `order_key`, so stripping every row (and
    with it every sheet locator) moves nothing."""
    sheet = "".join(
        f"## s{i}\n\n| Field | Value |\n|---|---|\n| Dashboard | grafana/s{i} |\n| Tier | gold |\n\n"
        for i in range(12)
    )
    docs = {"book.xlsx": sheet}
    with_rows = _scored("dashboard", docs, 0.0)
    stripped = rescore(
        "dashboard",
        [("file:book.xlsx", "book.xlsx", "sha", [dataclasses.replace(p, row=None) for p in _passages(sheet, True)])],
        scoring=scoring(),
        weight=0.0,
        proximity=template_tune().proximity,
        column_weight=0.0,
    )
    assert len({s.score for s in with_rows[:12]}) == 1, "precondition: twelve rows tie"
    assert [s.passage.ordinal for s in with_rows] == [s.passage.ordinal for s in stripped]
    small = dict(budget=120, source="fetched", per_doc_fraction=1.0, citation_overhead=0)
    assert [c.ordinal for c in assemble(with_rows, **small).citations] == [
        c.ordinal for c in assemble(stripped, **small).citations
    ]
