"""Mutating / build command handlers — print output, return an exit code."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from fux import (baseline, build, check, config, context, fix, gate, hookinstall,
                 importer, initcmd, mcpserver, paths, serve)
from fux.cliutil import root
from fux.findings import blocking


def cmd_init(args) -> int:
    info = initcmd.run(Path.cwd(), recall=args.recall)
    print(f"✔ Fux initialised at {info['footprint']}")
    print(f"  hooks wired   → {info['settings']}")
    print(f"  pointer added → {info['claude_md']}")
    print(f"  codex guide   → {info['agents_md']}")
    print(f"  copilot guide → {info['copilot_instructions']}")
    if info["copilot_prompts"]:
        print(f"  copilot prompts → {Path(info['copilot_prompts'][0]).parent}/")
    print("Next: `fux new formula <id>` to author your first rule, then `fux build`.")
    return 0


def cmd_hooks(args) -> int:
    """install | uninstall | status across git + claude + codex + copilot surfaces."""
    picked = [s for s in hookinstall.SURFACES if getattr(args, s, False)]
    surfaces = None if (getattr(args, "all", False) or not picked) else picked
    if args.action == "status":
        for surface, on in hookinstall.status(root()).items():
            print(f"  {'✔' if on else '·'} {surface:<8} {'wired' if on else 'not wired'}")
        return 0
    fn = hookinstall.uninstall if args.action == "uninstall" else hookinstall.install
    kw = {} if args.action == "uninstall" else {"recall": getattr(args, "recall", False)}
    verb = "removed from" if args.action == "uninstall" else "wired into"
    print(f"✔ Fux hooks {verb}:")
    for surface, where in fn(root(), surfaces, **kw).items():
        print(f"  {surface:<8} → {where}")
    return 0


def cmd_build(args) -> int:
    s = build.run(root(), full=getattr(args, "full", False),
                  no_xref=getattr(args, "no_xref", False),
                  profile=getattr(args, "profile", False))
    print(f"✔ Built: {s['active']} active rules · {s['code_files']} code files · "
          f"{s['edges']} edges · {s['communities']} communities → {s['out']}")
    if s.get("profile"):
        total = sum(secs for _, secs in s["profile"])
        print("  phase timings:")
        for phase, secs in s["profile"]:
            pct = (secs / total * 100) if total else 0.0
            print(f"    {phase:<18} {secs*1000:8.1f} ms  {pct:5.1f}%")
        print(f"    {'total':<18} {total*1000:8.1f} ms")
    return 0


def cmd_pii_scan(args) -> int:
    """Deterministic PII probe: hard identifiers (PAN/Aadhaar/account) in non-plan
    `.py`/`.md` → exit 2 (blocks the gate). $0, stdlib, no LLM (port of dante)."""
    from fux import gitutil, piiscan
    here = Path.cwd()
    given = list(getattr(args, "paths", None) or [])
    if given:
        targets = [Path(p) for p in given]
    else:
        # Scan the whole working tree: tracked ∪ untracked-not-ignored, so a stray
        # PAN in a new file is caught *before* `git add` — PII must not enter the
        # tree. Falls back to a raw walk when this isn't a git repo.
        names = gitutil.tracked_files(here, ["*.py", "*.md"]) + \
            gitutil.untracked_files(here, ["*.py", "*.md"])
        names = list(dict.fromkeys(names)) or \
            [str(p) for p in here.rglob("*.py")] + [str(p) for p in here.rglob("*.md")]
        targets = [here / n for n in names]
    hits = piiscan.scan(targets)
    print(piiscan.render(hits))
    return 2 if hits else 0


def cmd_self_build(_args) -> int:
    from fux import selfbuild
    s = selfbuild.build()
    print(f"✔ Self-knowledge bundle: {s['nodes']} nodes · {s['edges']} edges · "
          f"{s['rules']} rules → {s['bundle']}")
    return 0


def cmd_check(args) -> int:
    here = root()
    findings = check.run(here)
    if getattr(args, "baseline_write", None):
        n = baseline.write(Path(args.baseline_write), findings)
        print(f"✔ baseline written: {n} finding(s) → {args.baseline_write}")
        return 0
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
    base = Path(args.baseline) if getattr(args, "baseline", None) else None
    code, report = gate.run(here, strict_lint=args.strict_lint, baseline=base)
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
    """Copy bundled seed data (schema, hooks, global rules, skills) to agent homes.

    Equivalent to what install.sh does for a PyPI-installed package.
    Idempotent: global rules and packs are skipped if already present.
    """
    data = paths.bundled_data_dir()
    home_fux = paths.claude_home() / "fux"
    skills_dir = paths.claude_home() / "skills"
    codex_skills_dir = paths.codex_home() / "skills"
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
    for name in ("plan", "adr", "debate", "critic", "trace", "savings", "distill", "fetch-rules", "ingest", "propose-rules"):
        src = skills_src / name
        if src.exists():
            _copy_skill(src, skills_dir / f"fux-{name}")
    print(f"✔ sub-skills  → {skills_dir}/fux-{{plan,adr,debate,critic,trace,savings,distill,fetch-rules,ingest,propose-rules}}/")

    codex_skills_dir.mkdir(parents=True, exist_ok=True)
    _copy_skill(skills_src / "fux", codex_skills_dir / "fux")
    for name in ("plan", "adr", "debate", "critic", "trace", "savings", "distill", "fetch-rules", "ingest", "propose-rules"):
        src = skills_src / name
        if src.exists():
            _copy_skill(src, codex_skills_dir / f"fux-{name}")
    print(f"✔ codex skills → {codex_skills_dir}/fux*")

    print("\n✔ Fux assets installed.")
    print("  In any project: fux init  →  fux new formula <id>  →  fux build")
    return 0


def _copy_skill(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        if f.is_file():
            shutil.copy2(f, dst / f.name)
