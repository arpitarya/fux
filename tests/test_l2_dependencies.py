"""L2's two veto commands, promoted from prose to a test.

**What this enforces:** [SR-LAW-2](../records/0004_LAW-2-zero-cost.md) §Veto
condition -- (1) a dependency appears in `pyproject.toml` that no accepted
record names; (2) a feature extra appears under `[project.optional-dependencies]`
other than `dev`; and the second command's licence check: every runtime
dependency resolves to an OSI-approved SPDX identifier. Also the Node twin
([SR-LAW-8](../records/0010_LAW-8-node-22.md)): the published Node package carries
no `dependencies`. W-246 (B-054).

Today `dependencies = []`, so the loops below hold vacuously; the test exists so
the first dependency that arrives is checked the day it arrives, not on the day
somebody remembers to run the prose command.
"""

from __future__ import annotations

import importlib.metadata as md
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The list the veto command carries, verbatim.
OSI = {
    "MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "ISC", "MPL-2.0",
    "GPL-2.0-only", "GPL-3.0-only", "LGPL-2.1-only", "LGPL-3.0-only", "PSF-2.0",
}  # fmt: skip


def _project() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def _dep_names() -> list[str]:
    return [re.split(r"[<>=!~\[ ;]", d, maxsplit=1)[0] for d in _project()["dependencies"]]


def test_no_feature_extras_other_than_dev():
    """SR-LAW-2 veto 2: fux ships packaged; `[project.optional-dependencies]` is `{dev}` only."""
    extras = set(_project().get("optional-dependencies", {}))
    assert extras <= {"dev"}, f"L2: fux ships packaged; no feature extras. Found {sorted(extras - {'dev'})}"


def test_node_package_has_no_runtime_dependencies():
    """SR-LAW-2 decision 2 (packaged, no extras), Node side: `node/package.json` has no `dependencies`."""
    pkg = json.loads((ROOT / "node" / "package.json").read_text(encoding="utf-8"))
    assert not pkg.get("dependencies"), f"node/package.json declares dependencies: {pkg['dependencies']}"
    assert not pkg.get("optionalDependencies") and not pkg.get("peerDependencies")


def test_every_runtime_dependency_is_named_by_an_accepted_record():
    """SR-LAW-2 veto 1: a dependency no accepted record names is decision 3 failing."""
    accepted = [
        p.read_text(encoding="utf-8")
        for p in sorted((ROOT / "records").glob("[0-9]*.md"))
        if re.search(r"^status:\s*accepted\s*$", p.read_text(encoding="utf-8"), re.M)
    ]
    for name in _dep_names():
        assert any(name.lower() in t.lower() for t in accepted), (
            f"L2 d3: runtime dependency {name!r} is named by no accepted record"
        )


def test_every_runtime_dependency_has_an_osi_licence():
    """SR-LAW-2 veto, second command: every runtime dependency resolves to an OSI SPDX identifier."""
    for name in _dep_names():
        m = md.metadata(name)
        lic = m.get("License-Expression") or m.get("License") or "?"
        assert lic in OSI, f"L2: {name} has licence {lic!r}, not on the OSI list -- REVIEW"
