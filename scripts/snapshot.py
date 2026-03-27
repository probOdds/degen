#!/usr/bin/env python3
"""
Snapshot: capture all currently graduated Pump.fun tokens with prices.
Quick one-time snapshot for analysis.
"""
import json
import subprocess
from datetime import datetime, timezone

def curl_json(url, timeout=15):
    try:
        result = subprocess.run(
            ["curl", "-s", "-H", "User-Agent: Mozilla/5.0", url],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        return json.loads(result.stdout)
    except Exception:
        return None

now = datetime.now(timezone.utc)
print(f"Pump.fun Graduation Snapshot — {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
print("=" * 80)

# Get currently live tokens
data = curl_json("https://frontend-api-v3.pump.fun/coins/currently-live?limit=50")
if not data:
    print("Failed to fetch Pump.fun data")
    exit(1)

graduated = [t for t in data if t.get("complete") is True]
approaching = [t for t in data if not t.get("complete") and (t.get("usd_market_cap") or 0) > 40000]

print(f"\nGraduated tokens (complete=True): {len(graduated)}")
print(f"{'Symbol':>12} | {'Name':<25} | {'MCap':>12} | {'Social':>10} | {'Mint':>15}")
print("-" * 80)

for t in graduated:
    symbol = t.get("symbol", "?")
    name = t.get("name", "?")[:25]
    mcap = t.get("usd_market_cap", 0) or 0
    mint = t.get("mint", "?")[:15]
    
    social = []
    if t.get("twitter"): social.append("tw")
    if t.get("telegram"): social.append("tg")
    if t.get("website"): social.append("web")
    social_str = ",".join(social) if social else "none"
    
    print(f"{symbol:>12} | {name:<25} | ${mcap:>11,.0f} | {social_str:>10} | {mint}...")

print(f"\n\nApproaching graduation (>$40K mcap, not yet complete): {len(approaching)}")
print(f"{'Symbol':>12} | {'Name':<25} | {'MCap':>12} | {'% to Grad':>10}")
print("-" * 65)

for t in sorted(approaching, key=lambda x: x.get("usd_market_cap", 0) or 0, reverse=True):
    symbol = t.get("symbol", "?")
    name = t.get("name", "?")[:25]
    mcap = t.get("usd_market_cap", 0) or 0
    pct = mcap / 69000 * 100
    print(f"{symbol:>12} | {name:<25} | ${mcap:>11,.0f} | {pct:>8.1f}%")

# Get Jupiter prices for graduated tokens
print(f"\n\nJupiter prices for graduated tokens:")
print("-" * 60)
for t in graduated[:10]:
    mint = t.get("mint", "")
    symbol = t.get("symbol", "?")
    jup = curl_json(f"https://api.jup.ag/price/v2?ids={mint}")
    if jup:
        price_data = jup.get("data", {}).get(mint, {})
        price = price_data.get("price", "N/A")
        print(f"  {symbol:>10} | ${price}")
    else:
        print(f"  {symbol:>10} | price unavailable")
