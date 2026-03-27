# Degen

Solana memecoin trading system focused on Pump.fun graduation momentum trades.

## Status: Phase 0 — Data Collection (Live)

**Started:** March 27, 2026
**Server:** Hetzner (root@188.34.136.239)
**Dashboard:** [probodds.com/collector/degen](https://probodds.com/collector/degen)
**API:** [api.probodds.com/degen/status](https://api.probodds.com/degen/status)

Graduation observer and price tracker are running on the Hetzner server, collecting data on Pump.fun token graduations and their post-graduation price action. No capital deployed.

**Previous project:** Lost $1,288 on Polymarket over 12 strategy iterations. Key lesson learned: validate strategy with real data BEFORE deploying capital. This project starts with observation, not code.

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
