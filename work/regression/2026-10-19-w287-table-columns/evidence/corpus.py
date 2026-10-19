#!/usr/bin/env python3
"""W-287's tabular corpus and its questions — seeded, deterministic, generated.

    python3 corpus.py <out-dir>

writes `<out-dir>/docs/**` (the corpus) and `<out-dir>/questions.jsonl` (the
questions, each with its answer). Same seed, same bytes: no clock, no set
order, zip entries stamped with a fixed time. `sha256` of every file is
printed so the pre-registration can freeze the corpus by hash.

**Not a golden set.** The answers come from the generator that wrote the
corpus, as in SR-TABULAR's run (`work/regression/2026-09-06-csv-chunk-
granularity/`), so L11 does not reach them and every number is `informed`.

## What it carries — SR-WORK-TESTDATA, and SR-RS decision 23

Every shape the work item names, so the feature can move it (T1):

| shape | where | defect / mechanism |
|---|---|---|
| sparse `.xlsx` rows, dated cells, a merged title banner | `tickets-2026q2.xlsx` | A1, A2-xlsx, A4 |
| `<thead>`, `<caption>`, `colspan`/`rowspan` | `tickets-net.html` | A2 |
| pipe-less GFM table | `hosts.md` | A5 |
| `gridSpan` / `vMerge` | `oncall.docx` | A3 |
| `Field \\| Value` property sheets, `.md` and `.xlsx` | `service-*.md`, `services.xlsx` | B5 |
| key columns, column-naming questions | every ticket table | B3, B4 |
| prose that shares the tables' vocabulary | `runbooks/*.md` | collateral (C2) |

**Headroom by construction (T3), never by ranking.** Each table question has a
DECOY row built to beat the answer row on term counts at baseline, and the
generator records the count that makes it so:

- **F1 key lookup** (`owner of INC520014`): the decoy row's notes carry the key
  twice and the question's column word once; the answer row carries the key
  once. Higher tf on every query term, rows of matched length.
- **F3 column filter** (`payments with status blocked`): the decoy rows share
  the service and say the status word twice in their notes; the answer row's
  Status cell says it once.
- **F4 record field** (`payments pager`): the decoy row's value says the field
  word twice; the answer row names it once, as its field.
- **F2 combination** (SR-TABULAR's set B shape): common terms, only the
  combination identifies the row; no decoy, no column named. Reported in the
  slice; no mechanism is aimed at it.

Prose questions (`P`) are answered by a runbook passage that shares words with
table rows; they are the slice's complement, where only collateral can show.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import random
import sys
import zipfile
from pathlib import Path

SEED = 287
ZIP_TIME = (2026, 1, 1, 0, 0, 0)

OWNERS = ["Aarav", "Bina", "Chetan", "Divya", "Esha", "Farhan", "Gauri", "Hari",
          "Ira", "Jai", "Kavya", "Lalit", "Meera", "Nikhil", "Oviya", "Pranav"]
SERVICES = ["payments", "ledger", "search", "billing", "auth",
            "catalog", "shipping", "invoices", "reports", "gateway"]
STATUSES = ["open", "closed", "blocked", "pending", "resolved"]
FILLER = ["followed up with vendor", "waiting on change window", "rollback tested in staging",
          "root cause in config drift", "customer informed by support", "monitoring added after fix",
          "patch shipped to canary", "capacity raised for the weekend", "alert threshold tuned",
          "postmortem scheduled for friday", "handover notes in the channel", "retry storm after deploy"]

#: Column word a question uses -> the column it names, and the phrasings.
F1_FORMS = {
    "Owner": ["owner of {k}", "{k} owner", "who is the owner of {k}"],
    "Status": ["status of {k}", "{k} status", "what is the status of {k}"],
    "Raised": ["when was {k} raised", "{k} raised on", "raised date for {k}"],
    "Service": ["service for {k}", "{k} service", "which service is {k} raised against"],
}
COLUMN_WORD = {"Owner": "owner", "Status": "status", "Raised": "raised", "Service": "service"}
HEADER = ["Ticket", "Owner", "Status", "Service", "Raised", "Notes"]

FIELDS = ["Owner", "Pager", "Tier", "Region", "Runbook", "Escalation", "Dashboard"]
FIELD_WORD = {"Owner": "owner", "Pager": "pager", "Tier": "tier", "Region": "region",
              "Dashboard": "dashboard"}


def _filler(rng: random.Random) -> str:
    return rng.choice(FILLER)


def _date(rng: random.Random, quarter: int) -> dt.date:
    start = dt.date(2026, 3 * (quarter - 1) + 1, 1)
    return start + dt.timedelta(days=rng.randrange(0, 89))


def ticket_table(rng: random.Random, prefix: str, quarter: int, n: int = 40):
    """`(rows, questions)` for one ticket tracker: `n` rows, keyed `prefix`."""
    keys = [f"{prefix}{rng.randrange(1000, 9999):04d}{i:02d}" for i in range(n)]
    rows = []
    for key in keys:
        rows.append({
            "Ticket": key, "Owner": rng.choice(OWNERS), "Status": rng.choice(STATUSES),
            "Service": rng.choice(SERVICES), "Raised": _date(rng, quarter), "Notes": _filler(rng),
        })
    questions = []
    used: set[int] = set()

    def pick(exclude: set[int]) -> int:
        while True:
            i = rng.randrange(n)
            if i not in exclude:
                return i

    # F1 — eight key lookups, two per column; each takes a decoy row of its own.
    for column in ["Owner", "Status", "Raised", "Service"] * 2:
        answer = pick(used)
        used.add(answer)
        decoy = pick(used)
        used.add(decoy)
        key = rows[answer]["Ticket"]
        form = rng.choice(F1_FORMS[column])
        word = COLUMN_WORD[column]
        # The decoy names the key twice and the column word once; its filler is
        # cut so the row is no longer than the answer row's.
        rows[decoy]["Notes"] = f"{word} for {key} rechecked, see {key}"
        questions.append({
            "family": "F1", "question": form.format(k=key), "row": answer, "column": column,
            "construction": {"decoy_row": decoy, "key_tf": [1, 2], f"{word}_tf": [1, 2]},
        })

    # F3 — four column filters: (service, status) unique to the answer row, two
    # decoys in the same service saying the status word twice in their notes.
    for _ in range(4):
        answer = pick(used)
        used.add(answer)
        service = rows[answer]["Service"]
        status = rows[answer]["Status"]
        for i, row in enumerate(rows):
            if i != answer and row["Service"] == service and row["Status"] == status:
                row["Status"] = next(s for s in STATUSES if s != status)
        decoys = []
        for _ in range(2):
            d = pick(used)
            used.add(d)
            rows[d]["Service"] = service
            rows[d]["Status"] = next(s for s in STATUSES if s != status)
            rows[d]["Notes"] = f"{status} twice, {status} until vendor fix"
            decoys.append(d)
        questions.append({
            "family": "F3", "question": f"{service} with status {status}", "row": answer,
            "column": "Status",
            "construction": {"decoy_rows": decoys, f"{status}_tf": [1, 2]},
        })

    # F2 — three combinations: owner + service + status, unique to the row.
    for _ in range(3):
        answer = pick(used)
        used.add(answer)
        r = rows[answer]
        for i, row in enumerate(rows):
            if i != answer and (row["Owner"], row["Service"], row["Status"]) == (r["Owner"], r["Service"], r["Status"]):
                row["Owner"] = next(o for o in OWNERS if o != r["Owner"])
        questions.append({
            "family": "F2", "question": f"{r['Owner']} {r['Service']} {r['Status']}", "row": answer,
            "column": "Ticket", "construction": {"decoy_rows": []},
        })
    _check_tracker(rows, questions)
    return rows, questions, used


def _check_tracker(rows, questions) -> None:
    """Every construction claim, re-checked on the FINAL rows — a later step may
    have moved a cell an earlier question was built on. Fails loudly."""
    for q in questions:
        r = rows[q["row"]]
        c = q["construction"]
        if q["family"] == "F1":
            key = r["Ticket"]
            assert key not in r["Notes"], q
            assert rows[c["decoy_row"]]["Notes"].count(key) == 2, q
        elif q["family"] == "F3":
            same = [i for i, x in enumerate(rows) if (x["Service"], x["Status"]) == (r["Service"], r["Status"])]
            assert same == [q["row"]], (q, same)
            status = r["Status"]
            for d in c["decoy_rows"]:
                assert rows[d]["Service"] == r["Service"] and rows[d]["Notes"].count(status) == 2, q
            assert status not in r["Notes"], q
        elif q["family"] == "F2":
            triple = (r["Owner"], r["Service"], r["Status"])
            same = [i for i, x in enumerate(rows) if (x["Owner"], x["Service"], x["Status"]) == triple]
            assert same == [q["row"]], (q, same)


def md_table(header: list[str], rows: list[list[str]], *, edge_pipes: bool = True) -> str:
    cells = lambda r: [str(c).replace("|", "\\|") for c in r]
    if edge_pipes:
        lines = ["| " + " | ".join(cells(header)) + " |", "|" + "---|" * len(header)]
        lines += ["| " + " | ".join(cells(r)) + " |" for r in rows]
    else:
        lines = [" | ".join(cells(header)), " | ".join(["---"] * len(header))]
        lines += [" | ".join(cells(r)) for r in rows]
    return "\n".join(lines)


def _as_list(row: dict) -> list[str]:
    return [row[c].isoformat() if isinstance(row[c], dt.date) else row[c] for c in HEADER]


# -- formats ----------------------------------------------------------------


def write_csv(rows) -> bytes:
    out = io.StringIO()
    import csv

    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(HEADER)
    for row in rows:
        writer.writerow(_as_list(row))
    return out.getvalue().encode()


def _zip(parts: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        for name in sorted(parts):
            archive.writestr(zipfile.ZipInfo(name, date_time=ZIP_TIME), parts[name])
    return buf.getvalue()


_SS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _col(i: int) -> str:
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(ord("A") + r) + s
    return s


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(ref: str, text: str) -> str:
    return f"<c r='{ref}' t='inlineStr'><is><t>{_esc(text)}</t></is></c>"


def write_xlsx(sheets: list[tuple[str, str]], *, styles: bool) -> bytes:
    """`sheets` is `(name, sheetData+mergeCells xml)`; style 1 is a date."""
    parts = {
        "xl/workbook.xml": f'<?xml version="1.0"?><workbook xmlns="{_SS}"><sheets>'
        + "".join(f'<sheet name="{_esc(n)}"/>' for n, _ in sheets) + "</sheets></workbook>",
    }
    for i, (_name, body) in enumerate(sheets, start=1):
        parts[f"xl/worksheets/sheet{i}.xml"] = f'<?xml version="1.0"?><worksheet xmlns="{_SS}">{body}</worksheet>'
    if styles:
        parts["xl/styles.xml"] = (
            f'<?xml version="1.0"?><styleSheet xmlns="{_SS}">'
            "<cellXfs><xf numFmtId='0'/><xf numFmtId='14'/></cellXfs></styleSheet>"
        )
    return _zip(parts)


def xlsx_tickets(rows, banner: str, used: set[int]) -> str:
    """A tracker sheet: a merged banner in row 1, the header in row 3, Raised as
    a date serial with a date style, and EVERY fourth row's Owner left out
    (Excel omits an empty cell, so the row is sparse)."""
    epoch = dt.date(1899, 12, 30)
    out = [f"<row r='1'>{_inline('A1', banner)}</row>"]
    out.append("<row r='3'>" + "".join(_inline(f"{_col(i)}3", h) for i, h in enumerate(HEADER)) + "</row>")
    for n, row in enumerate(rows):
        r = n + 4
        cells = []
        for i, column in enumerate(HEADER):
            ref = f"{_col(i)}{r}"
            value = row[column]
            if column == "Owner" and n % 4 == 3 and n not in used:
                row["Owner"] = ""  # omitted: the cell is not in the XML at all
                continue
            if isinstance(value, dt.date):
                cells.append(f"<c r='{ref}' s='1'><v>{(value - epoch).days}</v></c>")
            else:
                cells.append(_inline(ref, value))
        out.append(f"<row r='{r}'>" + "".join(cells) + "</row>")
    return "<sheetData>" + "".join(out) + "</sheetData><mergeCells><mergeCell ref='A1:F1'/></mergeCells>"


def xlsx_record(fields: list[tuple[str, str]]) -> str:
    out = [f"<row r='1'>{_inline('A1', 'Field')}{_inline('B1', 'Value')}</row>"]
    for n, (f, v) in enumerate(fields, start=2):
        out.append(f"<row r='{n}'>{_inline(f'A{n}', f)}{_inline(f'B{n}', v)}</row>")
    return "<sheetData>" + "".join(out) + "</sheetData>"


def html_tickets(rows, caption: str) -> bytes:
    """`<thead>` with a two-row header (`Ticket` spanning both rows, `Detail`
    spanning Owner..Raised), a caption, and Notes."""
    head = (
        "<thead><tr><th rowspan='2'>Ticket</th><th colspan='4'>Detail</th><th rowspan='2'>Notes</th></tr>"
        "<tr><th>Owner</th><th>Status</th><th>Service</th><th>Raised</th></tr></thead>"
    )
    body = "".join(
        "<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in _as_list(r)) + "</tr>" for r in rows
    )
    return (
        "<html><head><title>Network incidents</title></head><body><h1>Network incidents</h1>"
        f"<p>Every network-side incident this quarter.</p><table><caption>{_esc(caption)}</caption>"
        f"{head}<tbody>{body}</tbody></table></body></html>"
    ).encode()


_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _tc(text: str, props: str = "") -> str:
    return f"<w:tc><w:tcPr>{props}</w:tcPr><w:p><w:r><w:t>{_esc(text)}</w:t></w:r></w:p></w:tc>"


def docx_oncall(rng: random.Random):
    """On-call rota: Team | Week | Primary | Secondary, Team merged vertically
    (`vMerge`) over its weeks. Returns `(bytes, rows, questions)`."""
    teams = ["edge", "core", "data", "mobile"]
    rows, xml = [], []
    xml.append(f"<w:tr>{_tc('Team')}{_tc('Week')}{_tc('Primary')}{_tc('Secondary')}</w:tr>")
    for team in teams:
        for j, week in enumerate(range(10, 14)):
            p, s = rng.sample(OWNERS, 2)
            rows.append({"Team": team, "Week": f"week {week}", "Primary": p, "Secondary": s})
            team_cell = _tc(team, '<w:vMerge w:val="restart"/>') if j == 0 else _tc("", "<w:vMerge/>")
            xml.append(f"<w:tr>{team_cell}{_tc(f'week {week}')}{_tc(p)}{_tc(s)}</w:tr>")
    doc = (
        f'<?xml version="1.0"?><w:document xmlns:w="{_W}"><w:body>'
        f'<w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr><w:r><w:t>On-call rota</w:t></w:r></w:p>'
        f"<w:tbl>{''.join(xml)}</w:tbl></w:body></w:document>"
    )
    picks = rng.sample(range(len(rows)), 4)
    questions = [
        {"family": "F1", "question": f"{rows[i]['Team']} {rows[i]['Week']} primary", "row": i,
         "column": "Primary", "construction": {"decoy_rows": []}}
        for i in picks
    ]
    return _zip({"word/document.xml": doc}), rows, questions


def hosts_md(rng: random.Random):
    """A pipe-less GFM table (A5): host | owner | region | role | notes."""
    rows = []
    for i in range(24):
        rows.append({"host": f"{rng.choice(['web', 'db', 'cache', 'queue'])}-{i:02d}",
                     "owner": rng.choice(OWNERS), "region": rng.choice(["eu", "us", "apac"]),
                     "role": rng.choice(["primary", "replica", "standby"]), "notes": _filler(rng)})
    questions = []
    used: set[int] = set()
    for column, word in [("owner", "owner"), ("region", "region"), ("role", "role"), ("owner", "owner")]:
        answer = rng.choice([i for i in range(24) if i not in used])
        used.add(answer)
        decoy = rng.choice([i for i in range(24) if i not in used])
        used.add(decoy)
        host = rows[answer]["host"]
        rows[decoy]["notes"] = f"{word} for {host} moved, see {host}"
        questions.append({"family": "F1", "question": f"{word} of {host}", "row": answer, "column": column,
                          "construction": {"decoy_row": decoy, "key_tf": [1, 2], f"{word}_tf": [1, 2]}})
    header = ["host", "owner", "region", "role", "notes"]
    text = "# Host inventory\n\nEvery host the platform team runs.\n\n" + md_table(
        header, [[r[c] for c in header] for r in rows], edge_pipes=False) + "\n"
    return text, rows, questions


def service_records(rng: random.Random):
    """Ten property sheets. Returns `{service: [(field, value)]}` and F4 questions."""
    sheets = {}
    for service in SERVICES:
        sheets[service] = [
            ("Owner", rng.choice(OWNERS)),
            ("Pager", f"{service}-oncall"),
            ("Tier", rng.choice(["gold", "silver", "bronze"])),
            ("Region", rng.choice(["eu", "us", "apac"])),
            ("Runbook", f"runbooks/{service}.md"),
            ("Escalation", "page the duty manager after 30 minutes"),
            ("Dashboard", f"grafana/{service}-overview"),
        ]
    questions = []
    pairs = [(s, f) for s in SERVICES for f in ("Owner", "Pager", "Tier", "Region", "Dashboard")]
    asked: dict[str, int] = {}
    chosen = []
    for service, field in rng.sample(pairs, len(pairs)):
        if asked.get(service, 0) < 2 and len(chosen) < 15:
            chosen.append((service, field))
            asked[service] = asked.get(service, 0) + 1
    seen: dict[str, int] = {}
    for service, field in chosen:
        word = FIELD_WORD[field]
        rows = sheets[service]
        # The decoy: a value that says the field word twice, in the same sheet —
        # its own decoy row per question (a service is asked at most twice).
        decoy_field = ["Escalation", "Runbook"][seen.get(service, 0)]
        seen[service] = seen.get(service, 0) + 1
        i = next(n for n, (f, _v) in enumerate(rows) if f == decoy_field)
        rows[i] = (decoy_field, f"{word} first, then the {word} rota")
        answer = next(n for n, (f, _v) in enumerate(rows) if f == field)
        form = rng.choice(["{s} {w}", "{w} for {s}", "{w} of the {s} service"])
        questions.append({"family": "F4", "service": service, "question": form.format(s=service, w=word),
                          "row": answer, "column": field,
                          "construction": {"decoy_row": i, f"{word}_tf": [1, 2]}})
    for q in questions:
        rows = sheets[q["service"]]
        word = FIELD_WORD[q["column"]]
        assert rows[q["construction"]["decoy_row"]][1].count(word) == 2, q
        assert word not in rows[q["row"]][1], q
    return sheets, questions


RUNBOOKS = {
    "payments": ("Rotating the payments pager", "The payments pager rotates every Monday at 09:00 IST and the outgoing owner hands over in the pay-ops channel."),
    "ledger": ("Ledger close", "Ledger close runs at 23:30 UTC; a blocked close is escalated to the finance duty manager, never retried by hand."),
    "search": ("Search reindex", "A full search reindex takes about forty minutes and is only started from the standby replica."),
    "billing": ("Billing disputes", "Billing disputes older than ninety days are closed by the support lead after a written notice."),
    "auth": ("Token signing keys", "Auth signing keys are rotated quarterly, and the old key stays valid for seven days after rotation."),
    "catalog": ("Catalog imports", "Catalog imports above fifty thousand items are split into batches by the import owner before upload."),
    "shipping": ("Carrier outages", "During a carrier outage shipping labels are queued, not cancelled, and the queue drains when the carrier recovers."),
    "invoices": ("Invoice numbering", "Invoice numbers are never reused; a voided invoice keeps its number with status void."),
    "reports": ("Report schedules", "Weekly reports are generated on Sunday night so the region leads read them first thing Monday."),
    "gateway": ("Gateway rate limits", "The gateway rate limit is raised only with a change ticket approved by the service owner."),
}
GENERAL = [
    ("incident-process", "Incident process", [
        ("Declaring an incident", "Anyone may declare an incident; the first responder becomes the owner until a commander is named."),
        ("Status updates", "During an incident the status page is updated every thirty minutes, even when nothing has changed."),
        ("Closing an incident", "An incident is closed only after the postmortem owner confirms the action items are filed."),
    ]),
    ("oncall-policy", "On-call policy", [
        ("Handover", "The primary hands over to the secondary at the end of each week, in writing, with every open ticket listed."),
        ("Pager fatigue", "If the pager fires more than ten times in one night the team lead reviews the alert thresholds the next day."),
        ("Swaps", "Rota swaps are agreed between the two engineers and recorded in the rota file before the week starts."),
    ]),
    ("change-policy", "Change policy", [
        ("Change windows", "Production changes go out in the Tuesday and Thursday windows unless the service owner approves an exception."),
        ("Rollback", "Every change carries a rollback plan that was tested in staging before the window opens."),
        ("Freeze", "The year-end change freeze starts on the fifteenth of December and blocks all non-emergency changes."),
    ]),
]


def prose(rng: random.Random):
    """Runbooks, one per service, and three policy documents. Returns `{path:
    text}` and the P questions, each answered by a phrase in one passage."""
    docs, questions = {}, []
    for service, (heading, sentence) in RUNBOOKS.items():
        text = (f"# {service} runbook\n\nOperational notes for the {service} service.\n\n"
                f"## {heading}\n\n{sentence}\n\n## Contacts\n\nSee the {service} property sheet for the owner and the pager.\n")
        docs[f"runbooks/{service}.md"] = text
        questions.append({"family": "P", "doc": f"docs/runbooks/{service}.md", "phrase": sentence[:48],
                          "question": _prose_question(service, heading)})
    for slug, title, sections in GENERAL:
        body = "".join(f"## {h}\n\n{s}\n\n" for h, s in sections)
        docs[f"runbooks/{slug}.md"] = f"# {title}\n\n{body}"
        for h, s in sections:
            questions.append({"family": "P", "doc": f"docs/runbooks/{slug}.md", "phrase": s[:48],
                              "question": _general_question(h)})
    return docs, questions


def _prose_question(service: str, heading: str) -> str:
    return {
        "payments": "when does the payments pager rotate",
        "ledger": "what happens when the ledger close is blocked",
        "search": "how long does a search reindex take",
        "billing": "who closes old billing disputes",
        "auth": "how often are auth signing keys rotated",
        "catalog": "how are large catalog imports split",
        "shipping": "what happens to shipping labels in a carrier outage",
        "invoices": "can a voided invoice number be reused",
        "reports": "when are weekly reports generated",
        "gateway": "who approves raising the gateway rate limit",
    }[service]


def _general_question(heading: str) -> str:
    return {
        "Declaring an incident": "who owns an incident before a commander is named",
        "Status updates": "how often is the status page updated during an incident",
        "Closing an incident": "when can an incident be closed",
        "Handover": "how does the primary hand over to the secondary",
        "Pager fatigue": "what happens if the pager fires too often at night",
        "Swaps": "how are on-call rota swaps recorded",
        "Change windows": "which days are the production change windows",
        "Rollback": "where is a change rollback plan tested",
        "Freeze": "when does the year-end change freeze start",
    }[heading]


def build(out: Path) -> list[dict]:
    rng = random.Random(SEED)
    docs: dict[str, bytes] = {}
    questions: list[dict] = []

    trackers = [
        ("tickets-2026q1.csv", "INC51", 1, "csv"),
        ("tickets-2026q2.xlsx", "INC52", 2, "xlsx"),
        ("tickets-ops.md", "CHG53", 3, "md"),
        ("tickets-net.html", "NET54", 4, "html"),
    ]
    for name, prefix, quarter, kind in trackers:
        rows, qs, used = ticket_table(rng, prefix, quarter)
        if kind == "csv":
            docs[name] = write_csv(rows)
            label = name
        elif kind == "xlsx":
            docs[name] = write_xlsx([("Incidents", xlsx_tickets(rows, "Q2 2026 incident tracker", used))], styles=True)
            label = "Incidents"
        elif kind == "md":
            docs[name] = ("# Operations changes\n\nEvery change ticket this quarter.\n\n"
                          + md_table(HEADER, [_as_list(r) for r in rows]) + "\n").encode()
            label = "Operations changes"
        else:
            docs[name] = html_tickets(rows, "Network incident log")
            label = "Network incident log"
        for q in qs:
            q.update(doc=f"docs/{name}", table=label, ordinal=q["row"] + 1,
                     answer_key=rows[q["row"]]["Ticket"], column_index=HEADER.index(q["column"]))
        questions += qs

    text, rows, qs = hosts_md(rng)
    docs["hosts.md"] = text.encode()
    for q in qs:
        q.update(doc="docs/hosts.md", table="Host inventory", ordinal=q["row"] + 1, answer_key=rows[q["row"]]["host"],
                 column_index=["host", "owner", "region", "role", "notes"].index(q["column"]))
    questions += qs

    raw, rows, qs = docx_oncall(rng)
    docs["oncall.docx"] = raw
    for q in qs:
        q.update(doc="docs/oncall.docx", table="On-call rota", ordinal=q["row"] + 1, answer_key=rows[q["row"]]["Week"],
                 column_index=["Team", "Week", "Primary", "Secondary"].index(q["column"]))
    questions += qs

    sheets, qs = service_records(rng)
    md_services = SERVICES[:5]
    for service in md_services:
        docs[f"service-{service}.md"] = (f"# {service} service\n\n"
                                        + md_table(["Field", "Value"], [list(p) for p in sheets[service]]) + "\n").encode()
    docs["services.xlsx"] = write_xlsx([(s, xlsx_record(sheets[s])) for s in SERVICES[5:]], styles=False)
    for q in qs:
        service = q.pop("service")
        if service in md_services:
            q.update(doc=f"docs/service-{service}.md", table=f"{service} service")
        else:
            q.update(doc="docs/services.xlsx", table=service)
        # A record row's cells are its one `(field, value)` pair: index 0.
        q.update(ordinal=q["row"] + 1, answer_key=sheets[service][q["row"]][0], column_index=0)
    questions += qs

    prose_docs, qs = prose(rng)
    for path, text in prose_docs.items():
        docs[path] = text.encode()
    questions += qs

    # Permute, then number — no id band carries a family (A11's rule, borrowed).
    rng.shuffle(questions)
    for n, q in enumerate(questions, start=1):
        q["id"] = f"w287-{n:03d}"
        q["slice"] = q["family"] != "P"
    root = out / "docs"
    for path in sorted(docs):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(docs[path])
    with (out / "questions.jsonl").open("w", encoding="utf-8") as fh:
        for q in questions:
            fh.write(json.dumps(q, sort_keys=True, default=str) + "\n")
    return questions


def main() -> int:
    out = Path(sys.argv[1])
    questions = build(out)
    for path in sorted(p for p in out.rglob("*") if p.is_file()):
        print(hashlib.sha256(path.read_bytes()).hexdigest(), path.relative_to(out).as_posix())
    families: dict[str, int] = {}
    for q in questions:
        families[q["family"]] = families.get(q["family"], 0) + 1
    print("questions", len(questions), json.dumps(families, sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
