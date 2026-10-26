#!/usr/bin/env python3
"""PreToolUse(Bash) — SR-ARCHITECTURE decision 12: only lockmaster writes to main.

An agent's `git commit` (or merge, cherry-pick, revert, am, rebase) while
`main` is checked out is refused, with the way round: `lockmaster start` /
`lockmaster submit`. lockmaster's own landing runs git from inside
`lockmaster`, never through the agent's Bash tool, so it is not seen here.

A `git push` that updates `main` passes only when it is plain: every option
is on SAFE_PUSH_OPTIONS and no refspec forces (`+`) or deletes (`:main`), so
the remote takes it only as a fast-forward of what lockmaster landed
(ruled by the decider, 2026-10-26). Anything else that would update `main`
is refused. An allow-list, so an option this hook does not know is refused.

A heredoc's body is text, not commands, and is not judged.

It binds agent sessions only: it is a Claude Code hook, so the decider's own
terminal is untouched and can still commit to main by hand (W-05 hazard).
The branch is `lockmaster.toml` `[main] branch`, else `main`.
Standard library only; it does not need lockmaster installed.
"""
import json
import os
import re
import shlex
import subprocess
import sys

WRITES = ("commit", "merge", "cherry-pick", "revert", "am", "rebase")
HARMLESS = ("--abort", "--quit", "-h", "--help")
# The only options a push that updates main may carry.
SAFE_PUSH_OPTIONS = {"-u", "--set-upstream", "-q", "--quiet", "-v", "--verbose", "--atomic",
                     "--follow-tags", "--no-follow-tags", "--porcelain", "--progress", "--no-progress"}
HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
OPERATORS = {"&&", "||", ";", "|", "&", ";;", "|&"}
# git's global options that take a value as the next word.
VALUED = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"}


def git(args, cwd):
    try:
        r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def main_branch(cwd):
    top = git(["rev-parse", "--show-toplevel"], cwd)
    if top:
        root = git(["worktree", "list", "--porcelain"], top)
        first = root.splitlines()[0][len("worktree "):] if root else top
        try:
            text = open(os.path.join(first, "lockmaster.toml"), encoding="utf-8").read()
        except OSError:
            text = ""
        m = re.search(r"^\[main\][^\[]*?^branch\s*=\s*[\"']([^\"']+)[\"']", text, re.M | re.S)
        if m:
            return m.group(1)
    return "main"


def without_heredocs(command):
    """The command with every heredoc body taken out: those lines are input, not commands."""
    out, ending = [], []
    for line in command.split("\n"):
        if ending:
            if line.strip() == ending[0]:
                ending.pop(0)
            continue
        out.append(line)
        ending = [m.group(2) for m in HEREDOC_RE.finditer(line)]
    return "\n".join(out)


def segments(command):
    command = without_heredocs(command)
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    seg = []
    try:
        for tok in lexer:
            if tok in OPERATORS:
                if seg:
                    yield seg
                seg = []
            else:
                seg.append(tok)
    except ValueError:  # unbalanced quotes: judge what was read
        pass
    if seg:
        yield seg


def refused(command, cwd):
    """The reason this command writes to main, or None."""
    for seg in segments(command):
        while seg and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", seg[0]):
            seg = seg[1:]  # VAR=value prefixes
        while seg and seg[0] in ("command", "env", "sudo", "exec", "nohup", "time"):
            seg = seg[1:]
        if not seg:
            continue
        if seg[0] == "cd":
            target = os.path.expanduser(seg[1]) if len(seg) > 1 else os.path.expanduser("~")
            cwd = os.path.normpath(os.path.join(cwd, target))
            continue
        if os.path.basename(seg[0]) != "git":
            continue
        here, i = cwd, 1
        while i < len(seg) and seg[i].startswith("-"):
            opt = seg[i]
            if opt == "-C" and i + 1 < len(seg):
                here = os.path.normpath(os.path.join(here, os.path.expanduser(seg[i + 1])))
            if opt in VALUED:
                i += 2
            else:
                i += 1
        if i >= len(seg):
            continue
        sub, rest = seg[i], seg[i + 1:]
        if not os.path.isdir(here):
            continue
        main = main_branch(here)
        current = git(["symbolic-ref", "--short", "-q", "HEAD"], here)
        if sub in WRITES and current == main and not any(a in HARMLESS for a in rest):
            return "`git {}` on {}".format(sub, main)
        if sub == "push":
            options = [a for a in rest if a.startswith("-")]
            refspecs = [a for a in rest if not a.startswith("-")][1:]
            targets_main = (not refspecs and current == main) or any(
                o in ("--all", "--mirror", "--branches") for o in options)
            unsafe = []
            for spec in refspecs:
                src, _, dst = spec.lstrip("+").partition(":")
                dst = dst or src
                if dst in (main, "refs/heads/" + main) or (dst == "HEAD" and current == main):
                    targets_main = True
                    if spec.startswith("+") or (":" in spec and not src):
                        unsafe.append(spec)
            if targets_main:
                unsafe += [o for o in options if o not in SAFE_PUSH_OPTIONS]
                if unsafe:
                    return "`git push {}` updates {} with {} — only a plain push may".format(
                        " ".join(rest), main, ", ".join(unsafe))
    return None


def main():
    try:
        hook = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    command = (hook.get("tool_input") or {}).get("command") or ""
    if "git" not in command:
        return 0
    why = refused(command, hook.get("cwd") or os.getcwd())
    if not why:
        return 0
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            "Refused: {}. Only lockmaster writes to main, and only a plain push sends it "
            "(SR-ARCHITECTURE decision 12). "
            "Work on a change instead: `lockmaster start <W-nn> --paths <path>…`, edit in its "
            "worktree, then `lockmaster submit -m \"…\"` — it lands on main for you. "
            "The decider can still commit to main by hand from a terminal.").format(why)}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
