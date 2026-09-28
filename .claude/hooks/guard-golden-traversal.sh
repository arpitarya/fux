#!/usr/bin/env bash
# PreToolUse(Bash) — the THIRD sealed-key guard: a recursive read that never
# names the key folder. W-223, ruled by Arpit 2026-09-27: "implement the hard
# guard".
#
# 🔴 **The route it closes.** `guard-golden-answer.sh` and `guard-sealed-key.sh`
# check what a call NAMES. On 2026-09-25 a `grep -rln "W-222"` from the repo
# root named nothing under the golden tree, filtered its OUTPUT with `grep -v`,
# and still READ every file there, key directory included (W-223). Neither hook
# could see it; L11 decision 9 left it to prose. This hook refuses it.
#
# **The rule, per shell segment** (split on ; && || | & and newlines):
#   a recursive walker    grep/egrep/fgrep -r|-R|--recursive, rg, ag, ack, fd,
#                         find, tree, ls -R
#   whose root can reach  the repo root, `work/`, `work/golden/`, `..`, `~`,
#   the golden tree       `$HOME`, `$PWD`, `$CLAUDE_PROJECT_DIR`, `*`, `/`, an
#                         absolute ancestor of the repo — or NO path at all
#                         (the walker's implicit `.`) while cwd is one of those
#   and carries no        --exclude-dir=…golden…, -g/--glob '!…golden…',
#   golden exclusion      -E/--exclude …golden…, find's -path …golden… -prune,
#                         or -not/! -path …golden…
#   is DENIED.
#
# ⚠ **Why this is not the gate SR-WORK-GOLDEN once refused.** Its refused row —
# *"it would have to block every grep over work/"* — is true of a hook that
# matches `work/`. This one does not: `grep -r x work/open`, `rg x src`,
# `find records -name '*.md'` all pass, because their roots cannot reach the
# tree. Only a walk that CAN reach it, with no exclusion, is refused, and the
# fix is one flag, named in the message.
#
# ⚠ **Not caught, by design, and still prose (L11 decision 9):** a program that
# walks on its own (`python -c "os.walk('.')"`, a script), a path built at
# runtime (`grep -r x "$(pwd)"`), and `git grep` — which reads tracked files
# only, and the key is never tracked (`test_golden_key_never_committed.py`).
# Tokens are split on whitespace, so a quoted pattern with spaces can be read
# as a root; the error is toward DENY, which costs one exclusion flag.
#
# 🔴 **Hardened by W-227** (ruled by Arpit 2026-09-27, *"go with the
# recommendation"*). On 2026-09-27 a multi-line command whose LAST line was
# `grep -rn … work … | grep -v "^work/golden"` ran in a live session. Replayed
# through this hook on stdin afterwards, byte for byte, it is DENIED — so the
# route was not the parser as written, and the live cause is not reproduced.
# What W-227 closes is every way this file could ALLOW without deciding:
#   - **Any failure denies.** awk exiting anything but 0 (a runtime error, a
#     killed process) used to fall through to `exit 0`. Only a clean 0 allows.
#   - **A payload jq cannot parse is denied outright.** It used to be scanned as
#     raw text, where one JSON line of `\"`-escaped quotes reads as a single
#     quoted string and hides every command inside it.
#   - **Heredoc bodies are sorted by what they feed.** A body fed to a shell
#     (bash, sh, zsh, eval, ssh, xargs …) is checked line by line as commands;
#     a body fed to anything else (`python3 - <<'EOF'`, `cat <<EOF`) is data and
#     no longer parsed as shell — so a Python line mentioning `find` cannot trip
#     it, and the command AFTER the terminator is still checked.
#
# THIS HOOK IS NOT THE RULE — L11 is (records/0012_LAW-11-sealed-answer-key.md);
# the guard list is records/0066_WORK-golden.md. Deregistered by
# `just golden-unlock` and restored by `just golden-lock` with the other two.
# Fails CLOSED: a payload jq cannot parse is scanned as raw text.
set -uo pipefail
INPUT=$(cat)

deny() {
  [ -n "${1:-}" ] && { echo "$1" >&2; exit 2; }
  echo "BLOCKED by LAW L11 (W-223 guard): this recursive walk can reach work/golden/, where the sealed answer key lives, and it carries no exclusion. Filtering the OUTPUT (grep -v) is not enough — the walk itself reads the files. Add an exclusion to the command: grep -r … --exclude-dir=golden · rg … -g '!work/golden/**' · find … -path ./work/golden -prune -o … · fd … -E golden — or start the walk below a directory that cannot contain the tree (src/, records/, work/open/). See records/0012_LAW-11-sealed-answer-key.md decision 9." >&2
  exit 2
}

if printf '%s' "$INPUT" | jq -e . >/dev/null 2>&1; then
  [ "$(printf '%s' "$INPUT" | jq -r '.tool_name // ""')" = "Bash" ] || exit 0
  CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // ""')
  CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // ""')
else
  # W-227: fail CLOSED. A raw-text scan of a JSON payload reads it as one quoted
  # string, so it could never have found the walk it was there to find.
  deny "BLOCKED by LAW L11 (W-227 guard): the hook could not parse this tool call, and a guard that cannot read a command does not allow it. See records/0012_LAW-11-sealed-answer-key.md decision 9."
fi
PROJ=${CLAUDE_PROJECT_DIR:-}
[ -n "$CWD" ] || CWD=$(pwd)
[ -n "$PROJ" ] || PROJ=$(pwd)

printf '%s\n' "$CMD" | awk -v cwd="$CWD" -v proj="$PROJ" '
function strip(t) { gsub(/["'"'"'`]/, "", t); return t }
function trim_slash(t) { while (length(t) > 1 && substr(t, length(t)) == "/") t = substr(t, 1, length(t) - 1); return t }
function cwd_risky(   rel) {
  c = trim_slash(cwd); p = trim_slash(proj)
  if (c == p) return 1
  if (index(p "/", c "/") == 1) return 1          # cwd is an ancestor of the repo
  if (index(c, p "/") != 1) return 1               # outside the repo: unknown, fail closed
  rel = substr(c, length(p) + 2)
  return (rel == "work" || rel == "work/golden")
}
function root_risky(t,   u, p) {
  t = strip(t); if (t == "") return 0
  if (t == "." || t == "./" || t == "*" || t == "./*") return cwd_risky()
  if (t ~ /^\.\.(\/\.\.)*\/?$/ || t ~ /^\.\.\//) return 1
  if (t == "/" || t == "~" || t == "~/") return 1
  if (t ~ /^\$\{?(HOME|PWD|CLAUDE_PROJECT_DIR)\}?\/?$/) return 1
  if (t ~ /(^|\/)work\/?$/ || t ~ /(^|\/)golden\/?$/) return 1
  if (t ~ /^\//) {
    u = trim_slash(t); p = trim_slash(proj)
    if (index(p "/", u "/") == 1) return 1         # the repo or an ancestor of it
    if (u == p "/work" || u == p "/work/golden") return 1
  }
  if (t ~ /(^|\/)fux\/?$/) return 1
  return 0
}
function excluded(s) {
  s = tolower(s)
  if (s ~ /--exclude-dir[= ]*[^ ]*golden/) return 1
  if (s ~ /(^| )(-g|--glob|--iglob)[= ]*["'"'"']?![^ ]*golden/) return 1
  if (s ~ /(^| )(-e|--exclude)[= ]*["'"'"']?[^ ]*golden/ && s ~ /(^| )fd( |$)/) return 1
  if (s ~ /-i?path[ ]+["'"'"']?[^ ]*golden[^ ]*["'"'"']?[ ]+-prune/) return 1
  if (s ~ /(-not|!|\\!)[ ]+-i?(path|wholename)[ ]+["'"'"']?[^ ]*golden/) return 1
  return 0
}
function base(t,   n, a) { t = strip(t); n = split(t, a, "/"); return a[n] }
# Quoted strings become one token: quotes dropped, and the spaces and shell
# operators inside them turned to "_", so `grep -rE "a|b" src` stays ONE
# segment with the root `src`, and `-g '"'"'!work/golden/**'"'"'` keeps its text.
function neutral(line,   out, i, ch, q) {
  out = ""; q = ""
  for (i = 1; i <= length(line); i++) {
    ch = substr(line, i, 1)
    if (q != "") {
      if (ch == q) { q = ""; continue }
      if (ch ~ /[ \t;|&()`<]/) ch = "_"
      out = out ch; continue
    }
    if (ch == "\"" || ch == "'"'"'") { q = ch; continue }
    out = out ch
  }
  return out
}
function takes_value(cmd, t) {
  if (cmd ~ /grep$/) return t ~ /^(-A|-B|-C|-m|-e|-f|-d|-D|--include|--exclude|--exclude-dir|--regexp|--file|--max-count|--context|--after-context|--before-context)$/
  if (cmd == "rg")   return t ~ /^(-A|-B|-C|-m|-e|-f|-g|-t|-T|-M|-j|-r|-E|--glob|--iglob|--type|--type-not|--max-count|--context|--after-context|--before-context|--regexp|--file|--max-depth|--maxdepth|--max-columns|--threads|--sort|--sortr|--encoding|--ignore-file|--pre|--replace)$/
  if (cmd == "ag" || cmd == "ack") return t ~ /^(-A|-B|-C|-m|-G|--ignore|--ignore-dir)$/
  if (cmd == "fd")   return t ~ /^(-e|-E|-t|-d|-x|-X|-j|-S|--extension|--exclude|--type|--max-depth|--exec|--exec-batch|--threads|--size|--changed-within|--changed-before)$/
  if (cmd == "tree") return t ~ /^(-L|-P|-I|-o)$/
  return 0
}
function check(seg,   n, tok, i, b, cmd, k, rec, isfind, pat_skipped, has_e, roots, risky, t) {
  n = split(seg, tok, /[ \t]+/)
  cmd = ""; k = 0
  for (i = 1; i <= n; i++) {
    b = base(tok[i])
    if (b ~ /^(grep|egrep|fgrep|rg|ag|ack|fd|find|tree|ls)$/) { cmd = b; k = i; break }
  }
  if (cmd == "") return 0
  rec = (cmd ~ /^(rg|ag|ack|fd|find|tree)$/); isfind = (cmd == "find"); has_e = 0
  for (i = k + 1; i <= n; i++) {
    t = tok[i]
    if (cmd ~ /grep$/ && (t ~ /^-[a-zA-Z]*[rR]/ || t == "--recursive" || t == "--dereference-recursive" || t ~ /^--directories=recurse/)) rec = 1
    if (cmd == "ls" && t ~ /^-[a-zA-Z]*R/) rec = 1
    if (t == "-e" || t ~ /^--regexp/ || t == "-f" || t ~ /^--file=/) has_e = 1
  }
  if (!rec || excluded(seg)) return 0
  roots = 0; risky = 0; pat_skipped = 0
  for (i = k + 1; i <= n; i++) {
    t = tok[i]
    if (t == "") continue
    if (isfind) {
      if (t ~ /^-/ || t == "!" || t == "\\!" || t == "\\") break
      roots++; if (root_risky(t)) risky = 1; continue
    }
    if (t ~ /^-/) { if (takes_value(cmd, t)) i++; continue }
    if (t ~ /^[0-9]*>/ || t ~ /^</) break                     # a redirection ends the args
    if (cmd ~ /^(grep|egrep|fgrep|rg|ag|ack|fd)$/ && !has_e && !pat_skipped) { pat_skipped = 1; continue }
    roots++; if (root_risky(t)) risky = 1
  }
  if (roots == 0) risky = cwd_risky()
  return risky
}
# W-227 — heredocs. `feeds_shell` is the base name of the command the heredoc
# is attached to: a shell runs its body, anything else reads it as data.
function feeds_shell(pre,   n, parts, w, i, b) {
  gsub(/&&|\|\||[;|&(]/, "\n", pre)
  n = split(pre, parts, "\n"); pre = parts[n]
  n = split(pre, w, /[ \t]+/)
  for (i = 1; i <= n; i++) {
    if (w[i] == "" || w[i] ~ /^[A-Za-z_][A-Za-z0-9_]*=/ || w[i] ~ /^(sudo|env|command|exec|nohup|time)$/) continue
    b = base(w[i])
    return (b ~ /^(sh|bash|zsh|dash|ksh|fish|eval|source|\.|xargs|ssh|parallel)$/)
  }
  return 1                                          # nothing named it: treat as a shell, fail closed
}
{
  raw = $0
  if (in_doc) {
    t = raw
    if (doc_tabs) sub(/^\t+/, "", t)
    if (t == doc_term) { in_doc = 0; next }
    if (!doc_shell) next                             # data, not commands
  }
  # Matched on the NEUTRAL line (W-230): a `<<EOF` inside quotes is text to bash,
  # and read raw it would make every later line look like a data body.
  line = neutral(raw)
  if (!in_doc && match(line, /<<-?[ \t]*[A-Za-z_][A-Za-z0-9_]*/) && substr(line, RSTART - 1, 1) != "<" && substr(line, RSTART + 2, 1) != "<") {
    marker = substr(line, RSTART, RLENGTH)
    doc_tabs = (substr(marker, 3, 1) == "-")
    doc_term = marker; sub(/^<<-?[ \t]*/, "", doc_term)
    doc_shell = feeds_shell(substr(line, 1, RSTART - 1))
    in_doc = 1
  }
  gsub(/\\[()]/, " ", line)                         # the find grouping, escaped parens, is not a subshell
  gsub(/\$\(/, ";", line); gsub(/`/, ";", line)
  gsub(/&&|\|\||[;|&()]/, "\n", line)
  m = split(line, segs, "\n")
  for (s = 1; s <= m; s++) if (check(segs[s])) hit = 1
}
END { exit hit ? 3 : 0 }
'
rc=$?
# W-227: only a clean 0 allows. 3 is a found walk; anything else — an awk error,
# a signal — is a hook that did not decide, and that is a deny.
[ "$rc" -eq 0 ] || deny
exit 0
