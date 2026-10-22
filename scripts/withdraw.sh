#!/usr/bin/env bash
# Withdraw a half-published release: deprecate every npm package and list the
# PyPI yank page of every distribution of VERSION that reached a registry.
#
#   scripts/withdraw.sh 4.1.1 --report   list what is published (read-only)
#   scripts/withdraw.sh 4.1.1            deprecate on npm (your npm login + 2FA),
#                                        and print the PyPI yank pages
#
# Why it exists: one release is 19 PyPI distributions and 2 npm packages, the
# publish jobs run separately, and a failure part-way (a missing trusted
# publisher, PyPI's 429) leaves some names on VERSION and some not. The rule —
# withdraw it whole, then cut the next patch, never re-publish a number — is
# SR-WORK-RELEASE's; this script states none of its own.
#
# Run by Arpit. A CI OIDC token may publish but may not deprecate, and PyPI has
# no yank API at all — so the withdrawal is one hand, on purpose. Taken from
# codelaw's scripts/withdraw.sh, 2026-10-21.
set -euo pipefail
v="${1:?usage: withdraw.sh VERSION [--report]}"
report="${2:-}"
cd "$(git rev-parse --show-toplevel)"

# 4.2.0-alpha.3 -> 4.2.0a3 for PyPI; a final version is unchanged.
pv="$(python3 - "$v" <<'PY'
import re, sys
v = sys.argv[1]
m = re.fullmatch(r"(\d+\.\d+\.\d+)-(alpha|beta|rc)\.(\d+)", v)
print(m.group(1) + {"alpha": "a", "beta": "b", "rc": "rc"}[m.group(2)] + m.group(3) if m else v)
PY
)"

pypi_names=(fux-engine)
for d in packages/fux-*/; do [ -f "$d/pyproject.toml" ] && pypi_names+=("$(basename "$d")"); done
npm_names=(fux-engine @fux-engine/reader)

echo "## fux $v — what reached a registry"
echo
found=0
yank=()
for n in "${pypi_names[@]}"; do
  code="$(curl -s -o /dev/null -w '%{http_code}' "https://pypi.org/pypi/$n/$pv/json" || echo 000)"
  if [ "$code" = 200 ]; then
    echo "- PyPI  $n $pv — published"; found=1
    yank+=("https://pypi.org/manage/project/$n/release/$pv/")
  else
    echo "- PyPI  $n $pv — absent"
  fi
done
deprecate=()
for n in "${npm_names[@]}"; do
  if [ -n "$(npm view "$n@$v" version 2>/dev/null)" ]; then
    echo "- npm   $n@$v — published"; found=1; deprecate+=("$n")
  else
    echo "- npm   $n@$v — absent"
  fi
done
echo

if [ "$found" = 0 ]; then echo "Nothing of $v reached a registry; nothing to withdraw."; exit 0; fi
[ "$report" = "--report" ] && exit 0

for n in "${deprecate[@]}"; do
  echo "npm deprecate $n@$v"
  npm deprecate "$n@$v" "fux $v was withdrawn: it reached the registries only in part. Use the next release."
done
if [ "${#yank[@]}" -gt 0 ]; then
  echo
  echo "PyPI has no yank API — yank each by hand (reason: partial release), then cut the next patch:"
  printf '  %s\n' "${yank[@]}"
fi
