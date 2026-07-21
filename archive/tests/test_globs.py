"""Glob matching with recursive `**` semantics (fnmatch can't do this)."""
from __future__ import annotations

from fux import globs


def test_double_star_matches_top_level_and_nested():
    pat = "backend/app/modules/brokers/**/*.py"
    assert globs.match("backend/app/modules/brokers/aggregator.py", pat)      # directly under
    assert globs.match("backend/app/modules/brokers/groww/groww_source.py", pat)  # nested
    assert not globs.match("backend/app/modules/other/x.py", pat)


def test_single_star_is_one_segment():
    assert globs.match("a/b.py", "a/*.py")
    assert not globs.match("a/b/c.py", "a/*.py")


def test_leading_double_star():
    assert globs.match_any("x/y/node_modules/z.js", ["**/node_modules/**"])
    assert globs.match_any("foo.py", ["**/*.py"])
