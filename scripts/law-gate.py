#!/usr/bin/env python3
"""law-gate — refuse a release whose artefacts break a law.

A law with no gate gets walked past by the next release (codelaw's lesson,
2026-10-20, taken here 2026-10-21). This reads what WILL ship — the wheels and
sdist in `dist/` and the npm directories — never the source tree that built
them, and refuses when any of them breaks a law that can be read off an
artefact:

    completeness  one wheel per distribution — fux-engine and every
                  packages/fux-* directory — plus fux-engine's sdist, all on
                  the one version in src/fux/__init__.py (SR-WORK-RELEASE)
    L2            every distribution declares an OSI licence; every runtime
                  dependency on a fux package is pinned `==` this version; a
                  third-party runtime dependency is refused unless an accepted
                  record names it (THIRD_PARTY below, empty today)
    L7            every wheel's Requires-Python floor is 3.12 or later
    L8            every npm package.json declares "engines": {"node": ">=22"}
    L10           an npm directory carries its `files` list and package.json
                  and nothing else — one .mjs, no src/; no wheel carries Node
                  source, and only fux-writer may carry the one bundle

    python3 scripts/law-gate.py dist --npm node/dist node/dist-scoped
    python3 scripts/law-gate.py dist --npm node/dist --report   # list, exit 0

Run by ci.yml's build job on every push and by publish.yml before either
registry job exists. Exit 1 when any check fails. The rules are the law
records' (SR-LAW-2, SR-LAW-7, SR-LAW-8, SR-LAW-10); this script states none of
its own. Stdlib only.
"""
from __future__ import annotations

import argparse
import email.parser
import json
import re
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: SPDX identifiers on the OSI approved-licence list that a fux distribution
#: may carry. L2 admits permissive and copyleft alike; this is the subset in
#: plausible use, and a licence outside it fails loudly rather than passing
#: on a guess.
OSI_SPDX = frozenset({
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0",
    "PSF-2.0", "Zlib", "LGPL-2.1-only", "LGPL-3.0-only", "GPL-2.0-only",
    "GPL-3.0-only", "AGPL-3.0-only",
})

#: Third-party runtime dependencies an accepted record names. L2: permission
#: is not authorization. Empty — no fux distribution depends on anything but
#: fux packages. A name added here cites its record in the comment beside it.
THIRD_PARTY: frozenset[str] = frozenset()

PYTHON_FLOOR = (3, 12)          # L7
NODE_ENGINES = ">=22"           # L8


def version() -> str:
    text = (ROOT / "src" / "fux" / "__init__.py").read_text(encoding="utf-8")
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', text, re.M)
    if not m:
        sys.exit("law-gate: no __version__ in src/fux/__init__.py")
    return m.group(1)


def pep440(v: str) -> str:
    """`4.2.0-alpha.3` → `4.2.0a3`; a final version is unchanged."""
    m = re.fullmatch(r"(\d+\.\d+\.\d+)-(alpha|beta|rc)\.(\d+)", v)
    if not m:
        return v
    return m.group(1) + {"alpha": "a", "beta": "b", "rc": "rc"}[m.group(2)] + m.group(3)


def expected_dists() -> list[str]:
    """fux-engine and one distribution per packages/fux-* directory."""
    pkgs = sorted(p.name for p in (ROOT / "packages").glob("fux-*") if (p / "pyproject.toml").is_file())
    return ["fux-engine", *pkgs]


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def metadata(wheel: Path):
    with zipfile.ZipFile(wheel) as z:
        name = next(n for n in z.namelist() if n.endswith(".dist-info/METADATA"))
        return email.parser.Parser().parsestr(z.read(name).decode("utf-8")), z.namelist()


def licence(meta) -> str:
    return (meta.get("License-Expression") or meta.get("License") or "").strip()


def check_dist(dist: Path, want: str) -> list[str]:
    errs: list[str] = []
    wheels = {norm(w.name.split("-")[0]): w for w in sorted(dist.glob("*.whl"))}
    expected = {norm(n) for n in expected_dists()}
    for n in sorted(expected - wheels.keys()):
        errs.append(f"completeness: no wheel for {n} — a release missing one breaks every install that needs it")
    for n in sorted(wheels.keys() - expected):
        errs.append(f"completeness: {wheels[n].name} is no fux distribution — nothing ships that nobody declared")
    sdists = sorted(dist.glob("fux_engine-*.tar.gz"))
    if len(sdists) != 1:
        errs.append(f"completeness: expected one fux_engine sdist, found {len(sdists)}")
    elif not sdists[0].name.startswith(f"fux_engine-{want}."):
        errs.append(f"completeness: {sdists[0].name} is not version {want}")

    for n, w in sorted(wheels.items()):
        meta, names = metadata(w)
        if meta["Version"] != want:
            errs.append(f"completeness: {w.name} is version {meta['Version']}, the release is {want}")
        lic = licence(meta)
        if lic not in OSI_SPDX:
            errs.append(f"L2: {w.name} declares licence {lic!r}, not an OSI SPDX id this gate knows")
        req = (meta.get("Requires-Python") or "").replace(" ", "")
        m = re.fullmatch(r">=(\d+)\.(\d+)(?:\.\d+)?", req)
        if not m or (int(m.group(1)), int(m.group(2))) < PYTHON_FLOOR:
            errs.append(f"L7: {w.name} Requires-Python is {req!r}, the floor is >=3.12")
        for dep in meta.get_all("Requires-Dist") or []:
            if "extra ==" in dep:
                continue
            dname = norm(re.split(r"[\s;<>=!~\[(]", dep, maxsplit=1)[0])
            if dname.startswith("fux-"):
                if not re.search(rf"==\s*{re.escape(want)}\b", dep):
                    errs.append(f"L2: {w.name} depends on {dep!r} — a fux package is pinned =={want}")
            elif dname not in THIRD_PARTY:
                errs.append(f"L2: {w.name} depends on {dep!r} — no accepted record names it")
        # L10 for every wheel: no Node module tree, and at most ONE .mjs — the
        # bundle fux-writer vendors today. W-292 removes that copy; a wheel with
        # no .mjs passes, a second one or a stray module never does.
        mjs = [x for x in names if x.endswith(".mjs")]
        if mjs and (n != "fux-writer" or mjs != ["fux/templates/node/fux.mjs"]):
            errs.append(f"L10: {w.name} ships {mjs} — only fux-writer may carry one bundled fux.mjs")
        if any("/node/src/" in x for x in names):
            errs.append(f"L10: {w.name} ships the Node module tree")
        if "fux/templates/node/package.json" in names:
            with zipfile.ZipFile(w) as z:
                pj = json.loads(z.read("fux/templates/node/package.json"))
            errs.extend(check_package_json(pj, f"{w.name}:fux/templates/node/package.json", want))
    return errs


def check_package_json(pj: dict, where: str, want: str) -> list[str]:
    errs = []
    if (pj.get("engines") or {}).get("node") != NODE_ENGINES:
        errs.append(f"L8: {where} engines.node is {(pj.get('engines') or {}).get('node')!r}, must be {NODE_ENGINES!r}")
    if pj.get("version") != want:
        errs.append(f"completeness: {where} is version {pj.get('version')!r}, the release is {want}")
    lic = pj.get("license", "")
    if lic not in OSI_SPDX:
        errs.append(f"L2: {where} declares licence {lic!r}, not an OSI SPDX id this gate knows")
    if pj.get("dependencies"):
        errs.append(f"L2: {where} has runtime dependencies {sorted(pj['dependencies'])} — no accepted record names one")
    return errs


def check_npm(d: Path, want: str) -> list[str]:
    pj_path = d / "package.json"
    if not pj_path.is_file():
        return [f"completeness: {d}/package.json is missing — build the bundle first"]
    pj = json.loads(pj_path.read_text(encoding="utf-8"))
    errs = check_package_json(pj, str(pj_path), want)
    allowed = set(pj.get("files", [])) | {"package.json"}
    present = {p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file()}
    for p in sorted(present - allowed):
        errs.append(f"L10: {d}/{p} would ship — the npm package is its `files` list and nothing else")
    for p in sorted(allowed - present):
        errs.append(f"completeness: {d}/{p} is in `files` but missing")
    if sum(p.endswith(".mjs") for p in present) != 1 or (d / "src").exists():
        errs.append(f"L10: {d} is not one bundled .mjs")
    return errs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("dist", type=Path, help="the directory holding the wheels and sdist")
    ap.add_argument("--npm", type=Path, nargs="*", default=[], help="npm package directories")
    ap.add_argument("--report", action="store_true", help="list every failure, exit 0")
    a = ap.parse_args(argv)
    want = pep440(version())
    errs = check_dist(a.dist, want)
    for d in a.npm:
        errs.extend(check_npm(d, version()))
    for e in errs:
        print(f"✗ {e}")
    if not errs:
        n = len(list(a.dist.glob("*.whl")))
        print(f"✔ law-gate: {n} wheels, 1 sdist, {len(a.npm)} npm package(s) — every law holds on what ships ({want})")
        return 0
    print(f"\nlaw-gate: {len(errs)} failure(s) — publish nothing until each is fixed", file=sys.stderr)
    return 0 if a.report else 1


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):  # ✔/✗ on a Windows console
        try:
            _s.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    raise SystemExit(main())
