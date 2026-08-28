"""R10 — the separation floor. MEASURES; `render.py` reports.

Executes the FROZEN pre-registration verbatim.

⚠ **Run it only under the frozen conditions** — `.fux/enrich/` absent and
`.fux/tune.toml` at defaults. Running it against the playground's normal
(enriched, reranked) state produces a different table under the same filename,
which happened once while this run was being filed and is why rendering is a
separate script over the saved `per-query.json`.

Bins, threshold, monotonicity rule and the separation==1.0 special case are all
read off `PRE-REGISTRATION.md` and are NOT choices made here.
"""
import json, subprocess, sys
from pathlib import Path

PG = Path.home() / "my_programs" / "fux-playground"
PY_ = PG / ".venv" / "bin" / "python"
T = 0.75          # ADR-QUALITY's frozen confidence target
NBINS = 10        # fixed before the data existed

def ask(q, top):
    p = subprocess.run([str(PY_), "-m", "fux.cli", "ask", q, "--json", "--top", str(top), "--band"],
                       cwd=PG, capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit(f"ask failed: {p.stderr[:300]}")
    return json.loads(p.stdout)

rows = []
for line in (PG / "goldens" / "queries.jsonl").read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    g = json.loads(line)
    want = g.get("max_rank", 1)
    d = ask(g["q"], max(5, want))
    locs = [r["loc"] for r in d["results"]]
    rank = next((i + 1 for i, l in enumerate(locs) if l == g["doc"]), None)
    correct = rank is not None and rank <= want
    sep = (d.get("confidence") or {}).get("separation")
    rows.append({"id": g["id"], "separation": sep, "correct": bool(correct),
                 "rank": rank, "max_rank": want, "band": (d.get("confidence") or {}).get("band")})

# --- the fixed bins -------------------------------------------------------
bins = [[] for _ in range(NBINS)]
for r in rows:
    s = min(max(r["separation"], 0.0), 1.0)
    idx = NBINS - 1 if s >= 1.0 else int(s * NBINS)
    bins[idx].append(r)

print(f"n = {len(rows)} goldens, {sum(r['correct'] for r in rows)} correct\n")
print(f"{'bin':<14}{'n':>4}{'correct':>9}{'P(correct)':>12}   note")
rates = []
for i, b in enumerate(bins):
    lo, hi = i / NBINS, (i + 1) / NBINS
    n = len(b); c = sum(r["correct"] for r in b)
    rate = (c / n) if n else None
    rates.append((lo, n, c, rate))
    shown = f"{rate:.2f}" if rate is not None else "--"
    note = "" if n else "empty bin"
    if n and n < 5: note = f"n={n}: interval far wider than +/-0.4"
    print(f"[{lo:.1f},{hi:.1f})   {n:>4}{c:>9}{shown:>12}   {note}")

# --- separation == 1.0, reported separately (frozen special case) ---------
ones = [r for r in rows if r["separation"] is not None and r["separation"] >= 1.0]
print(f"\nseparation == 1.0 (structural: exactly one document scored): "
      f"n={len(ones)}, correct={sum(r['correct'] for r in ones)}")

# --- the frozen floor rule ------------------------------------------------
floor = None
for i, (lo, n, c, rate) in enumerate(rates):
    if rate is None or rate < T:
        continue
    if all(rt is None or rt >= T for _, _, _, rt in rates[i:]):
        floor = lo
        break
print(f"\nlowest bin reaching P(correct) >= {T} AND staying >= it for every higher bin: "
      f"{'none' if floor is None else f'{floor:.1f}'}")
any_reaches = any(rt is not None and rt >= T for _, _, _, rt in rates)
occupied = [(lo, rt) for lo, n, c, rt in rates if n]
all_exceed = occupied and all(rt >= T for _, rt in occupied)
print(f"any bin reaches {T}: {any_reaches}   every OCCUPIED bin exceeds {T}: {bool(all_exceed)}")
Path(__file__).with_name("per-query.json").write_text(json.dumps(rows, indent=1))
