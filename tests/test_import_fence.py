"""The network fence, enforced: query/index must never import the network modules."""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).parent.parent / "src" / "fux"
NETWORK_MODULES = ("ingest.web", "ingest.cdp", "ingest.ws", "ingest .web")
FENCED_PACKAGES = ("query", "index")


def test_query_and_index_never_import_network_modules():
    offenders = []
    for package in FENCED_PACKAGES:
        for path in (SRC / package).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for line in text.splitlines():
                stripped = line.split("#")[0]
                if re.search(r"\b(import|from)\b.*\b(web|cdp|ws)\b", stripped) and (
                    "ingest" in stripped or "websocket" in stripped
                ):
                    offenders.append(f"{path.relative_to(SRC)}: {line.strip()}")
    assert not offenders, "network modules leaked past the fence:\n" + "\n".join(offenders)


def test_network_imports_only_under_ingest():
    for path in SRC.rglob("*.py"):
        if path.parent.name == "ingest":
            continue
        text = path.read_text(encoding="utf-8")
        assert "urllib.request" not in text, f"{path} uses the network outside the ingest fence"
        assert "import socket" not in text, f"{path} opens sockets outside the ingest fence"
