#!/usr/bin/env python3
"""
Graduation Observer — Phase 0 Data Collection
==============================================
Monitors Pump.fun API for tokens that have completed their bonding curve
(graduated), then tracks their post-graduation price action via Jupiter.

Data saved to data/graduations_{date}.jsonl for analysis.

Uses subprocess curl for HTTPS (bypasses Python 3.14 SSL cert issues on macOS).
"""
import json
import subprocess
import time
import os
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

LOG_FILE = DATA_DIR / f"graduations_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"

# How often to check for new graduations (seconds)
POLL_INTERVAL = 20
# How many tokens to fetch per poll
FETCH_LIMIT = 50


def curl_json(url, timeout=15):
    """Fetch JSON via curl (avoids Python SSL issues on macOS)."""
    try:
        result = subprocess.run(
            ["curl", "-s", "-H", "User-Agent: Mozilla/5.0", url],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return None
        if not result.stdout.strip():
            return None
        return json.loads(result.stdout)
    except (json.JSONDecodeError, subprocess.TimeoutExpired, Exception):
        return None


def get_graduated_tokens(limit=50):
    """Get recently graduated tokens from Pump.fun API (complete=true)."""
    url = f"https://frontend-api-v3.pump.fun/coins/currently-live?limit={limit}"
    data = curl_json(url)
    if not data or not isinstance(data, list):
        return []
    return [t for t in data if t.get("complete") is True]


def get_all_recent_tokens(limit=50):
    """Get all recent tokens including non-graduated ones for context."""
    url = f"https://frontend-api-v3.pump.fun/coins/currently-live?limit={limit}"
    data = curl_json(url)
    if not data or not isinstance(data, list):
        return []
    return data


def get_dexscreener_price(mint_address):
    """Get current token price from DexScreener API."""
    url = f"https://api.dexscreener.com/latest/dex/tokens/{mint_address}"
    data = curl_json(url)
    if not data:
        return None
    pairs = data.get("pairs")
    if not pairs:
        return None
    # Use the first (highest liquidity) pair
    price = pairs[0].get("priceUsd")
    return float(price) if price else None


def get_token_detail(mint_address):
    """Get detailed token info from Pump.fun."""
    url = f"https://frontend-api-v3.pump.fun/coins/{mint_address}"
    return curl_json(url)


def log_entry(entry):
    """Append entry to JSONL log."""
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    print("=" * 60)
    print("  GRADUATION OBSERVER — Phase 0 Data Collection")
    print("=" * 60)
    print(f"  Log: {LOG_FILE}")
    print(f"  Poll interval: {POLL_INTERVAL}s")
    print(f"  Press Ctrl+C to stop\n")

    # Track known graduated tokens to detect NEW graduations
    known_grads = set()
    snapshot_count = 0
    new_grad_count = 0

    # Initial load — mark all current graduated tokens as "already known"
    print("  Loading currently graduated tokens...")
    initial = get_graduated_tokens(limit=FETCH_LIMIT)
    for t in initial:
        mint = t.get("mint", "")
        if mint:
            known_grads.add(mint)
    print(f"  {len(known_grads)} graduated tokens loaded. Watching for NEW ones...\n")

    while True:
        try:
            now = datetime.now(timezone.utc)
            snapshot_count += 1

            # Fetch current token list
            all_tokens = get_all_recent_tokens(limit=FETCH_LIMIT)
            graduated = [t for t in all_tokens if t.get("complete") is True]
            approaching = [t for t in all_tokens if not t.get("complete") and (t.get("usd_market_cap") or 0) > 50000]

            # Detect NEW graduations
            new_grads = []
            for t in graduated:
                mint = t.get("mint", "")
                if mint and mint not in known_grads:
                    known_grads.add(mint)
                    new_grads.append(t)

            # Log new graduations
            for t in new_grads:
                new_grad_count += 1
                mint = t.get("mint", "")
                symbol = t.get("symbol", "?")
                name = t.get("name", "?")[:30]
                mcap = t.get("usd_market_cap", 0) or 0
                has_twitter = bool(t.get("twitter"))
                has_telegram = bool(t.get("telegram"))
                has_website = bool(t.get("website"))

                # Get DexScreener price
                dex_price = get_dexscreener_price(mint)

                # Get more details
                detail = get_token_detail(mint)
                creator = None
                if detail and isinstance(detail, dict):
                    creator = detail.get("creator", "")

                entry = {
                    "ts": now.isoformat(),
                    "event": "graduation",
                    "mint": mint,
                    "symbol": symbol,
                    "name": name,
                    "mcap": mcap,
                    "dex_price": dex_price,
                    "has_twitter": has_twitter,
                    "has_telegram": has_telegram,
                    "has_website": has_website,
                    "creator": creator,
                    "image_uri": t.get("image_uri", ""),
                }
                log_entry(entry)

                social = []
                if has_twitter:
                    social.append("tw")
                if has_telegram:
                    social.append("tg")
                if has_website:
                    social.append("web")
                social_str = ",".join(social) if social else "none"

                print(f"  🎓 [{now.strftime('%H:%M:%S')}] NEW GRADUATION: {symbol:>10} ({name}) | mcap=${mcap:,.0f} | social=[{social_str}] | mint={mint[:12]}...")

            # Show tokens approaching graduation (near $69K)
            if approaching and snapshot_count % 5 == 0:
                print(f"  [{now.strftime('%H:%M:%S')}] Approaching graduation ({len(approaching)} tokens >$50K):")
                for t in approaching[:3]:
                    mcap = t.get("usd_market_cap", 0) or 0
                    pct = mcap / 69000 * 100
                    print(f"    {t.get('symbol','?'):>10} | mcap=${mcap:,.0f} ({pct:.0f}% to graduation)")

            # Status update
            if snapshot_count % 10 == 0:
                log_lines = sum(1 for _ in open(LOG_FILE)) if LOG_FILE.exists() else 0
                total_grads = len(graduated)
                print(f"  [{now.strftime('%H:%M:%S')}] Snapshot #{snapshot_count} | Live grads: {total_grads} | New grads detected: {new_grad_count} | Log: {log_lines} entries | Known: {len(known_grads)}")

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print(f"\n\n  Stopped. {snapshot_count} snapshots, {new_grad_count} new graduations detected.")
            if LOG_FILE.exists():
                lines = sum(1 for _ in open(LOG_FILE))
                print(f"  Log: {LOG_FILE} ({lines} entries)")
            break
        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    main()
