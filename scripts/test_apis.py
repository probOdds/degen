#!/usr/bin/env python3
"""Test available APIs for monitoring Pump.fun graduations."""
import json
import urllib.request
import time

def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

print("=" * 60)
print("1. DexScreener — Latest Solana Pairs")
print("=" * 60)
try:
    data = fetch("https://api.dexscreener.com/latest/dex/pairs/solana")
    pairs = data.get("pairs", [])
    print(f"  Pairs returned: {len(pairs)}")
    for p in pairs[:5]:
        base = p.get("baseToken", {})
        symbol = base.get("symbol", "?")
        name = base.get("name", "?")
        address = base.get("address", "?")[:12]
        fdv = p.get("fdv", 0)
        vol = p.get("volume", {}).get("h24", 0)
        dex = p.get("dexId", "?")
        created = p.get("pairCreatedAt", 0)
        price_usd = p.get("priceUsd", "0")
        info = p.get("info", {})
        print(f"  {symbol} ({name[:20]}) | mcap=${fdv:,.0f} | vol24h=${vol:,.0f} | dex={dex} | addr={address}...")
except Exception as e:
    print(f"  ERROR: {e}")

print()
print("=" * 60)
print("2. DexScreener — Token Profiles (new listings)")
print("=" * 60)
try:
    data = fetch("https://api.dexscreener.com/token-profiles/latest/v1")
    if isinstance(data, list):
        print(f"  Profiles returned: {len(data)}")
        sol_profiles = [p for p in data if p.get("chainId") == "solana"]
        print(f"  Solana profiles: {len(sol_profiles)}")
        for p in sol_profiles[:5]:
            print(f"  {p.get('tokenAddress', '?')[:12]}... | links={[l.get('label','?') for l in p.get('links', [])]}")
    else:
        print(f"  Response type: {type(data)}")
except Exception as e:
    print(f"  ERROR: {e}")

print()
print("=" * 60)
print("3. DexScreener — Boosted Tokens")
print("=" * 60)
try:
    data = fetch("https://api.dexscreener.com/token-boosts/latest/v1")
    if isinstance(data, list):
        print(f"  Boosted tokens: {len(data)}")
        sol_boosts = [b for b in data if b.get("chainId") == "solana"]
        print(f"  Solana boosted: {len(sol_boosts)}")
        for b in sol_boosts[:3]:
            print(f"  {b.get('tokenAddress','?')[:12]}... amount={b.get('amount',0)}")
except Exception as e:
    print(f"  ERROR: {e}")

print()
print("=" * 60)
print("4. Jupiter Price API (Solana token prices)")
print("=" * 60)
try:
    # Test with SOL price
    data = fetch("https://api.jup.ag/price/v2?ids=So11111111111111111111111111111111111111112")
    print(f"  SOL price: ${data.get('data', {}).get('So11111111111111111111111111111111111111112', {}).get('price', '?')}")
except Exception as e:
    print(f"  ERROR: {e}")

print()
print("=" * 60)
print("5. GMGN — Graduation/Migration feed")
print("=" * 60)
try:
    # Try GMGN new pairs endpoint
    data = fetch("https://gmgn.ai/defi/quotation/v1/pairs/sol/new_pairs?limit=10&orderby=open_timestamp&direction=desc")
    if isinstance(data, dict):
        pairs_data = data.get("data", {}).get("pairs", [])
        print(f"  GMGN pairs: {len(pairs_data)}")
        for p in pairs_data[:5]:
            print(f"  {p.get('base_token_info',{}).get('symbol','?')} | mcap=${p.get('market_cap',0):,.0f} | created={p.get('open_timestamp',0)}")
    else:
        print(f"  Response: {str(data)[:200]}")
except Exception as e:
    print(f"  ERROR: {e}")

print()
print("=" * 60)
print("6. Birdeye — New token listings")
print("=" * 60)
try:
    data = fetch("https://public-api.birdeye.so/defi/v2/tokens/new_listing?chain=solana&limit=5")
    print(f"  Response: {str(data)[:300]}")
except Exception as e:
    print(f"  ERROR: {e}")

print()
print("=" * 60)
print("7. Helius — Check if free API works")
print("=" * 60)
try:
    # Just check if we can reach Helius
    data = fetch("https://mainnet.helius-rpc.com/?api-key=test")
    print(f"  Response: {str(data)[:200]}")
except Exception as e:
    err_str = str(e)
    if "401" in err_str or "403" in err_str:
        print(f"  Auth required (expected) — need API key from dev.helius.xyz")
    else:
        print(f"  ERROR: {e}")
