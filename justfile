# justfile — the commands a human types.
#
# `just --list` to see them. Nothing here is required by the build: the suites,
# the generators and the gates are all runnable directly, and this file exists so
# that the one command an AGENT MUST NOT RUN has a name a human can type.
#
# 🔴 `golden-score` is that command. See L11 decision 13,
#    records/0012_LAW-11-sealed-answer-key.md.

# The one permitted home for an answer key — L11 decision 3. Gitignored, never
# committed, closed to every agent. Named here because guards match paths and an
# unnamed path is one nothing can cover.
sealed_key_dir := "work/golden/golden-answers"

py := if path_exists(".venv/bin/python") == "true" { ".venv/bin/python" } else { "python3" }

_default:
    @just --list

# ─────────────────────────────────────────────────────────────────────────────
# The sealed benchmark
# ─────────────────────────────────────────────────────────────────────────────

# L11 decision 13 (Arpit, 2026-09-21) permits exactly this and nothing wider: a
# named program, started by Arpit FROM HIS OWN SHELL, reading a key from the one
# permitted directory, emitting ids/ranks/counts and no answer.
#
# 🔴 No agent invokes it — not directly, not through a subagent, a hook, a skill
#    or a script it wrote. The guards were NOT relaxed for this recipe: they bind
#    a Claude tool call, and a command you type is not one. score.py refuses if it
#    sees a Claude Code environment, so running this from an agent's integrated
#    terminal is a refusal rather than a loophole.
#
#   just golden-score work/regression/2026-09-21-golden-three-engines
#
# Scores land in <run>/scores/<arm>/<rung>/set-<n>.json. Every number produced is
# `informed` permanently — decision 13, and decision 7's reasoning behind it.
#
# 🔴 ARPIT ONLY — score a filed hand-off run against the sealed answer key.
golden-score run key_dir=sealed_key_dir:
    #!/usr/bin/env bash
    set -euo pipefail
    shopt -s nullglob
    run="{{run}}"
    [ -d "$run/evidence" ] || { echo "no $run/evidence/ — is that a filed run?" >&2; exit 1; }
    n=0
    # Two layouts are in use: <run>/evidence/<arm>/rung-*/ (the multi-arm runs)
    # and <run>/evidence/rung-*/ (a single-arm ladder). Both are globbed; the
    # single-arm case is labelled `single` so an output path never collides.
    for handoff in "$run"/evidence/*/rung-*/handoff-set-*.jsonl "$run"/evidence/rung-*/handoff-set-*.jsonl; do
        rung="$(basename "$(dirname "$handoff")")"
        arm="$(basename "$(dirname "$(dirname "$handoff")")")"
        [ "$arm" = "evidence" ] && arm="single"
        s="$(basename "$handoff")"; s="${s#handoff-set-}"; s="${s%.jsonl}"
        {{py}} tools/golden-score/score.py \
            --handoff "$handoff" \
            --key "{{key_dir}}/set-${s}.jsonl" \
            --out "$run/scores/$arm/$rung/set-${s}.json" \
            --rung "$rung" --arm "$arm" --set "$s"
        n=$((n + 1))
    done
    [ "$n" -gt 0 ] || { echo "no handoff-set-*.jsonl under $run/evidence/" >&2; exit 1; }
    echo "scored $n hand-off(s) into $run/scores/"

# Safe for anyone, including an agent: it names the path and reads nothing in it.
#
# Check every guard around the sealed key is still standing. Opens nothing.
golden-guards:
    #!/usr/bin/env bash
    set -uo pipefail
    fail=0
    ok()   { printf '  ok    %s\n' "$1"; }
    bad()  { printf '  FAIL  %s\n' "$1"; fail=1; }
    echo "L11 guards — records/0012_LAW-11-sealed-answer-key.md"
    [ -z "$(git ls-files 'work/golden/golden-answer*')" ] \
        && ok "no key tracked on any committed ref" \
        || bad "SOMETHING UNDER THE KEY PATH IS TRACKED — declare a breach"
    git check-ignore -q "{{sealed_key_dir}}" \
        && ok "the key directory is gitignored" \
        || bad "the key directory is NOT gitignored"
    [ "$(grep -c 'golden-answer' .claude/settings.json)" -ge 14 ] \
        && ok "permissions.deny still names the path (>=14 rules)" \
        || bad "permissions.deny has fewer rules than expected"
    [ -x .claude/hooks/guard-golden-answer.sh ] \
        && ok "guard-golden-answer.sh is executable" \
        || bad "guard-golden-answer.sh missing or not executable"
    [ -x .claude/hooks/guard-sealed-key.sh ] \
        && ok "guard-sealed-key.sh is executable" \
        || bad "guard-sealed-key.sh missing or not executable"
    grep -q '!work/golden' .fux/sources/dirs \
        && ok "excluded from fux's own index" \
        || bad "not excluded from .fux/sources/dirs"
    # ⚠ Config surfaces only. `.claude/.locks/` is the per-asset write lock
    # (SR-WORK-BLOCKERS decision 7) and names every file a session EDITS — so a
    # bare `grep -r .claude/` flags the session that hardened score.py as if it
    # had wired an invocation. It is gitignored and ephemeral; it is not config.
    [ -z "$(grep -rl 'golden-score' .claude/settings.json .claude/hooks \
            .claude/commands .claude/agents .claude/skills .claude/rules \
            .claude/output-styles 2>/dev/null)" ] \
        && ok "no agent-side invocation of the scorer is wired" \
        || bad "a .claude config surface references the scorer — decision 13 forbids it"
    {{py}} scripts/gen-laws.py --check >/dev/null \
        && ok "CLAUDE.md's generated law view matches the records" \
        || bad "CLAUDE.md's law view has drifted — run scripts/gen-laws.py --write"
    exit "$fail"

# ─────────────────────────────────────────────────────────────────────────────
# Build & test — the four invocations CLAUDE.md names
# ─────────────────────────────────────────────────────────────────────────────

# The fast unit suite.
test:
    uv run pytest -q tests

# The package as a user sees it.
test-e2e:
    uv run pytest -q tests_e2e

# (`node --test node/test` bare is the broken invocation — work/MACHINE.md.)
#
# The Node reader's own units.
test-node:
    node --test node/test/*.test.mjs

# LESSONS.md: a red test on an uncommitted tree is invisible to every mechanism.
#
# Every suite, whole — the thing to run before believing a change is done.
test-all: test test-e2e test-node

# The published Node bundle (L10).
bundle:
    {{py}} -m fux.store.nodebundle node node/dist
