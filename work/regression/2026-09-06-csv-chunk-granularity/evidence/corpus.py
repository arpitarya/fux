"""Seeded, deterministic CSV corpus + query/row pairs (fux-lab TEST-PLAN §5)."""
import random, hashlib, json, pathlib

SEED = 20260906
SERVICES = ["quota-gateway","session-broker","billing-reconciler","webhook-relay","search-indexer",
            "config-store","ingest-worker","auth-proxy","ledger-svc","payments-rails","edge-cache","notify-fanout"]
REGIONS = ["eu-central","us-east","us-west","ap-south","sa-east"]
TEAMS = ["platform","identity","billing","edge","data-infra","growth","payments"]
TIERS = ["tier-0","tier-1","tier-2","tier-3"]
ACTIONS = ["drain the backlog then restart","roll back to the previous tag","failover to the standby region",
           "rotate the signing key and redeploy","replay the reconciliation window","rebuild the shard from snapshot",
           "scale the consumer group and wait","flush the stale config and reload"]

def build(n_files=12, rows_per_file=(300, 800)):
    rng = random.Random(SEED)
    files, pairs = {}, []
    for f in range(n_files):
        name = f"ops/service-matrix-{f:02d}.csv"
        n = rng.randint(*rows_per_file)
        rows = ["service,region,team,tier,oncall_action,review_window_days"]
        for r in range(n):
            rows.append("{},{},{},{},{},{}".format(
                f"{rng.choice(SERVICES)}-{r:04d}", rng.choice(REGIONS), rng.choice(TEAMS),
                rng.choice(TIERS), rng.choice(ACTIONS), rng.choice([7,14,30,90,180])))
        files[name] = "\n".join(rows) + "\n"
        pairs.append((name, n))
    # 40 pairs: plant one distinctive answerable row per query, spread across files
    rng2 = random.Random(SEED + 1)
    queries = []
    used = {}                                        # per file: rows already planted
    for i in range(40):
        name, n = pairs[i % len(pairs)]
        body = files[name].split("\n")
        taken = used.setdefault(name, set())
        while True:                                  # distinct rows: a collision
            target_row = rng2.randint(1, min(n - 1, 499))  # csv.MAX_ROWS=500
            if target_row not in taken:              # earlier plant
                taken.add(target_row)
                break
        svc = f"kestrel-{i:03d}"
        action = rng2.choice(ACTIONS)
        region = rng2.choice(REGIONS)
        days = rng2.choice([7, 14, 30, 90, 180])
        body[target_row] = f"{svc},{region},{rng2.choice(TEAMS)},{rng2.choice(TIERS)},{action},{days}"
        files[name] = "\n".join(body)
        queries.append({
            "q": f"{svc} oncall action",          # natural-ish: service name + column intent
            "doc": name,
            "row_text": body[target_row],
            "row_index": target_row,
        })
    return files, queries

if __name__ == "__main__":
    files, queries = build()
    out = pathlib.Path("corpus"); out.mkdir(exist_ok=True)
    for name, text in files.items():
        p = out / pathlib.Path(name).name
        p.write_text(text)
    pathlib.Path("pairs.jsonl").write_text("\n".join(json.dumps(q) for q in queries) + "\n")
    digest = hashlib.sha256("".join(files[k] for k in sorted(files)).encode()).hexdigest()[:16]
    print("files:", len(files), "| rows:", sum(t.count(chr(10)) for t in files.values()),
          "| pairs:", len(queries), "| corpus sha256[:16]:", digest)
