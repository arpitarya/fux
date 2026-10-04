"""Is `families.misfits[].missing` order a function of PYTHONHASHSEED on the SAME code?
usage: PYTHONHASHSEED=<n> PYTHONPATH=<head src> seed_check.py <root>"""
import json, sys
from pathlib import Path
from fux.inspect import as_dict, inspect_index
from fux.inspect._scan import read_index_view
root = Path(sys.argv[1])
view = read_index_view(root)
report = as_dict(inspect_index(root, probe_sample=None, retrieval_sample=None, progress=None, view=view,
                               top=view.config.triage_rows, rebuild_dictionary=False))
print(json.dumps([m["missing"] for m in report["families"]["misfits"]]))
