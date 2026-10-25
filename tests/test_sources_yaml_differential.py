"""The two `.fux/sources.yaml` readers agree — same outcome, same words (W-294 step 6).

`src/fux/acquire/sourcesfile.py` (over `yamlsubset.py`) and its Node twin
`node/src/ingest/sourcelist.mjs` (over `yamlsubset.mjs`) are both hand-rolled,
because L2 forbids a YAML package on either side. Two hand-rolled parsers drift
the moment nobody feeds them the same bytes, and a drift here is the worst kind:
the Python ingest and the Node reader would disagree about which documents are
sources — or one would refuse a committed file the other accepts.

So every fixture below goes through BOTH readers and the results must be equal:
the parsed paths with their flags and the URL entries with the attributes they
stated — or, for a refused file, the same error message, `file:lineno` included.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from fux.acquire import sourcesfile
from fux.errors import FuxError

ROOT = Path(__file__).resolve().parent.parent
NODE_SOURCELIST = (ROOT / "node" / "src" / "ingest" / "sourcelist.mjs").as_uri()
ORIGIN = ".fux/sources.yaml"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")

FIXTURES = {
    "empty": "",
    "only comments": "# nothing listed yet\n\n# still nothing\n",
    "paths, every list": (
        "paths:\n  include:\n    - docs\n    - README.md\n"
        "  archived:\n    - archive\n  enrich:\n    - docs\n    - handbook\n"
    ),
    "a url, every attribute": (
        "urls:\n  - url: https://wiki.corp/display/ENG/runbook\n    fetch: cdp\n"
        "    decoder: html\n    keep: false\n    ttl: 7d\n    enrich: true\n"
        "    archived: false\n    update: never\n"
    ),
    "both sections, out of order": (
        "urls:\n  - url: https://x.test/b\n    fetch: http\n    decoder: prose\n"
        "  - url: https://x.test/a\n    fetch: http\n    decoder: prose\n"
        "paths:\n  include:\n    - work\n    - docs\n"
    ),
    "typing traps stay text": (
        "paths:\n  include:\n    - no\n    - on\n    - null\n    - ~\n    - 1.10\n    - '010'\n"
    ),
    "quoted values": (
        "paths:\n  include:\n    - 'it''s here'\n    - \"dq path\"\n"
    ),
    "fragment is text, spaced hash is a comment": (
        "urls:\n  - url: https://x.test/page#frag\n    fetch: http\n    decoder: prose  # a note\n"
    ),
    # -- refused ---------------------------------------------------------------
    "flow list": "paths:\n  include: [docs]\n",
    "flow map": "urls:\n  - {url: https://x.test/a}\n",
    "anchor": "paths:\n  include: &a\n    - docs\n",
    "alias": "paths:\n  include:\n    - *a\n",
    "tag / bang": "paths:\n  include:\n    - !work/golden\n",
    "document marker": "---\npaths:\n  include:\n    - docs\n",
    "block scalar": "paths:\n  include: |\n    docs\n",
    "tab indent": "paths:\n\tinclude:\n\t\t- docs\n",
    "duplicate key": "paths:\n  include:\n    - docs\npaths:\n  include:\n    - work\n",
    "path twice": "paths:\n  include:\n    - docs\n    - docs\n",
    "url twice": (
        "urls:\n  - url: https://x.test/a\n    fetch: http\n    decoder: prose\n"
        "  - url: https://x.test/a\n    fetch: http\n    decoder: prose\n"
    ),
    "unknown top key": "dirs:\n  - docs\n",
    "unknown path list": "paths:\n  hidden:\n    - docs\n",
    "unknown url key": "urls:\n  - url: https://x.test/a\n    fetch: http\n    decoder: prose\n    meta: x\n",
    "empty list": "paths:\n  include:\n",
    "url missing decoder": "urls:\n  - url: https://x.test/a\n    fetch: http\n",
    "url missing fetch": "urls:\n  - url: https://x.test/a\n    decoder: prose\n",
    "non-http url": "urls:\n  - url: ftp://x.test/a\n    fetch: http\n    decoder: prose\n",
    "url under paths": "paths:\n  include:\n    - https://x.test/a\n",
    "absolute path": "paths:\n  include:\n    - /etc\n",
    "escaping path": "paths:\n  include:\n    - ../outside\n",
    "bad boolean": "urls:\n  - url: https://x.test/a\n    fetch: http\n    decoder: prose\n    keep: no\n",
    "bad ttl": "urls:\n  - url: https://x.test/a\n    fetch: http\n    decoder: prose\n    ttl: week\n",
    "bad update": "urls:\n  - url: https://x.test/a\n    fetch: http\n    decoder: prose\n    update: sometimes\n",
}


def _python(text: str) -> dict:
    try:
        parsed = sourcesfile.parse(text, origin=ORIGIN)
    except FuxError as exc:
        return {"error": str(exc)}
    return {
        "paths": [[e.value, {k: v for k, v in sorted(e.attrs.items())}] for e in parsed.paths],
        "urls": [[e.value, {k: e.attrs[k] for k in sorted(e.declared)}] for e in parsed.urls],
    }


def _node(texts: dict[str, str]) -> dict[str, dict]:
    script = (
        f"import({json.dumps(NODE_SOURCELIST)}).then(m => {{"
        " const texts = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
        " const out = {};"
        " for (const [name, text] of Object.entries(texts)) {"
        f"   try {{ const s = m.parseSources(text, {json.dumps(ORIGIN)});"
        "     const sorted = (o) => Object.fromEntries(Object.entries(o).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)));"
        "     out[name] = { paths: s.paths.map(e => [e.value, sorted(e.attrs)]),"
        "                   urls: s.urls.map(e => [e.value, sorted(e.attrs)]) };"
        "   } catch (e) { out[name] = { error: e.message }; }"
        " }"
        " process.stdout.write(JSON.stringify(out)); })"
    )
    done = subprocess.run(
        ["node", "-e", script], input=json.dumps(texts), capture_output=True, text=True,
        encoding="utf-8", check=True,
    )
    return json.loads(done.stdout)


@pytest.fixture(scope="module")
def node_results() -> dict[str, dict]:
    return _node(FIXTURES)


@pytest.mark.parametrize("name", sorted(FIXTURES))
def test_both_readers_agree(name, node_results):
    assert node_results[name] == _python(FIXTURES[name])


def test_the_refusals_are_refusals():
    """Agreement alone would pass if both readers accepted everything."""
    refused = [n for n in FIXTURES if n in _REFUSED]
    for name in refused:
        assert "error" in _python(FIXTURES[name]), f"{name!r} was accepted"
    for name in set(FIXTURES) - _REFUSED:
        assert "error" not in _python(FIXTURES[name]), f"{name!r} was refused: {_python(FIXTURES[name])}"


def test_the_bang_refusal_names_the_ignore_file():
    """Step 2: a `!` entry is pointed at `.fux/.fuxignore`, the one home of exclusion."""
    assert ".fux/.fuxignore" in _python(FIXTURES["tag / bang"])["error"]


def test_typing_traps_are_read_as_paths():
    paths = [p for p, _ in _python(FIXTURES["typing traps stay text"])["paths"]]
    assert sorted(paths) == sorted(["no", "on", "null", "~", "1.10", "010"])


_REFUSED = {
    name
    for name in FIXTURES
    if list(FIXTURES).index(name) >= list(FIXTURES).index("flow list")
}
