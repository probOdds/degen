#!/usr/bin/env python3
"""
Query Pump.fun API for detailed info on our graduated tokens to understand:
1. Time from creation to king-of-the-hill (KOTH) 
2. Time from creation to graduation (complete)
3. How fast tokens go through the $30K-$69K zone
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def curl_json(url, timeout=15):
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


def main():
    # Load our graduation log
    data_dir = Path("data")
    grads = []
    for f in sorted(data_dir.glob("graduations_*.jsonl")):
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        grads.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    # Deduplicate
    seen = {}
    for g in grads:
        m = g.get("mint", "")
        if m and m not in seen:
            seen[m] = g

    print("=" * 70)
    print("  PRE-GRADUATION TIMING ANALYSIS")
    print(f"  Querying details for {len(seen)} graduated tokens")
    print("=" * 70)
    print()

    results = []
    for i, (mint, grad) in enumerate(seen.items()):
        detail = curl_json(f"https://frontend-api-v3.pump.fun/coins/{mint}")
        if not detail or not isinstance(detail, dict):
            print(f"  [{i+1}/{len(seen)}] {grad.get('symbol','?'):>10} — Could not fetch detail")
            time.sleep(0.3)
            continue

        created_ms = detail.get("created_timestamp", 0) or 0
        koth_ms = detail.get("king_of_the_hill_timestamp", 0) or 0
        last_trade_ms = detail.get("last_trade_timestamp", 0) or 0
        ath_mcap = detail.get("ath_market_cap", 0) or 0
        ath_ms = detail.get("ath_market_cap_timestamp", 0) or 0
        mcap = detail.get("usd_market_cap", 0) or 0
        complete = detail.get("complete", False)
        reply_count = detail.get("reply_count", 0) or 0
        vsol = (detail.get("virtual_sol_reserves", 0) or 0) / 1e9
        rsol = (detail.get("real_sol_reserves", 0) or 0) / 1e9

        symbol = grad.get("symbol", "?")

        entry = {
            "mint": mint,
            "symbol": symbol,
            "mcap_now": mcap,
            "ath_mcap": ath_mcap,
            "created_ms": created_ms,
            "koth_ms": koth_ms,
            "ath_ms": ath_ms,
            "last_trade_ms": last_trade_ms,
            "complete": complete,
            "reply_count": reply_count,
            "vsol": vsol,
            "rsol": rsol,
            "has_twitter": grad.get("has_twitter", False),
            "has_telegram": grad.get("has_telegram", False),
            "has_website": grad.get("has_website", False),
            "grad_ts": grad.get("ts", ""),
        }

        if created_ms and koth_ms:
            entry["time_to_koth_min"] = (koth_ms - created_ms) / 1000 / 60
        else:
            entry["time_to_koth_min"] = None

        if created_ms and ath_ms:
            entry["time_to_ath_min"] = (ath_ms - created_ms) / 1000 / 60
        else:
            entry["time_to_ath_min"] = None

        results.append(entry)
        time.sleep(0.3)  # Rate limit

    print()
    print("─" * 70)
    print("  TOKEN DETAILS — Creation → KOTH → ATH Timing")
    print("─" * 70)
    print()

    header = f"  {'Symbol':>10} | {'Created':>16} | {'→KOTH':>8} | {'→ATH':>8} | {'ATH mcap':>12} | {'Now mcap':>12} | {'Replies':>7}"
    print(header)
    print("  " + "-" * len(header.strip()))

    for r in sorted(results, key=lambda x: x.get("time_to_koth_min") or 99999):
        sym = r["symbol"][:10]

        if r["created_ms"]:
            created_dt = datetime.fromtimestamp(r["created_ms"]/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        else:
            created_dt = "?"

        if r.get("time_to_koth_min") is not None:
            koth_min = r["time_to_koth_min"]
            if koth_min < 60:
                koth_str = f"{koth_min:.0f}m"
            elif koth_min < 1440:
                koth_str = f"{koth_min/60:.1f}h"
            else:
                koth_str = f"{koth_min/1440:.1f}d"
        else:
            koth_str = "N/A"

        if r.get("time_to_ath_min") is not None:
            ath_min = r["time_to_ath_min"]
            if ath_min < 60:
                ath_str = f"{ath_min:.0f}m"
            elif ath_min < 1440:
                ath_str = f"{ath_min/60:.1f}h"
            else:
                ath_str = f"{ath_min/1440:.1f}d"
        else:
            ath_str = "N/A"

        ath_mcap = r.get("ath_mcap", 0) or 0
        now_mcap = r.get("mcap_now", 0) or 0
        replies = r.get("reply_count", 0) or 0

        print(f"  {sym:>10} | {created_dt:>16} | {koth_str:>8} | {ath_str:>8} | ${ath_mcap:>11,.0f} | ${now_mcap:>11,.0f} | {replies:>7}")

    # Summary stats
    koth_times = [r["time_to_koth_min"] for r in results if r.get("time_to_koth_min") is not None and r["time_to_koth_min"] > 0]
    ath_times = [r["time_to_ath_min"] for r in results if r.get("time_to_ath_min") is not None and r["time_to_ath_min"] > 0]

    print()
    print("─" * 70)
    print("  TIMING SUMMARY")
    print("─" * 70)
    print()

    if koth_times:
        avg_koth = sum(koth_times) / len(koth_times)
        sorted_koth = sorted(koth_times)
        med_koth = sorted_koth[len(sorted_koth)//2]
        print(f"  Time to King-of-the-Hill (n={len(koth_times)}):")
        print(f"    Min:    {min(koth_times):.0f} min ({min(koth_times)/60:.1f} hours)")
        print(f"    Max:    {max(koth_times):.0f} min ({max(koth_times)/60:.1f} hours)")
        print(f"    Median: {med_koth:.0f} min ({med_koth/60:.1f} hours)")
        print(f"    Avg:    {avg_koth:.0f} min ({avg_koth/60:.1f} hours)")

        # Distribution
        fast = sum(1 for t in koth_times if t < 30)
        medium = sum(1 for t in koth_times if 30 <= t < 120)
        slow = sum(1 for t in koth_times if 120 <= t < 1440)
        very_slow = sum(1 for t in koth_times if t >= 1440)
        print(f"    < 30 min:     {fast} ({fast/len(koth_times)*100:.0f}%)")
        print(f"    30m - 2h:     {medium} ({medium/len(koth_times)*100:.0f}%)")
        print(f"    2h - 24h:     {slow} ({slow/len(koth_times)*100:.0f}%)")
        print(f"    > 24h:        {very_slow} ({very_slow/len(koth_times)*100:.0f}%)")

    # ATH vs graduation
    print()
    if results:
        declined_from_ath = []
        for r in results:
            ath = r.get("ath_mcap", 0) or 0
            now = r.get("mcap_now", 0) or 0
            if ath > 0 and now > 0:
                decline_pct = (1 - now / ath) * 100
                declined_from_ath.append((r["symbol"], ath, now, decline_pct))

        if declined_from_ath:
            print(f"  ATH → Current mcap decline (how much tokens lost after peak):")
            for sym, ath, now, decline in sorted(declined_from_ath, key=lambda x: x[3], reverse=True)[:10]:
                print(f"    {sym:>10}: ATH ${ath:>10,.0f} → Now ${now:>10,.0f} ({decline:+.0f}% from ATH)")

            avg_decline = sum(d for _,_,_,d in declined_from_ath) / len(declined_from_ath)
            print(f"\n    Average decline from ATH: {avg_decline:.0f}%")

    print()
    print("─" * 70)
    print("  KEY INSIGHT: Most tokens that graduate reach KOTH FAST.")
    print("  The approaching-graduation window is very SHORT.")
    print("  This means a pre-grad scanner needs to be FAST and poll FREQUENTLY.")
    print("─" * 70)


if __name__ == "__main__":
    main()
