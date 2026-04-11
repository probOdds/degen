#!/usr/bin/env python3
"""Query Pump.fun API to understand pre-graduation token data."""
import json
import subprocess
import sys


def curl_json(url, timeout=15):
    try:
        result = subprocess.run(
            ["curl", "-s", "-H", "User-Agent: Mozilla/5.0", url],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    # Fetch current tokens
    data = curl_json("https://frontend-api-v3.pump.fun/coins/currently-live?limit=50")
    if not data:
        print("ERROR: Could not fetch Pump.fun API")
        sys.exit(1)

    graduated = [t for t in data if t.get("complete") is True]
    not_grad = [t for t in data if t.get("complete") is not True]

    approaching = [t for t in not_grad if (t.get("usd_market_cap") or 0) > 30000]
    mid_cap = [t for t in not_grad if 10000 < (t.get("usd_market_cap") or 0) <= 30000]
    low_cap = [t for t in not_grad if (t.get("usd_market_cap") or 0) <= 10000]

    print("=" * 60)
    print("  PUMP.FUN API — Pre-Graduation Token Analysis")
    print("=" * 60)
    print()
    print(f"  Total tokens returned:          {len(data)}")
    print(f"  Graduated (complete=true):      {len(graduated)}")
    print(f"  NOT graduated:                  {len(not_grad)}")
    print(f"    Approaching (>$30K mcap):     {len(approaching)}")
    print(f"    Mid cap ($10K-$30K):          {len(mid_cap)}")
    print(f"    Low cap (<$10K):              {len(low_cap)}")
    print()

    # Show all fields for first token
    print("--- ALL FIELDS FOR FIRST TOKEN ---")
    if data:
        t = data[0]
        for k, v in t.items():
            if k in ["description", "image_uri"]:
                print(f"  {k}: [truncated]")
            else:
                val_str = str(v)
                if len(val_str) > 100:
                    val_str = val_str[:100] + "..."
                print(f"  {k}: {val_str}")
    print()

    # Show approaching graduation tokens
    print("--- TOKENS APPROACHING GRADUATION (>$30K, not yet graduated) ---")
    for t in sorted(approaching, key=lambda x: x.get("usd_market_cap", 0) or 0, reverse=True):
        mcap = t.get("usd_market_cap", 0) or 0
        pct = mcap / 69000 * 100
        has_tw = bool(t.get("twitter"))
        has_tg = bool(t.get("telegram"))
        has_wb = bool(t.get("website"))
        social = []
        if has_tw: social.append("TW")
        if has_tg: social.append("TG")
        if has_wb: social.append("WB")
        social_str = ",".join(social) if social else "none"

        print(f"  {t.get('symbol', '?'):>10} | mcap=${mcap:,.0f} ({pct:.0f}% to grad) | social=[{social_str}] | mint={t.get('mint', '')[:16]}...")
    print()

    # Check: does the API provide virtual_sol_reserves or bonding curve data?
    print("--- BONDING CURVE RELATED FIELDS ---")
    bc_fields = ["virtual_sol_reserves", "virtual_token_reserves", "bonding_curve",
                 "real_sol_reserves", "real_token_reserves", "total_supply",
                 "complete", "usd_market_cap", "market_cap"]
    if data:
        t = data[0]
        for f in bc_fields:
            if f in t:
                print(f"  {f}: {t[f]}")
            else:
                print(f"  {f}: NOT IN API RESPONSE")
    print()

    # Now get detailed info for an approaching token
    if approaching:
        mint = approaching[0].get("mint", "")
        print(f"--- DETAILED TOKEN INFO (approaching: {approaching[0].get('symbol', '?')}) ---")
        detail = curl_json(f"https://frontend-api-v3.pump.fun/coins/{mint}")
        if detail:
            for k, v in detail.items():
                if k in ["description", "image_uri", "profile_image"]:
                    print(f"  {k}: [truncated]")
                else:
                    val_str = str(v)
                    if len(val_str) > 120:
                        val_str = val_str[:120] + "..."
                    print(f"  {k}: {val_str}")
        else:
            print("  Could not fetch detail")
    print()

    # Also get detail for a graduated token for comparison
    if graduated:
        mint = graduated[0].get("mint", "")
        print(f"--- DETAILED TOKEN INFO (graduated: {graduated[0].get('symbol', '?')}) ---")
        detail = curl_json(f"https://frontend-api-v3.pump.fun/coins/{mint}")
        if detail:
            for k, v in detail.items():
                if k in ["description", "image_uri", "profile_image"]:
                    print(f"  {k}: [truncated]")
                else:
                    val_str = str(v)
                    if len(val_str) > 120:
                        val_str = val_str[:120] + "..."
                    print(f"  {k}: {val_str}")
        else:
            print("  Could not fetch detail")


if __name__ == "__main__":
    main()
