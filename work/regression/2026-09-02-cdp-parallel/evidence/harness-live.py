"""W-105's live check: real Chrome, real CDP, a real thread pool.

Each page's body states its own path. A response filed under the wrong URL is
therefore visible as a mismatch, which is exactly the corruption W-105 removes
and the thing no unit test in the repo can see.
"""
import http.server, importlib.util, json, os, shutil, socketserver, subprocess
import sys, tempfile, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

N_PAGES = 12
PORT_HTTP = 8781
PORT_CDP = 9223
PARALLEL = int(sys.argv[1]) if len(sys.argv) > 1 else 4
ARM = os.environ.get("ARM", "head")
ROWS = os.environ.get("ROWS", "")

REPO = "/Users/arpitarya/my_programs/fux"

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        # A little jitter so the workers actually interleave rather than
        # completing in issue order, which is what makes the race reachable.
        time.sleep(0.05 * ((hash(path) % 7) + 1))
        body = (f"<html><head><title>page {path}</title></head><body>"
                f"<h1>[MARKER:{path.strip(chr(47))}]</h1>"
                f"<p>this page is {path} and nothing else</p>"
                f"</body></html>").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("ETag", f'"etag-{path.strip("/")}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a):
        pass

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

def load_module():
    from importlib.machinery import SourceFileLoader
    loader = SourceFileLoader("cdp_live", os.path.join(REPO, "src/fux/templates/cdp.py.txt"))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cdp_live"] = mod
    loader.exec_module(mod)
    return mod

def tabs():
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT_CDP}/json", timeout=5) as r:
        return [t for t in json.loads(r.read()) if t.get("type") == "page"]

def main():
    srv = Server(("127.0.0.1", PORT_HTTP), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    profile = tempfile.mkdtemp(prefix="cdp-live-")
    chrome = subprocess.Popen(
        ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
         f"--remote-debugging-port={PORT_CDP}", f"--user-data-dir={profile}",
         "--no-first-run", "--no-default-browser-check", "--headless=new"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:
            tabs(); break
        except Exception:
            time.sleep(0.2)
    else:
        raise SystemExit("chrome never came up")

    before = {t["id"] for t in tabs()}
    print(f"tabs before: {len(before)}")

    mod = load_module()
    mod.configure({"cdp_port": PORT_CDP, "fetcher_max_parallel": PARALLEL,
                   "load_timeout_s": 60.0})
    print(f"MAX_PARALLEL = {mod.MAX_PARALLEL}")
    mod.connect()

    urls = [f"http://127.0.0.1:{PORT_HTTP}/p{i}" for i in range(1, N_PAGES + 1)]
    results = {}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        futures = {pool.submit(mod.fetch, u): u for u in urls}
        for fut, url in futures.items():
            try:
                body, ctype = fut.result()
                results[url] = (body.decode("utf-8", "replace"), ctype, None)
            except Exception as exc:
                results[url] = (None, None, repr(exc))
    elapsed = time.time() - t0

    during = {t["id"] for t in tabs()}
    print(f"tabs during/after fetch: {len(during)}  (+{len(during - before)} ours)")

    ok = bad = err = 0
    rows = []
    for url in urls:
        body, ctype, exc = results[url]
        want = "[MARKER:" + url.rsplit("/", 1)[1] + "]"
        if exc:
            verdict, err = "ERROR", err + 1
        elif want in body and sum(f"[MARKER:p{i}]" in body for i in range(1, N_PAGES+1)) == 1:
            verdict, ok = "match", ok + 1
        else:
            verdict, bad = "MISMATCH", bad + 1
        rows.append({"arm": ARM, "parallel": PARALLEL, "check": "fetch",
                     "url": url, "expected_marker": want,
                     "result": verdict, "pass": verdict == "match",
                     "detail": exc or ctype})
        print(f"  {verdict:9} {url}  {exc or ctype}")

    print(f"\nfetch: {ok} matched · {bad} MISMATCHED · {err} errored "
          f"in {elapsed:.1f}s at parallel={PARALLEL}")

    # validate() shares the session and must also take a per-thread tab.
    etags = {}
    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        futures = {pool.submit(mod.validate, u): u for u in urls}
        for fut, url in futures.items():
            try:
                etags[url] = fut.result()
            except Exception as exc:
                etags[url] = repr(exc)
    for url in urls:
        want_etag = f'"etag-{url.rsplit("/",1)[1]}"'
        got = etags[url]
        rows.append({"arm": ARM, "parallel": PARALLEL, "check": "validate",
                     "url": url, "expected_etag": want_etag,
                     "result": got, "pass": got == want_etag,
                     "detail": None})
    vok = sum(1 for u, e in etags.items() if e == f'"etag-{u.rsplit("/",1)[1]}"')
    print(f"validate: {vok}/{len(urls)} ETags matched their own URL")
    for u, e in sorted(etags.items()):
        if e != f'"etag-{u.rsplit("/",1)[1]}"':
            print(f"  MISMATCH {u} -> {e}")

    mod.close()
    time.sleep(0.5)
    after = {t["id"] for t in tabs()}
    leaked = after - before
    print(f"tabs after close(): {len(after)}  leaked: {len(leaked)}")

    chrome.terminate(); chrome.wait(timeout=10)
    srv.shutdown()
    shutil.rmtree(profile, ignore_errors=True)

    verdict = "PASS" if (bad == 0 and err == 0 and not leaked
                         and vok == len(urls)) else "FAIL"
    rows.append({"arm": ARM, "parallel": PARALLEL, "check": "tabs",
                 "url": None, "expected_leaked": 0,
                 "result": len(leaked), "pass": not leaked, "detail": None})
    if ROWS:
        with open(ROWS, "a", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
    print("\nRESULT:", verdict)

main()
