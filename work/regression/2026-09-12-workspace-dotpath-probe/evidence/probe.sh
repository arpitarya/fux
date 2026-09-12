#!/usr/bin/env bash
# W-149 hazard 3 probe: does a DOT-PREFIXED workspace path (.fux/node) link
# as a workspace member, in each package manager?
# arm "explicit": the root manifest declares ".fux/node"
# arm "glob":     the root manifest declares only "packages/*"  (control)
set -u
ROOT=/tmp/claude-0/-home-claude/b85eb4bd-aa6b-5b57-8e7e-c9e1e91c4123/scratchpad/probe
MEMBER=fux-workspace-reader
FUXV=2.0.0-alpha.7

mk() { # $1=dir $2=manager $3=arm
  local d=$1 mgr=$2 arm=$3 ws
  rm -rf "$d"; mkdir -p "$d/.fux/node" "$d/packages/keep"
  [ "$arm" = explicit ] && ws='[".fux/node", "packages/*"]' || ws='["packages/*"]'
  printf '{"name":"probe-root","private":true,"version":"0.0.0","workspaces":%s}\n' "$ws" > "$d/package.json"
  printf '{"name":"keepme","private":true,"version":"0.0.0"}\n' > "$d/packages/keep/package.json"
  # the shape-C stub exactly as fux setup would write it
  cat > "$d/.fux/node/package.json" <<EOF
{"name":"$MEMBER","private":true,"version":"0.0.0","dependencies":{"fux-engine":"$FUXV"}}
EOF
  if [ "$mgr" = pnpm ]; then
    python3 - "$d" "$arm" <<'PY'
import json,sys,pathlib
d,arm=sys.argv[1],sys.argv[2]
p=pathlib.Path(d)/"package.json"; o=json.loads(p.read_text()); o.pop("workspaces",None)
p.write_text(json.dumps(o)+"\n")
pk=["packages/*"] + ([".fux/node"] if arm=="explicit" else [])
(pathlib.Path(d)/"pnpm-workspace.yaml").write_text("packages:\n"+"".join(f"  - '{x}'\n" for x in pk))
PY
  fi
}

check() { # $1=dir  -> prints member/bin/dep
  local d=$1 m="no" b="no" dep="no"
  [ -e "$d/node_modules/$MEMBER" ] && m="yes"
  [ -e "$d/node_modules/.bin/fux" ] && b="yes"
  { [ -e "$d/node_modules/fux-engine" ] || [ -e "$d/.fux/node/node_modules/fux-engine" ]; } && dep="yes"
  echo "$m|$b|$dep"
}

printf '%-6s %-9s %-7s %-7s %-7s %-6s %s\n' MGR ARM MEMBER BIN DEP RC NOTE
for mgr in npm pnpm yarn bun; do
  command -v "$mgr" >/dev/null || { printf '%-6s %s\n' "$mgr" "MISSING"; continue; }
  for arm in explicit glob; do
    d="$ROOT/$mgr-$arm"; mk "$d" "$mgr" "$arm"
    case $mgr in
      npm)  out=$( cd "$d" && timeout 240 npm install  --no-audit --no-fund 2>&1 ); rc=$? ;;
      pnpm) out=$( cd "$d" && timeout 240 pnpm install --no-frozen-lockfile 2>&1 ); rc=$? ;;
      yarn) out=$( cd "$d" && timeout 240 yarn install --non-interactive 2>&1 ); rc=$? ;;
      bun)  out=$( cd "$d" && timeout 240 bun install 2>&1 ); rc=$? ;;
    esac
    echo "$out" > "$d/install.log"
    IFS='|' read -r m b dep <<<"$(check "$d")"
    note=$(echo "$out" | grep -iE "warn|error|not match|no projects|ignor" | head -1 | cut -c1-70)
    printf '%-6s %-9s %-7s %-7s %-7s %-6s %s\n' "$mgr" "$arm" "$m" "$b" "$dep" "$rc" "${note:-ok}"
  done
done
