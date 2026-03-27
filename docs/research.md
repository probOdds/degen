# Memecoin & Degen Trading — Research & Analysis

**Date:** March 27, 2026
**Status:** Research complete. Phase 0 (paper trading) pending.
**Prior experience:** Lost $1,288 on Polymarket over 12 strategy iterations (March 16-27, 2026). Key lesson: validate strategy with data BEFORE deploying capital.

---

## Table of Contents

1. [Market Overview](#1-market-overview)
2. [Platform & Infrastructure Landscape](#2-platform--infrastructure-landscape)
3. [Strategy Analysis (5 Approaches)](#3-strategy-analysis)
4. [Risk Landscape](#4-risk-landscape)
5. [Recommended Strategy: Graduation Scanner](#5-recommended-strategy-graduation-scanner)
6. [Phase Plan](#6-phase-plan)
7. [Lessons from Polymarket (What NOT to Repeat)](#7-lessons-from-polymarket)
8. [Reference Data](#8-reference-data)

---

## 1. Market Overview

### 1.1 The Memecoin Ecosystem in 2026

The memecoin sector operates primarily on two blockchains:

| Metric | Solana | Base (Ethereum L2) |
|--------|--------|-------------------|
| Block time | ~400ms | ~2 seconds |
| Transaction finality | ~12.8 seconds | 13+ minutes |
| Throughput | 1,000+ TPS | ~100 TPS |
| Memecoin volume share | ~70-80% | ~15-20% |
| Primary launchpad | Pump.fun | Various (no dominant one) |
| Tx cost | ~$0.001-$0.01 | ~$0.01-$0.10 |

**Solana dominates memecoin trading.** Pump.fun alone accounts for 60-70% of all Solana DEX transaction volume. The speed, low cost, and established tooling make it the clear choice.

### 1.2 Pump.fun Statistics (Dune Analytics, verified March 2026)

| Metric | Value | Source |
|--------|-------|--------|
| Total tokens deployed | 17,081,179 | Dune @hashed_official |
| Graduation rate | ~1-2% | Community analysis |
| Total revenue (SOL) | 6,579,966 SOL | Dune @hashed_official |
| Estimated revenue (USD) | ~$900M+ | At ~$140/SOL |
| Daily new tokens | 20,000-40,000 | Dune daily deploy chart |
| Graduation threshold | $69,000 market cap | Pump.fun documentation |
| Post-graduation DEX | Raydium / PumpSwap | Pump.fun documentation |
| Liquidity locked at graduation | ~$12K burned | Pump.fun documentation |

**Key insight:** Of 17 million tokens created, roughly 170,000-340,000 graduated. The other 16.7 million died on the bonding curve. Pump.fun earned ~$900M in fees regardless. The platform always wins.

### 1.3 Who Actually Makes Money?

**Banana Gun Bot Leaderboard (Dune Analytics, top users):**

| Rank | Chain | Total Volume | Buy Volume | Sell Volume | Trades | Tokens |
|------|-------|-------------|-----------|------------|--------|--------|
| 1 | Ethereum | $25.2M | $12.0M | $13.2M | 9,548 | 1,986 |
| 2 | Ethereum | $25.0M | $11.9M | $13.1M | 2,465 | 191 |
| 9 | Solana | $20.4M | $9.9M | $10.4M | 6,133 | 1,500 |
| 12 | Solana | $19.1M | $10.6M | $8.5M | 1,523 | 233 |
| 16 | Solana | $16.3M | $9.4M | $6.9M | 42,737 | 19,310 |

**Critical observations:**
- The top 25 users out of 1,456,710 total made $5M-$13M each
- Average user: 17 trades, $59.59 in fees paid (lifetime)
- Daily active users: ~6,800 (0.47% of all users)
- **Most users trade a few times and stop** — the 17-trade average tells the story
- The profitable ones trade THOUSANDS of times with high volume

**Banana Gun aggregate stats:**
- Lifetime volume: $16.2 billion
- Lifetime users: 1,456,710
- Lifetime bot fees: $86.8 million
- Average daily volume (7d MA): $3.3 million
- Average daily trades (7d MA): 13,499
- Average daily active users (7d MA): 6,772

### 1.4 The PvP Reality

Memecoin trading is a zero-sum game with negative expected value for most participants:

- **Token creators** extract value by selling their pre-mined allocation
- **Early snipers** (bots) extract value from later buyers
- **Platforms** (Pump.fun, Banana Gun, GMGN) extract value via fees
- **MEV bots** extract value via sandwich attacks on public transactions
- **Retail traders** are the net source of all this extracted value

For every winner, there are multiple losers. The question isn't "can money be made?" — it's "can WE be on the winning side consistently enough to overcome the structural disadvantages?"

---

## 2. Platform & Infrastructure Landscape

### 2.1 Trading Platforms (Execution)

| Platform | Type | Chain | Key Features | Fees |
|----------|------|-------|-------------|------|
| **Banana Gun** | Telegram bot | ETH, SOL, Base | Sub-second execution, MEV protection, auto-snipe, copy-trade | 0.5-1% of trade |
| **Trojan** | Telegram bot | Solana | Fast execution, DCA, copy-trade, volume leader on SOL | 0.5-1% |
| **BONKbot** | Telegram bot | Solana | Similar to Trojan, popular for quick trades | 0.5-1% |
| **Photon** | Web terminal | Solana | Advanced filters (LP size, age, volume), customizable | Variable |
| **Maestro** | Telegram bot | Multi-chain | Smart routing, AI-assisted, established | 1% |

**Recommendation for Phase 0-1:** Photon or GMGN web interface for observation. Banana Gun or Trojan for execution once we go live.

### 2.2 Analytics & Intelligence Platforms

| Platform | Purpose | Key Features | Cost |
|----------|---------|-------------|------|
| **GMGN.AI** | Smart money tracking | Graduation scanner, wallet tracking, copy-trade, security checks, pump cooking | Free + premium |
| **Birdeye** | On-chain analytics | Profitable trader leaderboard, bubble maps, MCP API for AI agents | Free + premium |
| **DexScreener** | Token discovery | Trending tokens, charts, new pairs, hot pairs | Free |
| **DexTools** | Analytics | Score system, pool analytics, trading history | Free + premium |
| **RugCheck.xyz** | Security | Token contract audit, honeypot detection, mint authority check | Free |

**Recommendation:** GMGN.AI as primary tool (graduation scanner + security checks in one place).

### 2.3 Infrastructure Components

| Component | Options | Purpose | Cost |
|-----------|---------|---------|------|
| **RPC Node** | Helius, QuickNode, Alchemy | Fast Solana access (public RPCs too slow) | Free tier → $50+/mo |
| **Jito Bundles** | Jito Labs | MEV protection + priority block inclusion | Per-tx tip (0.001-0.1 SOL) |
| **Wallet** | Phantom, Solflare | Key management, transaction signing | Free |
| **VPS** | AWS, QuantVPS | Low-latency server near Solana validators | $5-$50/mo |

**For Phase 0-1:** Only need a Phantom wallet and GMGN account. No VPS or premium RPC needed yet.

### 2.4 MEV Protection: Why It Matters

When you submit a swap transaction to Solana, MEV bots can:
1. **See your pending transaction** in the public mempool
2. **Front-run you** — buy before your transaction, inflating the price
3. **Back-run you** — sell after your transaction, pocketing the difference

This "sandwich attack" can cost 5-30% of your trade value on volatile memecoins.

**Solutions:**
- **Jito Bundles:** Bypass public mempool entirely. Your transaction goes directly to validators via a private relay with a "tip." Guarantees atomic execution in the order you specify. Cost: 0.001-0.1 SOL per bundle depending on competition.
- **Built-in protection:** Banana Gun, Trojan, and Photon all route through Jito by default.

---

## 3. Strategy Analysis

### 3.1 Strategy A: Blind Pump.fun Sniping

**Concept:** Monitor Pump.fun for new token creations. Buy within milliseconds of launch at the bottom of the bonding curve. Sell for profit if the token gains traction.

**Math:**
- ~30,000 tokens created daily
- ~1-2% graduate (~300-600)
- Average graduation provides ~10-50x return for first buyers
- But: first-buyer positions are dominated by bots with dedicated infra
- Realistic hit rate for non-optimized setup: <0.5%

**Verdict: ❌ NOT VIABLE at our level.** The competition for first-buyer slots is extreme. Professional snipers use dedicated RPCs, Jito bundles with high tips, and pre-computed transactions. We'd be buying after them at inflated prices. And 98% of tokens die regardless.

### 3.2 Strategy B: Copy-Trading Smart Wallets

**Concept:** Identify wallets with historically high win rates on GMGN/Birdeye. When they buy a token, automatically mirror the trade.

**How it works with existing tools:**
- GMGN has a built-in "Copy Trade" feature
- Set up wallet monitoring → auto-buy when target wallet buys
- Set take-profit and stop-loss parameters

**Problems:**
1. **Latency gap:** By the time copy-trade triggers, smart money already bought. You buy 20-50% higher.
2. **Bait wallets:** Developers create wallets that look profitable to lure copy-traders, then dump.
3. **Wallet rotation:** Profitable wallets frequently change addresses to avoid being front-run.
4. **Crowded trade:** If 100 bots copy the same wallet, the price impact is massive.
5. **Selection bias:** GMGN shows you current leaders. Past performance ≠ future results.

**Verdict: ⚠️ POSSIBLE but high risk.** Could work with careful wallet selection and tight risk limits. But the latency problem is structural and hard to overcome.

### 3.3 Strategy C: Graduation Scanner (Post-Migration Momentum)

**Concept:** Monitor Pump.fun for tokens that are about to "graduate" (reach $69K market cap, triggering automatic migration to Raydium/PumpSwap with burned liquidity). Buy during or immediately after the migration event, ride the momentum, sell within minutes.

**Why this has an edge:**
1. **Graduation is a verifiable on-chain event** — not a prediction, not a signal. It HAPPENED.
2. **Post-graduation momentum is real** — the token gets a new DEX listing, new pool of potential buyers who don't use Pump.fun discover it via DexScreener/Birdeye.
3. **Liquidity is locked and burned** — $12K of liquidity deposited and LP tokens burned. No rug pull of the LP is possible post-graduation.
4. **Filterable** — not all graduations are equal. Volume, holder count, social presence, and initial price action post-migration can be used to select winners.
5. **Time-bounded** — buy and sell within 5-10 minutes. No overnight risk.

**How it works mechanically:**
1. Token reaches $69K mcap on Pump.fun bonding curve
2. Pump.fun automatically creates a Raydium/PumpSwap liquidity pool
3. ~$12K of liquidity deposited, LP tokens burned (permanent liquidity)
4. Token is now tradeable on the main Solana DEX ecosystem
5. DexScreener, Birdeye, GMGN all pick up the new pair
6. New buyers discover the token → momentum → price increase
7. We buy early in this momentum phase and sell into strength

**Key filters (to separate winners from losers):**
- Post-migration volume in first 5 minutes (>$5K = healthy signal)
- Holder count (>50 unique holders = organic, not just dev + 2 bots)
- Social links (Twitter, Telegram present = someone is promoting it)
- Dev wallet % (dev holds <10% of supply = less dump risk)
- Price action (price increasing in first 60 seconds post-migration, not dumping)

**Risk/reward math:**
- Entry at $69K-$100K mcap
- Target exit: +30% ($90K-$130K mcap)
- Stop-loss: -15% ($59K-$85K mcap)
- Win rate needed for breakeven: 33% (with 30% take-profit / 15% stop-loss = 2:1 ratio)
- Estimated realistic win rate with filters: 30-45%
- At 35% WR with 2:1 ratio: EV per trade = 0.35 × $1.50 - 0.65 × $0.75 = **+$0.04 per $5 risked** (barely positive)
- At 40% WR with 2:1 ratio: EV per trade = 0.40 × $1.50 - 0.60 × $0.75 = **+$0.15 per $5 risked** (meaningful)

**Verdict: ✅ MOST PROMISING for our constraints.** Verifiable trigger, time-bounded risk, existing tool support, small capital viable.

### 3.4 Strategy D: Bonding Curve Sniper (Pre-Graduation)

**Concept:** Buy tokens early on the Pump.fun bonding curve when mcap is $5K-$20K. If they graduate ($69K), you make 3-14x. If they die (98%), you lose everything.

**Math:**
- If 2% of tokens graduate and you enter at $10K mcap:
  - 2% chance of 6.9x return
  - 98% chance of losing ~100% of position
  - EV per $5 trade: 0.02 × $29.50 - 0.98 × $5.00 = **-$4.31** (deeply negative)
- Would need 8%+ graduation rate or entry below $2K mcap to be EV-positive

**Verdict: ❌ NOT VIABLE without extreme token filtering.** The base rate is too unfavorable. Could work with an AI filter that improves graduation prediction to 10%+ accuracy, but we don't have that yet.

### 3.5 Strategy E: Platform/Tool Building

**Concept:** Instead of trading, build a tool (Telegram bot, analytics dashboard, scanner) and earn fees from other traders.

**Evidence this works:**
- Pump.fun: ~$900M revenue
- Banana Gun: $86.8M in bot fees
- GMGN, Photon, Trojan: all profitable businesses

**Verdict: 🤔 VIABLE but different game.** This is a product/engineering business, not a trading strategy. Requires months of development, user acquisition, and ongoing maintenance. Could be a long-term pursuit but doesn't solve the "make money from trading" objective.

---

## 4. Risk Landscape

### 4.1 Technical Risks

| Risk | Description | Likelihood | Impact | Mitigation |
|------|------------|-----------|--------|-----------|
| **Rug pull** | Token contract has hidden backdoor; dev drains liquidity | Medium | Total loss of position | RugCheck.xyz pre-trade scan; GMGN security checks |
| **Honeypot** | Can buy but sell function is disabled | Medium | Total loss + gas fees | RugCheck honeypot detection; test with tiny amount first |
| **Sandwich attack** | MEV bot front-runs your trade | High (without protection) | 5-30% price impact | Use Jito bundles via Banana Gun/Trojan |
| **Token mint** | Dev can mint unlimited tokens, diluting yours to zero | Medium | Total loss | Check if mint authority is revoked (GMGN shows this) |
| **Failed transaction** | Solana congestion, tx dropped | Medium | Missed trade + gas fee | Use priority fees + Jito; retry logic |

### 4.2 Market Risks

| Risk | Description | Likelihood | Impact | Mitigation |
|------|------------|-----------|--------|-----------|
| **Pump-and-dump** | Price spikes then collapses before you can sell | High | 50-100% loss | 10-minute max hold; auto stop-loss |
| **Dead graduation** | Token graduates but has zero follow-on volume | High (50%+) | Stuck in illiquid position | Only enter if post-migration volume > $5K in 5 min |
| **Market cooldown** | Overall memecoin market volume drops | Medium | Fewer opportunities | Monitor daily graduation count; pause if <100/day |
| **SOL price drop** | SOL drops while holding positions | Low (short hold times) | Indirect loss | Keep most capital as USDC; convert to SOL only for trades |

### 4.3 Operational Risks

| Risk | Description | Likelihood | Impact | Mitigation |
|------|------------|-----------|--------|-----------|
| **Emotional FOMO** | Chasing tokens that have already pumped 500% | High | Buy the top, sell the bottom | Max 5 trades/day; strict entry criteria |
| **Over-trading** | Making too many trades, fees eat profits | Medium | Net negative from fees | Daily trade limit; minimum edge threshold |
| **Key compromise** | Wallet private key stolen | Low | Total loss of all funds | Use dedicated trading wallet; never share key; hardware wallet for storage |
| **Platform failure** | GMGN/Banana Gun goes down during critical trade | Low | Missed exit, stuck position | Have backup platform ready; know manual swap process |

---

## 5. Recommended Strategy: Graduation Scanner

### 5.1 System Overview

```
Pump.fun Token Lifecycle:
                                                          
  Created ($0)  ──→  Bonding Curve ($0-$69K)  ──→  GRADUATION ($69K)  ──→  Raydium/PumpSwap
                     (we don't trade here)          ▲ OUR ENTRY ZONE         (DEX trading)
                                                    │
                                                    └── Filters applied here:
                                                        ✓ Post-migration volume > $5K
                                                        ✓ Holder count > 50
                                                        ✓ Mint authority revoked
                                                        ✓ No honeypot detected
                                                        ✓ Price trending up in first 60s
                                                        ✗ Skip if dev > 10% supply
                                                        ✗ Skip if no social links
```

### 5.2 Entry Rules

1. Token MUST have graduated (reached $69K on Pump.fun, migrated to DEX)
2. Post-migration 5-minute volume MUST be > $5,000
3. Price MUST be trending up (not dumping) in the first 60-120 seconds
4. RugCheck / GMGN security scan MUST pass (no honeypot, no unlimited mint)
5. Holder count MUST be > 50 unique addresses
6. Dev wallet MUST hold < 10% of supply
7. Maximum entry market cap: $200K (don't chase tokens that have already run)

### 5.3 Exit Rules

1. **Take profit:** +30% from entry price → sell entire position
2. **Stop loss:** -15% from entry price → sell entire position
3. **Time limit:** 10 minutes elapsed → sell entire position regardless of P&L
4. **Never hold overnight.** Period.

### 5.4 Position Sizing

Using Half-Kelly criterion with conservative estimates:

$$f^* = \frac{W \cdot R - (1-W)}{R} \times 0.5$$

Where $W$ = win rate (estimated 35%), $R$ = win/loss ratio (2.0):

$$f^* = \frac{0.35 \times 2.0 - 0.65}{2.0} \times 0.5 = \frac{0.05}{2.0} \times 0.5 = 1.25\%$$

At 1.25% of bankroll per trade with $300 capital: **$3.75 per trade.**

For practical purposes: **$5 per trade** (slightly above Half-Kelly, but adequate for minimum viable trade size on Solana).

### 5.5 Daily Limits

- Maximum 5 trades per day
- Maximum daily loss: $25 (5 × $5) — but stop after 3 consecutive losses
- If capital drops below $150, STOP trading and reassess

---

## 6. Phase Plan

### Phase 0: Paper Trading & Observation (1 week, $0 at risk)

**Objective:** Verify that the graduation scanner strategy has a positive expected value.

**Actions:**
1. Create a GMGN.AI account
2. Set up Phantom wallet on Solana (don't fund it yet)
3. Open GMGN graduation scanner ("New → Almost Bonded → Migrated" filters)
4. For every graduation event, record:
   - Token name and contract address
   - Time of graduation
   - Market cap at graduation
   - Post-migration 5-minute volume
   - Price at 1 min, 5 min, 10 min, 30 min post-migration
   - Whether security check passed (honeypot, mint authority)
   - Number of holders
5. After 50+ observations, calculate:
   - How many passed ALL entry filters?
   - Of those, what % hit +30% within 10 minutes?
   - What % hit -15% within 10 minutes?
   - What was the average P&L per "simulated" trade?
6. Decision: proceed to Phase 1 ONLY if simulated win rate > 30% with 2:1 ratio

**Tools needed:** GMGN.AI account (free), web browser, spreadsheet

### Phase 1: Minimum Viable Trading (10 trades, $50 at risk)

**Prerequisites:** Phase 0 shows win rate > 30% with 2:1 ratio

**Actions:**
1. Fund Phantom wallet with 0.5 SOL (~$70)
2. Connect to Banana Gun or Photon
3. Execute exactly 10 trades following the exact rules from Phase 0
4. $5 per trade, strict entry/exit rules
5. Log every trade: entry price, exit price, P&L, time held, reason for exit

**Success criteria:** 4+ of 10 trades profitable (40%+ win rate in live execution)

### Phase 2: Scale or Stop (20 more trades, $100 at risk)

**If Phase 1 succeeded (4+ wins):**
- Increase to $10 per trade
- Execute 20 more trades
- Continue logging everything
- If 8+ of 20 profitable → Phase 3

**If Phase 1 failed (<4 wins):**
- Analyze WHY trades failed
- Was it filter quality? Execution speed? Slippage?
- Adjust filters, repeat Phase 1 with adjusted rules
- If second attempt also fails → strategy doesn't work for us. STOP.

### Phase 3: Automation (only after 30+ validated trades)

**Build custom graduation scanner bot:**
- Language: TypeScript or Rust (depending on latency needs)
- Solana WebSocket subscription for Pump.fun graduation events
- Auto-filter based on validated criteria from Phases 0-2
- Auto-execute via Jupiter Swap API with Jito bundle
- Auto-sell on take-profit/stop-loss/timer
- Logging and P&L tracking

**Infrastructure:**
- Helius RPC (free tier or starter plan)
- VPS near Solana validators ($5-$20/mo)
- Jito bundle submission
- Dedicated trading wallet

This phase ONLY starts after we have 30+ live trades proving the edge.

---

## 7. Lessons from Polymarket (What NOT to Repeat)

| Mistake on Polymarket | How We Avoid It Here |
|----------------------|---------------------|
| Built full Rust engine before validating strategy | Phase 0 is paper trading with zero code written |
| Deployed $1,300 before proving edge | $50 maximum in Phase 1, only $5/trade |
| Changed multiple variables at once | One strategy, one filter set. Validate. Then adjust. |
| Assumed our analysis was correct without live data | Paper trade 50+ graduations before spending $1 |
| Ignored structural market problems (thin books, adverse selection) | AMMs have real liquidity — we can ALWAYS exit |
| Trusted theoretical math over empirical results | Win rate measured from live observation, not calculated |
| Rushed to build before observing | Phase 0 is literally just watching for a week |
| No hard stop-loss | $25/day max loss. $150 total stop. Defined before trade #1 |

---

## 8. Reference Data

### 8.1 Key URLs

| Resource | URL | Purpose |
|----------|-----|---------|
| Pump.fun | https://pump.fun | Token launchpad |
| GMGN.AI | https://gmgn.ai | Graduation scanner, smart money, security |
| Birdeye | https://birdeye.so | On-chain analytics, profitable traders |
| DexScreener | https://dexscreener.com | Token discovery, charts |
| RugCheck | https://rugcheck.xyz | Token security audit |
| Banana Gun | https://t.me/BananaGunSniper_bot | Trading bot (Telegram) |
| Photon | https://photon-sol.tinyastro.io | Trading terminal (web) |
| Helius | https://dev.helius.xyz | Solana RPC provider |
| Jito | https://jito-labs.gitbook.io | MEV protection/bundles |
| Dune (Pump.fun) | https://dune.com/hashed_official/pumpdotfun | Pump.fun on-chain stats |
| Dune (Banana Gun) | https://dune.com/whale_hunter/banana-gun-bot | Bot usage stats |

### 8.2 Key Technical Concepts

**Bonding Curve:** Pump.fun tokens launch on a mathematical price curve where each purchase increases the price. No external liquidity needed — the curve IS the market.

**Graduation:** When bonding curve buys push the token to $69K mcap, Pump.fun automatically deploys a Raydium/PumpSwap liquidity pool with ~$12K of liquidity and burns the LP tokens. The token is now tradeable on the open DEX market.

**PumpSwap:** Pump.fun's own AMM (launched 2025), an alternative to Raydium for post-graduation trading.

**Jito Bundle:** A way to submit transactions privately to Solana validators, bypassing the public mempool. Prevents MEV sandwich attacks. Requires a SOL "tip" to the validator.

**AMM (Automated Market Maker):** A smart contract that provides liquidity via a mathematical formula (typically x*y=k). Unlike order books, AMMs always have a price — you can always buy or sell, though price impact increases with trade size relative to pool liquidity.

**Slippage:** The difference between expected price and actual execution price. On small AMM pools, slippage can be 5-20% for even modest trade sizes. Set slippage tolerance in trading tools to avoid catastrophic fills.

### 8.3 Solana Wallet Setup

1. Install Phantom browser extension: https://phantom.app
2. Create new wallet (SAVE THE SEED PHRASE SECURELY)
3. This will be your TRADING wallet — keep the minimum needed
4. Store majority of SOL in a separate wallet or hardware wallet
5. Never share seed phrase or private key with anyone
6. The private key can be exported from Phantom: Settings → Security → Export Private Key
