#!/usr/bin/env python3
"""
Deep analysis of Pump.fun bonding curve mechanics.
Queries multiple API endpoints to understand:
1. How the bonding curve works mathematically
2. What returns look like at different entry points
3. What % of tokens at each mcap level eventually graduate
"""
import json
import subprocess
import sys
import time


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
    print("=" * 70)
    print("  PUMP.FUN BONDING CURVE — Deep Analysis")
    print("=" * 70)
    print()

    # =====================================================
    # 1. Fetch a range of tokens at different mcap levels
    # =====================================================
    # The /coins/currently-live endpoint gives us a snapshot
    # We need multiple API calls to see different mcap levels

    # Get currently live tokens
    live = curl_json("https://frontend-api-v3.pump.fun/coins/currently-live?limit=50")
    if not live:
        print("ERROR: Could not fetch live tokens")
        sys.exit(1)

    # Also try to get "king of the hill" (highest mcap approaching graduation)
    koth = curl_json("https://frontend-api-v3.pump.fun/coins/king-of-the-hill?limit=50")

    # Sort all tokens by mcap
    all_tokens = list(live)
    if koth and isinstance(koth, list):
        seen_mints = set(t.get("mint", "") for t in all_tokens)
        for t in koth:
            if t.get("mint", "") not in seen_mints:
                all_tokens.append(t)
                seen_mints.add(t.get("mint", ""))

    print(f"  Total tokens fetched: {len(all_tokens)}")
    print(f"    from /currently-live: {len(live)}")
    print(f"    from /king-of-the-hill: {len(koth) if koth else 0}")
    print()

    # Separate graduated vs not
    graduated = [t for t in all_tokens if t.get("complete") is True]
    on_curve = [t for t in all_tokens if t.get("complete") is not True]

    print(f"  Graduated: {len(graduated)}")
    print(f"  On bonding curve: {len(on_curve)}")
    print()

    # =====================================================
    # 2. Analyze bonding curve reserves
    # =====================================================
    print("─" * 70)
    print("  BONDING CURVE: Virtual Reserves at Different Mcap Levels")
    print("─" * 70)
    print()

    # The bonding curve uses a constant-product formula: x * y = k
    # virtual_sol_reserves * virtual_token_reserves = k
    # real_sol_reserves = virtual_sol_reserves - initial_virtual_sol
    # real_token_reserves = actual tokens remaining in the curve

    # For all tokens, compute k and analyze
    header = f"  {'Symbol':>10} | {'Mcap USD':>12} | {'vSOL':>14} | {'vTokens':>18} | {'rSOL':>14} | {'rTokens':>18} | {'k':>20} | {'Complete':>8}"
    print(header)
    print("  " + "-" * (len(header.strip())))

    sorted_tokens = sorted(all_tokens, key=lambda t: t.get("usd_market_cap", 0) or 0, reverse=True)

    for t in sorted_tokens[:40]:
        sym = t.get("symbol", "?")[:10]
        mcap = t.get("usd_market_cap", 0) or 0
        vsol = t.get("virtual_sol_reserves", 0)
        vtokens = t.get("virtual_token_reserves", 0)
        rsol = t.get("real_sol_reserves", 0)
        rtokens = t.get("real_token_reserves", 0)
        complete = t.get("complete", False)
        k = vsol * vtokens if vsol and vtokens else 0

        # Convert SOL from lamports (1 SOL = 1e9 lamports)
        vsol_sol = vsol / 1e9 if vsol else 0
        rsol_sol = rsol / 1e9 if rsol else 0

        print(f"  {sym:>10} | ${mcap:>11,.0f} | {vsol_sol:>10.2f} SOL | {vtokens:>18,} | {rsol_sol:>10.2f} SOL | {rtokens:>18,} | {k:>20.2e} | {'YES' if complete else 'no':>8}")

    # =====================================================
    # 3. Compute bonding curve math
    # =====================================================
    print()
    print("─" * 70)
    print("  BONDING CURVE MATH — Understanding the Returns")
    print("─" * 70)
    print()

    # Find a recently graduated token and a still-on-curve token
    # to understand the initial conditions

    # From the data, determine the initial virtual reserves
    # Initial state: approximately 30 SOL virtual, ~1 billion tokens virtual
    # When someone buys, SOL goes up, tokens go down (constant product)
    # Graduation happens when real_sol_reserves reaches ~85 SOL

    # Let's find the constants from graduated tokens
    if graduated:
        print("  Graduated token bonding curve state:")
        for t in graduated[:3]:
            vsol = t.get("virtual_sol_reserves", 0) / 1e9
            rsol = t.get("real_sol_reserves", 0) / 1e9
            vtokens = t.get("virtual_token_reserves", 0)
            rtokens = t.get("real_token_reserves", 0)
            total = t.get("total_supply", 0)
            mcap = t.get("usd_market_cap", 0) or 0
            k = (t.get("virtual_sol_reserves", 0)) * vtokens

            tokens_sold = total - rtokens if total and rtokens else 0
            pct_sold = tokens_sold / total * 100 if total else 0

            print(f"    {t.get('symbol', '?'):>10}:")
            print(f"      vSOL:          {vsol:.2f} SOL")
            print(f"      rSOL:          {rsol:.2f} SOL (actual SOL deposited by buyers)")
            print(f"      vTokens:       {vtokens:,}")
            print(f"      rTokens:       {rtokens:,}")
            print(f"      total_supply:  {total:,}")
            print(f"      tokens sold:   {tokens_sold:,} ({pct_sold:.1f}% of supply)")
            print(f"      k:             {k:.2e}")
            print(f"      USD mcap:      ${mcap:,.0f}")
            print()

    # Now for on-curve tokens at different levels
    if on_curve:
        print("  On-curve tokens at different levels:")
        # Sort by mcap
        on_curve_sorted = sorted(on_curve, key=lambda t: t.get("usd_market_cap", 0) or 0, reverse=True)
        for t in on_curve_sorted[:10]:
            vsol = t.get("virtual_sol_reserves", 0) / 1e9
            rsol = t.get("real_sol_reserves", 0) / 1e9
            vtokens = t.get("virtual_token_reserves", 0)
            rtokens = t.get("real_token_reserves", 0)
            total = t.get("total_supply", 0)
            mcap = t.get("usd_market_cap", 0) or 0

            tokens_sold = total - rtokens if total and rtokens else 0
            pct_sold = tokens_sold / total * 100 if total else 0

            # The bonding curve initial state: ~30 SOL virtual, ~1,073,000,000,000,000 tokens virtual
            # Real SOL starts at 0, increases as people buy
            # At graduation: real SOL = ~85 SOL, tokens remaining = very few

            # price per token = vsol / vtokens (in SOL terms)
            price_sol = vsol / vtokens if vtokens else 0
            price_usd = price_sol * 82.74 if price_sol else 0  # approximate SOL price

            # If this token graduates, buyer's return from current price
            # At graduation, mcap = ~$69K
            # Return = graduation_price / current_price - 1
            if mcap > 0:
                return_to_grad = (69000 / mcap - 1) * 100
            else:
                return_to_grad = 0

            print(f"    {t.get('symbol', '?'):>10} | mcap=${mcap:>8,.0f} | rSOL={rsol:>6.2f} | sold={pct_sold:.1f}% | price=${price_usd:.10f} | if-grad: {return_to_grad:+.0f}%")

    # =====================================================
    # 4. Compute theoretical returns
    # =====================================================
    print()
    print("─" * 70)
    print("  THEORETICAL RETURNS — If You Buy Pre-Grad at Different Points")
    print("─" * 70)
    print()
    print("  Assumption: You buy at mcap X, token graduates at $69K mcap")
    print("  Graduation gives ~10-15x from creation to graduation")
    print()

    entry_points = [
        (1000, "Very early ($1K mcap)"),
        (5000, "Early ($5K mcap)"),
        (10000, "Medium ($10K mcap)"),
        (20000, "Mid ($20K mcap)"),
        (30000, "Approaching ($30K mcap)"),
        (40000, "Close ($40K mcap)"),
        (50000, "Near ($50K mcap)"),
        (60000, "Almost ($60K mcap)"),
        (69000, "At graduation ($69K)"),
    ]

    for entry_mcap, label in entry_points:
        if entry_mcap > 0:
            return_pct = (69000 / entry_mcap - 1) * 100
            multiplier = 69000 / entry_mcap
            pnl_per_5 = 5.0 * (multiplier - 1)
            print(f"  Entry ${entry_mcap:>6,} ({label:>30s}): {return_pct:>8.0f}% return ({multiplier:.1f}x) → $5 becomes ${5*multiplier:.2f} (PnL: ${pnl_per_5:+.2f})")

    print()
    print("  BUT: Only ~1-2% of Pump.fun tokens graduate!")
    print("  Expected value calculation:")
    print()

    for grad_rate in [0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.50]:
        for entry_mcap_val in [5000, 10000, 20000, 40000]:
            multiplier = 69000 / entry_mcap_val
            ev = grad_rate * (5.0 * multiplier) + (1 - grad_rate) * 0 - 5.0
            ev_str = f"${ev:+.2f}" 
            print(f"    {grad_rate*100:.0f}% grad rate, buy at ${entry_mcap_val/1000:.0f}K: EV = {ev_str} per $5 trade")
        print()

    # =====================================================
    # 5. Key question: Can we get a BETTER graduation rate
    #    by filtering to tokens that are ALREADY approaching?
    # =====================================================
    print("─" * 70)
    print("  THE KEY QUESTION: Conditional Graduation Probability")
    print("─" * 70)
    print()
    print("  Base rate: ~1-2% of ALL tokens graduate")
    print("  But what if we only consider tokens at $30K+, $40K+, $50K+ mcap?")
    print("  The closer a token is to $69K, the higher the chance it graduates.")
    print()
    print("  This is the core of the pre-graduation strategy:")
    print("  If P(graduation | mcap > $50K) >> 2%, the math changes completely.")
    print()
    print("  To answer this, we need data we DON'T have yet:")
    print("  - Track tokens when they REACH $30K, $40K, $50K, $60K mcap")
    print("  - Record whether each one eventually graduates or dies")
    print("  - Compute conditional graduation rate at each mcap level")
    print()
    print("  Current observer ONLY logs tokens AFTER graduation.")
    print("  We need a NEW observer that watches pre-graduation tokens.")


if __name__ == "__main__":
    main()
