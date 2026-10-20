"""The fifteen plugin packages under `packages/` — SR-PLUGINS (W-289).

What is held here, each against the tree rather than a list typed twice:

- **every first-party package is a buildable project** with an OSI licence by
  SPDX identifier (L2), on fux's own version (P11), pinning `fux-core` and its
  declared dependencies at that version — **except a fetcher, which depends on
  nothing at all** (P10);
- **a fetcher package imports nothing from `fux`** — SR-FETCHER's isolation,
  which a convenience import would quietly break;
- **`fux-engine` depends on none of them**, and only the `dev` extra names
  them, so a test can import them and an install cannot pull them in;
- **the uv workspace covers every one**.
"""

from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path

import pytest

from fux import __version__, plugins

ROOT = Path(__file__).resolve().parents[1]
OSI = {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "ISC", "MPL-2.0"}
NAMES = sorted(plugins.first_party())


def _project(name: str) -> dict:
    return tomllib.loads((ROOT / "packages" / name / "pyproject.toml").read_text(encoding="utf-8"))


def _root_project() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_the_package_directories_are_exactly_the_first_party_table():
    on_disk = sorted(
        p.name
        for p in (ROOT / "packages").iterdir()
        if p.is_dir() and re.match(r"^fux-(decoder|fetcher|extension)-", p.name)
    )
    assert on_disk == NAMES


@pytest.mark.parametrize("name", NAMES)
def test_each_package_is_a_lockstep_osi_licensed_project(name):
    project = _project(name)["project"]
    assert project["name"] == name
    assert project["version"] == __version__, "P11: every plugin ships on fux's version"
    assert project["license"] in OSI, "L2: an OSI-approved SPDX identifier"
    assert project["license"] == "MIT", "the licence fux itself ships under"
    assert not project.get("optional-dependencies"), "L2: no optional extras"
    assert (ROOT / "packages" / name / "README.md").is_file()


@pytest.mark.parametrize("name", NAMES)
def test_each_package_depends_on_what_the_table_says_and_nothing_else(name):
    pkg = plugins.first_party()[name]
    deps = sorted(_project(name)["project"]["dependencies"])
    if pkg.kind == "fetcher":
        assert deps == [], "P10: a fetcher package depends on nothing from fux"
        return
    want = sorted([f"fux-core=={__version__}"] + [f"{d}=={__version__}" for d in pkg.depends])
    assert deps == want


@pytest.mark.parametrize("name", NAMES)
def test_each_wheel_carries_its_one_import_name(name):
    pkg = plugins.first_party()[name]
    wheel = _project(name)["tool"]["hatch"]["build"]["targets"]["wheel"]
    assert wheel["packages"] == [f"src/{pkg.module}"]


@pytest.mark.parametrize("name", [n for n in NAMES if plugins.first_party()[n].kind == "fetcher"])
def test_a_fetcher_package_imports_nothing_from_fux(name):
    """SR-FETCHER's isolation (SR-PLUGINS P10): a fetcher is a separate
    distribution precisely so that no `fux` module and no `fux` dependency
    reaches it, and none reaches into it."""
    pkg = plugins.first_party()[name]
    source = ROOT / "packages" / name / "src" / pkg.module
    for path in sorted(source.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0
        }
        assert "fux" not in imported, f"{path} imports fux"
        assert not {i for i in imported if i.startswith("fux_")}, f"{path} imports another plugin"


def test_fux_engine_depends_on_no_plugin_package():
    deps = " ".join(_root_project()["project"]["dependencies"])
    for name in NAMES:
        assert name not in deps, f"fux-engine must not depend on {name} (SR-PLUGINS)"
    for role in ("fux-core", "fux-reader", "fux-writer"):
        text = (ROOT / "packages" / role / "pyproject.toml").read_text(encoding="utf-8")
        assert not any(name in text for name in NAMES), f"{role} names a plugin package"


def test_only_the_dev_extra_names_the_plugins_for_the_tests():
    extras = _root_project()["project"]["optional-dependencies"]
    assert set(extras) == {"dev"}
    assert sorted(d for d in extras["dev"] if d in NAMES) == NAMES


def test_the_uv_workspace_covers_every_plugin_package():
    tool = _root_project()["tool"]["uv"]
    members = tool["workspace"]["members"]
    for name in NAMES:
        assert any(Path(f"packages/{name}").match(m) for m in members), name
        assert tool["sources"][name] == {"workspace": True}


def test_no_file_ships_in_two_wheels():
    """DoD 3: a plugin's import package is not also in `src/fux/`."""
    for name in NAMES:
        module = plugins.first_party()[name].module
        assert not (ROOT / "src" / module).exists()
        assert not (ROOT / "src" / "fux" / module).exists()


def test_the_fetcher_templates_are_gone_from_the_engine():
    """P9/P10: the fetchers moved into their packages; nothing seeds a copy."""
    templates = ROOT / "src" / "fux" / "templates"
    assert not (templates / "http.py.txt").exists()
    assert not (templates / "cdp.py.txt").exists()
