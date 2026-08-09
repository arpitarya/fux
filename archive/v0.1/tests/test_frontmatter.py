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


def test_string_that_looks_scalar_survives_roundtrip():
    """A *string* value whose bare form would re-parse as bool/None/list must keep
    its type across dump→split — else a ratified rule's content_seal drifts and
    `fux check` raises a false `tampered` (fux-lab finding)."""
    fm = {"id": "x", "type": "formula", "status": "active",
          "examples": [{"given": "gross=1000, n=4", "expect": "true"},
                       {"given": "n=0", "expect": "false"}],
          "note_null": "null", "note_list": "[not, a, list]"}
    again, _ = frontmatter.split(fmwrite.dump(fm, "body"))
    assert again["examples"][0]["expect"] == "true"      # str, not bool True
    assert again["examples"][1]["expect"] == "false"     # str, not bool False
    assert again["note_null"] == "null"                  # str, not None
    assert again["note_list"] == "[not, a, list]"        # str, not a parsed list
    # idempotent: a second round-trip is a fixed point
    twice, _ = frontmatter.split(fmwrite.dump(again, "body"))
    assert twice == again
