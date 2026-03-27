# Degen — Copilot Instructions

## Project Context
Solana memecoin graduation scanner. Monitors Pump.fun for tokens that graduate (reach $69K mcap, auto-migrate to Raydium/PumpSwap) and trades the post-migration momentum. Currently in **Phase 0 (observation / paper trading)** — collecting data on Pump.fun graduations on the Hetzner server.

**Previous experience:** Lost $1,288 on Polymarket over 12 strategy iterations (March 2026). The fundamental lesson: NEVER deploy capital before validating strategy with real data. NEVER build infrastructure before proving the edge exists.

**STATUS (March 27, 2026):** Phase 0 live. Graduation observer + price tracker running on Hetzner server (root@188.34.136.239). Status API on port 8004. Dashboard page at probodds.com/collector/degen. Collecting graduation events and post-graduation price action.

## CRITICAL RULES (learned from $1,288 in losses)

### Before ANY code is written:
1. Phase 0 (paper trading) MUST be complete with 50+ observations
2. Win rate MUST exceed 30% with 2:1 win/loss ratio in paper trading
3. Phase 1 (10 live trades at $5 each) MUST validate paper trading results
4. NEVER build automation before manual trading proves profitable

### When trading (Phase 1+):
1. Maximum $5 per trade (Phase 1), $10 per trade (Phase 2)
2. Maximum 5 trades per day
3. Maximum 10-minute hold time — hard exit after that
4. Take profit at +30%, stop loss at -15%
5. STOP trading if capital drops below $150
6. NEVER hold positions overnight
7. Every trade MUST be logged: entry, exit, P&L, reason

### When building (Phase 3+):
1. Strategy must be proven over 30+ live trades first
2. Change ONE variable at a time
3. Test with minimum size before scaling
4. Log everything — if it can't be measured, it can't be improved

## Infrastructure

### Server: Hetzner (root@188.34.136.239)
- 64GB RAM, Ubuntu, Python 3.12
- Shared with: basketball, soccer, dashboard, trading-collector
- Deploy dir: `/opt/probodds/degen/`
- Start script: `/opt/probodds/degen/start.sh` (starts all 3 processes)
- Logs: `/tmp/degen-observer.log`, `/tmp/degen-tracker.log`, `/tmp/degen-status-api.log`

### Running Processes
1. **Observer** (`scripts/observe_graduations.py`) — polls Pump.fun API every 20s, detects new graduations, logs to `data/graduations_{date}.jsonl`
2. **Price Tracker** (`scripts/track_prices.py`) — tails graduation log, tracks graduated token prices via DexScreener at 1m/5m/10m/30m checkpoints, logs to `data/price_tracking_{date}.jsonl`
3. **Status API** (`scripts/status_api.py`) — FastAPI on port 8004, exposes process health + data stats for dashboard

### Dashboard
- Page: `probodds.com/collector/degen`
- API: `api.probodds.com/degen/status` (nginx proxy → port 8004)
- Auto-refreshes every 10 seconds
- Shows: process health, graduation counts, recent graduations, data files

### Data Storage
- JSONL files in `/opt/probodds/degen/data/` (gitignored)
- One file per day: `graduations_{date}.jsonl`, `price_tracking_{date}.jsonl`
- JSONL is correct for Phase 0 — upgrade to Postgres only if Phase 1+ validates

## Architecture (Phase 3 — planned, not built)
- Chain: Solana
- Language: TypeScript or Rust
- RPC: Helius (Solana-specific, low latency)
- Execution: Jupiter Swap API + Jito bundles
- Monitoring: WebSocket subscription to Pump.fun graduation events
- Risk: Half-Kelly sizing, hard time limits, daily loss caps

## Key Files
- `docs/research.md` — Complete market research, strategy analysis, phase plan
- `docs/degen.md` — Background on memecoin infrastructure and concepts
- `docs/progress-log.md` — Daily progress, decisions, data snapshots
- `scripts/observe_graduations.py` — Graduation observer (Pump.fun API → JSONL)
- `scripts/track_prices.py` — Price tracker (DexScreener API → checkpoints)
- `scripts/status_api.py` — Dashboard status API (FastAPI, port 8004)
- `scripts/snapshot.py` — One-shot view of current graduated tokens
- `scripts/start.sh` — Server start script (all 3 processes)
- `README.md` — Project overview and current status
- `.env.example` — Environment variable template

## API Facts (Verified March 27, 2026)

### Working APIs
- **Pump.fun**: `https://frontend-api-v3.pump.fun/coins/currently-live` — returns token list, `complete=true` for graduated tokens. Fields: mint, symbol, name, usd_market_cap, twitter, telegram, website, creator, image_uri
- **Pump.fun detail**: `https://frontend-api-v3.pump.fun/coins/{mint}` — full token info
- **DexScreener**: `https://api.dexscreener.com/latest/dex/tokens/{mint}` — token pairs, priceUsd, volume, liquidity. Works from Hetzner, no auth needed.
- **Raydium API v3**: `https://api-v3.raydium.io/pools/info/list` — pool data, TVL, volume

### Non-Working / Issues
- **Jupiter v2** (`api.jup.ag/price/v2`): Returns 401 Unauthorized — requires API key now. Use DexScreener instead.
- **Jupiter v6** (`price.jup.ag/v6/price`): Returns empty/HTML. Likely deprecated.
- **GMGN.AI**: Returns 403 Forbidden — requires browser session/cookies.
- **Birdeye**: Returns 401 — requires API key.
- **DexScreener from macOS Python 3.14**: SSL cert error (Cloudflare). Works fine from Hetzner server.

## Solana / Memecoin Technical Facts
- Pump.fun graduation: token reaches $69K mcap on bonding curve → auto-migration to Raydium/PumpSwap
- ~$12K of liquidity deposited and LP tokens burned at graduation
- ~1-2% of all Pump.fun tokens graduate (17M+ tokens created, ~170K-340K graduated)
- Solana block time: ~400ms
- Jito bundles: private transaction relay, bypass public mempool, prevent MEV sandwich attacks

## Trading Platforms
- Banana Gun (Telegram): fastest execution, built-in MEV protection
- Photon (web): advanced filters, customizable interface
- GMGN (web): best analytics, graduation scanner, copy-trade

## DO NOT:
- Commit private keys, seed phrases, or wallet addresses to the repo
- Deploy capital before Phase 0 validation is complete
- Build automation before Phase 2 validation
- Trust training data over live market observation
- Assume theoretical models will work in practice
- Change multiple parameters simultaneously
