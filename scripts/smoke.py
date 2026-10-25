#!/usr/bin/env python3
"""The install smoke: what a consumer installs, from the built artefacts and NO
registry, gives the same answers from both readers.

    python scripts/smoke.py dist node/dist

- **PyPI half** — a fresh venv installs `fux-engine` from `dist/` alone
  (`--no-index`, so its three role packages must be there too), then sets up,
  ingests and builds a small fixture repository and asks it questions with
  **no Node on PATH**.
- **npm half** — `npm pack` of the bundle directory, installed into an empty
  prefix, asks the same repository the same questions with **no Python on
  PATH**.
- **The same answers.** Each verb's `--json` payload is compared parsed, with
  every score rounded to nine places — the differential arm's two ratified
  tolerances (SR-NODE-SEARCH): Python escapes non-ASCII and two libms may
  disagree in the last ulp. Anything else that differs fails. **At least one
  payload must carry results**, so two readers that both return nothing cannot
  pass.

The differential arm compares the module tree; this compares what ships —
codelaw's `smoke.sh`, taken here 2026-10-21. Linux and macOS (it builds PATH
from symlinks). Run by ci.yml's build job after `law-gate.py`. Stdlib only.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

#: The fixture: three documents, one with a non-ASCII name and title so the
#: ensure_ascii difference is exercised rather than assumed away.
DOCS = {
    "docs/retry.md": "# Card retry policy\n\nA declined card is retried three times, one hour apart, before the order is cancelled.\n",
    "docs/deploy.md": "# Deploy runbook\n\nDeploys go out on Tuesdays. Roll back with the blue-green switch; never hot-patch production.\n",
    "docs/café-rota.md": "# Café rota — naïve façade\n\nThe café opens at seven and closes when the last card retry clears.\n",
}

#: (verb, query, extra flags) — every reading verb both readers serve.
CALLS = [
    ("ask", "card retry", ("--no-tune", "--band")),
    ("ask", "café opens", ("--no-tune", "--band")),
    ("ask", "zzqx nothing matches", ("--no-tune", "--band")),
    ("find", "deploy tuesday", ("--no-tune",)),
    ("answer", "how many times is a card retried", ()),
]


def run(argv, cwd, path_dirs, check=True):
    env = {"HOME": os.environ.get("HOME", "/tmp"), "PATH": os.pathsep.join(map(str, path_dirs)),
           "LANG": "C.UTF-8", "PYTHONUTF8": "1"}
    proc = subprocess.run([str(a) for a in argv], cwd=cwd, env=env, capture_output=True,
                          text=True, encoding="utf-8")
    if check and proc.returncode != 0:
        sys.exit(f"smoke: {' '.join(map(str, argv))} exited {proc.returncode}\n{proc.stderr.strip()}")
    return proc.stdout


def only(tools: dict[str, str], into: Path) -> Path:
    """A directory holding symlinks to exactly these executables — a PATH that
    cannot reach anything else."""
    into.mkdir(parents=True)
    for name, target in tools.items():
        found = shutil.which(target)
        if not found:
            sys.exit(f"smoke: {target} is not on PATH")
        (into / name).symlink_to(found)
    return into


def rounded(x):
    if isinstance(x, float):
        return round(x, 9)
    if isinstance(x, list):
        return [rounded(v) for v in x]
    if isinstance(x, dict):
        return {k: rounded(v) for k, v in x.items()}
    return x


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    dist, npm_dir = (Path(a).resolve() for a in argv)
    work = Path(tempfile.mkdtemp(prefix="fux-smoke-"))
    try:
        git_only = only({"git": "git"}, work / "bin-git")
        node_only = only({"node": "node"}, work / "bin-node")

        # the fixture repository
        repo = work / "repo"
        for rel, text in DOCS.items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text, encoding="utf-8")
        # A fixture commit is never signed: a global commit.gpgsign would need a
        # gpg the PATH-restricted run cannot see.
        for args in (["init", "-q"], ["config", "user.email", "smoke@fux"], ["config", "user.name", "smoke"],
                     ["config", "commit.gpgsign", "false"], ["add", "-A"], ["commit", "-qm", "fixture"]):
            run(["git", *args], repo, [git_only])

        # PyPI half — no Node on PATH
        venv.create(work / "venv", with_pip=True)
        vbin = work / "venv" / ("Scripts" if os.name == "nt" else "bin")
        run([vbin / "python", "-m", "pip", "install", "-q", "--no-index", "--find-links", dist, "fux-engine"],
            work, [vbin, git_only])
        py_path = [vbin, git_only]
        for verb in (["setup", "--no-agents"], ["ingest"], ["build"]):
            run([vbin / "fux", *verb], repo, py_path)

        # npm half — no Python on PATH
        npm = shutil.which("npm")
        if not npm:
            sys.exit("smoke: npm is not on PATH")
        prefix = work / "npm"
        prefix.mkdir()
        tgz = subprocess.run([npm, "pack", str(npm_dir), "--silent", "--pack-destination", str(prefix)],
                             capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1]
        subprocess.run([npm, "install", "--silent", "--no-audit", "--no-fund", "--prefix", str(prefix),
                        str(prefix / tgz)], check=True)
        node_fux = prefix / "node_modules" / ".bin" / "fux"

        failures, carried = [], 0
        for verb, query, extra in CALLS:
            py = json.loads(run([vbin / "fux", verb, query, "--json", *extra], repo, py_path))
            nd = json.loads(run([node_fux, verb, query, "--json", *extra], repo, [node_only]))
            carried += bool(py.get("results"))
            if rounded(py) != rounded(nd):
                failures.append(f"{verb} {query!r}:\n  python={json.dumps(py, sort_keys=True)[:400]}\n"
                                f"  node  ={json.dumps(nd, sort_keys=True)[:400]}")
        for f in failures:
            print(f"✗ {f}")
        if not carried:
            print("✗ no payload carried a result — two empty readers prove nothing")
            return 1
        if failures:
            return 1
        print(f"✔ smoke: {len(CALLS)} calls, PyPI install (no Node) == npm install (no Python); "
              f"{carried} carried results")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    raise SystemExit(main(sys.argv[1:]))
