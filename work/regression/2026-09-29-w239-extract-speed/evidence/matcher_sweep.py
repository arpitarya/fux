import subprocess, time, sys
from pathlib import Path
from fux.query import identifiers as I
root = Path(".")
rules = I.for_root(root)
rx, groups, gated = I._compiled(rules)
assert gated is not None, "repo has a regex rule"
files = [f for f in subprocess.run(["git","ls-files","*.md"],capture_output=True,text=True).stdout.split("\n")
         if f and not f.startswith("work/golden/")]
n=bad=0; t_old=t_new=0.0
for f in files:
    p = root/f
    if not p.is_file(): continue
    text = p.read_text(encoding="utf-8", errors="replace")
    a=time.perf_counter(); old=[I._found(m, groups) for m in rx.finditer(text)]; b=time.perf_counter()
    new=rules.matches(text); c=time.perf_counter()
    t_old+=b-a; t_new+=c-b; n+=1
    if old!=new:
        bad+=1; print("MISMATCH", f, len(old), len(new))
print(f"{n} files, {bad} mismatches, {len(rules.rules)} families; old {t_old:.2f}s new {t_new:.2f}s ({t_old/t_new:.1f}x)")
