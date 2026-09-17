import os, sys, time, pathlib
d = pathlib.Path("d")
end = time.time() + 20
i = 0
while time.time() < end:
    i += 1
    p = d / f"{i%16:02x}.jsonl.tmp"
    p.write_bytes(b"x" * 4096)
    os.replace(p, d / f"{i%16:02x}.jsonl")
