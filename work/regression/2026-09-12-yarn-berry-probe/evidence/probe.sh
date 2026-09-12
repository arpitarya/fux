#!/bin/sh
# The Yarn Berry half of W-149's workspace probe. Reproduces both arms.
#
# The first probe (2026-09-12-workspace-dotpath-probe) covered npm, pnpm,
# yarn 1 and bun and named Berry as unmeasured. This is that second probe.
#
#   sh probe.sh /tmp/berry-probe
set -e
dir=${1:-/tmp/berry-probe}
export COREPACK_ENABLE_DOWNLOAD_PROMPT=0
rm -rf "$dir"; mkdir -p "$dir/packages/app" "$dir/.fux/node"; cd "$dir"

cat > package.json <<'J'
{
  "name": "berry-probe",
  "private": true,
  "packageManager": "yarn@4.1.0",
  "workspaces": ["packages/*", ".fux/node"]
}
J
printf '{\n  "name": "app",\n  "version": "1.0.0"\n}\n' > packages/app/package.json
# The shape-C stub exactly as `fux setup` writes it.
printf '{\n  "name": "fux-reader",\n  "private": true,\n  "version": "1.0.0",\n  "dependencies": {"fux-engine": "2.0.0-alpha.7"}\n}\n' > .fux/node/package.json

for linker in node-modules pnp; do
  echo "=== ARM: nodeLinker: $linker"
  printf 'nodeLinker: %s\nenableGlobalCache: true\n' "$linker" > .yarnrc.yml
  rm -rf node_modules .fux/node/node_modules yarn.lock .pnp.cjs
  corepack yarn install 2>&1 | tail -3
  echo "workspaces yarn itself reports:"; corepack yarn workspaces list 2>&1 | grep YN0000
  echo "root bin:";   ls -l node_modules/.bin/fux 2>/dev/null || echo "  (absent)"
  echo "member bin:"; ls -l .fux/node/node_modules/.bin/fux 2>/dev/null || echo "  (absent)"
done
