# Degen — Copilot Instructions

## Project Context
Solana memecoin graduation scanner. Monitors Pump.fun for tokens that graduate (reach $69K mcap, auto-migrate to Raydium/PumpSwap) and trades the post-migration momentum. Currently in Phase 0 (paper trading / observation).

**Previous experience:** Lost $1,288 on Polymarket over 12 strategy iterations (March 2026). The fundamental lesson: NEVER deploy capital before validating strategy with real data. NEVER build infrastructure before proving the edge exists.

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
- `README.md` — Project overview and current status
- `.env.example` — Environment variable template

## Solana / Memecoin Technical Facts
- Pump.fun graduation: token reaches $69K mcap on bonding curve → auto-migration to Raydium/PumpSwap
- ~$12K of liquidity deposited and LP tokens burned at graduation
- ~1-2% of all Pump.fun tokens graduate (17M+ tokens created, ~170K-340K graduated)
- Solana block time: ~400ms
- Jito bundles: private transaction relay, bypass public mempool, prevent MEV sandwich attacks
- GMGN.AI: primary tool for graduation scanning, wallet tracking, security checks
- RugCheck.xyz: pre-trade token security audit (honeypot, mint authority, LP lock)

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
