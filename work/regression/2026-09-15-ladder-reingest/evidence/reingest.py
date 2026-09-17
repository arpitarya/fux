"""W-186 — re-ingest every golden rung at the current engine, update its stamp.

The documented step (`work/golden/README.md`: *"if it does not [match], re-ingest
that rung once, update the record, and say so in the report"*), performed on all
eight. It touches `.fux/index/`, `.fux/tune.toml` and `fux.toml` and **no
document**, which the manifest check afterwards is what proves.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

FUX = Path("/Users/arpitarya/my_programs/fux")
LAB = Path("/Users/arpitarya/my_programs/fux-lab/corpora/golden")
sys.path.insert(0, str(FUX / "tools" / "differential"))
sys.path.insert(0, str(FUX / "src"))
import rungs  # noqa: E402

RETIRED_TUNE = ("archived_weight", "superseded_weight", "recency_half_life_days")
VERSION = subprocess.run([sys.executable, "-m", "fux.cli", "--version"],
                         cwd=FUX, capture_output=True, text=True).stdout.strip()


def fix_configs(root: Path) -> list[str]:
    changed = []
    tune = root / ".fux" / "tune.toml"
    if tune.is_file():
        text = tune.read_text(encoding="utf-8")
        kept = [l for l in text.splitlines(True)
                if not re.match(rf"^({'|'.join(RETIRED_TUNE)})\s*=", l)]
        if len(kept) != len(text.splitlines()):
            tune.write_text("".join(kept), encoding="utf-8")
            changed.append(f"tune.toml: dropped {len(text.splitlines()) - len(kept)} retired key(s)")
    cfg = root / "fux.toml"
    if cfg.is_file():
        text = cfg.read_text(encoding="utf-8")
        if re.search(r"^urls_file\s*=", text, re.M) and "[sources.url]" in text:
            lines = text.splitlines(True)
            url_line = next(l for l in lines if re.match(r"^urls_file\s*=", l))
            lines.remove(url_line)
            out = []
            for l in lines:
                out.append(l)
                if l.strip() == "[sources]":
                    out.append('urls_file = ".fux/sources/urls"\n')
            cfg.write_text("".join(out), encoding="utf-8")
            changed.append("fux.toml: urls_file moved to [sources]")
    return changed


def main() -> int:
    report = []
    for name in sorted(p.name for p in LAB.iterdir() if p.is_dir() and p.name.startswith("rung-")):
        root = LAB / name
        row: dict = {"rung": name}
        row["config"] = fix_configs(root)
        ing = subprocess.run([sys.executable, "-m", "fux.cli", "ingest", "--full"],
                             cwd=root, capture_output=True, text=True)
        row["ingest_rc"] = ing.returncode
        row["ingest"] = (ing.stdout or ing.stderr).strip().splitlines()[-1] if (ing.stdout or ing.stderr) else ""
        if ing.returncode != 0:
            row["error"] = (ing.stderr or ing.stdout)[:400]
            report.append(row)
            print(json.dumps(row)); continue

        # Commit the rung so `rung_head_commit` names a real commit.
        subprocess.run(["git", "add", "-A"], cwd=root, capture_output=True)
        subprocess.run(["git", "-c", "user.email=agent@fux.local", "-c", "user.name=fux agent",
                        "commit", "-qm", f"W-186: re-ingest at {VERSION} (fux.index.v3)"],
                       cwd=root, capture_output=True)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                              capture_output=True, text=True).stdout.strip()

        stamp = FUX / "work" / "golden" / "ladder" / f"{name}.index"
        meta = rungs.manifest(name)
        new_root = rungs.index_root_sha256(root)
        stamp.write_text(
            f"engine: {VERSION}\n"
            f"rung: {name}\n"
            f"documents: {meta['documents']}\n"
            f"index_root_sha256: {new_root}\n"
            f"rung_head_commit: {head}\n",
            encoding="utf-8",
        )
        row["index_root_sha256"] = new_root
        row["rung_head_commit"] = head[:12]
        row["verify"] = rungs.verify(name, root, documents_too=True)
        ask = subprocess.run([sys.executable, "-m", "fux.cli", "ask", "rate card", "--json", "--top", "3"],
                             cwd=root, capture_output=True, text=True)
        try:
            row["ask_results"] = len(json.loads(ask.stdout)["results"])
        except Exception:
            row["ask_results"] = f"FAILED rc={ask.returncode}: {(ask.stderr or '')[:120]}"
        report.append(row)
        print(json.dumps(row))
    Path(sys.argv[1]).write_text(json.dumps(report, indent=2), encoding="utf-8") if len(sys.argv) > 1 else None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
