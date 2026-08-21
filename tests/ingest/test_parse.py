from __future__ import annotations

from fux.ingest.parse import parse


def test_a_leading_utf8_bom_is_stripped_not_left_as_a_character():
    """`content.decode("utf-8")` alone leaves a literal U+FEFF at the start of
    the text, which lands inside the frontmatter delimiter or the first term
    and corrupts either. `utf-8-sig` strips it.
    """
    content = b"\xef\xbb\xbf# Title\n\nbody text\n"
    doc = parse(content)
    assert doc.body.startswith("# Title") or doc.body.startswith("\n")
    assert "﻿" not in doc.body
    assert "﻿" not in str(doc.meta)


def test_a_document_with_no_bom_is_unaffected():
    content = "# Title\n\nbody text\n".encode("utf-8")
    doc = parse(content)
    assert doc.body.startswith("# Title") or doc.body.startswith("\n")
