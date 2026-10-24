"""The fux YAML subset, read (W-294 step 6) — what it reads and what it refuses.

`acquire/yamlsubset.py` is hand-rolled because L2 rules out a YAML package. The
differential test (`tests/test_sources_yaml_differential.py`) holds it equal to
its Node twin; THIS file pins what the Python reader itself says, one refusal
per row of W-294 §Format, so a reader that silently started accepting one would
fail here even while both twins drifted together.

🔴 **Typing is the schema's.** The reader returns text for every scalar — the
typing traps (`no`, `on`, `null`, `~`, `1.10`, `010`) are pinned here as TEXT,
and `test_sourcesfile.py` pins what each position then accepts.
"""

from __future__ import annotations

import pytest

from fux.acquire import yamlsubset
from fux.errors import FuxError

ORIGIN = ".fux/sources.yaml"


def _parse(text):
    return yamlsubset.parse(text, origin=ORIGIN)


# -- what it reads -----------------------------------------------------------


def test_an_empty_or_comment_only_file_is_nothing():
    assert _parse("") is None
    assert _parse("# a note\n\n   # another\n") is None


def test_block_maps_and_lists_nest():
    root = _parse("paths:\n  include:\n    - docs\n    - work\n")
    include = root.pairs["paths"].value.pairs["include"].value
    assert [item.text for item in include.items] == ["docs", "work"]


@pytest.mark.parametrize("trap", ["no", "on", "null", "~", "1.10", "010", "true", "yes", "0x1f"])
def test_a_typing_trap_is_text(trap):
    """No scalar is ever a bool, a null or a number here — the schema decides."""
    root = _parse(f"k:\n  - {trap}\n")
    (item,) = root.pairs["k"].value.items
    assert isinstance(item, yamlsubset.Scalar)
    assert item.text == trap and not item.quoted


def test_single_and_double_quotes_are_read():
    root = _parse("k:\n  - 'it''s here'\n  - \"dq path\"\n")
    items = root.pairs["k"].value.items
    assert [(i.text, i.quoted) for i in items] == [("it's here", True), ("dq path", True)]


def test_a_hash_is_a_comment_only_at_line_start_or_after_whitespace():
    """YAML's own rule, and what keeps a URL fragment intact."""
    root = _parse("k:\n  - https://x.test/page#frag\n  - https://x.test/p #a note\n")
    assert [i.text for i in root.pairs["k"].value.items] == ["https://x.test/page#frag", "https://x.test/p"]


def test_a_key_with_nothing_after_it_is_null_not_absent():
    """The one shape the schema needs to tell `empty` from `absent`."""
    root = _parse("paths:\n")
    assert isinstance(root.pairs["paths"].value, yamlsubset.Null)


def test_every_node_carries_its_line():
    root = _parse("# header\npaths:\n  include:\n    - docs\n")
    pair = root.pairs["paths"]
    assert pair.line == 2
    (item,) = pair.value.pairs["include"].value.items
    assert item.line == 4


# -- what it refuses, each loudly and at file:line -----------------------------


@pytest.mark.parametrize(
    ("text", "line", "says"),
    [
        ("paths: {include: [docs]}\n", 1, "flow collection"),
        ("paths:\n  include: [docs]\n", 2, "flow collection"),
        ("paths:\n  include:\n    - &a docs\n", 3, "anchor"),
        ("paths:\n  include:\n    - *a\n", 3, "alias"),
        ("paths:\n  include:\n    - !work/golden\n", 3, "tag"),
        ("---\npaths:\n", 1, "document marker"),
        ("paths:\n  include:\n    - docs\n...\n", 4, "document marker"),
        ("urls:\n  - url: |\n      https://x.test/\n", 2, "block scalar"),
        ("urls:\n  - url: >\n      https://x.test/\n", 2, "block scalar"),
        ("paths:\n\tinclude:\n", 2, "tab"),
        ("paths:\n  include:\n    - docs\n  include:\n    - x\n", 4, "given twice in one map (first on line 2)"),
        ("%YAML 1.2\npaths:\n", 1, "directive"),
    ],
    ids=[
        "flow-map", "flow-list", "anchor", "alias", "tag", "doc-start", "doc-end",
        "block-literal", "block-folded", "tab", "duplicate-key", "directive",
    ],
)
def test_outside_the_subset_is_refused_naming_the_line(text, line, says):
    with pytest.raises(FuxError) as exc:
        _parse(text)
    message = str(exc.value)
    assert message.startswith(f"{ORIGIN}:{line}: "), message
    assert says in message


def test_a_tag_refusal_says_bang_is_not_an_exclusion_here():
    """`!work/golden` is the exact line a pre-W-294 `dirs` held. The refusal
    has to send its author to `.fux/.fuxignore`, not just say "no tags"."""
    with pytest.raises(FuxError, match=r"\.fux/\.fuxignore"):
        _parse("paths:\n  include:\n    - !work/golden\n")


def test_an_unclosed_quote_is_refused():
    with pytest.raises(FuxError, match=rf"{ORIGIN}:2: a quoted value is not closed"):
        _parse("k:\n  - 'open\n")
