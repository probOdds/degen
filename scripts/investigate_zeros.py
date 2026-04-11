#!/usr/bin/env python3
"""Quick investigation: why do so many tokens show exactly 0.0% change?"""
import json
from collections import defaultdict

prices = []
with open("data/price_tracking_2026-03-27.jsonl") as f:
    for line in f:
        prices.append(json.loads(line.strip()))

by_mint = defaultdict(list)
for p in prices:
    by_mint[p["mint"]].append(p)

zero_tokens = []
nonzero_tokens = []
for mint, recs in by_mint.items():
    pcts = [r.get("pct_change") for r in recs if r.get("pct_change") is not None]
    if pcts and all(p == 0.0 for p in pcts):
        zero_tokens.append((mint, recs))
    else:
        nonzero_tokens.append((mint, recs))

print(f"Tokens with ALL checkpoints at exactly 0.0%: {len(zero_tokens)} out of {len(by_mint)}")
print()

print("--- ZERO-CHANGE TOKEN DETAILS (first 8) ---")
for mint, recs in zero_tokens[:8]:
    sym = recs[0].get("symbol", "?")
    print(f"  {sym:>12s}: first_price={recs[0].get('first_price')}")
    for r in recs:
        print(f"    {r['checkpoint']:>4s}: price={r['price']}, first_price={r['first_price']}, same={r['price']==r['first_price']}")
    print()

print("--- NON-ZERO TOKEN EXAMPLES (first 5) ---")
for mint, recs in nonzero_tokens[:5]:
    sym = recs[0].get("symbol", "?")
    print(f"  {sym:>12s}:")
    for r in recs:
        pct = r.get("pct_change")
        pct_str = f"{pct:+.1f}%" if pct is not None else "null"
        print(f"    {r['checkpoint']:>4s}: price={r['price']}, first_price={r['first_price']}, pct={pct_str}")
    print()

# Also check: are these tokens truly stale (same price returned by DEX) or just
# very low volume tokens where price genuinely didn't move?
print("--- PRICE PRECISION CHECK ---")
print("Are zero-change tokens returning identical float values or just very close?")
for mint, recs in zero_tokens[:5]:
    sym = recs[0].get("symbol", "?")
    unique_prices = set(r["price"] for r in recs)
    print(f"  {sym:>12s}: {len(unique_prices)} unique price(s): {unique_prices}")
