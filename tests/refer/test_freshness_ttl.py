"""Phase 4 — `ttl=`, the duration grammar, and the sixth verdict.

Pure over data. No network, no clock, no browser.
"""

from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.ingest import sourcelist
from fux.refer import freshness


# -- the duration grammar ---------------------------------------------------


@pytest.mark.parametrize(
    "raw,seconds",
    [("0", 0), ("30s", 30), ("15m", 900), ("1h", 3600), ("24h", 86400), ("7d", 604800)],
)
def test_durations_parse(raw, seconds):
    assert sourcelist.parse_duration(raw) == seconds


@pytest.mark.parametrize("raw", ["1x", "", "abc", "-1h", "1", "h", "1.5h", " ", "1 h"])
def test_non_durations_are_rejected(raw):
    assert sourcelist.parse_duration(raw) is None


def test_sixty_minutes_and_one_hour_resolve_alike_but_are_different_text():
    # Stored verbatim, compared resolved: config order must never change a
    # committed byte, so the file keeps what a human wrote.
    assert sourcelist.parse_duration("60m") == sourcelist.parse_duration("1h")
    assert "60m" != "1h"


# -- the first typed attribute ----------------------------------------------


def test_ttl_is_typed_not_an_enum():
    ttl = next(a for a in sourcelist.URLS.attributes if a.name == "ttl")
    # A duration has no tuple of legal values; that is the whole reason
    # `Attribute` grew a validator.
    assert ttl.values == ()
    assert ttl.validate is not None


def test_enum_attributes_are_unchanged():
    # The enum is still the right shape for everything that has one.
    for name in ("fetch", "meta", "keep"):
        attr = next(a for a in sourcelist.URLS.attributes if a.name == name)
        assert attr.values and attr.validate is None


def test_ttl_defaults_to_a_day_not_to_zero():
    ttl = next(a for a in sourcelist.URLS.attributes if a.name == "ttl")
    # ttl=0 repo-wide turns every `fux ask` into a network operation against a
    # warm p95 of 27.2 ms.
    assert ttl.default == "24h"
    assert sourcelist.parse_duration(ttl.default) == 86400


def test_a_bad_ttl_on_a_line_is_refused_with_the_rule(tmp_path):
    urls = tmp_path / "urls"
    urls.write_text("https://x/a ttl=1x\n")
    with pytest.raises(FuxError, match="ttl='1x'"):
        sourcelist.read(tmp_path, "urls", sourcelist.URLS, missing_hint="")


def test_a_good_ttl_on_a_line_parses(tmp_path):
    urls = tmp_path / "urls"
    urls.write_text("https://x/a ttl=15m keep=false\n")
    entries = sourcelist.read(tmp_path, "urls", sourcelist.URLS, missing_hint="")
    assert entries[0].attrs["ttl"] == "15m"
    assert entries[0].attrs["keep"] == "false"
    assert "ttl" in entries[0].declared


def test_an_undeclared_line_takes_the_defaults(tmp_path):
    urls = tmp_path / "urls"
    urls.write_text("https://x/a\n")
    entry = sourcelist.read(tmp_path, "urls", sourcelist.URLS, missing_hint="")[0]
    assert entry.attrs["ttl"] == "24h"
    assert entry.attrs["keep"] == "true"      # ADR-ACQUIRED: keep is on by default
    assert entry.declared == frozenset()


# -- the sixth verdict ------------------------------------------------------


def test_the_five_existing_labels_are_unchanged():
    assert freshness.verify("a", "a").label == "current"
    assert freshness.verify("a", "b").label == "stale"
    assert freshness.verify("a", None).label == "unverified"
    assert freshness.cached("a", "a", 30, 300).label == "cached"


def test_as_ingested_is_its_own_position():
    v = freshness.as_ingested("a", "a")
    assert v.label == "as-ingested"
    # Decision 6's guarantee: nothing may collapse a weaker claim into a
    # stronger one. "We could not look" is not "we looked and it was fine".
    assert v.label != "current"
    assert v.label != "unverified"


def test_as_ingested_still_records_whether_the_shas_agreed():
    # Both facts kept, exactly as `cached` does. Dropping either would make
    # the verdict a smaller claim than the truth.
    assert freshness.as_ingested("a", "a").current is True
    assert freshness.as_ingested("a", "b").current is False


def test_a_mismatch_against_retained_bytes_is_an_index_defect_not_staleness():
    v = freshness.as_ingested("a", "b")
    assert v.label == "as-ingested"
    assert "index disagrees" in v.note
    # It is NOT `stale`: the source did not change, the record disagrees with
    # the bytes it was built from.
    assert v.label != "stale"


def test_a_ttl_hit_still_wins_over_as_ingested():
    # A cached hit means we looked recently; that is a stronger claim than
    # comparing retained bytes, so the ordering must not invert.
    v = freshness.Verdict(
        current=True, indexed_sha="a", fetched_sha="a", note="", age_seconds=5,
        from_acquired=True,
    )
    assert v.label == "cached"
