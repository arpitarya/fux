"""🔴 **The served page computes no score, no band and no rank.**

W-210's first hazard, as a gate. The three sample pages this feature was
designed from *did* restate the ranker — a BM25 replay and a JS port of
`walk.ppr()` — because they had no server to ask. The shipped page inherits none
of that code, and *"it does not any more"* is the kind of claim that stops being
true one helpful commit at a time.

**What the page is allowed to do arithmetic on**, and nothing else:

| allowed | why |
|---|---|
| a percentage of #1, for a bar width | presentation; the number shown is still fux's |
| the difference of two **printed** numbers | a delta between two fields is not a new claim |
| a share of the printed per-term contributions, for a stacked segment | same: `contribution` is a field of `--why` |

**What it may never do:** `Math.log`, an `idf`, a `k1`/`b` saturation, a
reciprocal-rank fusion, a walk, or a threshold comparison that decides a *band*.
The band is [SR-CONFIDENCE](../../records/0141_confidence.md)'s word and arrives
as one.

⚠ **This is a source gate, not a behavioural one, and that is deliberate.** A
behavioural test would need a second ranker to compare against — which is the
thing being forbidden. Reading the file is crude and it is the only check that
cannot be satisfied by making the second ranker agree.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fux.serve import PAGE

SOURCE = PAGE.read_text(encoding="utf-8")
SCRIPT = SOURCE.split("<script>", 1)[-1].split("</script>", 1)[0]

#: Every one of these is a piece of the ranker. A page that grew one has grown
#: a second implementation of something the engine already decided.
FORBIDDEN = {
    "Math.log": "idf is logarithmic — a log in the page is an idf in the page",
    "Math.exp": "no saturation curve belongs here",
    "Math.pow": "no saturation curve belongs here",
    "avg_wlen": "the length normaliser is the scorer's, not the page's",
    "avgWlen": "the length normaliser is the scorer's, not the page's",
    "weighted_tf": "BM25F's numerator is the scorer's",
    "weightedTf": "BM25F's numerator is the scorer's",
    "deriveWlen": "BM25F's denominator is the scorer's",
    "idf(": "an idf in the page is a second scorer",
    "1 - b +": "the BM25 saturation denominator, transcribed",
    "ppr(": "the walk is the graph plane's",
    "damping": "the walk is the graph plane's",
    "rrf": "fusion is compose.py's",
    "porter": "stemming is the analyzer's",
}

#: ⚠ **NOT in the list above, and the distinction is the point.** The page NAMES
#: `[index] stopwords` as a lever tag, which is exactly its job — proposing a
#: knob is not turning one. What it may not carry is a stopword LIST, or any
#: other copy of the analyzer's data, so the check is on the shape rather than
#: on the word. The first draft of this file forbade the substring `stopword`
#: outright and went red on the page doing the right thing.
_ANALYZER_DATA = re.compile(r'\bSTOPWORDS?\s*=|\["the",\s*"and"|\bstopwords\s*=\s*\[', re.I)


def test_the_page_names_levers_but_carries_no_analyzer_data():
    assert "[index] stopwords" in SCRIPT, (
        "the page should still NAME the stopword lever — proposing a knob is not turning one"
    )
    assert not _ANALYZER_DATA.search(SCRIPT), (
        "the page carries what looks like a stopword list. It may name the lever; "
        "the list itself is the analyzer's and a second copy would drift."
    )


@pytest.mark.parametrize("needle", sorted(FORBIDDEN))
def test_the_page_carries_no_piece_of_the_ranker(needle):
    lowered = SCRIPT.lower()
    assert needle.lower() not in lowered, (
        f"`{needle}` appears in the served page's script: {FORBIDDEN[needle]}.\n"
        "If a number cannot be pointed at in `ask --json --why`, it does not go "
        "on the page. Add the field to `--why` and amend SR-PROVENANCE instead."
    )


def test_the_page_never_reads_a_clock():
    """DoD 6 — no wall-clock number reaches the DOM.

    ⚠ **`ask --json` carries no `ms` fields today**, so the stepper shows stage
    *completion* rather than stage duration and prints no timing at all. That is
    the honest version of the requirement: L3 forbids wall-clock output in what
    fux writes, so a page that invented durations would be printing a number no
    verb produced. If `--why` ever gains `ms`, the stepper reads it — and this
    test still holds, because reading a field is not reading a clock.
    """
    for clock in ("Date.now", "new Date", "performance.now"):
        assert clock not in SCRIPT, (
            f"`{clock}` in the served page. The stepper reads what the JSON says "
            "and animates on frames; it never measures."
        )


def test_the_page_fetches_nothing_off_the_machine():
    """L4, and simply what an offline tool owes: it must render unplugged."""
    for external in ("http://", "https://", "//cdn", "fonts.googleapis", "unpkg", "jsdelivr"):
        assert external not in SOURCE, (
            f"`{external}` in the page. One file, inline, no external host — "
            "the page has to render with the network unplugged."
        )


def test_the_page_is_one_file_with_its_css_and_js_inline():
    assert "<style>" in SOURCE and "<script>" in SOURCE
    assert not re.search(r"<link[^>]+stylesheet", SOURCE), "no external stylesheet"
    assert not re.search(r"<script[^>]+src=", SOURCE), "no external script"


def test_the_page_only_asks_routes_this_server_serves():
    """A fetch to a path `serve/` does not answer is a 404 nobody sees but the user.

    The X-ray tabs' routes are read off the server's own table (W-220), so a
    route added there is served here without a second list to keep in step.
    """
    from fux.serve import _INSPECT_ROUTES

    served = {"/ask", "/graph", "/health", "/"} | set(_INSPECT_ROUTES)
    for path in re.findall(r'fetch\("([^"?]+)', SCRIPT):
        assert path in served, f"the page fetches {path!r}, which `serve/` does not route"


def test_the_two_provisional_thresholds_are_named_as_provisional():
    """SR-INSPECT's word, used the way SR-INSPECT uses it.

    The boilerplate line and the near-tie width are **not tuned to any corpus**.
    A page that printed a lever phrased on them without saying so would be
    passing off a guess as a measurement, which is the one thing an inspection
    tool must never do.
    """
    assert "provisional" in SCRIPT.lower(), "the thresholds must be marked in the source"
    assert "provisional" in SOURCE.split("<script>")[0].lower() or "provisional" in SCRIPT.lower()
    assert "<b>provisional</b>" in SCRIPT, "and the page must TELL THE READER, not just the reader of the source"
