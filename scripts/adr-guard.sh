#!/usr/bin/env bash
# adr-guard — refuse a commit that changes an ADR-owned component without
# touching a record. The same rule as `tests/test_adr_freshness.py`, run at the
# moment it is cheapest to obey.
#
# Install:
#     ln -sf ../../scripts/adr-guard.sh .git/hooks/pre-commit
#
# Escape hatch, when a change genuinely touches no recorded decision:
#     git commit -m "chore: bump dev deps
#
#     no ADR affected"
#
# That is a claim written into git history under your name, not a silent skip.
# Bypassing with --no-verify leaves no trace, so CI runs the same check.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
REGISTER="$ROOT/docs/adr/README.md"
[ -f "$REGISTER" ] || exit 0     # no register, nothing to guard

# Staged paths.
staged="$(git --no-optional-locks diff --cached --name-only)"
[ -n "$staged" ] || exit 0

# A record was staged -> the rule is satisfied.
if grep -qE '^(docs|work)/adr/[0-9]{4}_[^/]+\.md$' <<<"$staged"; then
  exit 0
fi

# The commit message, if one is available at this point (pre-commit gets it
# only for -m / -F; an editor message is checked by CI instead).
msg_file="${1:-$ROOT/.git/COMMIT_EDITMSG}"
if [ -f "$msg_file" ] && grep -qiE 'no[ -]adr[ -]affected|\[no-adr\]' "$msg_file"; then
  exit 0
fi

# Component paths from the ownership table, most specific first.
owned="$(awk '
  /<!-- OWNERSHIP-TABLE-START -->/ { on=1; next }
  /<!-- OWNERSHIP-TABLE-END -->/   { on=0 }
  on && /^\|/ {
    line=$0
    sub(/^\|[ \t]*/, "", line)
    split(line, c, "|")
    gsub(/[` \t]/, "", c[1])
    sub(/\/$/, "", c[1])
    if (c[1] != "" && c[1] != "component" && c[1] !~ /^-+$/) print c[1]
  }
' "$REGISTER" | awk '{ print length, $0 }' | sort -rn | cut -d" " -f2-)"

hits=""
while IFS= read -r f; do
  [ -n "$f" ] || continue
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    case "$f" in
      "$p"|"$p"/*) hits="$hits  $p -> $f"$'\n'; break ;;
    esac
  done <<<"$owned"
done <<<"$staged"

if [ -n "$hits" ]; then
  cat >&2 <<MSG

  ADR guard: this commit changes an ADR-owned component and updates no record.

$hits
  Either update the owning record (docs/adr/README.md has the ownership table)
  and stage it in this same commit, or say so in the commit message:

      no ADR affected

  Saying so explicitly is the rule. Skipping silently is not.

MSG
  exit 1
fi
exit 0
