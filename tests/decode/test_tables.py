"""W-287 stage A — every value under its TRUE column name.

One test per defect W-287 named, by number — the defects are stated in
[SR-TABULAR](../../records/0150_tabular.md) decision 8. Fixtures are built here, as `test_formats.py` builds its own, so
the input sits beside the assertion.

The assertions read the decoded Markdown back as `{column: value}` rather than
matching whole strings: the claim is attribution, and a test of attribution
that broke on a padding change would stop being run.
"""

from __future__ import annotations

from l12_fixtures import config_file
from l12_fixtures import configured_root, tune_text, write_config, write_tune

from fux.decode import decode
from fux.text.chunk import chunk

from test_formats import _SS, zf
from l12_fixtures import chunk_bounds


def _records(markdown: str) -> list[dict[str, str]]:
    """The first Markdown table in `markdown`, as one dict per data row."""
    lines = [line for line in markdown.split("\n") if line.startswith("|")]
    split = lambda line: [c.strip().replace("\\|", "|") for c in line.strip().strip("|").split(" | ")]
    header = split(lines[0])
    return [dict(zip(header, split(line))) for line in lines[2:]]


def _book(sheet: str, *, shared: list[str] = (), styles: str = "", workbook_pr: str = "") -> bytes:
    parts = {
        "xl/workbook.xml": f'<?xml version="1.0"?><workbook xmlns="{_SS}">{workbook_pr}'
        '<sheets><sheet name="Owners"/></sheets></workbook>',
        "xl/worksheets/sheet1.xml": f'<?xml version="1.0"?><worksheet xmlns="{_SS}">{sheet}</worksheet>',
    }
    if shared:
        parts["xl/sharedStrings.xml"] = (
            f'<?xml version="1.0"?><sst xmlns="{_SS}">'
            + "".join(f"<si><t>{s}</t></si>" for s in shared)
            + "</sst>"
        )
    if styles:
        parts["xl/styles.xml"] = f'<?xml version="1.0"?><styleSheet xmlns="{_SS}">{styles}</styleSheet>'
    return zf(parts)


def _s(ref: str, text: str) -> str:
    return f"<c r='{ref}' t='inlineStr'><is><t>{text}</t></is></c>"


# -- 1 · xlsx: a cell sits at its ADDRESS ----------------------------------


def test_defect_1_a_sparse_xlsx_row_keeps_every_value_under_its_column():
    """Excel OMITS an empty cell. Appending `<c>` elements in order put row 3's
    `open` under `Owner`, because the blank `Owner` cell was not there to push it
    right."""
    sheet = (
        "<sheetData>"
        f"<row r='1'>{_s('A1', 'Ticket')}{_s('B1', 'Owner')}{_s('C1', 'Status')}</row>"
        f"<row r='2'>{_s('A2', 'INC1')}{_s('B2', 'Alice')}{_s('C2', 'closed')}</row>"
        f"<row r='3'>{_s('A3', 'INC2')}{_s('C3', 'open')}</row>"
        "</sheetData>"
    )
    rows = _records(decode(_book(sheet), "owners.xlsx", configured_root()))
    assert rows[1] == {"Ticket": "INC2", "Owner": "", "Status": "open"}


def test_defect_1_a_table_that_starts_in_column_c_carries_no_empty_columns():
    sheet = (
        "<sheetData>"
        f"<row r='2'>{_s('C2', 'Ticket')}{_s('D2', 'Owner')}</row>"
        f"<row r='3'>{_s('C3', 'INC1')}{_s('D3', 'Alice')}</row>"
        "</sheetData>"
    )
    out = decode(_book(sheet), "owners.xlsx", configured_root())
    assert "| Ticket | Owner |" in out
    assert _records(out) == [{"Ticket": "INC1", "Owner": "Alice"}]


# -- 2 · xlsx: dates and booleans as people write them ---------------------

_STYLES = (
    '<numFmts count="1"><numFmt numFmtId="164" formatCode="dd&quot;/&quot;mmm&quot;/&quot;yyyy"/></numFmts>'
    "<cellStyleXfs><xf numFmtId='14'/></cellStyleXfs>"
    "<cellXfs>"
    "<xf numFmtId='0'/>"  # s=0: General
    "<xf numFmtId='14'/>"  # s=1: built-in date
    "<xf numFmtId='164'/>"  # s=2: custom date
    "<xf numFmtId='20'/>"  # s=3: built-in h:mm
    "<xf numFmtId='22'/>"  # s=4: built-in datetime
    "<xf numFmtId='164'/>"  # s=5: custom date again
    "</cellXfs>"
)


def _dated(cells: str, **kw) -> dict[str, str]:
    header = "".join(_s(f"{c}1", c) for c in "ABCDEFG")
    sheet = f"<sheetData><row r='1'>{header}</row><row r='2'>{cells}</row></sheetData>"
    return _records(decode(_book(sheet, styles=_STYLES, **kw), "d.xlsx", configured_root()))[0]


def test_defect_2_a_dated_cell_reads_as_an_iso_date_not_a_serial():
    row = _dated(
        "<c r='A2' s='1'><v>46214</v></c>"
        "<c r='B2' s='2'><v>46214</v></c>"
        "<c r='C2' s='3'><v>0.6041666666666666</v></c>"
        "<c r='D2' s='4'><v>46214.5</v></c>"
        "<c r='E2' t='b'><v>1</v></c>"
        "<c r='F2' t='b'><v>0</v></c>"
        "<c r='G2' s='0'><v>1.0000000000000001E-1</v></c>"
    )
    assert row == {
        "A": "2026-07-11",
        "B": "2026-07-11",
        "C": "14:30",
        "D": "2026-07-11 12:00",
        "E": "true",
        "F": "false",
        "G": "0.1",
    }


def test_defect_2_a_1904_workbook_counts_from_1904():
    row = _dated("<c r='A2' s='1'><v>0</v></c>", workbook_pr='<workbookPr date1904="1"/>')
    assert row["A"] == "1904-01-01"


def test_defect_2_the_1900_leap_day_that_never_existed_stays_a_number():
    """Serial 60 is 1900-02-29 — Lotus's bug, which Excel kept. Inventing a date
    for it would be a value the sheet never held."""
    assert _dated("<c r='A2' s='1'><v>60</v></c>")["A"] == "60"
    assert _dated("<c r='A2' s='1'><v>59</v></c>")["A"] == "1900-02-28"
    assert _dated("<c r='A2' s='1'><v>61</v></c>")["A"] == "1900-03-01"


def test_defect_2_an_undated_number_is_its_shortest_decimal():
    row = _dated("<c r='A2'><v>3.0</v></c><c r='B2'><v>12</v></c><c r='C2'><v>2.5</v></c>")
    assert (row["A"], row["B"], row["C"]) == ("3", "12", "2.5")


# -- 3 · the header is the header, not the first row -----------------------


def test_defect_3_an_xlsx_title_banner_is_prose_not_the_header():
    """The banner is merged across the top. Its words used to be the column name
    of every cell below it, and the real header became a data row."""
    sheet = (
        "<sheetData>"
        f"<row r='1'>{_s('A1', 'Q3 on-call roster')}</row>"
        f"<row r='3'>{_s('A3', 'Ticket')}{_s('B3', 'Owner')}{_s('C3', 'Status')}</row>"
        f"<row r='4'>{_s('A4', 'INC1')}{_s('B4', 'Alice')}{_s('C4', 'open')}</row>"
        "</sheetData><mergeCells><mergeCell ref='A1:C1'/></mergeCells>"
    )
    out = decode(_book(sheet), "roster.xlsx", configured_root())
    assert "## Owners\n\nQ3 on-call roster\n\n| Ticket | Owner | Status |" in out
    assert _records(out) == [{"Ticket": "INC1", "Owner": "Alice", "Status": "open"}]


def test_defect_3_a_merged_data_cell_repeats_into_its_span():
    sheet = (
        "<sheetData>"
        f"<row r='1'>{_s('A1', 'Team')}{_s('B1', 'Owner')}</row>"
        f"<row r='2'>{_s('A2', 'SRE')}{_s('B2', 'Alice')}</row>"
        f"<row r='3'>{_s('B3', 'Bob')}</row>"
        "</sheetData><mergeCells><mergeCell ref='A2:A3'/></mergeCells>"
    )
    rows = _records(decode(_book(sheet), "t.xlsx", configured_root()))
    assert rows == [{"Team": "SRE", "Owner": "Alice"}, {"Team": "SRE", "Owner": "Bob"}]


def test_defect_3_at_one_percent_the_first_row_is_the_header_as_before(tmp_path):
    """`[limits.xlsx] header_fill_percent = 1` is the pre-W-287 behaviour: any
    non-blank row reaches it, so the first one is the header."""
    formats = config_file(tmp_path, "formats")
    formats.write_text("[limits.xlsx]\nheader_fill_percent = 1\n", encoding="utf-8")
    write_config(tmp_path)
    sheet = (
        "<sheetData>"
        f"<row r='1'>{_s('A1', 'Q3 on-call roster')}</row>"
        f"<row r='2'>{_s('A2', 'Ticket')}{_s('B2', 'Owner')}</row>"
        "</sheetData>"
    )
    out = decode(_book(sheet), "roster.xlsx", tmp_path)
    assert out.split("\n")[2].startswith("| Q3 on-call roster |")


def test_defect_3_the_row_budget_counts_rows_below_the_header(tmp_path):
    """SR-TABULAR decision 3: the number a consumer writes is DATA rows. A banner
    above the header is neither header nor data and spends nothing."""
    write_tune(tmp_path, tune_text(index={"max_table_rows": 2}))
    write_config(tmp_path)
    rows = "".join(f"<row r='{i + 3}'>{_s(f'A{i + 3}', f'v{i}')}{_s(f'B{i + 3}', 'x')}</row>" for i in range(3))
    sheet = (
        f"<sheetData><row r='1'>{_s('A1', 'Banner')}</row>"
        f"<row r='2'>{_s('A2', 'Key')}{_s('B2', 'Val')}</row>{rows}</sheetData>"
    )
    out = decode(_book(sheet), "t.xlsx", tmp_path)
    assert [r["Key"] for r in _records(out)] == ["v0", "v1"]
    assert "table truncated" in out


def test_defect_3_an_html_thead_is_the_header_even_with_a_banner_first_row():
    html = (
        b"<table><thead><tr><th>Ticket</th><th>Owner</th></tr></thead>"
        b"<tbody><tr><td>INC1</td><td>Alice</td></tr></tbody></table>"
    )
    assert _records(decode(html, "a.html", configured_root())) == [{"Ticket": "INC1", "Owner": "Alice"}]


def test_defect_3_an_html_table_without_th_finds_its_header_by_fill():
    html = (
        b"<table><tr><td>Quarterly summary</td></tr>"
        b"<tr><td>Name</td><td>Q1</td><td>Q2</td></tr><tr><td>a</td><td>1</td><td>2</td></tr></table>"
    )
    out = decode(html, "a.html", configured_root())
    assert "Quarterly summary\n\n| Name | Q1 | Q2 |" in out
    assert _records(out) == [{"Name": "a", "Q1": "1", "Q2": "2"}]


# -- 4 · HTML spans, captions and nested tables ----------------------------


def test_defect_4_html_colspan_and_rowspan_expand_by_repeating_the_value():
    html = (
        b"<table><thead><tr><th rowspan=2>Team</th><th colspan=2>Contact</th></tr>"
        b"<tr><th>Name</th><th>Phone</th></tr></thead><tbody>"
        b"<tr><td rowspan=2>SRE</td><td>Alice</td><td>123</td></tr>"
        b"<tr><td>Bob</td><td>456</td></tr></tbody></table>"
    )
    rows = _records(decode(html, "a.html", configured_root()))
    assert rows == [
        {"Team": "SRE", "Contact Name": "Alice", "Contact Phone": "123"},
        {"Team": "SRE", "Contact Name": "Bob", "Contact Phone": "456"},
    ]


def test_defect_4_a_caption_is_the_tables_heading():
    html = b"<h2>Owners</h2><table><caption>On-call</caption><tr><th>a</th></tr><tr><td>1</td></tr></table>"
    out = decode(html, "a.html", configured_root())
    assert "## Owners\n\n### On-call\n\n| a |" in out


def test_defect_4_a_nested_table_is_flattened_into_its_cell_not_lost():
    """A `<table>` inside a cell reset the parser's table state: every outer row
    read so far was dropped, and the outer table's tail became a new table."""
    html = (
        b"<table><tr><th>Team</th><th>Notes</th></tr>"
        b"<tr><td>SRE</td><td>pager<table><tr><td>x</td><td>y</td></tr></table></td></tr>"
        b"<tr><td>DB</td><td>none</td></tr></table>"
    )
    rows = _records(decode(html, "a.html", configured_root()))
    assert rows == [{"Team": "SRE", "Notes": "pager x y"}, {"Team": "DB", "Notes": "none"}]


def test_defect_4_a_pipe_inside_an_html_cell_no_longer_adds_a_column():
    html = b"<table><tr><th>pair</th><th>n</th></tr><tr><td>B | B-node</td><td>60</td></tr></table>"
    assert _records(decode(html, "a.html", configured_root())) == [{"pair": "B | B-node", "n": "60"}]


# -- 5 · docx spans --------------------------------------------------------

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _tc(text: str, props: str = "") -> str:
    return f"<w:tc><w:tcPr>{props}</w:tcPr><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:tc>"


def _docx(body: str) -> bytes:
    return zf({"word/document.xml": f'<?xml version="1.0"?><w:document xmlns:w="{_W}"><w:body>{body}</w:body></w:document>'})


def test_defect_5_docx_gridspan_and_vmerge_keep_cells_under_their_columns():
    body = (
        "<w:tbl>"
        f"<w:tr>{_tc('Team')}{_tc('Owner')}{_tc('Status')}</w:tr>"
        f"<w:tr>{_tc('SRE', '<w:vMerge w:val=\"restart\"/>')}{_tc('Alice')}{_tc('open')}</w:tr>"
        f"<w:tr>{_tc('', '<w:vMerge/>')}{_tc('Bob, Carol', '<w:gridSpan w:val=\"2\"/>')}</w:tr>"
        "</w:tbl>"
    )
    rows = _records(decode(_docx(body), "a.docx", configured_root()))
    assert rows == [
        {"Team": "SRE", "Owner": "Alice", "Status": "open"},
        {"Team": "SRE", "Owner": "Bob, Carol", "Status": "Bob, Carol"},
    ]


def test_defect_5_a_nested_docx_table_is_read_once_inside_its_cell():
    inner = f"<w:tbl><w:tr>{_tc('x')}{_tc('y')}</w:tr></w:tbl>"
    body = (
        "<w:tbl>"
        f"<w:tr>{_tc('Team')}{_tc('Notes')}</w:tr>"
        f"<w:tr>{_tc('SRE')}<w:tc><w:p><w:r><w:t>pager</w:t></w:r></w:p>{inner}</w:tc></w:tr>"
        "</w:tbl>"
    )
    out = decode(_docx(body), "a.docx", configured_root())
    assert _records(out) == [{"Team": "SRE", "Notes": "pager x y"}]
    assert out.count("|---|") == 1, "the nested table was emitted again as a table of its own"


# -- 6 · a Markdown table without edge pipes is still a table --------------


def test_defect_6_a_pipeless_gfm_table_splits_one_row_per_passage():
    md = "# Owners\n\nTicket | Owner\n--- | ---\nINC1 | Alice\nINC2 | Bob\n"
    passages = chunk(md, **chunk_bounds(), line_numbers=True, frontmatter=False)
    rows = [p for p in passages if "INC" in p.text]
    assert len(rows) == 2
    assert all(p.text.startswith("# Owners\n\nTicket | Owner\n--- | ---\n") or p.text.startswith("Ticket | Owner\n--- | ---\n") for p in rows)
    assert (rows[1].line_start, rows[1].line_end) == (6, 6)


def test_defect_6_a_lone_rule_or_a_prose_pipe_is_not_a_table():
    md = "# Notes\n\nfirst line\n---\nthird | line\n"
    passages = chunk(md, **chunk_bounds(), line_numbers=True, frontmatter=False)
    assert len(passages) == 1


# -- the round-trip gate: what the ONE emitter writes, the chunker reads back --


def _grid_rows(markdown: str) -> list[tuple[str, ...]]:
    """Every row passage's values, as `text/chunk.py` parses them back."""
    passages = chunk(markdown, **chunk_bounds(), line_numbers=False, frontmatter=False)
    return [p.row.values for p in passages if p.row is not None]


def test_round_trip_every_format_reads_back_the_grid_it_wrote():
    """W-287 stage A's handshake with stage B: `_table.emit` writes a table, and
    `_table_bands` must read back exactly its cells — per format, because one
    defect in the shared emitter reaches all four at once. A cell holding `|`
    is in every format, so the escape is on the path every time."""
    want = [("INC1", "Alice | A", "open"), ("INC2", "Bob", "closed")]
    header = ("Ticket", "Owner", "Status")

    csv = ("Ticket,Owner,Status\n" + "".join(",".join(r) + "\n" for r in want)).encode()
    sheet = (
        "<sheetData>"
        + f"<row r='1'>{_s('A1', 'Ticket')}{_s('B1', 'Owner')}{_s('C1', 'Status')}</row>"
        + "".join(
            f"<row r='{n}'>" + "".join(_s(f"{c}{n}", v) for c, v in zip("ABC", row)) + "</row>"
            for n, row in enumerate(want, start=2)
        )
        + "</sheetData>"
    )
    html = (
        "<table><thead><tr>" + "".join(f"<th>{h}</th>" for h in header) + "</tr></thead><tbody>"
        + "".join("<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>" for row in want)
        + "</tbody></table>"
    ).encode()
    docx = _docx(
        "<w:tbl>"
        + "<w:tr>" + "".join(_tc(h) for h in header) + "</w:tr>"
        + "".join("<w:tr>" + "".join(_tc(v) for v in row) + "</w:tr>" for row in want)
        + "</w:tbl>"
    )
    root = configured_root()
    for name, raw in [("t.csv", csv), ("t.xlsx", _book(sheet)), ("t.html", html), ("t.docx", docx)]:
        assert _grid_rows(decode(raw, name, root)) == want, name
