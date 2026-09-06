import json, pathlib, statistics, sys, time, importlib
sys.path.insert(0, "/tmp/w/src")
from fux.decode import decode
import fux.refer._chunk as C
from fux.refer._rescore import rescore
from fux.refer._assemble import assemble, DEFAULT_BUDGET

PAIRS_FILE = sys.argv[1] if len(sys.argv) > 1 else "pairs.jsonl"
pairs = [json.loads(l) for l in open(PAIRS_FILE)]
corpus = {p.name: p.read_text() for p in pathlib.Path("corpus").glob("*.csv")}
decoded = {name: decode(text.encode(), name) for name, text in corpus.items()}

def run(arm, band):
    C.TABLE_ROWS_PER_PASSAGE = band
    hits1 = hits3 = 0; rr = []; noise = []; nbytes = []; npass = []
    t_chunk = []; t_res = []; t_asm = []
    for pr in pairs:
        loc = pathlib.Path(pr["doc"]).name
        md = decoded[loc]
        t0 = time.perf_counter(); passages = C.chunk(md); t1 = time.perf_counter()
        npass.append(len(passages))
        cand = [("file:" + loc, loc, "sha", passages)]
        t2 = time.perf_counter(); scored = rescore(pr["q"], cand); t3 = time.perf_counter()
        t4 = time.perf_counter()
        asm = assemble(scored, budget=DEFAULT_BUDGET, k=5, source="fetched")
        t5 = time.perf_counter()
        t_chunk.append((t1-t0)*1000); t_res.append((t3-t2)*1000); t_asm.append((t5-t4)*1000)
        cites = asm.citations
        total = sum(len(c.text.encode()) for c in cites)
        nbytes.append(total)
        # §3: match on the planted token, which survives the CSV -> Markdown
        # conversion. The first version of this compared a raw CSV line against
        # a Markdown table row and scored 0.0 on every arm.
        needle = pr.get("md_row") or pr["q"].split()[0]
        rank = next((i+1 for i, c in enumerate(cites) if needle in c.text), None)
        if rank == 1: hits1 += 1
        if rank and rank <= 3: hits3 += 1
        rr.append(1.0/rank if rank else 0.0)
        if rank:
            answer = len(pr["md_row"].encode())
            noise.append((total - answer) / total if total else 0.0)
    pct = lambda xs, p: sorted(xs)[min(len(xs)-1, int(round(p*(len(xs)-1))))]
    return {
        "arm": arm, "band_bytes": band, "pairs": len(pairs),
        "hit@1": round(hits1/len(pairs), 3), "hit@3": round(hits3/len(pairs), 3),
        "mrr": round(statistics.mean(rr), 3),
        "noise_ratio": round(statistics.mean(noise), 3) if noise else None,
        "bytes_returned_mean": int(statistics.mean(nbytes)),
        "passages_per_doc_mean": int(statistics.mean(npass)),
        "chunk_ms_p50": round(pct(t_chunk,.5),2), "chunk_ms_p95": round(pct(t_chunk,.95),2),
        "rescore_ms_p50": round(pct(t_res,.5),2), "rescore_ms_p95": round(pct(t_res,.95),2),
        "assemble_ms_p50": round(pct(t_asm,.5),2), "assemble_ms_p95": round(pct(t_asm,.95),2),
        "total_ms_p95": round(pct([a+b+c for a,b,c in zip(t_chunk,t_res,t_asm)],.95),2),
    }

results = [run("rows-58", 58), run("rows-11", 11), run("row", 1)]
pathlib.Path("results-" + pathlib.Path(PAIRS_FILE).stem + ".json").write_text(json.dumps(results, indent=2))
cols = ["arm","hit@1","hit@3","mrr","noise_ratio","bytes_returned_mean","passages_per_doc_mean",
        "chunk_ms_p95","rescore_ms_p95","total_ms_p95"]
print(" | ".join(c.ljust(12) for c in cols))
for r in results:
    print(" | ".join(str(r[c]).ljust(12) for c in cols))
