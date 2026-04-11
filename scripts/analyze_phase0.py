#!/usr/bin/env python3
"""
Phase 0 Data Analysis — Graduation Strategy Evaluation
========================================================
Analyzes collected graduation and price tracking data to determine:
1. What % of graduated tokens pumped >30% (win rate for TP)
2. What % hit -15% stop loss
3. Do social signals (twitter/telegram/website) matter?
4. Optimal entry timing (which checkpoint shows best risk/reward)
5. Overall: is the strategy viable for Phase 1?

Criteria for Phase 1 go:
- Win rate >30% with 2:1 win/loss ratio
"""
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")


def load_jsonl(filepath):
    """Load all records from a JSONL file."""
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
    # =====================================================
    # LOAD DATA
    # =====================================================
    grad_files = sorted(DATA_DIR.glob("graduations_*.jsonl"))
    price_files = sorted(DATA_DIR.glob("price_tracking_*.jsonl"))

    if not grad_files:
        print("ERROR: No graduation data files found in data/")
        sys.exit(1)
    if not price_files:
        print("ERROR: No price tracking data files found in data/")
        sys.exit(1)

    all_grads = []
    for f in grad_files:
        all_grads.extend(load_jsonl(f))

    all_prices = []
    for f in price_files:
        all_prices.extend(load_jsonl(f))

    print("=" * 70)
    print("  PHASE 0 DATA ANALYSIS — Graduation Strategy Evaluation")
    print("=" * 70)
    print()

    # =====================================================
    # SECTION 1: DATA QUALITY & OVERVIEW
    # =====================================================
    print("─" * 70)
    print("  1. DATA QUALITY & OVERVIEW")
    print("─" * 70)

    # Deduplicate graduations by mint (keep first seen)
    seen_mints = {}
    for g in all_grads:
        mint = g.get("mint", "")
        if mint and mint not in seen_mints:
            seen_mints[mint] = g

    unique_grads = list(seen_mints.values())
    total_records = len(all_grads)
    total_unique = len(unique_grads)
    duplicates = total_records - total_unique

    print(f"  Total graduation records:     {total_records}")
    print(f"  Unique graduated tokens:      {total_unique}")
    print(f"  Duplicate records:            {duplicates}")
    print(f"  Data files:                   {len(grad_files)} graduation, {len(price_files)} price tracking")

    # Time range
    timestamps = []
    for g in unique_grads:
        ts_str = g.get("ts", "")
        if ts_str:
            try:
                timestamps.append(datetime.fromisoformat(ts_str))
            except ValueError:
                pass

    if timestamps:
        first_ts = min(timestamps)
        last_ts = max(timestamps)
        duration_hours = (last_ts - first_ts).total_seconds() / 3600
        print(f"  First graduation:             {first_ts.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"  Last graduation:              {last_ts.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"  Collection duration:          {duration_hours:.1f} hours")
        if duration_hours > 0:
            rate = total_unique / duration_hours
            print(f"  Graduation rate:              {rate:.1f} per hour ({rate * 24:.0f} per day)")

    # Price tracking overview
    print(f"\n  Total price tracking records:  {len(all_prices)}")
    price_mints = set(p.get("mint", "") for p in all_prices)
    print(f"  Unique tokens tracked:        {len(price_mints)}")

    # Which tokens have which checkpoints
    token_checkpoints = defaultdict(set)
    for p in all_prices:
        mint = p.get("mint", "")
        cp = p.get("checkpoint", "")
        if mint and cp:
            token_checkpoints[mint].add(cp)

    for cp in ["1m", "5m", "10m", "30m"]:
        count = sum(1 for m, cps in token_checkpoints.items() if cp in cps)
        print(f"    Tokens with {cp:>3s} checkpoint: {count}")

    all_four = sum(1 for m, cps in token_checkpoints.items()
                   if {"1m", "5m", "10m", "30m"} <= cps)
    print(f"    Tokens with ALL 4:          {all_four}")

    # Tokens graduated but not tracked at all
    untracked = set(seen_mints.keys()) - price_mints
    print(f"    Graduated but NOT tracked:  {len(untracked)}")

    # Null first_price count
    null_first_price = sum(1 for p in all_prices if p.get("first_price") is None)
    null_pct_change = sum(1 for p in all_prices if p.get("pct_change") is None)
    print(f"    Records with null first_price: {null_first_price}")
    print(f"    Records with null pct_change:  {null_pct_change}")

    # =====================================================
    # SECTION 2: BUILD MERGED TOKEN DATASET
    # =====================================================
    # For each unique graduated token, merge in its price checkpoints

    # Build price data index: mint -> checkpoint -> record
    price_index = {}
    for p in all_prices:
        mint = p.get("mint", "")
        cp = p.get("checkpoint", "")
        if mint and cp:
            if mint not in price_index:
                price_index[mint] = {}
            # Keep the first checkpoint record per token per checkpoint
            if cp not in price_index[mint]:
                price_index[mint][cp] = p

    # Merge
    tokens = []
    for g in unique_grads:
        mint = g.get("mint", "")
        token = {
            "mint": mint,
            "symbol": g.get("symbol", "?"),
            "name": g.get("name", "?"),
            "mcap": g.get("mcap", 0) or 0,
            "dex_price_at_grad": g.get("dex_price"),
            "has_twitter": g.get("has_twitter", False),
            "has_telegram": g.get("has_telegram", False),
            "has_website": g.get("has_website", False),
            "ts": g.get("ts", ""),
        }

        # Count social signals
        socials = 0
        if token["has_twitter"]:
            socials += 1
        if token["has_telegram"]:
            socials += 1
        if token["has_website"]:
            socials += 1
        token["social_count"] = socials

        # Add price checkpoints
        if mint in price_index:
            for cp in ["1m", "5m", "10m", "30m"]:
                if cp in price_index[mint]:
                    rec = price_index[mint][cp]
                    token[f"{cp}_price"] = rec.get("price")
                    token[f"{cp}_pct"] = rec.get("pct_change")
                    token[f"{cp}_tp"] = rec.get("would_tp", False)
                    token[f"{cp}_sl"] = rec.get("would_sl", False)
                else:
                    token[f"{cp}_price"] = None
                    token[f"{cp}_pct"] = None
                    token[f"{cp}_tp"] = False
                    token[f"{cp}_sl"] = False
        else:
            for cp in ["1m", "5m", "10m", "30m"]:
                token[f"{cp}_price"] = None
                token[f"{cp}_pct"] = None
                token[f"{cp}_tp"] = False
                token[f"{cp}_sl"] = False

        tokens.append(token)

    # =====================================================
    # SECTION 3: CORE WIN RATE ANALYSIS
    # =====================================================
    print()
    print("─" * 70)
    print("  2. CORE WIN RATE ANALYSIS")
    print("─" * 70)
    print()
    print("  Strategy: Buy at graduation detection, TP at +30%, SL at -15%")
    print("  Question: At each checkpoint, how many tokens hit TP vs SL?")
    print()

    for cp in ["1m", "5m", "10m", "30m"]:
        tp_key = f"{cp}_tp"
        sl_key = f"{cp}_sl"
        pct_key = f"{cp}_pct"

        # Only consider tokens with valid data for this checkpoint
        valid = [t for t in tokens if t.get(pct_key) is not None]
        if not valid:
            print(f"  [{cp:>3s}] No valid data")
            continue

        tp_count = sum(1 for t in valid if t[tp_key])
        sl_count = sum(1 for t in valid if t[sl_key])
        neither = len(valid) - tp_count - sl_count
        win_rate = tp_count / len(valid) * 100 if valid else 0
        loss_rate = sl_count / len(valid) * 100 if valid else 0

        # Also compute average and median pct change
        pcts = [t[pct_key] for t in valid]
        avg_pct = sum(pcts) / len(pcts) if pcts else 0
        sorted_pcts = sorted(pcts)
        median_pct = sorted_pcts[len(sorted_pcts) // 2] if sorted_pcts else 0

        # Min / Max
        min_pct = min(pcts) if pcts else 0
        max_pct = max(pcts) if pcts else 0

        # Distribution buckets
        buckets = {
            "< -50%": 0, "-50 to -30%": 0, "-30 to -15%": 0,
            "-15 to 0%": 0, "0 to +15%": 0, "+15 to +30%": 0,
            "+30 to +50%": 0, "+50 to +100%": 0, "> +100%": 0,
        }
        for p in pcts:
            if p < -50:
                buckets["< -50%"] += 1
            elif p < -30:
                buckets["-50 to -30%"] += 1
            elif p < -15:
                buckets["-30 to -15%"] += 1
            elif p < 0:
                buckets["-15 to 0%"] += 1
            elif p < 15:
                buckets["0 to +15%"] += 1
            elif p < 30:
                buckets["+15 to +30%"] += 1
            elif p < 50:
                buckets["+30 to +50%"] += 1
            elif p < 100:
                buckets["+50 to +100%"] += 1
            else:
                buckets["> +100%"] += 1

        print(f"  [{cp:>3s}] {len(valid)} tokens with data")
        print(f"         TP hit (+30%):  {tp_count:>3d} ({win_rate:.1f}%)")
        print(f"         SL hit (-15%):  {sl_count:>3d} ({loss_rate:.1f}%)")
        print(f"         Neither:        {neither:>3d} ({neither/len(valid)*100:.1f}%)")
        print(f"         Avg change:     {avg_pct:+.1f}%")
        print(f"         Median change:  {median_pct:+.1f}%")
        print(f"         Range:          {min_pct:+.1f}% to {max_pct:+.1f}%")
        print(f"         Distribution:")
        for bucket_name, count in buckets.items():
            bar = "█" * count
            if count > 0:
                print(f"           {bucket_name:>15s}: {count:>3d} {bar}")
        print()

    # =====================================================
    # SECTION 4: WIN/LOSS RATIO ANALYSIS
    # =====================================================
    print("─" * 70)
    print("  3. WIN/LOSS RATIO (Simulated P&L)")
    print("─" * 70)
    print()
    print("  Simulating: $5 per trade, TP +30% ($6.50), SL -15% ($4.25)")
    print("  If neither TP nor SL hit, use actual % change at checkpoint")
    print()

    for cp in ["1m", "5m", "10m", "30m"]:
        pct_key = f"{cp}_pct"
        tp_key = f"{cp}_tp"
        sl_key = f"{cp}_sl"

        valid = [t for t in tokens if t.get(pct_key) is not None]
        if not valid:
            continue

        trade_size = 5.0
        total_pnl = 0
        wins = 0
        losses = 0
        total_win_pnl = 0
        total_loss_pnl = 0

        for t in valid:
            if t[tp_key]:
                pnl = trade_size * 0.30  # +$1.50
                total_pnl += pnl
                wins += 1
                total_win_pnl += pnl
            elif t[sl_key]:
                pnl = trade_size * -0.15  # -$0.75
                total_pnl += pnl
                losses += 1
                total_loss_pnl += pnl
            else:
                # Use actual change at checkpoint (capped — in reality we'd hold)
                pct = t[pct_key]
                pnl = trade_size * (pct / 100)
                total_pnl += pnl
                if pnl >= 0:
                    wins += 1
                    total_win_pnl += pnl
                else:
                    losses += 1
                    total_loss_pnl += pnl

        win_rate = wins / len(valid) * 100 if valid else 0
        avg_win = total_win_pnl / wins if wins > 0 else 0
        avg_loss = abs(total_loss_pnl / losses) if losses > 0 else 0
        wl_ratio = avg_win / avg_loss if avg_loss > 0 else float("inf")

        print(f"  [{cp:>3s}] Simulated over {len(valid)} trades ($5 each)")
        print(f"         Wins: {wins}  |  Losses: {losses}  |  Win Rate: {win_rate:.1f}%")
        print(f"         Total P&L:     ${total_pnl:+.2f}")
        print(f"         Avg Win:       ${avg_win:+.2f}")
        print(f"         Avg Loss:      ${avg_loss:.2f}")
        print(f"         Win/Loss Ratio: {wl_ratio:.2f}:1")
        print(f"         Capital needed: ${trade_size * len(valid):.0f} (${trade_size} × {len(valid)} trades)")
        print(f"         ROI:            {total_pnl / (trade_size * len(valid)) * 100:+.1f}%")
        print()

    # =====================================================
    # SECTION 5: SOCIAL SIGNAL ANALYSIS
    # =====================================================
    print("─" * 70)
    print("  4. SOCIAL SIGNAL ANALYSIS")
    print("─" * 70)
    print()
    print("  Do tokens with Twitter/Telegram/Website perform better?")
    print()

    # Analyze at each checkpoint
    for cp in ["1m", "5m", "10m", "30m"]:
        pct_key = f"{cp}_pct"
        valid = [t for t in tokens if t.get(pct_key) is not None]
        if not valid:
            continue

        print(f"  [{cp:>3s}] checkpoint:")

        # By individual social presence
        for signal_name, signal_key in [("Twitter", "has_twitter"), ("Telegram", "has_telegram"), ("Website", "has_website")]:
            with_signal = [t for t in valid if t.get(signal_key)]
            without_signal = [t for t in valid if not t.get(signal_key)]

            if with_signal:
                avg_with = sum(t[pct_key] for t in with_signal) / len(with_signal)
                tp_with = sum(1 for t in with_signal if t.get(f"{cp}_tp"))
                sl_with = sum(1 for t in with_signal if t.get(f"{cp}_sl"))
            else:
                avg_with = 0
                tp_with = 0
                sl_with = 0

            if without_signal:
                avg_without = sum(t[pct_key] for t in without_signal) / len(without_signal)
                tp_without = sum(1 for t in without_signal if t.get(f"{cp}_tp"))
                sl_without = sum(1 for t in without_signal if t.get(f"{cp}_sl"))
            else:
                avg_without = 0
                tp_without = 0
                sl_without = 0

            print(f"         {signal_name:>10s}:  WITH {len(with_signal):>3d} tokens avg {avg_with:+.1f}% (TP:{tp_with} SL:{sl_with})  |  WITHOUT {len(without_signal):>3d} tokens avg {avg_without:+.1f}% (TP:{tp_without} SL:{sl_without})")

        # By social count (0, 1, 2, 3)
        for sc in range(4):
            group = [t for t in valid if t.get("social_count", 0) == sc]
            if group:
                avg_g = sum(t[pct_key] for t in group) / len(group)
                tp_g = sum(1 for t in group if t.get(f"{cp}_tp"))
                sl_g = sum(1 for t in group if t.get(f"{cp}_sl"))
                wr_g = tp_g / len(group) * 100
                print(f"         {sc} socials:   {len(group):>3d} tokens, avg {avg_g:+.1f}%, WR {wr_g:.0f}%, TP:{tp_g} SL:{sl_g}")
        print()

    # =====================================================
    # SECTION 6: MARKET CAP AT GRADUATION ANALYSIS
    # =====================================================
    print("─" * 70)
    print("  5. MARKET CAP AT GRADUATION")
    print("─" * 70)
    print()

    mcaps = [t["mcap"] for t in tokens if t["mcap"] and t["mcap"] > 0]
    if mcaps:
        avg_mcap = sum(mcaps) / len(mcaps)
        sorted_mcaps = sorted(mcaps)
        median_mcap = sorted_mcaps[len(sorted_mcaps) // 2]
        print(f"  Average mcap at graduation:  ${avg_mcap:,.0f}")
        print(f"  Median mcap at graduation:   ${median_mcap:,.0f}")
        print(f"  Min:                         ${min(mcaps):,.0f}")
        print(f"  Max:                         ${max(mcaps):,.0f}")
        print()

        # Buckets for mcap and performance correlation
        mcap_buckets = [
            ("< $10K", 0, 10000),
            ("$10K-$50K", 10000, 50000),
            ("$50K-$100K", 50000, 100000),
            ("$100K-$500K", 100000, 500000),
            ("$500K+", 500000, float("inf")),
        ]

        for cp in ["5m", "10m", "30m"]:
            pct_key = f"{cp}_pct"
            valid = [t for t in tokens if t.get(pct_key) is not None and t["mcap"] and t["mcap"] > 0]
            if not valid:
                continue

            print(f"  [{cp:>3s}] Performance by mcap at graduation:")
            for bucket_name, low, high in mcap_buckets:
                group = [t for t in valid if low <= t["mcap"] < high]
                if group:
                    avg_g = sum(t[pct_key] for t in group) / len(group)
                    tp_g = sum(1 for t in group if t.get(f"{cp}_tp"))
                    sl_g = sum(1 for t in group if t.get(f"{cp}_sl"))
                    wr = tp_g / len(group) * 100
                    print(f"         {bucket_name:>12s}: {len(group):>3d} tokens, avg {avg_g:+.1f}%, WR {wr:.0f}%, TP:{tp_g} SL:{sl_g}")
            print()

    # =====================================================
    # SECTION 7: TOKEN-BY-TOKEN DETAIL TABLE
    # =====================================================
    print("─" * 70)
    print("  6. TOKEN-BY-TOKEN DETAIL")
    print("─" * 70)
    print()

    # Build detail for tokens that have price data
    tracked_tokens = [t for t in tokens if t.get("1m_pct") is not None or t.get("5m_pct") is not None or t.get("10m_pct") is not None or t.get("30m_pct") is not None]

    # Sort by best performance (30m if available, else 10m, 5m, 1m)
    def sort_key(t):
        for cp in ["30m", "10m", "5m", "1m"]:
            pct = t.get(f"{cp}_pct")
            if pct is not None:
                return pct
        return -999
    tracked_tokens.sort(key=sort_key, reverse=True)

    header = f"  {'Symbol':>10s} | {'Mcap':>10s} | {'1m':>8s} | {'5m':>8s} | {'10m':>8s} | {'30m':>8s} | {'TW':>2s} {'TG':>2s} {'WB':>2s} | Outcome"
    print(header)
    print("  " + "-" * len(header.strip()))

    for t in tracked_tokens:
        symbol = t["symbol"][:10]
        mcap_str = f"${t['mcap']:,.0f}" if t["mcap"] else "N/A"

        pct_strs = {}
        for cp in ["1m", "5m", "10m", "30m"]:
            pct = t.get(f"{cp}_pct")
            if pct is not None:
                pct_strs[cp] = f"{pct:+.1f}%"
            else:
                pct_strs[cp] = "---"

        tw = "Y" if t["has_twitter"] else "."
        tg = "Y" if t["has_telegram"] else "."
        wb = "Y" if t["has_website"] else "."

        # Determine outcome
        outcome = ""
        for cp in ["1m", "5m", "10m", "30m"]:
            if t.get(f"{cp}_tp"):
                outcome = f"TP@{cp}"
                break
            if t.get(f"{cp}_sl"):
                outcome = f"SL@{cp}"
                break
        if not outcome:
            # Use latest available checkpoint
            for cp in ["30m", "10m", "5m", "1m"]:
                pct = t.get(f"{cp}_pct")
                if pct is not None:
                    if pct > 0:
                        outcome = f"+{pct:.0f}%@{cp}"
                    else:
                        outcome = f"{pct:.0f}%@{cp}"
                    break

        print(f"  {symbol:>10s} | {mcap_str:>10s} | {pct_strs['1m']:>8s} | {pct_strs['5m']:>8s} | {pct_strs['10m']:>8s} | {pct_strs['30m']:>8s} | {tw:>2s} {tg:>2s} {wb:>2s} | {outcome}")

    # =====================================================
    # SECTION 8: TIMING ANALYSIS — ACTUAL ELAPSED TIMES
    # =====================================================
    print()
    print("─" * 70)
    print("  7. TIMING ANALYSIS — Actual Elapsed Minutes at Checkpoints")
    print("─" * 70)
    print()
    print("  The tracker fires checkpoints when elapsed_min >= target.")
    print("  Due to polling intervals, actual elapsed can vary.")
    print()

    # Look at the actual elapsed times from the price tracking data
    # to understand when checkpoints actually fire
    checkpoint_elapsed = defaultdict(list)
    for p in all_prices:
        cp = p.get("checkpoint", "")
        # We need to compute elapsed from graduation to checkpoint
        mint = p.get("mint", "")
        if mint in seen_mints and cp:
            grad_ts_str = seen_mints[mint].get("ts", "")
            price_ts_str = p.get("ts", "")
            if grad_ts_str and price_ts_str:
                try:
                    grad_ts = datetime.fromisoformat(grad_ts_str)
                    price_ts = datetime.fromisoformat(price_ts_str)
                    elapsed = (price_ts - grad_ts).total_seconds() / 60
                    checkpoint_elapsed[cp].append(elapsed)
                except ValueError:
                    pass

    for cp in ["1m", "5m", "10m", "30m"]:
        if cp in checkpoint_elapsed:
            vals = checkpoint_elapsed[cp]
            avg_e = sum(vals) / len(vals)
            min_e = min(vals)
            max_e = max(vals)
            sorted_vals = sorted(vals)
            median_e = sorted_vals[len(sorted_vals) // 2]
            print(f"  [{cp:>3s}] n={len(vals)}, avg={avg_e:.1f}m, median={median_e:.1f}m, min={min_e:.1f}m, max={max_e:.1f}m")

    # =====================================================
    # SECTION 9: TOKENS WITH NULL FIRST_PRICE
    # =====================================================
    print()
    print("─" * 70)
    print("  8. DATA GAPS — Tokens with null dex_price at graduation")
    print("─" * 70)
    print()

    null_price_tokens = [t for t in tokens if t.get("dex_price_at_grad") is None]
    non_null_price_tokens = [t for t in tokens if t.get("dex_price_at_grad") is not None]

    print(f"  Tokens with dex_price at graduation:    {len(non_null_price_tokens)}")
    print(f"  Tokens WITHOUT dex_price at graduation: {len(null_price_tokens)}")
    if null_price_tokens:
        print(f"  (These tokens may not have had DEX pairs yet at detection time)")
        print(f"  Null-price tokens:")
        for t in null_price_tokens:
            print(f"    {t['symbol']:>10s} | mcap ${t['mcap']:,.0f} | tw:{int(t['has_twitter'])} tg:{int(t['has_telegram'])} wb:{int(t['has_website'])}")

    # =====================================================
    # SECTION 10: PEAK PERFORMANCE (Best case scenario)
    # =====================================================
    print()
    print("─" * 70)
    print("  9. PEAK PERFORMANCE — Maximum gain per token across all checkpoints")
    print("─" * 70)
    print()

    for t in tokens:
        max_pct = None
        for cp in ["1m", "5m", "10m", "30m"]:
            pct = t.get(f"{cp}_pct")
            if pct is not None:
                if max_pct is None or pct > max_pct:
                    max_pct = pct
        t["max_pct"] = max_pct

    tokens_with_max = [t for t in tokens if t["max_pct"] is not None]
    if tokens_with_max:
        # How many ever exceeded +30%?
        ever_tp = sum(1 for t in tokens_with_max if t["max_pct"] >= 30)
        ever_sl = sum(1 for t in tokens_with_max if t["max_pct"] < -15)  # max gain was still below -15
        print(f"  Tokens with price data:        {len(tokens_with_max)}")
        print(f"  Tokens that EVER hit +30%:     {ever_tp} ({ever_tp/len(tokens_with_max)*100:.1f}%)")
        print(f"  Tokens whose BEST was < -15%:  {ever_sl} ({ever_sl/len(tokens_with_max)*100:.1f}%)")
        print()

        sorted_by_max = sorted(tokens_with_max, key=lambda t: t["max_pct"], reverse=True)
        print(f"  Top 10 best performers:")
        for t in sorted_by_max[:10]:
            print(f"    {t['symbol']:>10s}: max {t['max_pct']:+.1f}% | mcap ${t['mcap']:,.0f} | tw:{int(t['has_twitter'])} tg:{int(t['has_telegram'])} wb:{int(t['has_website'])}")

        print(f"\n  Bottom 10 worst performers:")
        for t in sorted_by_max[-10:]:
            print(f"    {t['symbol']:>10s}: max {t['max_pct']:+.1f}% | mcap ${t['mcap']:,.0f} | tw:{int(t['has_twitter'])} tg:{int(t['has_telegram'])} wb:{int(t['has_website'])}")

    # =====================================================
    # SECTION 11: FINAL VERDICT
    # =====================================================
    print()
    print("=" * 70)
    print("  10. FINAL VERDICT — Phase 1 Go/No-Go")
    print("=" * 70)
    print()
    print("  Criteria: Win Rate >30% AND Win/Loss Ratio >2:1")
    print()

    # Use the checkpoint with the most complete data for the verdict
    for cp in ["30m", "10m", "5m", "1m"]:
        pct_key = f"{cp}_pct"
        tp_key = f"{cp}_tp"
        sl_key = f"{cp}_sl"
        valid = [t for t in tokens if t.get(pct_key) is not None]
        if len(valid) < 10:
            continue

        tp_count = sum(1 for t in valid if t[tp_key])
        sl_count = sum(1 for t in valid if t[sl_key])
        win_rate = tp_count / len(valid) * 100

        # Compute W/L ratio using simulated P&L
        trade_size = 5.0
        total_win_pnl = 0
        total_loss_pnl = 0
        wins = 0
        losses = 0
        for t in valid:
            if t[tp_key]:
                total_win_pnl += trade_size * 0.30
                wins += 1
            elif t[sl_key]:
                total_loss_pnl += trade_size * 0.15
                losses += 1
            else:
                pct = t[pct_key]
                pnl = trade_size * (pct / 100)
                if pnl >= 0:
                    total_win_pnl += pnl
                    wins += 1
                else:
                    total_loss_pnl += abs(pnl)
                    losses += 1

        avg_win = total_win_pnl / wins if wins > 0 else 0
        avg_loss = total_loss_pnl / losses if losses > 0 else 0.01
        wl_ratio = avg_win / avg_loss

        wr_pass = "PASS ✓" if win_rate > 30 else "FAIL ✗"
        wl_pass = "PASS ✓" if wl_ratio > 2 else "FAIL ✗"
        overall = "GO" if win_rate > 30 and wl_ratio > 2 else "NO-GO"

        print(f"  [{cp:>3s}] Best checkpoint with {len(valid)} tokens:")
        print(f"         Win Rate (TP hit):    {win_rate:.1f}% — {wr_pass}")
        print(f"         Win/Loss Ratio:       {wl_ratio:.2f}:1 — {wl_pass}")
        print(f"         Verdict:              >>> {overall} <<<")
        print()
        break  # Use the best (longest) checkpoint

    print("=" * 70)
    print("  END OF ANALYSIS")
    print("=" * 70)


if __name__ == "__main__":
    main()
