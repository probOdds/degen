#!/usr/bin/env python3
"""Test APIs with SSL fix for macOS Python."""
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
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        return json.loads(r.read())

# 1. DexScreener — Latest Solana Pairs
print("=== 1. DexScreener Latest Solana Pairs ===")
try:
    data = fetch("https://api.dexscreener.com/latest/dex/pairs/solana")
    pairs = data.get("pairs", [])
    print(f"Pairs: {len(pairs)}")
    for p in pairs[:5]:
        b = p.get("baseToken", {})
        sym = b.get("symbol", "?")
        name = b.get("name", "?")[:25]
        fdv = p.get("fdv", 0) or 0
        vol = (p.get("volume") or {}).get("h24", 0) or 0
        dex = p.get("dexId", "?")
        created = p.get("pairCreatedAt", 0)
        price = p.get("priceUsd", "0")
        print(f"  {sym:>10} | {name:<25} | mcap=${fdv:>12,.0f} | vol=${vol:>10,.0f} | dex={dex} | ${price}")
except Exception as e:
    print(f"  ERROR: {e}")

# 2. Jupiter Price API
print("\n=== 2. Jupiter Price API ===")
try:
    data = fetch("https://api.jup.ag/price/v2?ids=So11111111111111111111111111111111111111112")
    sol_data = data.get("data", {}).get("So11111111111111111111111111111111111111112", {})
    print(f"  SOL price: ${sol_data.get('price', '?')}")
except Exception as e:
    print(f"  ERROR: {e}")

# 3. DexScreener — Search for pump.fun graduated tokens
print("\n=== 3. DexScreener — Search 'pump' tokens ===")
try:
    data = fetch("https://api.dexscreener.com/latest/dex/search?q=pump")
    pairs = data.get("pairs", [])
    sol_pairs = [p for p in pairs if p.get("chainId") == "solana"]
    print(f"  Total pairs: {len(pairs)}, Solana: {len(sol_pairs)}")
    for p in sol_pairs[:3]:
        b = p.get("baseToken", {})
        print(f"  {b.get('symbol','?')} | mcap=${(p.get('fdv',0) or 0):,.0f} | dex={p.get('dexId','?')}")
except Exception as e:
    print(f"  ERROR: {e}")

# 4. DexScreener — Token Profiles (latest)
print("\n=== 4. DexScreener — Token Profiles ===")
try:
    data = fetch("https://api.dexscreener.com/token-profiles/latest/v1")
    if isinstance(data, list):
        sol_profiles = [p for p in data if p.get("chainId") == "solana"]
        print(f"  Total profiles: {len(data)}, Solana: {len(sol_profiles)}")
        for p in sol_profiles[:5]:
            addr = p.get("tokenAddress", "?")[:12]
            links = [l.get("type", "?") for l in p.get("links", [])]
            print(f"  {addr}... | links={links}")
    else:
        print(f"  Unexpected: {type(data)}")
except Exception as e:
    print(f"  ERROR: {e}")

# 5. Check Raydium API for new pools
print("\n=== 5. Raydium — New AMM Pools ===")
try:
    data = fetch("https://api-v3.raydium.io/pools/info/list?poolType=all&poolSortField=default&sortType=desc&pageSize=5&page=1")
    pools = data.get("data", {}).get("data", [])
    print(f"  Pools: {len(pools)}")
    for p in pools[:5]:
        mint_a = p.get("mintA", {}).get("symbol", "?")
        mint_b = p.get("mintB", {}).get("symbol", "?")
        tvl = p.get("tvl", 0)
        vol = p.get("day", {}).get("volume", 0)
        print(f"  {mint_a}/{mint_b} | tvl=${tvl:,.0f} | vol=${vol:,.0f}")
except Exception as e:
    print(f"  ERROR: {e}")

# 6. GMGN — Try different endpoints
print("\n=== 6. GMGN API Endpoints ===")
endpoints = [
    "https://gmgn.ai/defi/quotation/v1/rank/sol/swaps/1h?orderby=marketcap&direction=desc&limit=5",
    "https://gmgn.ai/defi/quotation/v1/pairs/sol/new_pairs?limit=5",
    "https://gmgn.ai/api/v1/sol/tokens/trending?limit=5",
]
for ep in endpoints:
    try:
        data = fetch(ep)
        print(f"  {ep.split('/')[-1].split('?')[0]}: OK — {str(data)[:150]}")
    except Exception as e:
        print(f"  {ep.split('/')[-1].split('?')[0]}: {e}")
