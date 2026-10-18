#!/usr/bin/env python3
"""Copy the built Node bundle and give it the scoped npm name (W-282 F4).

    python scripts/npm-scoped.py node/dist node/dist-scoped

The Node reader publishes twice from ONE bundle: as `fux-engine` (unchanged)
and as `@fux-engine/reader`. The bytes are the bundle's; only `package.json`'s
`name` changes, read from `src/fux/constants.toml [distributions] npm_reader`
(L12), with public access because a scoped package is private by default.
Stdlib only: the release workflow runs it before anything is installed.
"""

from __future__ import annotations

import json
import shutil
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def scoped_name() -> str:
    data = tomllib.loads((ROOT / "src" / "fux" / "constants.toml").read_text(encoding="utf-8"))
    return data["distributions"]["npm_reader"]


def write(src: Path, dst: Path) -> Path:
    if not (src / "package.json").is_file():
        raise SystemExit(f"{src}: no package.json — build the bundle first")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    manifest = json.loads((dst / "package.json").read_text(encoding="utf-8"))
    manifest["name"] = scoped_name()
    manifest.setdefault("publishConfig", {})["access"] = "public"
    (dst / "package.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return dst


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: npm-scoped.py <built bundle dir> <out dir>")
    out = write(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"[ok] {out}: {scoped_name()}")
