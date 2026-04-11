#!/usr/bin/env python3
"""
Pre-Graduation Observer — Phase 0B Data Collection
====================================================
Monitors Pump.fun bonding curve tokens BEFORE graduation to answer:
  "What % of tokens at $10K/$20K/$30K/$40K/$50K mcap actually graduate?"

Tracks tokens as they cross mcap thresholds on the bonding curve.
Records whether each token eventually graduates or dies back.

Data saved to data/pregrad_{date}.jsonl for analysis.

Uses subprocess curl for HTTPS (bypasses Python SSL issues).
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

LOG_FILE = DATA_DIR / f"pregrad_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"

# Mcap thresholds to track (tokens crossing these levels)
THRESHOLDS = [5000, 10000, 20000, 30000, 40000, 50000, 60000]

# How often to poll the API (seconds)
POLL_INTERVAL = 15

# How many tokens to fetch per poll
FETCH_LIMIT = 200

# Stop tracking a token after this many minutes of no progress
STALE_TIMEOUT_MIN = 120

# How often to check individual stale tokens via detail API (every N polls)
DETAIL_CHECK_INTERVAL = 20


def curl_json(url, timeout=15):
    """Fetch JSON via curl (avoids Python SSL issues)."""
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


def log_entry(entry):
    """Append entry to JSONL log."""
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    print("=" * 60)
    print("  PRE-GRADUATION OBSERVER — Phase 0B")
    print("=" * 60)
    print(f"  Log:            {LOG_FILE}")
    print(f"  Poll interval:  {POLL_INTERVAL}s")
    print(f"  Thresholds:     {THRESHOLDS}")
    print(f"  Press Ctrl+C to stop\n")

    # State: track tokens we've seen cross thresholds
    # {mint: {
    #   symbol, name, first_seen_ts, mcap_at_first_seen,
    #   thresholds_crossed: {threshold: {ts, mcap, rsol}},
    #   highest_mcap, last_seen_mcap, last_seen_ts,
    #   graduated: bool, died: bool
    # }}
    tracking = {}
    poll_count = 0
    events_logged = 0

    while True:
        try:
            now = datetime.now(timezone.utc)
            now_iso = now.isoformat()
            poll_count += 1

            # Fetch current live tokens
            data = curl_json(
                f"https://frontend-api-v3.pump.fun/coins/currently-live?limit={FETCH_LIMIT}"
            )
            if not data or not isinstance(data, list):
                if poll_count % 10 == 0:
                    print(f"  [{now.strftime('%H:%M:%S')}] API returned no data, retrying...")
                time.sleep(POLL_INTERVAL)
                continue

            # Separate graduated and on-curve tokens
            graduated_mints = set()
            on_curve = {}  # mint -> token data

            for t in data:
                mint = t.get("mint", "")
                if not mint:
                    continue
                if t.get("complete") is True:
                    graduated_mints.add(mint)
                else:
                    on_curve[mint] = t

            # Process on-curve tokens: check threshold crossings
            for mint, t in on_curve.items():
                mcap = t.get("usd_market_cap", 0) or 0
                rsol = (t.get("real_sol_reserves", 0) or 0) / 1e9
                symbol = t.get("symbol", "?")
                name = (t.get("name", "?") or "?")[:40]

                # Skip tokens below our lowest threshold
                if mcap < THRESHOLDS[0]:
                    continue

                # Initialize tracking if new
                if mint not in tracking:
                    tracking[mint] = {
                        "symbol": symbol,
                        "name": name,
                        "first_seen_ts": now_iso,
                        "first_seen_mcap": mcap,
                        "thresholds_crossed": {},
                        "highest_mcap": mcap,
                        "last_seen_mcap": mcap,
                        "last_seen_ts": now_iso,
                        "graduated": False,
                        "died": False,
                        "has_twitter": bool(t.get("twitter")),
                        "has_telegram": bool(t.get("telegram")),
                        "has_website": bool(t.get("website")),
                    }
                    print(f"  [{now.strftime('%H:%M:%S')}] NEW: {symbol:>10} at ${mcap:,.0f}")

                info = tracking[mint]

                # Update tracking state
                info["last_seen_mcap"] = mcap
                info["last_seen_ts"] = now_iso
                if mcap > info["highest_mcap"]:
                    info["highest_mcap"] = mcap

                # Check threshold crossings
                for threshold in THRESHOLDS:
                    thresh_key = str(threshold)
                    if thresh_key not in info["thresholds_crossed"] and mcap >= threshold:
                        info["thresholds_crossed"][thresh_key] = {
                            "ts": now_iso,
                            "mcap": mcap,
                            "rsol": round(rsol, 2),
                        }

                        # Log the threshold crossing event
                        entry = {
                            "ts": now_iso,
                            "event": "threshold_crossed",
                            "mint": mint,
                            "symbol": symbol,
                            "name": name,
                            "threshold": threshold,
                            "mcap": mcap,
                            "rsol": round(rsol, 2),
                            "has_twitter": info["has_twitter"],
                            "has_telegram": info["has_telegram"],
                            "has_website": info["has_website"],
                        }
                        log_entry(entry)
                        events_logged += 1

                        pct_to_grad = mcap / 69000 * 100
                        print(f"  [{now.strftime('%H:%M:%S')}] ↑ {symbol:>10} crossed ${threshold/1000:.0f}K (now ${mcap:,.0f}, {pct_to_grad:.0f}% to grad)")

            # Check if any tracked tokens just graduated
            for mint in list(tracking.keys()):
                info = tracking[mint]
                if info["graduated"] or info["died"]:
                    continue

                if mint in graduated_mints:
                    info["graduated"] = True
                    symbol = info["symbol"]

                    # Log graduation event
                    entry = {
                        "ts": now_iso,
                        "event": "graduated",
                        "mint": mint,
                        "symbol": symbol,
                        "name": info["name"],
                        "first_seen_mcap": info["first_seen_mcap"],
                        "highest_mcap": info["highest_mcap"],
                        "thresholds_crossed": info["thresholds_crossed"],
                        "time_tracked_min": round(
                            (now - datetime.fromisoformat(info["first_seen_ts"])).total_seconds() / 60, 1
                        ),
                        "has_twitter": info["has_twitter"],
                        "has_telegram": info["has_telegram"],
                        "has_website": info["has_website"],
                    }
                    log_entry(entry)
                    events_logged += 1

                    thresholds_str = ", ".join(
                        f"${int(k)/1000:.0f}K" for k in sorted(info["thresholds_crossed"].keys(), key=int)
                    )
                    print(f"  [{now.strftime('%H:%M:%S')}] 🎓 {symbol:>10} GRADUATED! Crossed: [{thresholds_str}]")

            # Periodically check for tokens that died (fell below thresholds)
            # A token "died" if it was tracked but hasn't been seen in the API
            # for STALE_TIMEOUT_MIN minutes and isn't graduated
            if poll_count % DETAIL_CHECK_INTERVAL == 0:
                for mint in list(tracking.keys()):
                    info = tracking[mint]
                    if info["graduated"] or info["died"]:
                        continue

                    # Check if token is stale (not seen in recent API results)
                    last_seen = datetime.fromisoformat(info["last_seen_ts"])
                    stale_min = (now - last_seen).total_seconds() / 60

                    if stale_min < STALE_TIMEOUT_MIN:
                        continue

                    # Token hasn't appeared in the API for a while.
                    # Check if it graduated via detail endpoint
                    detail = curl_json(f"https://frontend-api-v3.pump.fun/coins/{mint}")
                    time.sleep(0.3)

                    if detail and isinstance(detail, dict):
                        if detail.get("complete") is True:
                            # It graduated while we weren't watching closely
                            info["graduated"] = True
                            symbol = info["symbol"]
                            mcap = detail.get("usd_market_cap", 0) or 0

                            entry = {
                                "ts": now_iso,
                                "event": "graduated",
                                "mint": mint,
                                "symbol": symbol,
                                "name": info["name"],
                                "first_seen_mcap": info["first_seen_mcap"],
                                "highest_mcap": info["highest_mcap"],
                                "final_mcap": mcap,
                                "thresholds_crossed": info["thresholds_crossed"],
                                "time_tracked_min": round(stale_min, 1),
                                "note": "detected_via_detail_check",
                                "has_twitter": info["has_twitter"],
                                "has_telegram": info["has_telegram"],
                                "has_website": info["has_website"],
                            }
                            log_entry(entry)
                            events_logged += 1
                            print(f"  [{now.strftime('%H:%M:%S')}] 🎓 {symbol:>10} GRADUATED (detected late)")
                        else:
                            # Token is still on the curve but not in the live feed
                            # Check its current mcap
                            mcap = detail.get("usd_market_cap", 0) or 0
                            if mcap < THRESHOLDS[0]:
                                # Died — fell below our lowest threshold
                                info["died"] = True
                                symbol = info["symbol"]

                                entry = {
                                    "ts": now_iso,
                                    "event": "died",
                                    "mint": mint,
                                    "symbol": symbol,
                                    "name": info["name"],
                                    "first_seen_mcap": info["first_seen_mcap"],
                                    "highest_mcap": info["highest_mcap"],
                                    "final_mcap": mcap,
                                    "thresholds_crossed": info["thresholds_crossed"],
                                    "time_tracked_min": round(stale_min, 1),
                                    "has_twitter": info["has_twitter"],
                                    "has_telegram": info["has_telegram"],
                                    "has_website": info["has_website"],
                                }
                                log_entry(entry)
                                events_logged += 1
                                print(f"  [{now.strftime('%H:%M:%S')}] 💀 {symbol:>10} DIED (mcap=${mcap:,.0f}, was ${info['highest_mcap']:,.0f})")
                            else:
                                # Still alive, update tracking
                                info["last_seen_mcap"] = mcap
                                info["last_seen_ts"] = now_iso
                    else:
                        # Can't fetch detail — assume died if stale > 4 hours
                        if stale_min > 240:
                            info["died"] = True
                            symbol = info["symbol"]
                            entry = {
                                "ts": now_iso,
                                "event": "died",
                                "mint": mint,
                                "symbol": symbol,
                                "name": info["name"],
                                "first_seen_mcap": info["first_seen_mcap"],
                                "highest_mcap": info["highest_mcap"],
                                "final_mcap": info["last_seen_mcap"],
                                "thresholds_crossed": info["thresholds_crossed"],
                                "time_tracked_min": round(stale_min, 1),
                                "note": "assumed_dead_no_api_response",
                                "has_twitter": info["has_twitter"],
                                "has_telegram": info["has_telegram"],
                                "has_website": info["has_website"],
                            }
                            log_entry(entry)
                            events_logged += 1
                            print(f"  [{now.strftime('%H:%M:%S')}] 💀 {symbol:>10} DIED (no API response, stale {stale_min:.0f}m)")

            # Status update
            if poll_count % 20 == 0:
                active = sum(1 for i in tracking.values() if not i["graduated"] and not i["died"])
                grads = sum(1 for i in tracking.values() if i["graduated"])
                deaths = sum(1 for i in tracking.values() if i["died"])
                log_lines = sum(1 for _ in open(LOG_FILE)) if LOG_FILE.exists() else 0
                print(f"  [{now.strftime('%H:%M:%S')}] Poll #{poll_count} | Active: {active} | Graduated: {grads} | Died: {deaths} | Events: {log_lines}")

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print(f"\n\n  Stopped. {poll_count} polls, {events_logged} events logged.")
            if LOG_FILE.exists():
                lines = sum(1 for _ in open(LOG_FILE))
                print(f"  Log: {LOG_FILE} ({lines} entries)")

            # Print summary
            active = sum(1 for i in tracking.values() if not i["graduated"] and not i["died"])
            grads = sum(1 for i in tracking.values() if i["graduated"])
            deaths = sum(1 for i in tracking.values() if i["died"])
            print(f"\n  Summary: {len(tracking)} tokens tracked, {grads} graduated, {deaths} died, {active} still active")

            # Conditional graduation rates
            if tracking:
                print(f"\n  Conditional graduation rates:")
                for threshold in THRESHOLDS:
                    thresh_key = str(threshold)
                    crossed = [i for i in tracking.values() if thresh_key in i["thresholds_crossed"]]
                    if crossed:
                        grad_count = sum(1 for i in crossed if i["graduated"])
                        rate = grad_count / len(crossed) * 100
                        print(f"    ${threshold/1000:.0f}K: {grad_count}/{len(crossed)} graduated ({rate:.0f}%)")

            break
        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    main()
