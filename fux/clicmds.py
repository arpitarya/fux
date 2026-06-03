"""Mutating / build command handlers — print output, return an exit code."""
from __future__ import annotations

from pathlib import Path

from fux import (build, check, config, context, fix, gate, initcmd, mcpserver,
                 paths, serve)
from fux.cliutil import root
from fux.findings import blocking


def cmd_init(args) -> int:
    info = initcmd.run(Path.cwd(), recall=args.recall)
    print(f"✔ Fux initialised at {info['footprint']}")
    print(f"  hooks wired   → {info['settings']}")
    print(f"  pointer added → {info['claude_md']}")
    print("Next: `fux new formula <id>` to author your first rule, then `fux build`.")
    return 0


def cmd_build(_args) -> int:
    s = build.run(root())
    print(f"✔ Built: {s['active']} active rules · {s['code_files']} code files · "
          f"{s['edges']} edges · {s['communities']} communities → {s['out']}")
    return 0


def cmd_check(args) -> int:
    here = root()
    findings = check.run(here)
    if args.fix:
        for n in fix.apply(here, findings):
            print(f"✔ fixed: {n}")
        findings = check.run(here)
    for f in findings:
        print(f.line())
    if not findings:
        print("✔ No drift — all rules current.")
    mode = config.load(paths.Footprint(here).config).get("mode")
    return 2 if (mode == "strict" and blocking(findings)) else 0


def cmd_context(_args) -> int:
    here = paths.find_project_root()
    if here:
        print(context.run(here))
    return 0


def cmd_gate(args) -> int:
    here = root()
    if args.install:
        hook = gate.install_precommit(here)
        print(f"✔ pre-commit gate installed → {hook}")
        print("  it runs `fux gate` on every commit; bypass once with `git commit --no-verify`.")
        return 0
    code, report = gate.run(here, strict_lint=args.strict_lint)
    print(report)
    return code


def cmd_mcp(_args) -> int:
    return mcpserver.serve()


def cmd_serve(args) -> int:
    return serve.serve(root(), port=args.port)
