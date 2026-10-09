#!/bin/bash
# W-250 DoD 2 — exercise the fux-index merge driver on a scratch clone of the fux repo.
set -euo pipefail
SP="$1"; SRC=/Users/arpitarya/my_programs/fux
export PATH="$SRC/.venv/bin:$PATH"
W="$SP/w250-clone"; rm -rf "$W"
git clone -q "$SRC" "$W"; cd "$W"
git config user.name "W-250 exercise"; git config user.email "w250@example.invalid"
rm -f .git/hooks/commit-msg   # the sr-guard is not under test here
echo "== fux hooks"; fux hooks
echo "== base ingest"; time fux ingest --no-fetch >/dev/null 2>&1 || { echo "base ingest failed"; fux ingest --no-fetch 2>&1 | tail -5; exit 1; }
git add -A .fux .gitattributes && git commit -qm "base: hooks + re-ingest" --allow-empty
BASE=$(git rev-parse HEAD)
git checkout -qb side-a
printf '\n\nW-250 merge exercise, side A — a line only branch A adds.\n' >> work/compare/section-units.compare.md
time fux ingest --no-fetch >/dev/null 2>&1
git add -A && git commit -qm "side A: edit + re-ingest"
echo "side A changed: $(git diff --name-only $BASE HEAD -- .fux/index | tr '\n' ' ')"
git checkout -q "$BASE"; git checkout -qb side-b
printf '\n\nW-250 merge exercise, side B — a line only branch B adds.\n' >> work/regression/2026-08-24-rerank-and-goldens/ANALYSIS.md
time fux ingest --no-fetch >/dev/null 2>&1
git add -A && git commit -qm "side B: edit + re-ingest"
echo "side B changed: $(git diff --name-only $BASE HEAD -- .fux/index | tr '\n' ' ')"
echo "== shared index files changed on both sides:"
comm -12 <(git diff --name-only $BASE side-a -- .fux/index | sort) <(git diff --name-only $BASE side-b -- .fux/index | sort)
echo "== merge side-a into side-b"
set +e; git merge --no-edit side-a; RC=$?; set -e
echo "merge exit: $RC"; git status --short | head -20
echo "== conflict markers in index: $(grep -l '^<<<<<<<' .fux/index/* 2>/dev/null | wc -l)"
echo "== merged index vs a fresh ingest of the merged tree"
git stash -q 2>/dev/null || true
fux ingest --no-fetch >/dev/null 2>&1
echo "index files differing from fresh ingest: $(git status --porcelain .fux/index | wc -l)"
git status --porcelain .fux/index | head
