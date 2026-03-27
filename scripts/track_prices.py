#!/usr/bin/env python3
"""
Price Tracker — Follows new graduated tokens and records price action.
Reads from the graduation observer's log and tracks prices at 1m, 5m, 10m, 30m.
Run alongside observe_graduations.py.
"""
import json
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")
GRAD_LOG = DATA_DIR / f"graduations_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
PRICE_LOG = DATA_DIR / f"price_tracking_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"


def curl_json(url, timeout=10):
    try:
        result = subprocess.run(
            ["curl", "-s", "-H", "User-Agent: Mozilla/5.0", url],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except Exception:
        return None


def get_jupiter_price(mint):
    data = curl_json(f"https://api.jup.ag/price/v2?ids={mint}")
    if not data:
        return None
    token = data.get("data", {}).get(mint, {})
    price = token.get("price")
    return float(price) if price else None


def get_raydium_pool_price(pool_id):
    """Get current pool info from Raydium."""
    data = curl_json(f"https://api-v3.raydium.io/pools/info/ids?ids={pool_id}")
    if not data:
        return None
    pools = data.get("data", [])
    if pools:
        return {
            "price": pools[0].get("price", 0),
            "tvl": pools[0].get("tvl", 0),
            "vol": (pools[0].get("day") or {}).get("volume", 0),
        }
    return None


def main():
    print(f"Price Tracker — Phase 0")
    print(f"Reading graduations from: {GRAD_LOG}")
    print(f"Logging prices to: {PRICE_LOG}")
    print(f"Press Ctrl+C to stop\n")
    
    # Track tokens we're monitoring: {mint: {first_seen, symbol, prices: []}}
    tracking = {}
    processed_lines = 0
    
    while True:
        try:
            now = datetime.now(timezone.utc)
            
            # Read new graduation entries
            if GRAD_LOG.exists():
                with open(GRAD_LOG) as f:
                    lines = f.readlines()
                
                for line in lines[processed_lines:]:
                    try:
                        entry = json.loads(line.strip())
                        mint = entry.get("mint", "")
                        if mint and mint not in tracking and entry.get("event") == "new_pool":
                            tracking[mint] = {
                                "symbol": entry.get("symbol", "?"),
                                "name": entry.get("name", "?"),
                                "pool_id": entry.get("pool_id", ""),
                                "first_seen": entry.get("ts", ""),
                                "first_price": entry.get("jup_price"),
                                "first_tvl": entry.get("tvl", 0),
                                "prices": [],
                                "checkpoints": {},  # 1m, 5m, 10m, 30m
                            }
                            print(f"  Tracking: {entry.get('symbol','?')} ({mint[:12]}...)")
                    except json.JSONDecodeError:
                        pass
                
                processed_lines = len(lines)
            
            # Check prices for all tracked tokens
            active_tokens = []
            for mint, info in list(tracking.items()):
                first_seen_str = info.get("first_seen", "")
                if not first_seen_str:
                    continue
                
                try:
                    first_seen = datetime.fromisoformat(first_seen_str)
                except ValueError:
                    continue
                
                elapsed_min = (now - first_seen).total_seconds() / 60
                
                # Stop tracking after 60 minutes
                if elapsed_min > 60:
                    continue
                
                active_tokens.append((mint, info, elapsed_min))
            
            for mint, info, elapsed_min in active_tokens:
                price = get_jupiter_price(mint)
                
                if price is not None:
                    info["prices"].append({
                        "ts": now.isoformat(),
                        "elapsed_min": round(elapsed_min, 1),
                        "price": price,
                    })
                    
                    # Record checkpoints
                    first_price = info.get("first_price")
                    if first_price and first_price > 0:
                        pct_change = (price - first_price) / first_price * 100
                    else:
                        pct_change = None
                    
                    # Checkpoint logic
                    for cp_name, cp_min in [("1m", 1), ("5m", 5), ("10m", 10), ("30m", 30)]:
                        if cp_name not in info["checkpoints"] and elapsed_min >= cp_min:
                            info["checkpoints"][cp_name] = {
                                "price": price,
                                "pct_change": pct_change,
                                "elapsed": round(elapsed_min, 1),
                            }
                            
                            # Check if this would have been profitable
                            hit_tp = pct_change is not None and pct_change >= 30
                            hit_sl = pct_change is not None and pct_change <= -15
                            
                            status = ""
                            if hit_tp:
                                status = " *** TAKE PROFIT HIT ***"
                            elif hit_sl:
                                status = " *** STOP LOSS HIT ***"
                            
                            pct_str = f"{pct_change:+.1f}%" if pct_change is not None else "N/A"
                            print(f"  [{now.strftime('%H:%M:%S')}] {info['symbol']:>10} @ {cp_name}: ${price:.8f} ({pct_str}){status}")
                            
                            # Log checkpoint
                            log_entry = {
                                "ts": now.isoformat(),
                                "mint": mint,
                                "symbol": info["symbol"],
                                "checkpoint": cp_name,
                                "price": price,
                                "first_price": first_price,
                                "pct_change": pct_change,
                                "would_tp": hit_tp,
                                "would_sl": hit_sl,
                            }
                            with open(PRICE_LOG, "a") as f:
                                f.write(json.dumps(log_entry) + "\n")
                
                # Small delay between API calls to avoid rate limits
                time.sleep(0.5)
            
            if not active_tokens:
                pass  # Silent when nothing to track
            
            # Poll every 30 seconds
            time.sleep(30)
            
        except KeyboardInterrupt:
            print(f"\n\nStopped.")
            
            # Print summary
            print(f"\nSummary:")
            for mint, info in tracking.items():
                cps = info.get("checkpoints", {})
                cp_str = " | ".join(
                    f"{k}: {v.get('pct_change', 0):+.1f}%" if v.get("pct_change") is not None else f"{k}: N/A"
                    for k, v in sorted(cps.items())
                )
                print(f"  {info['symbol']:>10}: {cp_str}")
            
            break
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
