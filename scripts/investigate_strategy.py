#!/usr/bin/env python3
"""
Deep investigation of pre-grad data quality and strategic implications.

Questions to answer:
1. Why do some "died" tokens have >$69K mcap (e.g., ANIME at $2.7M)?
   Are these really on the bonding curve, or are they already-graduated
   tokens that our observer was wrongly tracking?

2. Why do $40K+ tokens show 0% graduation? If they're on the bonding
   curve at $40K, they're 58% of the way to graduation. Why would they
   have LOWER graduation rates than $30K tokens?

3. How does the "realistic EV" change if we exclude these anomalous tokens?

4. What is the actual executable strategy — sell at graduation or hold?

5. What does Phase 1 look like concretely?
"""
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")


def load_jsonl(filepath):
    records = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def main():
    # Load all pre-grad data
    all_records = []
    for f in sorted(DATA_DIR.glob("pregrad_*.jsonl")):
        all_records.extend(load_jsonl(f))

    # Load graduation and price data for cross-reference
    all_grads = []
    for f in sorted(DATA_DIR.glob("graduations_*.jsonl")):
        all_grads.extend(load_jsonl(f))
    all_prices = []
    for f in sorted(DATA_DIR.glob("price_tracking_*.jsonl")):
        all_prices.extend(load_jsonl(f))

    # Build per-token summary
    tokens = {}
    for r in all_records:
        mint = r.get("mint", "")
        if not mint:
            continue
        if mint not in tokens:
            tokens[mint] = {
                "symbol": r.get("symbol", "?"),
                "outcome": "active",
                "thresholds_crossed": set(),
                "first_seen_mcap": None,
                "highest_mcap": None,
                "final_mcap": None,
                "time_tracked_min": None,
                "death_reason": None,
                "has_twitter": r.get("has_twitter", False),
                "has_telegram": r.get("has_telegram", False),
                "has_website": r.get("has_website", False),
            }
        if r["event"] == "threshold_crossed":
            tokens[mint]["thresholds_crossed"].add(r["threshold"])
        elif r["event"] == "graduated":
            tokens[mint]["outcome"] = "graduated"
            tokens[mint]["first_seen_mcap"] = r.get("first_seen_mcap")
            tokens[mint]["highest_mcap"] = r.get("highest_mcap")
            tokens[mint]["time_tracked_min"] = r.get("time_tracked_min")
        elif r["event"] == "died":
            tokens[mint]["outcome"] = "died"
            tokens[mint]["first_seen_mcap"] = r.get("first_seen_mcap")
            tokens[mint]["highest_mcap"] = r.get("highest_mcap")
            tokens[mint]["final_mcap"] = r.get("final_mcap")
            tokens[mint]["time_tracked_min"] = r.get("time_tracked_min")
            tokens[mint]["death_reason"] = r.get("death_reason")

    # ================================================================
    print("=" * 70)
    print("  INVESTIGATION 1: Anomalous High-Mcap 'Died' Tokens")
    print("=" * 70)
    print()
    print("  These tokens 'died' but had very high mcaps.")
    print("  Are they really bonding curve tokens? Or already graduated?")
    print()

    # Find died tokens with highest_mcap > $69K (graduation threshold)
    anomalous = []
    for mint, t in tokens.items():
        if t["outcome"] == "died":
            high = t.get("highest_mcap", 0) or 0
            if high > 69000:
                anomalous.append((mint, t))

    anomalous.sort(key=lambda x: x[1].get("highest_mcap", 0) or 0, reverse=True)

    # Cross-reference with graduation log — were these tokens actually graduated?
    grad_mints = set()
    for g in all_grads:
        m = g.get("mint", "")
        if m:
            grad_mints.add(m)

    print(f"  Died tokens with highest_mcap > $69K: {len(anomalous)}")
    print()
    for mint, t in anomalous:
        high = t.get("highest_mcap", 0) or 0
        final = t.get("final_mcap", 0) or 0
        reason = t.get("death_reason", "?")
        in_grad_log = mint in grad_mints
        thresholds = sorted(t["thresholds_crossed"])
        thresh_str = ", ".join(f"${th/1000:.0f}K" for th in thresholds)

        print(f"  {t['symbol']:>12} | high ${high:>10,.0f} | final ${final:>10,.0f} | reason: {reason}")
        print(f"               | in graduation log: {in_grad_log} | thresholds: [{thresh_str}]")
        print()

    # Count how many anomalous tokens exist
    anomalous_mints = set(m for m, _ in anomalous)
    print(f"  FINDING: {len(anomalous)} tokens 'died' with mcap > $69K")
    print(f"  Of these, {sum(1 for m in anomalous_mints if m in grad_mints)} are also in the graduation log")
    print()

    # ================================================================
    print("=" * 70)
    print("  INVESTIGATION 2: $40K+ Tokens — Why 0% Graduation?")
    print("=" * 70)
    print()

    tokens_40k = [(m, t) for m, t in tokens.items() if 40000 in t["thresholds_crossed"]]
    print(f"  Tokens that crossed $40K: {len(tokens_40k)}")
    for mint, t in tokens_40k:
        high = t.get("highest_mcap", 0) or 0
        final = t.get("final_mcap", 0) or 0
        reason = t.get("death_reason", "?")
        outcome = t["outcome"]
        in_grad = mint in grad_mints
        print(f"  {t['symbol']:>12} | outcome: {outcome} | high ${high:>10,.0f} | final ${final:>8,.0f} | reason: {reason} | in_grad_log: {in_grad}")
    print()

    tokens_50k = [(m, t) for m, t in tokens.items() if 50000 in t["thresholds_crossed"]]
    print(f"  Tokens that crossed $50K: {len(tokens_50k)}")
    for mint, t in tokens_50k:
        high = t.get("highest_mcap", 0) or 0
        final = t.get("final_mcap", 0) or 0
        reason = t.get("death_reason", "?")
        outcome = t["outcome"]
        in_grad = mint in grad_mints
        print(f"  {t['symbol']:>12} | outcome: {outcome} | high ${high:>10,.0f} | final ${final:>8,.0f} | reason: {reason} | in_grad_log: {in_grad}")
    print()

    # ================================================================
    print("=" * 70)
    print("  INVESTIGATION 3: Corrected EV (Excluding Anomalies)")
    print("=" * 70)
    print()

    # If tokens with highest_mcap > $69K are actually already-graduated tokens
    # that our observer incorrectly tracked, they should be excluded.
    # Let's compute EV both ways.

    clean_tokens = {m: t for m, t in tokens.items()
                    if not ((t.get("highest_mcap", 0) or 0) > 100000 and t["outcome"] == "died")}
    excluded = len(tokens) - len(clean_tokens)
    print(f"  Excluded {excluded} tokens with died + highest_mcap > $100K (likely not real bonding curve tokens)")
    print()

    for threshold in [5000, 10000, 20000, 30000]:
        # Original
        crossed_orig = [t for t in tokens.values() if threshold in t["thresholds_crossed"]]
        resolved_orig = [t for t in crossed_orig if t["outcome"] in ("graduated", "died")]
        grads_orig = len([t for t in resolved_orig if t["outcome"] == "graduated"])

        # Clean
        crossed_clean = [t for t in clean_tokens.values() if threshold in t["thresholds_crossed"]]
        resolved_clean = [t for t in crossed_clean if t["outcome"] in ("graduated", "died")]
        grads_clean = len([t for t in resolved_clean if t["outcome"] == "graduated"])

        if not resolved_orig:
            continue

        rate_orig = grads_orig / len(resolved_orig) * 100
        rate_clean = grads_clean / len(resolved_clean) * 100 if resolved_clean else 0

        # Compute realistic EV both ways
        multiplier = 69000 / threshold
        trade_size = 5.0

        # Original realistic EV
        pnl_orig = 0
        for t in resolved_orig:
            if t["outcome"] == "graduated":
                pnl_orig += trade_size * (multiplier - 1)
            else:
                final = t.get("final_mcap", 0) or 0
                recovery = final / threshold if threshold > 0 else 0
                pnl_orig += trade_size * (recovery - 1) if recovery > 0 else -trade_size
        ev_orig = pnl_orig / len(resolved_orig)

        # Clean realistic EV
        pnl_clean = 0
        for t in resolved_clean:
            if t["outcome"] == "graduated":
                pnl_clean += trade_size * (multiplier - 1)
            else:
                final = t.get("final_mcap", 0) or 0
                recovery = final / threshold if threshold > 0 else 0
                pnl_clean += trade_size * (recovery - 1) if recovery > 0 else -trade_size
        ev_clean = pnl_clean / len(resolved_clean) if resolved_clean else 0

        # Worst case EV (unchanged, since anomalous tokens are all "died")
        ev_worst = (grads_clean / len(resolved_clean)) * trade_size * multiplier - trade_size if resolved_clean else 0

        print(f"  ${threshold/1000:.0f}K:")
        print(f"    Original:  {grads_orig}/{len(resolved_orig)} = {rate_orig:.1f}% | realistic EV = ${ev_orig:+.2f}")
        print(f"    Cleaned:   {grads_clean}/{len(resolved_clean)} = {rate_clean:.1f}% | realistic EV = ${ev_clean:+.2f}")
        print(f"    Worst-case EV (cleaned): ${ev_worst:+.2f}")
        print()

    # ================================================================
    print("=" * 70)
    print("  INVESTIGATION 4: Optimal Strategy — Sell at Graduation or Hold?")
    print("=" * 70)
    print()

    # For graduated tokens, compare:
    # Strategy A: Sell immediately at graduation (take the 2.3x from $30K entry)
    # Strategy B: Hold and apply post-grad TP/SL rules

    price_by_mint = defaultdict(list)
    for p in all_prices:
        price_by_mint[p.get("mint", "")].append(p)

    grad_data_by_mint = {}
    for g in all_grads:
        m = g.get("mint", "")
        if m and m not in grad_data_by_mint:
            grad_data_by_mint[m] = g

    grad_tokens_30k = [(m, t) for m, t in tokens.items()
                       if t["outcome"] == "graduated" and 30000 in t["thresholds_crossed"]]

    print(f"  Graduated tokens that crossed $30K: {len(grad_tokens_30k)}")
    print()
    print(f"  Strategy A: Sell at graduation ($30K → $69K = 2.3x)")
    print(f"  Strategy B: Hold for post-grad momentum (TP +30% / SL -15%)")
    print()

    strat_a_pnl = 0
    strat_b_pnl = 0
    strat_b_details = []

    for mint, t in grad_tokens_30k:
        # Strategy A: always $6.50 profit per $5 trade
        a_pnl = 5.0 * (69000 / 30000 - 1)
        strat_a_pnl += a_pnl

        # Strategy B: depends on post-grad performance
        b_pnl = a_pnl  # start with the bonding curve gain
        value_at_grad = 5.0 * (69000 / 30000)  # $11.50

        if mint in price_by_mint:
            prices = price_by_mint[mint]
            # Find if TP or SL was hit (use earliest checkpoint that hits)
            hit_tp = False
            hit_sl = False
            best_pct = 0
            for p in prices:
                pct = p.get("pct_change")
                if pct is not None:
                    if p.get("would_tp") and not hit_tp:
                        hit_tp = True
                        best_pct = 30  # capped at TP
                    elif p.get("would_sl") and not hit_sl and not hit_tp:
                        hit_sl = True
                        best_pct = -15  # capped at SL

            if hit_tp:
                post_grad_return = value_at_grad * 0.30  # +30%
                b_pnl = a_pnl + post_grad_return
            elif hit_sl:
                post_grad_return = value_at_grad * -0.15  # -15%
                b_pnl = a_pnl + post_grad_return
            else:
                # Use last available checkpoint
                last_pct = None
                for p in sorted(prices, key=lambda x: x.get("checkpoint", ""), reverse=True):
                    if p.get("pct_change") is not None:
                        last_pct = p["pct_change"]
                        break
                if last_pct is not None:
                    post_grad_return = value_at_grad * (last_pct / 100)
                    b_pnl = a_pnl + post_grad_return
        else:
            b_pnl = a_pnl  # no price data, assume sell at grad

        strat_b_pnl += b_pnl
        strat_b_details.append((t["symbol"], a_pnl, b_pnl, b_pnl - a_pnl))

    n = len(grad_tokens_30k)
    if n > 0:
        print(f"  Strategy A total P&L: ${strat_a_pnl:+.2f} (${strat_a_pnl/n:+.2f}/trade)")
        print(f"  Strategy B total P&L: ${strat_b_pnl:+.2f} (${strat_b_pnl/n:+.2f}/trade)")
        print(f"  Difference (B - A):   ${strat_b_pnl - strat_a_pnl:+.2f} (${(strat_b_pnl - strat_a_pnl)/n:+.2f}/trade)")
        print()

        print(f"  Per-token breakdown:")
        for sym, a, b, diff in sorted(strat_b_details, key=lambda x: x[3], reverse=True):
            print(f"    {sym:>12}: A=${a:+.2f}  B=${b:+.2f}  diff=${diff:+.2f}")
        print()

        b_better = sum(1 for _, _, _, d in strat_b_details if d > 0)
        a_better = sum(1 for _, _, _, d in strat_b_details if d < 0)
        print(f"  B better in {b_better}/{n} cases, A better in {a_better}/{n} cases")

    # ================================================================
    print()
    print("=" * 70)
    print("  INVESTIGATION 5: Phase 1 Feasibility — Execution Requirements")
    print("=" * 70)
    print()

    # How much time do you have to act when a token crosses $30K?
    print("  How fast do tokens move from $30K to graduation?")
    print("  (For graduated tokens that crossed $30K)")
    print()

    for mint, t in grad_tokens_30k:
        sym = t["symbol"]
        tracked = t.get("time_tracked_min")
        # We need the time specifically from $30K crossing to graduation
        # Look at snapshot data for this token
        snaps = [r for r in all_records
                 if r.get("mint") == mint and r["event"] == "snapshot"]
        snaps.sort(key=lambda s: s.get("elapsed_min", 0))

        # Find when $30K was crossed (from threshold events)
        thresh_events = [r for r in all_records
                        if r.get("mint") == mint and r["event"] == "threshold_crossed" and r.get("threshold") == 30000]
        if thresh_events:
            thresh_ts = thresh_events[0].get("ts", "")
        else:
            thresh_ts = ""

        # Find graduation event
        grad_events = [r for r in all_records
                      if r.get("mint") == mint and r["event"] == "graduated"]
        if grad_events:
            grad_ts = grad_events[0].get("ts", "")
        else:
            grad_ts = ""

        if thresh_ts and grad_ts:
            try:
                t30 = datetime.fromisoformat(thresh_ts)
                tgrad = datetime.fromisoformat(grad_ts)
                delta = (tgrad - t30).total_seconds() / 60
                print(f"  {sym:>12}: $30K → graduation in {delta:.1f} min")
            except (ValueError, TypeError):
                print(f"  {sym:>12}: timing data unavailable")
        else:
            print(f"  {sym:>12}: no $30K threshold event or no graduation event")

    # ================================================================
    print()
    print("=" * 70)
    print("  INVESTIGATION 6: What Does Phase 1 Look Like Concretely?")
    print("=" * 70)
    print()

    # How many $30K crossings per day?
    thresh_30k_events = [r for r in all_records
                        if r["event"] == "threshold_crossed" and r.get("threshold") == 30000]
    if thresh_30k_events:
        first_ts = min(datetime.fromisoformat(r["ts"]) for r in thresh_30k_events)
        last_ts = max(datetime.fromisoformat(r["ts"]) for r in thresh_30k_events)
        days = (last_ts - first_ts).total_seconds() / 86400
        if days > 0:
            rate_per_day = len(thresh_30k_events) / days
            print(f"  $30K crossings observed: {len(thresh_30k_events)}")
            print(f"  Over {days:.1f} days")
            print(f"  Rate: {rate_per_day:.1f} per day")
            print()

    # What time of day do they happen?
    hours = Counter()
    for r in thresh_30k_events:
        ts = datetime.fromisoformat(r["ts"])
        hours[ts.hour] += 1
    if hours:
        print(f"  $30K crossings by hour (UTC):")
        for h in range(24):
            c = hours.get(h, 0)
            bar = "█" * c if c > 0 else ""
            if c > 0:
                print(f"    {h:02d}:00: {c:>2d} {bar}")

    print()
    print("  Phase 1 operational requirements:")
    print(f"    - Trades per day: ~{rate_per_day:.0f} opportunities (at $30K threshold)" if thresh_30k_events and days > 0 else "    - Trades per day: unknown")
    print(f"    - Capital needed: $5 × 10 trades = $50 (Phase 1)")
    print(f"    - SOL needed: ~0.06 SOL per trade + gas (~$5 at ~$83/SOL)")
    print(f"    - Total SOL: ~1 SOL ($83) covers 10 trades + gas")
    print(f"    - Tools: Phantom wallet + Pump.fun interface or Photon")
    print(f"    - Alert: Need real-time notification when $30K crossing detected")
    print(f"    - Action window: minutes (need to be available and fast)")

    print()
    print("=" * 70)
    print("  CONCLUSIONS & RECOMMENDED NEXT STEPS")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
