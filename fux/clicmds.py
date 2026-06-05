"""Mutating / build command handlers — print output, return an exit code."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from fux import (build, check, config, context, fix, gate, importer, initcmd,
                 mcpserver, paths, serve)
from fux.cliutil import root
from fux.findings import blocking


def cmd_init(args) -> int:
    info = initcmd.run(Path.cwd(), recall=args.recall)
    print(f"✔ Fux initialised at {info['footprint']}")
    print(f"  hooks wired   → {info['settings']}")
    print(f"  pointer added → {info['claude_md']}")
    print("Next: `fux new formula <id>` to author your first rule, then `fux build`.")
    return 0


def cmd_build(args) -> int:
    s = build.run(root(), full=getattr(args, "full", False))
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


def cmd_import(args) -> int:
    created, skipped = importer.import_docs(root(), args.paths, rtype=args.type,
                                            domain=args.domain, force=args.force)
    for p in created:
        print(f"✔ imported → {p}")
    if skipped:
        print(f"· skipped {len(skipped)} existing (use --force to overwrite)")
    if created:
        print(f"Next: review the {len(created)} entr(y/ies), set `code_refs`, then `fux build`.")
    elif not skipped:
        print("fux: no .md files found to import.")
    return 0


def cmd_import_memory(args) -> int:
    created, skipped = importer.import_memory(root(), scope=args.scope, force=args.force)
    for p in created:
        print(f"✔ imported memory → {p}")
    if skipped:
        print(f"· skipped {len(skipped)} existing (use --force to overwrite)")
    if not created and not skipped:
        print("fux: no home-dir memory found for this project.")
    return 0


def cmd_setup(_args) -> int:
    """Copy bundled seed data (schema, hooks, global rules, skills) to ~/.claude/fux/.

    Equivalent to what install.sh does for a PyPI-installed package.
    Idempotent: global rules and packs are skipped if already present.
    """
    data = paths.bundled_data_dir()
    home_fux = paths.claude_home() / "fux"
    skills_dir = paths.claude_home() / "skills"
    home_fux.mkdir(parents=True, exist_ok=True)

    # schema.json
    shutil.copy2(data / "schema.json", home_fux / "schema.json")
    print(f"✔ schema      → {home_fux / 'schema.json'}")

    # hooks (chmod +x each script)
    dest_hooks = home_fux / "hooks"
    dest_hooks.mkdir(parents=True, exist_ok=True)
    for sh in sorted((data / "hooks").glob("*.sh")):
        dst = dest_hooks / sh.name
        shutil.copy2(sh, dst)
        dst.chmod(dst.stat().st_mode | 0o111)
    print(f"✔ hooks       → {dest_hooks}/")

    # packs (skip if already present — user may have customised)
    dest_packs = home_fux / "packs"
    if not dest_packs.exists():
        shutil.copytree(data / "packs", dest_packs)
        print(f"✔ packs       → {dest_packs}/")
    else:
        print(f"· packs       → {dest_packs}/ (exists — skipped)")

    # global rules seed (init as a git repo so users can push to a private remote)
    dest_global = home_fux / "global"
    if not dest_global.exists():
        shutil.copytree(data / "global", dest_global)
        for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                    ["git", "commit", "-qm", "seed global best practices"]):
            subprocess.run(cmd, cwd=dest_global, check=False,
                           capture_output=True)
        print(f"✔ global      → {dest_global}/ (git-initialised)")
        print("  Add a private remote to sync global rules across machines.")
    else:
        print(f"· global      → {dest_global}/ (exists — skipped)")

    # skills
    skills_dir.mkdir(parents=True, exist_ok=True)
    skills_src = data / "skills"
    _copy_skill(skills_src / "fux", skills_dir / "fux")
    print(f"✔ /fux skill  → {skills_dir / 'fux'}/")
    for name in ("plan", "adr", "trace", "savings", "distill", "fetch-rules"):
        src = skills_src / name
        if src.exists():
            _copy_skill(src, skills_dir / f"fux-{name}")
    print(f"✔ sub-skills  → {skills_dir}/fux-{{plan,adr,trace,savings,distill,fetch-rules}}/")

    print("\n✔ Fux assets installed.")
    print("  In any project: fux init  →  fux new formula <id>  →  fux build")
    return 0


def _copy_skill(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        if f.is_file():
            shutil.copy2(f, dst / f.name)
