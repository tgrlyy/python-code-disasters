#!/usr/bin/env python3
import sys
from collections import defaultdict
counts = defaultdict(int)
for line in sys.stdin:
    k, v = line.strip().split("\t")
    counts[k] += int(v)
for k in sorted(counts):
    print(f"{k}\t{counts[k]}")