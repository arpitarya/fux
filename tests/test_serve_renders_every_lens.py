"""Every lens `fux inspect` reports has a renderer on the explorer's Index tab.

W-229, ruled by Arpit on 2026-09-28 ([SR-SERVE](../records/0158_serve.md)
decision 16): *"everything in inspect should be present in `serve` so that we can
see visually."* **A lens `fux inspect` reports and the explorer does not show
is a defect**, and this is the test that makes it one.

It reads the page's SOURCE, the way `tests/serve/test_page_computes_nothing.py`
does: for every top-level key of a real report's `as_dict()`, `page.html` must
read `r.<key>` somewhere. A new lens — W-228's `families` first — fails here
until it has a card, so it cannot ship invisible.

The keys that are not lenses are named, and only those: `corpus` (the header
line), `levers` (every card prints its own lens's `lever`) and `triage_count`
(printed inside the triage card).
"""

from __future__ import annotations

import re
from pathlib import Path

from fux.inspect import as_dict

from test_inspect_xray import corpus, report  # noqa: F401 — the fixtures, reused

PAGE = Path(__file__).resolve().parents[1] / "src" / "fux" / "serve" / "page.html"

#: Report keys that are not lenses, and why each needs no card of its own.
NOT_A_LENS = {
    "corpus": "the L0 header line reads it",
    "levers": "each card prints its own lens's `lever`",
    "triage_count": "printed inside the triage card",
}


def test_every_lens_the_report_carries_has_a_renderer(report):  # noqa: F811
    page = PAGE.read_text(encoding="utf-8")
    keys = sorted(as_dict(report))
    missing = [
        key for key in keys
        if key not in NOT_A_LENS and not re.search(rf"\br\.{re.escape(key)}\b", page)
    ]
    assert not missing, (
        f"`fux inspect` reports {missing} and the explorer's Index tab renders none of "
        "them. Give each a card in page.html's renderIndex (W-229) — a lens the "
        "explorer does not show is a defect."
    )


def test_the_exemptions_are_still_report_keys(report):  # noqa: F811
    """An exemption for a key the report no longer carries is a stale hole."""
    assert set(NOT_A_LENS) <= set(as_dict(report))


def test_every_lens_card_prints_its_lever():
    """DoD 1: each card carries its lens's lever from LEVERS, never one the page
    invents — so the page reads `.lever` and holds no lever text of its own."""
    page = PAGE.read_text(encoding="utf-8")
    for renderer in ("renderBoilerplate", "renderFindability", "renderDuplication", "renderCoverage", "renderGraph", "renderChunks"):
        body = page.split(f"function {renderer}(", 1)[1].split("\nfunction ", 1)[0]
        assert "leverLine(" in body and ".lever" in body, f"{renderer} prints no lever"
    assert "fux enrich`, `fux correct`" not in page, "a LEVERS string was copied into the page"
