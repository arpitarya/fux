# Fux — task runner. Fits the existing probe + just gating model (plan §10.9).
python := env_var_or_default("FUX_PYTHON", "python3.14")

# List recipes
default:
    @just --list

# Run the test suite
test:
    {{python}} -m pytest -q

# Lint (ruff if available; no-op otherwise — Fux governs knowledge, not code style)
lint:
    @command -v ruff >/dev/null 2>&1 && ruff check fux || echo "ruff not installed — skipping"

# The PR gate: schema, dead refs, conflicts, staleness, and invariants must pass.
# Fails the build on any blocking finding (plan §10.9). Run inside a target project.
fux-check:
    {{python}} -m fux build
    {{python}} -m fux check
    {{python}} -m fux verify

# Install the engine into ~/.claude/fux + the /fux skill
install:
    ./install.sh

# Audit branch protection vs the committed source of truth (.github/branch-protection.json).
# Branch protection is GitHub config Fux cannot seal — this is the scheduled drift guard
# (handoff §1/§3). Fails loudly if the required checks or enforce_admins ever drift.
# Requires gh authenticated; read access is enough.
audit-protection owner="arpitarya" repo="fux" branch="main":
    ./scripts/audit-branch-protection.sh {{owner}} {{repo}} {{branch}}
