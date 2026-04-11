#!/usr/bin/env python3
"""Quick sample size check for pre-grad data."""
import json
from collections import Counter
from pathlib import Path

DATA_DIR = Path("/opt/probodds/degen/data")

all_records = []
for f in sorted(DATA_DIR.glob("pregrad_*.jsonl")):
    with open(f) as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    all_records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

events = Counter(r["event"] for r in all_records)
print(f"Total records: {len(all_records)}")
for e, c in events.most_common():
    print(f"  {e}: {c}")

tokens = {}
for r in all_records:
    mint = r.get("mint", "")
    if not mint:
        continue
    if mint not in tokens:
        tokens[mint] = {"outcome": "active", "thresholds": set()}
    if r["event"] == "threshold_crossed":
        tokens[mint]["thresholds"].add(r["threshold"])
    elif r["event"] == "graduated":
        tokens[mint]["outcome"] = "graduated"
    elif r["event"] == "died":
        tokens[mint]["outcome"] = "died"

outcomes = Counter(t["outcome"] for t in tokens.values())
print(f"\nUnique tokens: {len(tokens)}")
for o, c in outcomes.most_common():
    print(f"  {o}: {c}")

print(f"\nConditional graduation rates (resolved only):")
for thresh in [5000, 10000, 20000, 30000, 40000, 50000, 60000]:
    crossed = [t for t in tokens.values() if thresh in t["thresholds"]]
    resolved = [t for t in crossed if t["outcome"] in ("graduated", "died")]
    grads = [t for t in resolved if t["outcome"] == "graduated"]
    active = [t for t in crossed if t["outcome"] == "active"]
    if crossed:
        r = len(grads) / len(resolved) * 100 if resolved else 0
        print(f"  ${thresh/1000:.0f}K: {len(grads)}/{len(resolved)} graduated ({r:.1f}%) | {len(active)} active | {len(crossed)} total")
