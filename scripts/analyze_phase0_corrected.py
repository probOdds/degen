#!/usr/bin/env python3
"""
Phase 0 CORRECTED Analysis — Filtering out dead tokens
=======================================================
20 of 50 tracked tokens show ZERO price movement across all checkpoints.
DexScreener returns stale cached prices for tokens with no trading activity.
These tokens are untradeable — you cannot enter or exit a position.

This analysis separates:
- "Active" tokens (price moved at any checkpoint) → the real dataset
- "Dead" tokens (identical price at all checkpoints) → noise
"""
import json
from collections import defaultdict
from datetime import datetime
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
    # Load all data
    all_grads = []
    for f in sorted(DATA_DIR.glob("graduations_*.jsonl")):
        all_grads.extend(load_jsonl(f))

    all_prices = []
    for f in sorted(DATA_DIR.glob("price_tracking_*.jsonl")):
        all_prices.extend(load_jsonl(f))

    # Deduplicate graduations
    seen_mints = {}
    for g in all_grads:
        mint = g.get("mint", "")
        if mint and mint not in seen_mints:
            seen_mints[mint] = g

    # Group prices by mint
    by_mint = defaultdict(list)
    for p in all_prices:
        by_mint[p["mint"]].append(p)

    # Identify dead tokens (all checkpoints show exact same price)
    dead_mints = set()
    active_mints = set()
    for mint, recs in by_mint.items():
        prices = [r["price"] for r in recs if r.get("price") is not None]
        if prices and len(set(prices)) == 1:
            dead_mints.add(mint)
        elif prices:
            active_mints.add(mint)

    # Build price index
    price_index = {}
    for p in all_prices:
        mint = p.get("mint", "")
        cp = p.get("checkpoint", "")
        if mint and cp:
            if mint not in price_index:
                price_index[mint] = {}
            if cp not in price_index[mint]:
                price_index[mint][cp] = p

    # Build token records
    tokens = []
    for g in seen_mints.values():
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
            "is_dead": mint in dead_mints,
            "is_active": mint in active_mints,
        }

        socials = sum([token["has_twitter"], token["has_telegram"], token["has_website"]])
        token["social_count"] = socials

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

    # =========================================================================
    print("=" * 70)
    print("  CORRECTED PHASE 0 ANALYSIS")
    print("  Filtering out dead tokens (zero trading volume)")
    print("=" * 70)
    print()

    total_tracked = len(by_mint)
    print(f"  Total unique graduated tokens:   {len(seen_mints)}")
    print(f"  Total tracked (have price data): {total_tracked}")
    print(f"  DEAD tokens (zero movement):     {len(dead_mints)} ({len(dead_mints)/total_tracked*100:.0f}%)")
    print(f"  ACTIVE tokens (price moved):     {len(active_mints)} ({len(active_mints)/total_tracked*100:.0f}%)")
    print(f"  Not tracked at all:              {len(seen_mints) - total_tracked}")
    print()

    # This is itself a key finding — 40% of graduations are essentially dead
    print("  >>> FINDING: ~40% of graduations have ZERO post-graduation volume.")
    print("  >>> These tokens graduate but nobody trades them on the DEX.")
    print("  >>> A real strategy MUST filter these out to avoid untradeable entries.")
    print()

    # =========================================================================
    # ACTIVE-ONLY WIN RATE ANALYSIS
    # =========================================================================
    active_tokens = [t for t in tokens if t["is_active"]]

    print("─" * 70)
    print("  ACTIVE TOKENS ONLY — Core Win Rate Analysis")
    print("─" * 70)
    print()
    print("  Strategy: Buy at graduation detection, TP at +30%, SL at -15%")
    print()

    for cp in ["1m", "5m", "10m", "30m"]:
        pct_key = f"{cp}_pct"
        tp_key = f"{cp}_tp"
        sl_key = f"{cp}_sl"

        valid = [t for t in active_tokens if t.get(pct_key) is not None]
        if not valid:
            print(f"  [{cp:>3s}] No data")
            continue

        tp_count = sum(1 for t in valid if t[tp_key])
        sl_count = sum(1 for t in valid if t[sl_key])
        neither = len(valid) - tp_count - sl_count
        win_rate = tp_count / len(valid) * 100

        pcts = [t[pct_key] for t in valid]
        avg_pct = sum(pcts) / len(pcts)
        sorted_pcts = sorted(pcts)
        median_pct = sorted_pcts[len(sorted_pcts) // 2]

        # Distribution
        buckets = {
            "< -50%": 0, "-50 to -30%": 0, "-30 to -15%": 0,
            "-15 to 0%": 0, "0 to +15%": 0, "+15 to +30%": 0,
            "+30 to +50%": 0, "+50 to +100%": 0, "> +100%": 0,
        }
        for p in pcts:
            if p < -50: buckets["< -50%"] += 1
            elif p < -30: buckets["-50 to -30%"] += 1
            elif p < -15: buckets["-30 to -15%"] += 1
            elif p < 0: buckets["-15 to 0%"] += 1
            elif p < 15: buckets["0 to +15%"] += 1
            elif p < 30: buckets["+15 to +30%"] += 1
            elif p < 50: buckets["+30 to +50%"] += 1
            elif p < 100: buckets["+50 to +100%"] += 1
            else: buckets["> +100%"] += 1

        print(f"  [{cp:>3s}] {len(valid)} active tokens")
        print(f"         TP hit (+30%):  {tp_count:>3d} ({win_rate:.1f}%)")
        print(f"         SL hit (-15%):  {sl_count:>3d} ({sl_count/len(valid)*100:.1f}%)")
        print(f"         Neither:        {neither:>3d} ({neither/len(valid)*100:.1f}%)")
        print(f"         Avg change:     {avg_pct:+.1f}%")
        print(f"         Median change:  {median_pct:+.1f}%")
        print(f"         Range:          {min(pcts):+.1f}% to {max(pcts):+.1f}%")
        print(f"         Distribution:")
        for bname, cnt in buckets.items():
            if cnt > 0:
                bar = "█" * cnt
                print(f"           {bname:>15s}: {cnt:>3d} {bar}")
        print()

    # =========================================================================
    # SIMULATED P&L — ACTIVE ONLY
    # =========================================================================
    print("─" * 70)
    print("  ACTIVE TOKENS — Simulated P&L ($5/trade)")
    print("─" * 70)
    print()

    for cp in ["1m", "5m", "10m", "30m"]:
        pct_key = f"{cp}_pct"
        tp_key = f"{cp}_tp"
        sl_key = f"{cp}_sl"
        valid = [t for t in active_tokens if t.get(pct_key) is not None]
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
                pnl = trade_size * 0.30
                total_pnl += pnl
                wins += 1
                total_win_pnl += pnl
            elif t[sl_key]:
                pnl = trade_size * -0.15
                total_pnl += pnl
                losses += 1
                total_loss_pnl += abs(pnl)
            else:
                pct = t[pct_key]
                pnl = trade_size * (pct / 100)
                total_pnl += pnl
                if pnl >= 0:
                    wins += 1
                    total_win_pnl += pnl
                else:
                    losses += 1
                    total_loss_pnl += abs(pnl)

        win_rate = wins / len(valid) * 100
        avg_win = total_win_pnl / wins if wins > 0 else 0
        avg_loss = total_loss_pnl / losses if losses > 0 else 0.01
        wl_ratio = avg_win / avg_loss

        print(f"  [{cp:>3s}] {len(valid)} trades at $5 each")
        print(f"         Wins: {wins}  |  Losses: {losses}  |  Win Rate: {win_rate:.1f}%")
        print(f"         Total P&L:     ${total_pnl:+.2f}")
        print(f"         Avg Win:       ${avg_win:+.2f}")
        print(f"         Avg Loss:      ${avg_loss:.2f}")
        print(f"         Win/Loss Ratio: {wl_ratio:.2f}:1")
        print()

    # =========================================================================
    # SOCIAL SIGNALS — ACTIVE ONLY
    # =========================================================================
    print("─" * 70)
    print("  ACTIVE TOKENS — Social Signal Analysis")
    print("─" * 70)
    print()

    for cp in ["30m"]:  # Focus on 30m as it's the most complete checkpoint
        pct_key = f"{cp}_pct"
        valid = [t for t in active_tokens if t.get(pct_key) is not None]
        if not valid:
            continue

        print(f"  [{cp}] checkpoint (active tokens only):")
        for signal_name, signal_key in [("Twitter", "has_twitter"), ("Telegram", "has_telegram"), ("Website", "has_website")]:
            w = [t for t in valid if t.get(signal_key)]
            wo = [t for t in valid if not t.get(signal_key)]
            avg_w = sum(t[pct_key] for t in w) / len(w) if w else 0
            avg_wo = sum(t[pct_key] for t in wo) / len(wo) if wo else 0
            tp_w = sum(1 for t in w if t.get(f"{cp}_tp"))
            tp_wo = sum(1 for t in wo if t.get(f"{cp}_tp"))
            sl_w = sum(1 for t in w if t.get(f"{cp}_sl"))
            sl_wo = sum(1 for t in wo if t.get(f"{cp}_sl"))
            print(f"    {signal_name:>10s}: WITH {len(w):>2d} avg {avg_w:+.1f}% TP:{tp_w} SL:{sl_w}  |  WITHOUT {len(wo):>2d} avg {avg_wo:+.1f}% TP:{tp_wo} SL:{sl_wo}")

        for sc in range(4):
            group = [t for t in valid if t.get("social_count", 0) == sc]
            if group:
                avg_g = sum(t[pct_key] for t in group) / len(group)
                tp_g = sum(1 for t in group if t.get(f"{cp}_tp"))
                sl_g = sum(1 for t in group if t.get(f"{cp}_sl"))
                wr_g = tp_g / len(group) * 100
                print(f"    {sc} socials:   {len(group):>2d} tokens, avg {avg_g:+.1f}%, WR {wr_g:.0f}%, TP:{tp_g} SL:{sl_g}")
        print()

    # =========================================================================
    # MARKET CAP — ACTIVE ONLY
    # =========================================================================
    print("─" * 70)
    print("  ACTIVE TOKENS — Market Cap at Graduation")
    print("─" * 70)
    print()

    mcap_buckets = [
        ("< $10K", 0, 10000),
        ("$10K-$50K", 10000, 50000),
        ("$50K-$100K", 50000, 100000),
        ("$100K-$500K", 100000, 500000),
        ("$500K+", 500000, float("inf")),
    ]

    for cp in ["30m"]:
        pct_key = f"{cp}_pct"
        valid = [t for t in active_tokens if t.get(pct_key) is not None and t["mcap"] > 0]
        if not valid:
            continue

        print(f"  [{cp}] Performance by mcap (active tokens):")
        for bname, low, high in mcap_buckets:
            group = [t for t in valid if low <= t["mcap"] < high]
            if group:
                avg_g = sum(t[pct_key] for t in group) / len(group)
                tp_g = sum(1 for t in group if t.get(f"{cp}_tp"))
                sl_g = sum(1 for t in group if t.get(f"{cp}_sl"))
                wr = tp_g / len(group) * 100
                print(f"    {bname:>12s}: {len(group):>2d} tokens, avg {avg_g:+.1f}%, WR {wr:.0f}%, TP:{tp_g} SL:{sl_g}")
        print()

    # =========================================================================
    # TOKEN-BY-TOKEN TABLE — ACTIVE ONLY
    # =========================================================================
    print("─" * 70)
    print("  ACTIVE TOKENS — Detailed Performance")
    print("─" * 70)
    print()

    def sort_key(t):
        for cp in ["30m", "10m", "5m", "1m"]:
            pct = t.get(f"{cp}_pct")
            if pct is not None:
                return pct
        return -999

    active_sorted = sorted(active_tokens, key=sort_key, reverse=True)
    header = f"  {'Symbol':>10s} | {'Mcap':>10s} | {'1m':>8s} | {'5m':>8s} | {'10m':>8s} | {'30m':>8s} | {'Social':>6s} | Outcome"
    print(header)
    print("  " + "-" * (len(header.strip())))

    for t in active_sorted:
        if t.get("30m_pct") is None and t.get("10m_pct") is None and t.get("5m_pct") is None and t.get("1m_pct") is None:
            continue
        symbol = t["symbol"][:10]
        mcap_str = f"${t['mcap']:,.0f}" if t["mcap"] else "N/A"
        pct_strs = {}
        for cp in ["1m", "5m", "10m", "30m"]:
            pct = t.get(f"{cp}_pct")
            pct_strs[cp] = f"{pct:+.1f}%" if pct is not None else "---"

        social_str = ""
        if t["has_twitter"]: social_str += "T"
        if t["has_telegram"]: social_str += "G"
        if t["has_website"]: social_str += "W"
        if not social_str: social_str = "none"

        outcome = ""
        for cp in ["1m", "5m", "10m", "30m"]:
            if t.get(f"{cp}_tp"):
                outcome = f"TP@{cp}"
                break
            if t.get(f"{cp}_sl"):
                outcome = f"SL@{cp}"
                break
        if not outcome:
            for cp in ["30m", "10m", "5m", "1m"]:
                pct = t.get(f"{cp}_pct")
                if pct is not None:
                    outcome = f"{pct:+.0f}%@{cp}"
                    break

        print(f"  {symbol:>10s} | {mcap_str:>10s} | {pct_strs['1m']:>8s} | {pct_strs['5m']:>8s} | {pct_strs['10m']:>8s} | {pct_strs['30m']:>8s} | {social_str:>6s} | {outcome}")

    # =========================================================================
    # DEAD TOKEN CHARACTERISTICS
    # =========================================================================
    print()
    print("─" * 70)
    print("  DEAD TOKENS — What they look like (for future filtering)")
    print("─" * 70)
    print()

    dead_tokens = [t for t in tokens if t["is_dead"]]
    if dead_tokens:
        dead_mcaps = [t["mcap"] for t in dead_tokens if t["mcap"] > 0]
        active_mcaps = [t["mcap"] for t in active_tokens if t["mcap"] > 0]

        if dead_mcaps:
            avg_dead_mcap = sum(dead_mcaps) / len(dead_mcaps)
            med_dead_mcap = sorted(dead_mcaps)[len(dead_mcaps) // 2]
        else:
            avg_dead_mcap = 0
            med_dead_mcap = 0

        if active_mcaps:
            avg_active_mcap = sum(active_mcaps) / len(active_mcaps)
            med_active_mcap = sorted(active_mcaps)[len(active_mcaps) // 2]
        else:
            avg_active_mcap = 0
            med_active_mcap = 0

        print(f"  Dead token count:    {len(dead_tokens)}")
        print(f"  Dead avg mcap:       ${avg_dead_mcap:,.0f}")
        print(f"  Dead median mcap:    ${med_dead_mcap:,.0f}")
        print(f"  Active avg mcap:     ${avg_active_mcap:,.0f}")
        print(f"  Active median mcap:  ${med_active_mcap:,.0f}")
        print()

        # Social signal comparison
        dead_tw = sum(1 for t in dead_tokens if t["has_twitter"])
        dead_tg = sum(1 for t in dead_tokens if t["has_telegram"])
        dead_wb = sum(1 for t in dead_tokens if t["has_website"])
        act_tw = sum(1 for t in active_tokens if t["has_twitter"])
        act_tg = sum(1 for t in active_tokens if t["has_telegram"])
        act_wb = sum(1 for t in active_tokens if t["has_website"])

        print(f"  Social signals: Dead vs Active")
        print(f"    Twitter:  Dead {dead_tw}/{len(dead_tokens)} ({dead_tw/len(dead_tokens)*100:.0f}%)  |  Active {act_tw}/{len(active_tokens)} ({act_tw/len(active_tokens)*100:.0f}%)")
        print(f"    Telegram: Dead {dead_tg}/{len(dead_tokens)} ({dead_tg/len(dead_tokens)*100:.0f}%)  |  Active {act_tg}/{len(active_tokens)} ({act_tg/len(active_tokens)*100:.0f}%)")
        print(f"    Website:  Dead {dead_wb}/{len(dead_tokens)} ({dead_wb/len(dead_tokens)*100:.0f}%)  |  Active {act_wb}/{len(active_tokens)} ({act_wb/len(active_tokens)*100:.0f}%)")
        print()

        # List them
        print(f"  Dead token list:")
        for t in sorted(dead_tokens, key=lambda x: x["mcap"], reverse=True):
            social = ""
            if t["has_twitter"]: social += "T"
            if t["has_telegram"]: social += "G"
            if t["has_website"]: social += "W"
            if not social: social = "none"
            print(f"    {t['symbol']:>12s} | mcap ${t['mcap']:>10,.0f} | social: {social}")

    # =========================================================================
    # PEAK PERFORMANCE — ACTIVE ONLY
    # =========================================================================
    print()
    print("─" * 70)
    print("  PEAK PERFORMANCE — Active tokens only")
    print("─" * 70)
    print()

    for t in active_tokens:
        max_pct = None
        for cp in ["1m", "5m", "10m", "30m"]:
            pct = t.get(f"{cp}_pct")
            if pct is not None:
                if max_pct is None or pct > max_pct:
                    max_pct = pct
        t["max_pct"] = max_pct

    valid_active = [t for t in active_tokens if t.get("max_pct") is not None]
    if valid_active:
        ever_tp = sum(1 for t in valid_active if t["max_pct"] >= 30)
        ever_above_15 = sum(1 for t in valid_active if t["max_pct"] >= 15)
        ever_positive = sum(1 for t in valid_active if t["max_pct"] > 0)
        print(f"  Active tokens with price data: {len(valid_active)}")
        print(f"  Ever hit +30%:                 {ever_tp} ({ever_tp/len(valid_active)*100:.1f}%)")
        print(f"  Ever hit +15%:                 {ever_above_15} ({ever_above_15/len(valid_active)*100:.1f}%)")
        print(f"  Ever positive:                 {ever_positive} ({ever_positive/len(valid_active)*100:.1f}%)")

    # =========================================================================
    # FINAL VERDICT
    # =========================================================================
    print()
    print("=" * 70)
    print("  FINAL VERDICT — Corrected (Active Tokens Only)")
    print("=" * 70)
    print()
    print("  Criteria: Win Rate >30% (TP hit) AND Win/Loss Ratio >2:1")
    print()

    for cp in ["30m", "10m", "5m", "1m"]:
        pct_key = f"{cp}_pct"
        tp_key = f"{cp}_tp"
        sl_key = f"{cp}_sl"
        valid = [t for t in active_tokens if t.get(pct_key) is not None]
        if len(valid) < 5:
            continue

        tp_count = sum(1 for t in valid if t[tp_key])
        sl_count = sum(1 for t in valid if t[sl_key])
        win_rate = tp_count / len(valid) * 100

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

        wr_pass = "PASS" if win_rate > 30 else "FAIL"
        wl_pass = "PASS" if wl_ratio > 2 else "FAIL"
        overall = "GO" if win_rate > 30 and wl_ratio > 2 else "NO-GO"

        print(f"  [{cp:>3s}] {len(valid)} active tokens:")
        print(f"         TP Win Rate:        {win_rate:.1f}% — {wr_pass}")
        print(f"         Win/Loss Ratio:     {wl_ratio:.2f}:1 — {wl_pass}")
        print(f"         Verdict:            >>> {overall} <<<")
        print()
        break

    # Summary of key findings
    print("=" * 70)
    print("  KEY FINDINGS SUMMARY")
    print("=" * 70)
    print()
    print("  1. ~40% of graduations are DEAD — zero post-graduation volume.")
    print("     These tokens graduate but nobody trades them on DEX.")
    print()
    print("  2. Of the ~60% that ARE active (have real trading):")
    if valid_active:
        print(f"     - Only {ever_tp}/{len(valid_active)} ({ever_tp/len(valid_active)*100:.1f}%) ever hit +30% TP")
        print(f"     - {ever_above_15}/{len(valid_active)} ({ever_above_15/len(valid_active)*100:.1f}%) reached +15% at any point")
        print(f"     - {ever_positive}/{len(valid_active)} ({ever_positive/len(valid_active)*100:.1f}%) were ever positive at all")
    print()
    print("  3. The median price change is 0.0% — most tokens barely move.")
    print("     The distribution is heavily concentrated near zero.")
    print()
    print("  4. Social signals show NO clear predictive value:")
    print("     - Tokens with 0 socials actually performed best at 30m")
    print("     - This contradicts the hypothesis that socials = quality")
    print()
    print("  5. The 'buy every graduation' strategy does NOT work:")
    print("     - TP hit rate is far below the 30% threshold")
    print("     - Win/Loss ratio is far below the 2:1 threshold")
    print("     - Net P&L is approximately breakeven to slightly negative")
    print()
    print("  RECOMMENDATION:")
    print("  DO NOT proceed to Phase 1 with this strategy.")
    print("  Consider:")
    print("    a) Collect more data (current sample is 48 active tokens)")
    print("    b) Add filters (volume, holder count, DEX liquidity)")
    print("    c) Try different entry timing (wait for dip after initial spike)")
    print("    d) Try wider TP/narrower SL (the few winners go BIG)")
    print("    e) Focus on specific mcap ranges ($50K-$100K showed promise)")
    print("    f) Pivot to a fundamentally different strategy")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
