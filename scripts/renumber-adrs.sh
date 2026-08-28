#!/usr/bin/env bash
#
# renumber-adrs.sh — ONE-SHOT migration, 2026-08-27. Delete this file after it
# has run and the commit has landed. It is not a maintained tool.
#
# WHAT IT DOES
#   Closes the `0025` hole in `docs/adr/`. `ADR-CODES-TABLE` was archived with
#   no successor (its subject, the dense lane, was deleted), vacating `0025`.
#   Every record from `0026` up moves down by one, so the live line reads
#   `0001`-`0044` with no gaps.
#
#   Ruled by Arpit, 2026-08-27, with the cost stated and accepted: a bare number
#   in any document written before today may name a different record afterwards.
#   `work/WORKLOG.md` is append-only and some of its sentences therefore cannot
#   be corrected. **Names survive a renumber; numbers do not** — which is the
#   register's cite-by-name rule, learned again the expensive way.
#
# WHY A SCRIPT AND NOT AN AGENT EDIT
#   The Cowork surface cannot rename or unlink a file (see `work/MACHINE.md`),
#   and a 20-file rename touching every relative link in `docs/`, `work/`,
#   `src/`, `tests/` and `archive/` is the wrong thing to do by hand in any
#   case. One deterministic pass is reviewable as a diff; 300 hand edits are not.
#
# RUN IT FROM THE REPOSITORY ROOT:
#     bash scripts/renumber-adrs.sh
#
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# old_slug:new_slug — ascending, so every target is free when it is claimed.
# The slug makes each token unique, so the rewrite pass cannot chain a rename
# into the one above it.
PAIRS=(
  "0026_runtime-manifest:0025_runtime-manifest"
  "0027_runtime-stamp:0026_runtime-stamp"
  "0028_runtime-stats:0027_runtime-stats"
  "0029_graph:0028_graph"
  "0030_refer-plane:0029_refer-plane"
  "0031_types-list:0030_types-list"
  "0032_hooks:0031_hooks"
  "0033_merge-driver:0032_merge-driver"
  "0034_cache:0033_cache"
  "0035_agent-policy:0034_agent-policy"
  "0036_predictions:0035_predictions"
  "0037_archived-content:0036_archived-content"
  "0038_tuning:0037_tuning"
  "0039_mcp:0038_mcp"
  "0040_enrich:0039_enrich"
  "0041_rerank:0040_rerank"
  "0042_decode:0041_decode"
  "0043_locks:0042_locks"
  "0044_quality-contract:0043_quality-contract"
  "0045_confidence:0044_confidence"
)

echo "== 1/4  preflight"
fail=0
for pair in "${PAIRS[@]}"; do
  old="docs/adr/${pair%%:*}.md"
  new="docs/adr/${pair##*:}.md"
  if [ ! -f "$old" ]; then echo "   MISSING source: $old"; fail=1; fi
  if [ -e "$new" ]; then echo "   TARGET EXISTS:  $new"; fail=1; fi
done
# 0025 must be free, and the ADR-CONFIDENCE duplicate must already be gone.
if compgen -G "docs/adr/0025_*.md" > /dev/null; then
  echo "   0025 is not free"; fail=1
fi
if [ -e docs/adr/0043_confidence.md ]; then
  echo "   docs/adr/0043_confidence.md still exists — delete it first"; fail=1
fi
if [ "$fail" -ne 0 ]; then echo "!! preflight failed; nothing was changed"; exit 1; fi
echo "   ok — 20 renames, 0025 free"

echo "== 2/4  git mv"
for pair in "${PAIRS[@]}"; do
  git mv "docs/adr/${pair%%:*}.md" "docs/adr/${pair##*:}.md"
  echo "   ${pair%%:*}.md -> ${pair##*:}.md"
done

echo "== 3/4  rewriting references across every tracked text file"
python3 - <<'PY'
import subprocess, pathlib

pairs = [
  ("0026_runtime-manifest","0025_runtime-manifest"),
  ("0027_runtime-stamp","0026_runtime-stamp"),
  ("0028_runtime-stats","0027_runtime-stats"),
  ("0029_graph","0028_graph"),
  ("0030_refer-plane","0029_refer-plane"),
  ("0031_types-list","0030_types-list"),
  ("0032_hooks","0031_hooks"),
  ("0033_merge-driver","0032_merge-driver"),
  ("0034_cache","0033_cache"),
  ("0035_agent-policy","0034_agent-policy"),
  ("0036_predictions","0035_predictions"),
  ("0037_archived-content","0036_archived-content"),
  ("0038_tuning","0037_tuning"),
  ("0039_mcp","0038_mcp"),
  ("0040_enrich","0039_enrich"),
  ("0041_rerank","0040_rerank"),
  ("0042_decode","0041_decode"),
  ("0043_locks","0042_locks"),
  ("0044_quality-contract","0043_quality-contract"),
  ("0045_confidence","0044_confidence"),
]
# The token includes ".md", so a bare number in prose is NEVER touched. Prose
# numbers are already a defect under the register's cite-by-name rule; silently
# rewriting them would be guessing at which ones mean a record.
table = {f"{o}.md": f"{n}.md" for o, n in pairs}

files = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True
                       ).stdout.decode().split("\0")
changed = hits = 0
for f in filter(None, files):
    p = pathlib.Path(f)
    try:
        text = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
        continue
    out, n = text, 0
    for old, new in table.items():
        if old in out:
            n += out.count(old)
            out = out.replace(old, new)
    if n:
        p.write_text(out, encoding="utf-8")
        changed += 1
        hits += n
        print(f"   {f}  ({n})")
print(f"   -- {hits} references in {changed} files")
PY

echo "== 4/4  frontmatter titles and the register's display column"
python3 - <<'PY'
import pathlib, re

pairs = [
  ("0026","0025","runtime-manifest"), ("0027","0026","runtime-stamp"),
  ("0028","0027","runtime-stats"),    ("0029","0028","graph"),
  ("0030","0029","refer-plane"),      ("0031","0030","types-list"),
  ("0032","0031","hooks"),            ("0033","0032","merge-driver"),
  ("0034","0033","cache"),            ("0035","0034","agent-policy"),
  ("0036","0035","predictions"),      ("0037","0036","archived-content"),
  ("0038","0037","tuning"),           ("0039","0038","mcp"),
  ("0040","0039","enrich"),           ("0041","0040","rerank"),
  ("0042","0041","decode"),           ("0043","0042","locks"),
  ("0044","0043","quality-contract"), ("0045","0044","confidence"),
]

# a) `title: ADR-NAME (0045) — ...` in each renamed record's frontmatter
for old, new, slug in pairs:
    p = pathlib.Path(f"docs/adr/{new}_{slug}.md")
    text = p.read_text(encoding="utf-8")
    fixed = re.sub(rf"^(title:.*)\({old}\)", rf"\1({new})", text, count=1,
                   flags=re.M)
    if fixed != text:
        p.write_text(fixed, encoding="utf-8")
        print(f"   title  {p.name}")

# b) the register's display column: `| [0045](0044_confidence.md) |` — the link
#    half was already rewritten in step 3, the bracketed label was not.
reg = pathlib.Path("docs/adr/README.md")
text = reg.read_text(encoding="utf-8")
for old, new, slug in pairs:
    text = text.replace(f"| [{old}]({new}_{slug}.md)", f"| [{new}]({new}_{slug}.md)")
reg.write_text(text, encoding="utf-8")
print("   display column  docs/adr/README.md")
PY

cat <<'EOF'

== done. NOTHING IS COMMITTED. Verify before you trust it:

    git status
    git diff --stat
    grep -rn "004[0-5]_\|003[0-9]_\|002[6-9]_" --include='*.md' --include='*.py' . \
      | grep -v '^./archive/v0.26' | grep -v '\.git/'   # should show only live paths
    uv run pytest -q tests

  Then commit the rename and the link rewrite together — they are one change:

    git add -A
    git commit -m "docs(adr): close the 0025 hole; renumber 0026-0045 down by one

    no ADR affected"

  Then delete this script; it is one-shot.
EOF
