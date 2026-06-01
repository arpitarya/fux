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
