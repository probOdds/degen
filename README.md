# Degen

Solana memecoin trading system focused on Pump.fun graduation momentum trades.

## Status: SHELVED — No Executable Edge Found

**Duration:** March 27 – April 11, 2026 (16 days)
**Outcome:** No profitable strategy identified after thorough data collection and live trading validation.

### What We Found

Over 14 days, we tracked **1,372 unique tokens** on the Pump.fun bonding curve and observed their outcomes:

| Entry Threshold | Tokens Resolved | Graduated | Rate | Breakeven | Viable? |
|:--|:--|:--|:--|:--|:--|
| $5K | 1,352 | 41 | 3.0% | 7.2% | No |
| $10K | 766 | 40 | 5.2% | 14.5% | No |
| $20K | 308 | 38 | 12.3% | 29.0% | No |
| **$30K** | **56** | **28** | **50.0%** | **43.5%** | **Marginal** |

The $30K threshold showed the only positive theoretical EV (+$0.75/trade), but this did not survive real-world execution. Live Phase 1 trading was **net negative** — slippage, gas, and the inability to catch fast-graduating tokens (75% go $30K→$69K in <5 minutes) eliminated the thin edge.

### Key Lessons
1. **Data-first approach was correct** — 16 days of observation before risking capital prevented large losses
2. **Theoretical EV ≠ executable EV** — thin edges get destroyed by friction
3. **Social signals have zero predictive value** for graduation or post-graduation performance
4. **Post-graduation momentum is a coin flip** — 48% hit +30% TP, 48% hit -15% SL
5. **Manual execution cannot capture fast-moving tokens** — fundamental speed disadvantage

### What Still Runs
Observer processes remain on Hetzner (low resource usage). Data collects passively. Telegram alerts fire on $30K+ bonding curve crossings.

**Previous project:** Lost $1,288 on Polymarket over 12 strategy iterations (March 2026).

## Strategy: Graduation Scanner

Monitor Pump.fun for tokens that reach $69K market cap ("graduation"), triggering automatic migration to Raydium/PumpSwap. Buy during the post-migration momentum window, sell within minutes.

**Why this strategy:**
- Graduation is a verifiable on-chain event (not a prediction)
- Post-graduation momentum is driven by new DEX discovery
- Liquidity is locked and burned ($12K LP burned at graduation)
- AMMs provide real, instant exit liquidity (unlike Polymarket's thin order books)
- Time-bounded: trades last 5-10 minutes, no overnight risk
- Small capital viable: $5-$10 per trade on $300-$500 bankroll

**Why on Solana:**
- 70-80% of all memecoin volume
- 400ms block times (vs 2s on Base)
- Pump.fun is Solana-native
- Best tooling ecosystem (GMGN, Photon, Banana Gun, Jito)

## Phase Plan

| Phase | Duration | Capital at Risk | Goal |
|-------|----------|----------------|------|
| **Phase 0** | 1 week | $0 | Paper trade 50+ graduations, measure win rate |
| **Phase 1** | 1-2 weeks | $50 | 10 live trades at $5 each, validate execution |
| **Phase 2** | 2 weeks | $100 | 20 trades at $10 each, confirm edge holds live |
| **Phase 3** | Ongoing | $300-$500 | Automate proven strategy with custom bot |

**Phase 3 only starts after 30+ validated trades prove the edge.**

## Rules (Non-Negotiable)

1. Maximum $5 per trade in Phase 1
2. Maximum 5 trades per day
3. Maximum 10-minute hold time per trade
4. Take profit at +30%, stop loss at -15%
5. Stop trading entirely if capital drops below $150
6. Never hold overnight
7. Every trade logged with entry, exit, P&L, and reason
8. No code gets built until Phase 2 validates the strategy

## Project Structure

```
.github/
  copilot-instructions.md   Project context, rules, API facts
docs/
  research.md               Full research & analysis
  degen.md                  Memecoin infrastructure concepts
  progress-log.md           Daily progress & decisions
scripts/
  observe_graduations.py    Pump.fun graduation detector (→ JSONL)
  track_prices.py           Post-graduation price tracker (DexScreener → JSONL)
  status_api.py             FastAPI dashboard status endpoint (port 8004)
  snapshot.py               One-shot current graduated tokens view
  start.sh                  Server start script (all 3 processes)
data/                       (server only, gitignored)
  graduations_{date}.jsonl  Detected graduation events
  price_tracking_{date}.jsonl Price checkpoints (1m/5m/10m/30m)
```

## Documentation

- [Full Research & Analysis](docs/research.md) — Market overview, platform landscape, 5 strategy evaluations, risk analysis, detailed plan
- [Degen Trading Concepts](docs/degen.md) — Background on memecoin infrastructure, MEV, bonding curves, AI agents
- [Progress Log](docs/progress-log.md) — Daily progress, decisions, data snapshots

## Tools

| Tool | Purpose | Phase |
|------|---------|-------|
| [Pump.fun API](https://frontend-api-v3.pump.fun) | Graduation detection (primary data source) | Phase 0+ |
| [DexScreener API](https://api.dexscreener.com) | Token price data (replaces Jupiter v2) | Phase 0+ |
| [GMGN.AI](https://gmgn.ai) | Manual graduation scanning, security checks | Phase 1+ |
| [Phantom](https://phantom.app) | Solana wallet | Phase 1+ |
| [Banana Gun](https://t.me/BananaGunSniper_bot) | Trade execution with MEV protection | Phase 1+ |
| [RugCheck](https://rugcheck.xyz) | Pre-trade security audit | Phase 0+ |
| [DexScreener](https://dexscreener.com) | Token charts and discovery | Phase 0+ |
| [Helius](https://dev.helius.xyz) | Solana RPC (for automation) | Phase 3 |
