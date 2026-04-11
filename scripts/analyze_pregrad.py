#!/usr/bin/env python3
"""
Pre-Graduation Analysis v2 — Full Analysis with v2 Observer Data
===================================================================
Analyzes pre-grad observer data to determine:
1. Conditional graduation probabilities at each mcap threshold
2. Expected value of buying at each threshold
3. Death timing and reasons (v2 data)
4. Mcap trajectory analysis (v2 snapshots)
5. Social signal correlation
6. Cross-reference with post-graduation performance
7. Final go/no-go decision with confidence intervals
"""
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")
THRESHOLDS = [5000, 10000, 20000, 30000, 40000, 50000, 60000]


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


def wilson_ci(successes, total, z=1.96):
    """Wilson score confidence interval for a proportion."""
    if total == 0:
        return 0, 0, 0
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denom
    lo = max(0, centre - spread)
    hi = min(1, centre + spread)
    return p, lo, hi


def main():
    # Load all data
    pregrad_files = sorted(DATA_DIR.glob("pregrad_*.jsonl"))
    if not pregrad_files:
        print("ERROR: No pregrad data files found")
        sys.exit(1)

    all_records = []
    for f in pregrad_files:
        all_records.extend(load_jsonl(f))

    grad_files = sorted(DATA_DIR.glob("graduations_*.jsonl"))
    all_grads = []
    for f in grad_files:
        all_grads.extend(load_jsonl(f))

    price_files = sorted(DATA_DIR.glob("price_tracking_*.jsonl"))
    all_prices = []
    for f in price_files:
        all_prices.extend(load_jsonl(f))

    # Separate event types
    threshold_crossings = [r for r in all_records if r["event"] == "threshold_crossed"]
    graduated_events = [r for r in all_records if r["event"] == "graduated"]
    died_events = [r for r in all_records if r["event"] == "died"]
    snapshots = [r for r in all_records if r["event"] == "snapshot"]

    print("=" * 70)
    print("  PRE-GRADUATION ANALYSIS v2 — Full Report")
    print("=" * 70)
    print()

    # ── 1. DATA OVERVIEW ──
    print("─" * 70)
    print("  1. DATA OVERVIEW")
    print("─" * 70)
    print()
    print(f"  Data files:             {len(pregrad_files)}")
    for f in pregrad_files:
        print(f"    {f.name}")
    print(f"  Total records:          {len(all_records)}")
    print(f"    Threshold crossings:  {len(threshold_crossings)}")
    print(f"    Graduated:            {len(graduated_events)}")
    print(f"    Died:                 {len(died_events)}")
    print(f"    Snapshots:            {len(snapshots)}")

    timestamps = []
    for r in all_records:
        ts = r.get("ts", "")
        if ts:
            try:
                timestamps.append(datetime.fromisoformat(ts))
            except ValueError:
                pass
    if timestamps:
        first, last = min(timestamps), max(timestamps)
        hours = (last - first).total_seconds() / 3600
        print(f"  Period:                 {first.strftime('%Y-%m-%d %H:%M')} → {last.strftime('%Y-%m-%d %H:%M')} UTC")
        print(f"  Duration:               {hours:.1f} hours ({hours/24:.1f} days)")
    print()

    # ── 2. BUILD PER-TOKEN SUMMARY ──
    tokens = {}
    for r in all_records:
        mint = r.get("mint", "")
        if not mint:
            continue
        if mint not in tokens:
            tokens[mint] = {
                "symbol": r.get("symbol", "?"),
                "name": r.get("name", "?"),
                "thresholds_crossed": {},
                "outcome": "active",
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
            tokens[mint]["thresholds_crossed"][r["threshold"]] = {
                "ts": r.get("ts", ""),
                "mcap": r.get("mcap", 0),
                "rsol": r.get("rsol", 0),
            }
        elif r["event"] == "graduated":
            tokens[mint]["outcome"] = "graduated"
            tokens[mint]["first_seen_mcap"] = r.get("first_seen_mcap")
            tokens[mint]["highest_mcap"] = r.get("highest_mcap")
            tokens[mint]["time_tracked_min"] = r.get("time_tracked_min")
            for tk, tv in r.get("thresholds_crossed", {}).items():
                thresh_int = int(tk)
                if thresh_int not in tokens[mint]["thresholds_crossed"]:
                    tokens[mint]["thresholds_crossed"][thresh_int] = tv
        elif r["event"] == "died":
            tokens[mint]["outcome"] = "died"
            tokens[mint]["first_seen_mcap"] = r.get("first_seen_mcap")
            tokens[mint]["highest_mcap"] = r.get("highest_mcap")
            tokens[mint]["final_mcap"] = r.get("final_mcap")
            tokens[mint]["time_tracked_min"] = r.get("time_tracked_min")
            tokens[mint]["death_reason"] = r.get("death_reason")
            for tk, tv in r.get("thresholds_crossed", {}).items():
                thresh_int = int(tk)
                if thresh_int not in tokens[mint]["thresholds_crossed"]:
                    tokens[mint]["thresholds_crossed"][thresh_int] = tv

    for t in tokens.values():
        t["social_count"] = sum([t["has_twitter"], t["has_telegram"], t["has_website"]])

    outcomes = Counter(t["outcome"] for t in tokens.values())
    total_tokens = len(tokens)
    print("─" * 70)
    print("  2. TOKEN SUMMARY")
    print("─" * 70)
    print()
    print(f"  Unique tokens tracked: {total_tokens}")
    for o, c in outcomes.most_common():
        print(f"    {o:>12s}: {c:>3d} ({c/total_tokens*100:.1f}%)")
    print()

    # ── 3. CONDITIONAL GRADUATION PROBABILITY ──
    print("─" * 70)
    print("  3. CONDITIONAL GRADUATION PROBABILITY")
    print("     P(graduation | token crossed threshold X)")
    print("     95% Wilson confidence intervals")
    print("─" * 70)
    print()

    for threshold in THRESHOLDS:
        crossed = [t for t in tokens.values() if threshold in t["thresholds_crossed"]]
        if not crossed:
            continue
        resolved = [t for t in crossed if t["outcome"] in ("graduated", "died")]
        grads = [t for t in resolved if t["outcome"] == "graduated"]
        active = [t for t in crossed if t["outcome"] == "active"]

        if resolved:
            rate, ci_lo, ci_hi = wilson_ci(len(grads), len(resolved))
            print(f"  ${threshold/1000:.0f}K threshold:")
            print(f"    Crossed: {len(crossed)}  |  Resolved: {len(resolved)}  |  Active: {len(active)}")
            print(f"    Graduated: {len(grads)}  |  Died: {len(resolved) - len(grads)}")
            print(f"    >>> RATE: {rate*100:.1f}%  (95% CI: {ci_lo*100:.1f}% – {ci_hi*100:.1f}%)")
            print()

    # ── 4. EXPECTED VALUE ──
    print("─" * 70)
    print("  4. EXPECTED VALUE — Is Pre-Grad Buying Viable?")
    print("─" * 70)
    print()
    print("  Buy $5 when token crosses threshold.")
    print("  If graduates ($69K): return = $69K / entry_mcap × $5")
    print("  If dies: WORST CASE = total loss; REALISTIC = sell at final mcap")
    print()

    for threshold in THRESHOLDS:
        crossed = [t for t in tokens.values() if threshold in t["thresholds_crossed"]]
        resolved = [t for t in crossed if t["outcome"] in ("graduated", "died")]
        if len(resolved) < 5:
            continue

        grads = [t for t in resolved if t["outcome"] == "graduated"]
        deaths = [t for t in resolved if t["outcome"] == "died"]
        grad_rate = len(grads) / len(resolved)

        multiplier = 69000 / threshold
        breakeven_rate = 1 / multiplier
        trade_size = 5.0

        # Worst case: total loss on death
        ev_worst = grad_rate * trade_size * multiplier + (1 - grad_rate) * 0 - trade_size

        # Realistic: sell at final mcap on death
        total_pnl = 0
        for t in resolved:
            if t["outcome"] == "graduated":
                total_pnl += trade_size * (multiplier - 1)
            else:
                final = t.get("final_mcap", 0) or 0
                recovery = final / threshold if threshold > 0 else 0
                total_pnl += trade_size * (recovery - 1) if recovery > 0 else -trade_size
        avg_pnl = total_pnl / len(resolved)

        _, ci_lo, ci_hi = wilson_ci(len(grads), len(resolved))
        ev_lo = ci_lo * trade_size * multiplier - trade_size
        ev_hi = ci_hi * trade_size * multiplier - trade_size

        is_positive = ev_worst > 0
        verdict = "POSITIVE EV" if is_positive else "NEGATIVE EV"

        print(f"  ${threshold/1000:.0f}K ({len(resolved)} resolved, {grad_rate*100:.1f}% grad rate, breakeven={breakeven_rate*100:.1f}%):")
        print(f"    {multiplier:.1f}x multiplier  |  $5 → ${trade_size * multiplier:.2f} if graduates")
        print(f"    WORST CASE EV:     ${ev_worst:+.2f}/trade  (95% CI: ${ev_lo:+.2f} to ${ev_hi:+.2f})")
        print(f"    REALISTIC EV:      ${avg_pnl:+.2f}/trade")
        print(f"    >>> {verdict}")
        print()

    # ── 5. DEATH ANALYSIS ──
    print("─" * 70)
    print("  5. DEATH ANALYSIS — When and Why Do Tokens Die?")
    print("─" * 70)
    print()

    died_tokens = [t for t in tokens.values() if t["outcome"] == "died"]

    # Death timing
    death_times = [t["time_tracked_min"] for t in died_tokens if t.get("time_tracked_min") is not None]
    if death_times:
        sorted_dt = sorted(death_times)
        print(f"  Death timing (n={len(death_times)}):")
        print(f"    Min:    {min(death_times):.1f} min")
        print(f"    Median: {sorted_dt[len(sorted_dt)//2]:.1f} min")
        print(f"    Avg:    {sum(death_times)/len(death_times):.1f} min")
        print(f"    Max:    {max(death_times):.1f} min")

        buckets = [(0, 5), (5, 15), (15, 30), (30, 60), (60, 120), (120, 360), (360, 9999)]
        for lo, hi in buckets:
            count = sum(1 for t in death_times if lo <= t < hi)
            if count > 0:
                label = f"{lo}-{hi}m" if hi < 9999 else f"{lo}m+"
                bar = "█" * min(count, 40)
                print(f"    {label:>8s}: {count:>3d} {bar}")
        print()

    # Death reasons (v2 data)
    reasons = Counter()
    for t in died_tokens:
        r = t.get("death_reason", "unknown (v1 data)")
        # Normalize
        if r and "below" in r:
            reasons["below $3K floor"] += 1
        elif r and "dropped" in r:
            reasons["dropped 50%+ from high"] += 1
        elif r and "stale" in r:
            reasons["stale timeout"] += 1
        elif r and "no API" in r:
            reasons["no API response"] += 1
        else:
            reasons[r or "unknown (v1 data)"] += 1

    if reasons:
        print(f"  Death reasons:")
        for reason, count in reasons.most_common():
            print(f"    {reason}: {count}")
        print()

    # How high did died tokens get?
    died_highs = [(t.get("highest_mcap", 0) or 0) for t in died_tokens]
    if died_highs:
        print(f"  Died tokens — highest mcap reached:")
        mcap_buckets = [
            ("$5K-$10K", 5000, 10000), ("$10K-$20K", 10000, 20000),
            ("$20K-$30K", 20000, 30000), ("$30K-$40K", 30000, 40000),
            ("$40K-$50K", 40000, 50000), ("$50K+", 50000, 999999),
        ]
        for name, lo, hi in mcap_buckets:
            count = sum(1 for h in died_highs if lo <= h < hi)
            if count > 0:
                bar = "█" * min(count, 40)
                print(f"    {name:>12s}: {count:>3d} {bar}")
        print()

    # ── 6. GRADUATION TIMING ──
    print("─" * 70)
    print("  6. GRADUATED TOKENS — Timing and Path")
    print("─" * 70)
    print()

    grad_tokens = [(m, t) for m, t in tokens.items() if t["outcome"] == "graduated"]
    if grad_tokens:
        grad_times = [t["time_tracked_min"] for _, t in grad_tokens if t.get("time_tracked_min")]
        if grad_times:
            sorted_gt = sorted(grad_times)
            print(f"  Graduation timing (n={len(grad_times)}):")
            print(f"    Min:    {min(grad_times):.1f} min")
            print(f"    Median: {sorted_gt[len(sorted_gt)//2]:.1f} min")
            print(f"    Avg:    {sum(grad_times)/len(grad_times):.1f} min")
            print(f"    Max:    {max(grad_times):.1f} min")
            print()

        print(f"  Graduated token details:")
        for mint, t in sorted(grad_tokens, key=lambda x: x[1].get("time_tracked_min") or 999):
            thresholds_str = " → ".join(f"${k/1000:.0f}K" for k in sorted(t["thresholds_crossed"].keys()))
            time_str = f"{t['time_tracked_min']:.0f}m" if t.get("time_tracked_min") else "?"
            social = []
            if t["has_twitter"]: social.append("TW")
            if t["has_telegram"]: social.append("TG")
            if t["has_website"]: social.append("WB")
            print(f"    {t['symbol']:>12} | {time_str:>5} | [{','.join(social) or 'none'}] | {thresholds_str}")

        # Threshold-to-threshold timing for graduated tokens
        print()
        print(f"  Threshold-to-threshold timing (graduated tokens):")
        for mint, t in grad_tokens:
            thresholds_sorted = sorted(t["thresholds_crossed"].keys())
            if len(thresholds_sorted) < 2:
                continue
            prev_ts = None
            steps = []
            for th in thresholds_sorted:
                info = t["thresholds_crossed"][th]
                ts_str = info.get("ts", "") if isinstance(info, dict) else ""
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str)
                        if prev_ts:
                            delta = (ts - prev_ts).total_seconds() / 60
                            steps.append(f"${th/1000:.0f}K(+{delta:.0f}m)")
                        else:
                            steps.append(f"${th/1000:.0f}K")
                        prev_ts = ts
                    except (ValueError, TypeError):
                        pass
            if steps:
                print(f"    {t['symbol']:>12}: {' → '.join(steps)}")
    print()

    # ── 7. SOCIAL SIGNALS ──
    print("─" * 70)
    print("  7. SOCIAL SIGNALS — Do They Predict Graduation?")
    print("─" * 70)
    print()

    resolved = [t for t in tokens.values() if t["outcome"] in ("graduated", "died")]
    if resolved:
        for signal_name, signal_key in [("Twitter", "has_twitter"), ("Telegram", "has_telegram"), ("Website", "has_website")]:
            with_s = [t for t in resolved if t.get(signal_key)]
            without_s = [t for t in resolved if not t.get(signal_key)]
            g_with = sum(1 for t in with_s if t["outcome"] == "graduated")
            g_without = sum(1 for t in without_s if t["outcome"] == "graduated")
            r_with = g_with / len(with_s) * 100 if with_s else 0
            r_without = g_without / len(without_s) * 100 if without_s else 0
            print(f"  {signal_name:>10}: WITH {len(with_s):>3d} → {g_with} grad ({r_with:.1f}%)  |  WITHOUT {len(without_s):>3d} → {g_without} grad ({r_without:.1f}%)")

        print()
        for sc in range(4):
            group = [t for t in resolved if t.get("social_count", 0) == sc]
            if group:
                g = sum(1 for t in group if t["outcome"] == "graduated")
                r = g / len(group) * 100
                print(f"  {sc} socials: {len(group):>3d} tokens, {g} graduated ({r:.1f}%)")
    print()

    # ── 8. TRAJECTORY ANALYSIS (v2 snapshot data) ──
    if snapshots:
        print("─" * 70)
        print("  8. TRAJECTORY ANALYSIS — Mcap Paths Over Time (v2 data)")
        print("─" * 70)
        print()

        # Group snapshots by mint
        snap_by_mint = defaultdict(list)
        for s in snapshots:
            snap_by_mint[s.get("mint", "")].append(s)

        # For graduated tokens, show their mcap trajectory
        print(f"  Graduated token trajectories (snapshot data):")
        for mint, t in grad_tokens:
            if mint not in snap_by_mint:
                continue
            snaps = sorted(snap_by_mint[mint], key=lambda s: s.get("elapsed_min", 0))
            traj = []
            for s in snaps:
                elapsed = s.get("elapsed_min", 0)
                mcap = s.get("mcap", 0)
                traj.append(f"{elapsed:.0f}m:${mcap/1000:.0f}K")
            if traj:
                # Show max 10 points
                if len(traj) > 10:
                    step = len(traj) // 10
                    traj = traj[::step][:10]
                print(f"    {t['symbol']:>12}: {' → '.join(traj)}")

        # For a sample of died tokens with multiple snapshots, show paths
        print()
        print(f"  Sample died token trajectories:")
        died_with_snaps = [(m, t) for m, t in tokens.items()
                          if t["outcome"] == "died" and m in snap_by_mint and len(snap_by_mint[m]) >= 3]
        died_with_snaps.sort(key=lambda x: x[1].get("highest_mcap", 0) or 0, reverse=True)
        for mint, t in died_with_snaps[:8]:
            snaps = sorted(snap_by_mint[mint], key=lambda s: s.get("elapsed_min", 0))
            traj = []
            for s in snaps:
                elapsed = s.get("elapsed_min", 0)
                mcap = s.get("mcap", 0)
                traj.append(f"{elapsed:.0f}m:${mcap/1000:.0f}K")
            if len(traj) > 8:
                step = len(traj) // 8
                traj = traj[::step][:8]
            death_r = t.get("death_reason", "?")
            print(f"    {t['symbol']:>12}: {' → '.join(traj)} [{death_r}]")
        print()

    # ── 9. CROSS-REFERENCE: Pre-Grad → Post-Grad ──
    print("─" * 70)
    print("  9. CROSS-REFERENCE — Pre-Grad Graduated → Post-Grad Performance")
    print("─" * 70)
    print()

    grad_mints = {m for m, t in tokens.items() if t["outcome"] == "graduated"}

    price_by_mint = defaultdict(list)
    for p in all_prices:
        price_by_mint[p.get("mint", "")].append(p)

    grad_data_by_mint = {}
    for g in all_grads:
        mint = g.get("mint", "")
        if mint and mint not in grad_data_by_mint:
            grad_data_by_mint[mint] = g

    tp_count = 0
    sl_count = 0
    total_with_price = 0

    for mint in grad_mints:
        t = tokens[mint]
        symbol = t["symbol"]
        thresholds_str = " → ".join(f"${k/1000:.0f}K" for k in sorted(t["thresholds_crossed"].keys()))

        print(f"  {symbol:>12} (path: {thresholds_str}):")

        if mint in grad_data_by_mint:
            g = grad_data_by_mint[mint]
            print(f"    Graduation mcap: ${g.get('mcap', 0):,.0f}")

        if mint in price_by_mint:
            total_with_price += 1
            prices = sorted(price_by_mint[mint], key=lambda p: p.get("checkpoint", ""))
            hit_tp = False
            hit_sl = False
            for p in prices:
                cp = p.get("checkpoint", "?")
                pct = p.get("pct_change")
                tp = p.get("would_tp", False)
                sl = p.get("would_sl", False)
                pct_str = f"{pct:+.1f}%" if pct is not None else "N/A"
                flag = " *** TP ***" if tp else (" *** SL ***" if sl else "")
                print(f"    {cp:>4}: {pct_str}{flag}")
                if tp: hit_tp = True
                if sl: hit_sl = True
            if hit_tp: tp_count += 1
            if hit_sl and not hit_tp: sl_count += 1
        else:
            print(f"    No post-graduation price data")
        print()

    if total_with_price > 0:
        print(f"  Post-grad summary: {tp_count}/{total_with_price} hit TP ({tp_count/total_with_price*100:.0f}%)")
        print(f"                     {sl_count}/{total_with_price} hit SL ({sl_count/total_with_price*100:.0f}%)")
    print()

    # ── 10. COMBINED RETURN: Pre-Grad + Post-Grad ──
    print("─" * 70)
    print("  10. COMBINED RETURN — Total Strategy P&L")
    print("─" * 70)
    print()
    print("  Strategy: Buy $5 on bonding curve when token crosses $5K.")
    print("  If it graduates → HOLD and apply post-grad TP/SL rules.")
    print("  If it dies → lose investment (or sell at final mcap).")
    print()

    threshold = 5000
    crossed = [t for t in tokens.values() if threshold in t["thresholds_crossed"]]
    resolved_tokens = [t for t in crossed if t["outcome"] in ("graduated", "died")]
    if resolved_tokens:
        trade_size = 5.0
        total_combined_pnl = 0
        trade_details = []

        for t in resolved_tokens:
            if t["outcome"] == "graduated":
                # Pre-grad gain: $5K → $69K = 13.8x
                pre_grad_gain = trade_size * (69000 / threshold - 1)

                # Find this token's post-grad performance
                # Use the best available checkpoint
                mint_matches = [m for m, tk in tokens.items() if tk is t]
                post_grad_pct = 0
                if mint_matches:
                    mint = mint_matches[0]
                    if mint in price_by_mint:
                        for p in price_by_mint[mint]:
                            pct = p.get("pct_change")
                            if pct is not None and p.get("would_tp"):
                                post_grad_pct = 30  # TP at +30%
                                break
                        if post_grad_pct == 0:
                            # Use 30m checkpoint if no TP
                            for p in price_by_mint[mint]:
                                if p.get("checkpoint") == "30m" and p.get("pct_change") is not None:
                                    post_grad_pct = p["pct_change"]
                                    break

                # Total: pre-grad gain + post-grad gain on the graduated position
                invested = trade_size
                value_at_grad = trade_size * (69000 / threshold)
                post_grad_pnl = value_at_grad * (post_grad_pct / 100)
                total_pnl = (value_at_grad - invested) + post_grad_pnl
                total_combined_pnl += total_pnl
                trade_details.append(("GRAD", t["symbol"], total_pnl))
            else:
                # Died: partial recovery
                final = t.get("final_mcap", 0) or 0
                recovery = final / threshold if threshold > 0 else 0
                pnl = trade_size * (recovery - 1) if recovery > 0 else -trade_size
                total_combined_pnl += pnl
                trade_details.append(("DIED", t["symbol"], pnl))

        avg_combined = total_combined_pnl / len(resolved_tokens)
        wins = sum(1 for _, _, p in trade_details if p > 0)
        losses = sum(1 for _, _, p in trade_details if p <= 0)

        print(f"  Results over {len(resolved_tokens)} trades at $5 each:")
        print(f"    Total P&L:     ${total_combined_pnl:+.2f}")
        print(f"    Avg P&L/trade: ${avg_combined:+.2f}")
        print(f"    Wins: {wins}  |  Losses: {losses}  |  Win Rate: {wins/len(resolved_tokens)*100:.1f}%")
        print(f"    Capital used:  ${trade_size * len(resolved_tokens):.0f}")
        print(f"    ROI:           {total_combined_pnl / (trade_size * len(resolved_tokens)) * 100:+.1f}%")
        print()

        # Show top winners and losers
        trade_details.sort(key=lambda x: x[2], reverse=True)
        print(f"  Top 5 winners:")
        for outcome, sym, pnl in trade_details[:5]:
            print(f"    {sym:>12} ({outcome}): ${pnl:+.2f}")
        print(f"  Worst 5 losers:")
        for outcome, sym, pnl in trade_details[-5:]:
            print(f"    {sym:>12} ({outcome}): ${pnl:+.2f}")
    print()

    # ── 11. FINAL VERDICT ──
    print("=" * 70)
    print("  11. FINAL VERDICT")
    print("=" * 70)
    print()
    print("  Criteria: Positive EV with 95% CI lower bound > 0")
    print()

    for threshold in THRESHOLDS:
        crossed = [t for t in tokens.values() if threshold in t["thresholds_crossed"]]
        resolved = [t for t in crossed if t["outcome"] in ("graduated", "died")]
        if len(resolved) < 10:
            continue

        grads = [t for t in resolved if t["outcome"] == "graduated"]
        rate, ci_lo, ci_hi = wilson_ci(len(grads), len(resolved))
        multiplier = 69000 / threshold
        breakeven = 1 / multiplier

        ev_point = rate * 5.0 * multiplier - 5.0
        ev_lo = ci_lo * 5.0 * multiplier - 5.0
        ev_hi = ci_hi * 5.0 * multiplier - 5.0

        confident_positive = ci_lo > breakeven
        verdict = "GO ✓" if confident_positive else ("MARGINAL ~" if ev_point > 0 else "NO-GO ✗")

        print(f"  ${threshold/1000:.0f}K: rate={rate*100:.1f}% CI=[{ci_lo*100:.1f}%-{ci_hi*100:.1f}%] breakeven={breakeven*100:.1f}%")
        print(f"       EV=${ev_point:+.2f} CI=[${ev_lo:+.2f}, ${ev_hi:+.2f}]")
        print(f"       >>> {verdict}")
        print()

    print("=" * 70)
    print("  END OF ANALYSIS")
    print("=" * 70)


if __name__ == "__main__":
    main()
