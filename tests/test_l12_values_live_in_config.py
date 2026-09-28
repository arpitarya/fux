"""SR-LAW-12 §Veto condition — the AST test W-225 stage 7 owed.

*"One AST-based test (Python `ast`; a tokenizer pass over `.mjs`) that fails on
any such literal not in its reviewed allow-list of decision-6 sites."* The
scanner is `l12_lib.py`; the allow-list is `l12_allow.toml`.

A site is `path::scope::kind::literal`. Two directions, because an allow-list
that only grows stops being reviewed:

- every literal the scanner finds is listed, under a category;
- every listed site still exists.

⚠ **What this does NOT see**, stated so a green run is read correctly: a
boolean in a class body (the ratified scanner skips it — the R8 dataclass
question is open in the compare doc), a string inside a function body that is
not path-like, and anything the Node lexer cannot place in a scope.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

from l12_lib import ROOT, scan_all

ALLOW = Path(__file__).with_name("l12_allow.toml")

#: The categories decision 6 (and 6a) names, plus the two that are NOT a
#: permission: stage 5f's remaining `inspect` work and the open questions.
CATEGORIES = {
    "identity", "key-name", "enum-tag", "vocabulary", "message", "grammar",
    "presentation", "bootstrap", "pending-w228", "for-arpit",
}


def _allowed() -> dict[str, str]:
    data = tomllib.loads(ALLOW.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for group in data["allow"]:
        assert group["category"] in CATEGORIES, group["category"]
        assert group["basis"] and group["why"], group["category"]
        for key in group["sites"]:
            assert key not in out, f"{key} is listed twice"
            out[key] = group["category"]
    return out


def test_every_literal_the_scanner_finds_is_allow_listed():
    allowed = _allowed()
    missing = sorted({s.key for s in scan_all()} - set(allowed))
    assert not missing, (
        "a literal value in engine code that no category covers (SR-LAW-12):\n  "
        + "\n  ".join(missing[:40])
        + ("\n  …" if len(missing) > 40 else "")
        + "\n\nMove it to a config file — `src/fux/constants.toml` if it is fixed, the "
        "consumer's TOML if it is tunable — or, if it is code by decision 6, list it "
        "in tests/l12_allow.toml under its category. A new category is a ruling."
    )


def test_every_allow_listed_site_still_exists():
    stale = sorted(set(_allowed()) - {s.key for s in scan_all()})
    assert not stale, (
        "tests/l12_allow.toml lists sites the scanner no longer finds — delete them:\n  "
        + "\n  ".join(stale)
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_both_planes_read_the_same_constants():
    """SR-LAW-12 decision 4: Python and Node read the same key from the same file.

    Both loaders parse `src/fux/constants.toml` whole; the results must be equal.
    """
    import tomllib as _t

    py = _t.loads((ROOT / "src" / "fux" / "constants.toml").read_text(encoding="utf-8"))
    script = (
        "import('./node/src/config/toml.mjs').then(m => {"
        " const fs = require('node:fs');"
        " const t = fs.readFileSync('src/fux/constants.toml', 'utf8');"
        " process.stdout.write(JSON.stringify(m.parseToml(t, 'constants.toml')));"
        "})"
    )
    out = subprocess.run(
        ["node", "-e", script], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    assert json.loads(out) == json.loads(json.dumps(py))
