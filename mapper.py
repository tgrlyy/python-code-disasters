#!/usr/bin/env python3
import sys, os

fname = os.environ.get("mapreduce_map_input_file", "UNKNOWN")

if "python-code-disasters/" in fname:
    fname = fname.split("python-code-disasters/", 1)[1]
    fname = "python-code-disasters/" + fname

for _ in sys.stdin:
    print(f"{fname}\t1")