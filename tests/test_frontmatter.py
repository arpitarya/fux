"""Frontmatter parse + serialize round-trip over the shapes Fux emits."""
from __future__ import annotations

from fux import fmwrite, frontmatter

SAMPLE = """---
id: day-pnl
type: formula
status: active
code_refs:
  - src/a.py#L1-L2
related: [x, y]
edges:
  depends-on: [inr-normalization]
  supersedes: []
examples:
  - given: "1L holding +2%"
    expect: "2000"
---
**Rule:** body text.
"""


def test_split_parses_scalars_lists_nested_and_seq_of_maps():
    fm, body = frontmatter.split(SAMPLE)
    assert fm["id"] == "day-pnl"
    assert fm["type"] == "formula"
    assert fm["code_refs"] == ["src/a.py#L1-L2"]
    assert fm["related"] == ["x", "y"]           # inline flow list
    assert fm["edges"]["depends-on"] == ["inr-normalization"]
    assert fm["edges"]["supersedes"] == []
    assert fm["examples"][0] == {"given": "1L holding +2%", "expect": "2000"}
    assert body.startswith("**Rule:**")


def test_dump_then_split_is_stable():
    fm, body = frontmatter.split(SAMPLE)
    again, body2 = frontmatter.split(fmwrite.dump(fm, body))
    assert again["id"] == fm["id"]
    assert again["related"] == fm["related"]
    assert again["edges"]["depends-on"] == ["inr-normalization"]
    assert again["examples"] == fm["examples"]
    assert body2.strip() == body.strip()


def test_no_frontmatter_returns_empty():
    fm, body = frontmatter.split("# just markdown\n")
    assert fm == {}
    assert body == "# just markdown\n"
