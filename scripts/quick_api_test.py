#!/usr/bin/env python3
"""Quick test: DexScreener and Jupiter APIs only."""
import ssl
import json
import urllib.request

try:
    import certifi
    ctx = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
        return json.loads(r.read())

print("=== DexScreener Latest Solana Pairs ===")
try:
    data = fetch("https://api.dexscreener.com/latest/dex/pairs/solana")
    pairs = data.get("pairs", [])
    print(f"Pairs returned: {len(pairs)}")
    for p in pairs[:5]:
        b = p.get("baseToken", {})
        sym = b.get("symbol", "?")
        name = b.get("name", "?")[:25]
        fdv = p.get("fdv") or 0
        vol = (p.get("volume") or {}).get("h24", 0) or 0
        dex = p.get("dexId", "?")
        price = p.get("priceUsd", "0")
        created = p.get("pairCreatedAt", 0)
        labels = p.get("labels", [])
        print(f"  {sym:>10} | {name:<25} | mcap=${fdv:>12,.0f} | vol=${vol:>10,.0f} | {dex} | labels={labels}")
except Exception as e:
    print(f"  ERROR: {e}")

print()
print("=== Jupiter Price API ===")
try:
    data = fetch("https://api.jup.ag/price/v2?ids=So11111111111111111111111111111111111111112")
    sol = data.get("data", {}).get("So11111111111111111111111111111111111111112", {})
    print(f"  SOL price: ${sol.get('price', '?')}")
except Exception as e:
    print(f"  ERROR: {e}")

print()
print("=== Raydium Pools API ===")
try:
    data = fetch("https://api-v3.raydium.io/pools/info/list?poolType=all&poolSortField=default&sortType=desc&pageSize=5&page=1")
    pools_data = data.get("data", {})
    pools = pools_data.get("data", [])
    print(f"  Pools: {len(pools)}")
    for p in pools[:3]:
        ma = p.get("mintA", {}).get("symbol", "?")
        mb = p.get("mintB", {}).get("symbol", "?")
        tvl = p.get("tvl", 0) or 0
        vol = (p.get("day") or {}).get("volume", 0) or 0
        print(f"  {ma}/{mb} | tvl=${tvl:,.0f} | vol=${vol:,.0f}")
except Exception as e:
    print(f"  ERROR: {e}")
