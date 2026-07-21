#!/usr/bin/env bash
# AI-review — the second-set-of-eyes check for a PR.
#
#   scripts/ai-review.sh
#
# A solo human cannot approve his own PR, so the missing human approval is
# replaced by a *check*: a separate reviewer identity re-verifies the merge
# result and exits non-zero on problems. Two hard rules:
#
#   1. SEPARATION OF DUTIES. The reviewer identity must differ from the PR
#      author. If author == reviewer this job REFUSES (exit 3).
#   2. MODEL-FREE. Per the engine's non-negotiables ($0, stdlib-only, no LLM
#      on the maintenance path) this is the deterministic second pass: both
#      test suites on the merge result (they carry the determinism, golden,
#      eval-gate, and packaging-budget assertions) plus hard-invariant probes
#      on the PR diff. The judgment layer stays with the host agent in-session.
#
# Env (provided by the workflow):
#   PR_AUTHOR    — GitHub login of the PR author
#   REVIEWER     — the reviewer identity for this job (a constant, != any human)
#   BASE_SHA     — base ref sha to diff against
set -euo pipefail

REVIEWER="${REVIEWER:-fux-ci-reviewer}"
PR_AUTHOR="${PR_AUTHOR:-}"
BASE_SHA="${BASE_SHA:-}"

echo "AI-review — deterministic second pass"
echo "  reviewer: $REVIEWER"
echo "  author:   ${PR_AUTHOR:-<unknown>}"

# 1. Separation of duties — the reviewer may never be the author.
if [ -n "$PR_AUTHOR" ] && [ "$PR_AUTHOR" = "$REVIEWER" ]; then
  echo "✗ ai-review REFUSES: reviewer identity ($REVIEWER) == PR author ($PR_AUTHOR)." >&2
  echo "  Separation of duties: the reviewer is never the author." >&2
  exit 3
fi
echo "  ✔ separation of duties: reviewer != author"

# 2. Hard-invariant probes on the PR diff.
if [ -n "$BASE_SHA" ]; then
  echo
  echo "  → PR diff"
  git diff "$BASE_SHA"...HEAD --stat | sed 's/^/    /'

  # 2a. The runtime must stay dependency-free: pyproject dependencies = [].
  if ! python - <<'PY'
import sys, tomllib
deps = tomllib.load(open("pyproject.toml", "rb"))["project"]["dependencies"]
sys.exit(0 if deps == [] else 1)
PY
  then
    echo "✗ ai-review BLOCKS: [project] dependencies is no longer empty — the \$0" >&2
    echo "  stdlib-only runtime is a non-negotiable (CLAUDE.md)." >&2
    exit 2
  fi
  echo "  ✔ runtime dependencies still empty (\$0 law)"

  # 2b. No obvious credentials in the changed lines.
  if git diff "$BASE_SHA"...HEAD -- . ':(exclude)archive' \
      | grep -E '^\+' \
      | grep -Eiq '(api[_-]?key|secret[_-]?key|hf_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z]+ PRIVATE KEY)'
  then
    echo "✗ ai-review BLOCKS: the diff appears to add a credential." >&2
    exit 2
  fi
  echo "  ✔ no credential-shaped additions in the diff"
fi

# 3. Deterministic verification of the merge result.
echo
echo "  → both suites on the merge result"
pytest -q tests
pytest -q tests_e2e

echo
echo "✔ ai-review: deterministic second pass green"
