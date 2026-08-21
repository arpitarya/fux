#!/usr/bin/env bash
# adr-guard — refuse a commit that changes an ADR-owned component without
# touching its OWNING record. The same rule as `tests/test_adr_freshness.py`,
# run at the moment it is cheapest to obey.
#
# Install as a `commit-msg` hook, not `pre-commit`: this check has to read the
# commit message to honor the escape hatch, and at `pre-commit` time the
# message does not exist yet (`.git/COMMIT_EDITMSG` at that point is still the
# PREVIOUS commit's leftover message, or empty — reading it there checks the
# wrong thing). `commit-msg` runs after the message is written and still
# before the commit is created, and git passes its path as $1.
#
#     ln -sf ../../scripts/adr-guard.sh .git/hooks/commit-msg
#
# Escape hatch, when a change genuinely touches no recorded decision — its own
# line, nothing else on it:
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

# The commit message: required as $1 (the commit-msg hook contract). Without
# it, this cannot check the escape hatch or resolve which specific record a
# component's owner needs — running it any other way is a misinstallation.
msg_file="${1:?adr-guard.sh must run as a commit-msg hook, invoked with the message file path as \$1 — see the install line at the top of this script}"
[ -f "$msg_file" ] || exit 0

# A line reading exactly "no ADR affected" (or "[no-adr]") -> the rule is
# satisfied. Anchored to its own line, deliberately: a substring inside
# unrelated prose ("no ADR affected the parser, only tests") must not exempt
# the commit by accident.
if grep -qiE '^[[:space:]]*(no[ -]adr[ -]affected|\[no-adr\])[[:space:]]*$' "$msg_file"; then
  exit 0
fi

# component<TAB>owner, from the ownership table, most specific component first.
owned="$(awk -F'|' '
  /<!-- OWNERSHIP-TABLE-START -->/ { on=1; next }
  /<!-- OWNERSHIP-TABLE-END -->/   { on=0 }
  on && /^\|/ {
    comp=$2; owner=$3
    gsub(/[` \t]/, "", comp); gsub(/[*` \t]/, "", owner)
    sub(/\/$/, "", comp)
    if (comp != "" && comp != "component" && comp !~ /^-+$/) print comp "\t" owner
  }
' "$REGISTER" | awk -F'\t' '{ print length($1), $0 }' | sort -rn | cut -d" " -f2- )"

# ADR-NAME<TAB>path, from the register's record-listing table. Every live link
# is relative to docs/adr/ (work/adr/ is empty as of this writing — the v0.30
# superseded-pending set finished migrating into docs/adr/); if a future link
# ever points elsewhere this falls back to treating the owner as unresolved,
# same as the Python side does, rather than guessing a path. Portable grep+sed,
# not `awk`'s 3-arg `match()` — that is a gawk extension, and macOS ships bwk
# awk, which does not have it.
names="$(grep -oE '\[[0-9]{4}\]\([^)]*\) \| \*\*ADR-[A-Z0-9-]+\*\*' "$REGISTER" | \
  sed -E 's/\[[0-9]{4}\]\(([^)]*)\) \| \*\*(ADR-[A-Z0-9-]+)\*\*/\2\t\1/')"

hits=""
while IFS= read -r f; do
  [ -n "$f" ] || continue
  owner=""
  while IFS=$'\t' read -r p o; do
    [ -n "$p" ] || continue
    case "$f" in
      "$p"|"$p"/*) owner="$o"; break ;;
    esac
  done <<<"$owned"
  [ -n "$owner" ] || continue

  record=""
  if [[ "$owner" == ADR-* ]]; then
    while IFS=$'\t' read -r name link; do
      [ "$name" = "$owner" ] || continue
      case "$link" in
        */*) continue ;;  # not a bare docs/adr/ filename — unresolved, skip rather than guess
        *) record="docs/adr/$link" ;;
      esac
      break
    done <<<"$names"
  elif [[ "$owner" =~ ^W-[0-9]{2}$ ]]; then
    for cand in "$ROOT"/work/open/"$owner"-*.md; do
      [ -f "$cand" ] || continue
      record="work/open/$(basename "$cand")"
      break
    done
  fi
  [ -n "$record" ] || continue  # owner does not resolve — test_adr_ownership.py's job, not this one

  if ! grep -qxF "$record" <<<"$staged"; then
    hits="$hits  $f -> owned by $owner, whose record is $record (not staged)"$'\n'
  fi
done <<<"$staged"

if [ -n "$hits" ]; then
  cat >&2 <<MSG

  ADR guard: this commit changes an ADR-owned component and does not update
  its OWNING record (staging some other record does not count).

$hits
  Either update the owning record and stage it in this same commit, or say so
  in the commit message, on its own line:

      no ADR affected

  Saying so explicitly is the rule. Skipping silently is not.

MSG
  exit 1
fi
exit 0
