"""Passage scoring on the fetched bytes.

**One scorer, not two.** This reuses `query/bm25f.py` — weight-then-saturate
once, never a per-field BM25 summed. Writing a second scorer for passages is
how the index and the refer plane end up disagreeing about what "relevant"
means, and the disagreement surfaces as an answer whose top citation is not the
top document.

The corpus statistics are the *passage set's*, not the index's, and that is
deliberate: the question here is "which part of these documents answers the
query", which is a different question from "which document answers it". The
index already answered the second one — that is what produced the candidates.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from ..constants import fixed
from ..text.analyzer import analyze
from ..query.bm25f import Scoring, derive_wlen, score_record
from ..query.rerank import Proximity, passage_boost
from ..query.scan import query_term_hashes
from ..text.tokenize import tokenize
from ..text.chunk import Passage

__all__ = ["ScoredPassage", "rescore"]

#: W-287 C3 — a spreadsheet's rows are cited `book.xlsx#Sheet!R12`: the
#: extensions the `.xlsx` decoder claims, read from where that decoder reads them.
_SHEET_SUFFIXES = tuple(fixed("decoders.xlsx", "extensions"))


@dataclass(frozen=True)
class ScoredPassage:
    """A passage with its score and the document it came from."""

    doc_id: str
    loc: str
    sha: str
    passage: Passage
    score: float
    #: W-287 B3 — the columns a query term NAMED, in column order: the cell an
    #: answer prints first. Empty when none was named or the mechanism is off.
    columns_matched: tuple[str, ...] = ()

    @property
    def nbytes(self) -> int:
        return self.passage.nbytes

    @property
    def locator(self) -> str:
        """A citable address an agent can act on: `path:L12-L40`.

        **W-76 Phase 5 changed this from `path#p3`.** An agent acts on a
        citation by opening a file at a line; a passage ordinal forced a
        second call to work out which lines those were. The ordinal survives
        as `passage.ordinal` and in the `--json` payload (never MCP, which
        addresses spans by line number and does no chunking), because it is
        stable across a reflow that moves every line number — which is exactly
        when a stored citation would otherwise point somewhere else silently.

        Falls back to the ordinal form when a passage carries no line range,
        which is the case for a passage built by something other than the
        chunker. A wrong line number is worse than an honest ordinal.

        **A spreadsheet row is `book.xlsx#Sheet!R12`** (W-287 C3, SR-ANSWER
        decision 9): the sheet and the data row, from 1, header not counted. The
        decoded Markdown's line numbers exist nowhere, and `#p12` names nothing
        a person can open; a sheet and a row are what Excel can.
        """
        table = self.passage.table
        if table is not None and self.loc.lower().endswith(_SHEET_SUFFIXES):
            return f"{self.loc}#{table[0]}!R{table[1]}"
        return self.order_key

    @property
    def order_key(self) -> str:
        """What a tie between equal scores is broken on: the positional locator,
        `path:L12-L40` or `path#p3`, for EVERY passage.

        🔴 **Never the displayed locator.** W-287's C3 changed how a spreadsheet
        row is *cited*; breaking ties on that string reordered rows that score
        identically — and, where the budget cut a tie, changed WHICH row was
        cited — with the ranking key off. Found by the run's G0 gate
        (`work/regression/2026-10-19-w287-table-columns/`). A citation's address
        is presentation and may not move an order.
        """
        if self.passage.line_start and self.passage.line_end:
            return f"{self.loc}:L{self.passage.line_start}-L{self.passage.line_end}"
        return f"{self.loc}#p{self.passage.ordinal}"


def rescore(
    query: str,
    candidates: list[tuple[str, str, str, list[Passage]]],
    *,
    scoring: Scoring,
    weight: float,
    proximity: Proximity,
    column_weight: float,
) -> list[ScoredPassage]:
    """Score every passage of every fetched document against the query.

    `candidates` is `(doc_id, loc, sha, passages)` per fetched document.
    Returns every passage scored, sorted by `(-score, locator)` — ties break on
    the locator, never on iteration order, because the assembler downstream
    must be able to promise byte-identical output.

    ## `weight` is the reranker's, and it is the SAME constant (W-108)

    BM25 over a passage is still a bag of words: a passage that says the
    question back and a passage that scatters the same words over forty lines
    score identically. `query/rerank.py` already fixed exactly this for
    *documents*, with a bounded multiplicative uplift over `passage_boost` —
    and `boost()` already chunks a document with **this plane's chunker** to do
    it. So the passage the reranker scored and the passage `answer` cites are
    the same object, and the arithmetic that ranked the first may as well score
    the second.

    **One constant, not a second knob.** `weight` is `[ranking]
    rerank_weight` — the value `_maybe_rerank` is passed — not a new
    `[refer]` key. Two knobs for one signal is how they drift apart, and the
    first day they disagree, `answer` cites a passage the ranking did not
    prefer for a reason nobody can name.

    ⚠ **It is therefore OFF wherever `rerank_weight` is.** The template ships
    `0.0`, the uplift is `1 + 0 * x`,
    and every bundle is byte-identical to the one this function produced before
    W-108 — proved by
    `tests/refer/test_rescore.py::test_weight_zero_is_byte_identical_to_the_unweighted_score`.
    Whether that default moves is Arpit's open call, listed under *Blocked on
    Arpit*; W-108 is not allowed to move it and does not.

    ## `column_weight` — a table row by row AND by column (W-287 stage B)

    `[ranking] table_column_weight`. **`0.0` is OFF, and off is the pre-W-287
    path, untouched**: every passage goes through `_terms_of` and nothing else
    runs. Above zero, a ROW passage (`passage.row`) is scored on three fields
    instead of two — `_row_terms` — and gains the column selector's bonus,
    `_selector`. A passage that is not a row is scored exactly as before, at
    any value; only the passage set's `avg_wlen` moves under it.
    """
    hashes = query_term_hashes(query)
    if not hashes:
        return []
    # Analyzed once per call, not once per passage: `passage_boost` is called
    # for every passage of every fetched document, and re-analyzing the query
    # inside that loop would be the same work three-to-thirty times over.
    query_terms = analyze(query) if weight > 0 else []
    tables = column_weight > 0
    if tables:
        scoring = _with_columns(scoring, column_weight)

    rows: list[tuple[str, str, str, Passage, dict[str, list[int]], int]] = []
    df: dict[str, int] = {}
    total_wlen = 0

    for doc_id, loc, sha, passages in candidates:
        for passage in passages:
            if tables and passage.row is not None:
                terms, flen = _row_terms(passage)
            else:
                terms, flen = _terms_of(passage)
            rows.append((doc_id, loc, sha, passage, terms, flen))
            total_wlen += derive_wlen(flen, scoring)
            for term in terms:
                df[term] = df.get(term, 0) + 1

    if not rows:
        return []
    n = len(rows)
    avg_wlen = total_wlen / n if n else 0.0

    scored = []
    for doc_id, loc, sha, passage, terms, flen in rows:
        score = score_record(terms, flen, hashes, df, n, avg_wlen, scoring)
        matched: tuple[str, ...] = ()
        if tables and passage.row is not None:
            bonus, matched = _selector(passage.row, hashes, df, n, avg_wlen, scoring)
            if bonus:
                score += bonus
        scored.append(
            ScoredPassage(
                doc_id=doc_id,
                loc=loc,
                sha=sha,
                passage=passage,
                score=_uplift(score, query_terms, passage, weight, proximity),
                columns_matched=matched,
            )
        )
    scored.sort(key=lambda s: (-s.score, s.order_key))
    return scored


def _uplift(
    score: float, query_terms: list[str], passage: Passage, weight: float, proximity: Proximity
) -> float:
    """The bounded multiplicative uplift, or the score untouched.

    **Multiplicative, exactly as `rerank.rerank` does it**, and for its reason:
    a proximity signal in `[0, 1]` and a BM25 score are on unrelated scales, so
    *adding* them lets proximity outweigh a real term match on any corpus where
    BM25 happens to score low. `weight` bounds what a perfect match may add.

    The early return is not an optimisation — it is the byte-identity
    guarantee. At `weight <= 0` this function is the identity on `score`, with
    no float arithmetic performed at all, so no last-bit difference can enter a
    bundle on a repo that never turned the reranker on.
    """
    if weight <= 0:
        return score
    return score * (1.0 + weight * passage_boost(query_terms, analyze(passage.text), proximity))


def _terms_of(passage: Passage) -> tuple[dict[str, list[int]], int]:
    """`{hash: [tf_heading, tf_body]}` and the passage's length, its own fields.

    A passage's *heading* is its heading line and its *body* is its text, which
    is the same two-field shape the index uses — so the weights carry over
    unchanged rather than being re-picked here.
    """
    from .. import store as store_mod

    from ..store import TF_FIELDS

    body_i = TF_FIELDS.index("body")
    heading_i = TF_FIELDS.index("heading")
    width = len(TF_FIELDS)

    # A passage has exactly two of the five fields: its own heading and its own
    # text. `title`, `path` and `ctx` are document-level and would be identical
    # across every passage of a document, so including them would add a
    # constant to each and change no ordering while making every vector longer.
    terms: dict[str, list[int]] = {}
    for word in tokenize(passage.heading):
        terms.setdefault(store_mod.term_hash(word), [0] * width)[heading_i] += 1
    body = tokenize(passage.text)
    for word in body:
        terms.setdefault(store_mod.term_hash(word), [0] * width)[body_i] += 1

    flen = [0] * width
    flen[heading_i] = len(tokenize(passage.heading))
    flen[body_i] = len(body)
    return terms, flen


def _ctx_index() -> int:
    from ..store import TF_FIELDS

    return TF_FIELDS.index("ctx")


def _with_columns(scoring: Scoring, column_weight: float) -> Scoring:
    """`scoring` with the passage's column-name field at `column_weight`.

    **Column names ride in the `ctx` slot**, which a passage never otherwise
    fills: `_terms_of` gives a passage its heading and its body and nothing
    else, so a non-row passage has a zero `ctx` count and no weight placed
    there can move its score. BM25F is weight-then-saturate, so a row's column
    names at a weight equal to `body`'s score exactly as they did inside the
    body; a different weight moves a table's rows, uniformly, against every
    other passage.
    """
    at = _ctx_index()
    weights = tuple(column_weight if i == at else w for i, w in enumerate(scoring.weights))
    return dataclasses.replace(scoring, weights=weights)


def _row_terms(passage: Passage) -> tuple[dict[str, list[int]], list[int]]:
    """A ROW passage's terms on three fields (W-287 B2, B4, B5).

    - **heading** — the section (the sheet, the caption) and, when the table has
      one, the row's KEY value (B4): `INC6014999` names its row the way a
      heading names a section. A record's key is its field name: `Pager` names
      the `Pager | sre-oncall` row.
    - **columns** (the `ctx` slot) — the header's cells; for a record table
      (B5), the row's own first cell, its field name, and the generic header
      (`Field | Value`) contributes nothing.
    - **body** — everything else the passage holds: its cells, and any prose
      the first row of a table carries above it.

    Every term of the passage's text is counted exactly once except the key
    value, which is ALSO in the body: a row is found by its key in both fields.
    """
    from .. import store as store_mod
    from ..store import TF_FIELDS

    row = passage.row
    body_i = TF_FIELDS.index("body")
    heading_i = TF_FIELDS.index("heading")
    ctx_i = _ctx_index()
    width = len(TF_FIELDS)

    heading = tokenize(passage.heading)
    if row.key >= 0:
        heading += tokenize(row.values[row.key])
    names = tokenize(row.values[0]) if row.record else tokenize(" ".join(row.columns))
    # The body is the text with the header line's terms taken out — once each,
    # because the header appears once — and, for a record, its field name too.
    body: dict[str, int] = {}
    for word in tokenize(passage.text):
        body[word] = body.get(word, 0) + 1
    removed = tokenize(" ".join(row.columns))
    if row.record:
        removed += names
    for word in removed:
        if body.get(word, 0) > 0:
            body[word] -= 1

    terms: dict[str, list[int]] = {}
    for word in heading:
        terms.setdefault(store_mod.term_hash(word), [0] * width)[heading_i] += 1
    for word in names:
        terms.setdefault(store_mod.term_hash(word), [0] * width)[ctx_i] += 1
    for word, count in body.items():
        if count:
            terms.setdefault(store_mod.term_hash(word), [0] * width)[body_i] += count

    flen = [0] * width
    flen[heading_i] = len(heading)
    flen[ctx_i] = len(names)
    flen[body_i] = sum(body.values())
    return terms, flen


def _selector(row, hashes: list[str], df, n: int, avg_wlen: float, scoring: Scoring):
    """`(bonus, columns_matched)` — the column selector (W-287 B3).

    A query term that is a word of a column's NAME selects that column; for a
    record, a row's field name. The query's OTHER terms are then scored, with
    the passage set's own BM25F, against the selected cell(s) alone, and that
    score is the bonus: *"status open"* lifts the row whose Status cell says
    `open` above the row that says it in its notes. A query that names a column
    and nothing else selects it and adds nothing.
    """
    from .. import store as store_mod
    from ..store import TF_FIELDS

    names = [row.values[0]] if row.record else list(row.columns)
    cells = [row.values[1]] if row.record else list(row.values)
    wanted = set(hashes)
    selected: list[int] = []
    named: set[str] = set()
    for i, name in enumerate(names):
        hit = {store_mod.term_hash(w) for w in tokenize(name)} & wanted
        if hit:
            selected.append(i)
            named |= hit
    if not selected:
        return 0.0, ()
    matched = tuple(names[i] for i in selected)
    remaining = [h for h in hashes if h not in named]
    if not remaining:
        return 0.0, matched
    body_i = TF_FIELDS.index("body")
    width = len(TF_FIELDS)
    words = tokenize(" ".join(cells[i] for i in selected if i < len(cells)))
    terms: dict[str, list[int]] = {}
    for word in words:
        terms.setdefault(store_mod.term_hash(word), [0] * width)[body_i] += 1
    flen = [0] * width
    flen[body_i] = len(words)
    return score_record(terms, flen, remaining, df, n, avg_wlen, scoring), matched
