# Degen — Progress Log

## 2026-03-27 — Day 1: Project Setup & Phase 0 Launch

### Context
Pivoted from Polymarket trading (probOdds/polymarket, formerly probodds-trading) after losing $1,288 across 12 strategy iterations. The fundamental problem: Polymarket's thin order books and adverse selection make profitable trading nearly impossible without $20K+ capital. Decided to explore Solana memecoin trading with a "validate before building" approach.

### Research Phase (Morning)
- Deep-dived into memecoin/degen trading landscape
- Verified market data via Dune Analytics:
  - Pump.fun: 17.1M tokens deployed, $900M+ revenue, ~1-2% graduation rate
  - Banana Gun: 1.46M lifetime users, $16.2B volume, $86.8M fees
  - Top 25 Banana Gun users made $5-13M each
- Evaluated 5 strategies with math:
  1. **Graduation Scanner** (SELECTED) — 2:1 risk/reward, verifiable events
  2. Copy Trading — parasitic, alpha decays with followers
  3. New Token Sniper — 99% rug rate, needs sub-100ms latency
  4. Trending/Volume Scanner — too late by definition
  5. AI/Social Scanner — unproven, overcrowded
- Created comprehensive research doc at `docs/research.md`

### API Discovery (Midday)
- **Pump.fun API**: `frontend-api-v3.pump.fun/coins/currently-live` — WORKING. Returns token data with `complete=True` for graduated tokens
- **Jupiter Price API v2**: Returns 401 Unauthorized — now requires API key
- **DexScreener API**: WORKING from Hetzner server. Returns token pairs with priceUsd, volume, liquidity
- **Raydium API v3**: WORKING for pool data
- **GMGN.AI**: 403 Forbidden (needs browser session)
- **Birdeye**: 401 (needs API key)
- **macOS Python 3.14 SSL issue**: Cloudflare blocks DexScreener/Jupiter from local machine. Scripts use subprocess curl workaround. All APIs work fine from Hetzner.

### Scripts Built
1. **`observe_graduations.py`** — Polls Pump.fun every 20s, detects new graduated tokens (complete=True), logs mint/symbol/mcap/social info + DexScreener price to JSONL
2. **`track_prices.py`** — Tails graduation log, fetches DexScreener prices at 1m/5m/10m/30m checkpoints, simulates TP+30%/SL-15% hits
3. **`snapshot.py`** — One-shot view of current graduated tokens
4. **`status_api.py`** — FastAPI on port 8004 exposing process health + data stats for dashboard monitoring

### Deployment
- **Server**: Hetzner `root@188.34.136.239` (probodds-server, 64GB RAM, Ubuntu, Python 3.12)
  - Same server as basketball, soccer, dashboard, trading-collector
  - Found server IP in basketball copilot-instructions.md
- **Deploy dir**: `/opt/probodds/degen/`
- **Data dir**: `/opt/probodds/degen/data/` (JSONL files, gitignored)
- **Nginx**: Added `/degen/` proxy to `api.probodds.com` → port 8004
- **Start script**: `/opt/probodds/degen/start.sh` — starts observer, tracker, status API

### Dashboard Integration
- Added degen observer page to probodds-dashboard at `/collector/degen`
- Follows same pattern as collector page:
  - API client: `src/lib/api/degen.ts`
  - React Query hook: `src/lib/hooks/use-degen-queries.ts` (10s auto-refresh)
  - Page: `src/app/collector/degen/page.tsx`
- Shows: process health banners, today's stats, recent graduations with Pump.fun links, data files
- Deployed static build to `/opt/probodds/dashboard/releases/20260327-185830-degen/`
- Live at: `https://probodds.com/collector/degen`

### Data Collected (Day 1 — partial, started ~6:40 PM UTC)
- **8 graduations** detected in ~15 minutes of operation
- **18 price checkpoints** recorded
- Extrapolated rate: ~30-40 graduations/day (need 50+ for analysis)

### Key Decisions
1. **JSONL over Postgres** for Phase 0 — correct tool for ~200 entries/day of exploratory data. Upgrade to Postgres only if Phase 1 validates.
2. **DexScreener over Jupiter** — Jupiter v2 now requires auth. DexScreener works without auth, provides priceUsd directly.
3. **Added to collector section** in dashboard nav rather than a new top-level section — degen is observation tooling, not a separate sport.

### Repos Affected
- `probOdds/degen` — new scripts, status API, updated docs
- `probOdds/probodds-dashboard` — new degen page, API client, nav item
- Server config: nginx proxy added to `/etc/nginx/sites-enabled/probodds-api`

### Open Questions for Phase 0 Analysis
Once 50+ graduations collected (estimated: 1-2 days):
1. What % of graduated tokens pump >30% within 10 minutes?
2. Do social signals (twitter/telegram/website) correlate with pump probability?
3. Does market cap at graduation predict post-graduation behavior?
4. What's the optimal entry timing (1m? 2m? 5m after graduation)?
5. Does creator history matter? (repeat creators vs unique)

### Next Steps
- [ ] Let observer run 24-48 hours to collect 50+ graduation events
- [ ] Pull data and analyze: graduation outcomes, filter effectiveness
- [ ] Calculate simulated win rate with TP+30%/SL-15%
- [ ] If >30% WR with 2:1 ratio → proceed to Phase 1 manual trading
- [ ] If not → adjust filters or abandon strategy

---

### Polymarket Closure (also March 27)
- AWS Dublin Lightsail instance DELETED
- Git history squashed (removed leaked private key + API keys)
- Repo renamed from probodds-trading → polymarket
- Final P&L: -$1,288 of $1,300 deposited ($11 remaining on-chain)
- 98 verified trades: 90W/8L = 91.8% WR but negative EV due to adverse selection at extreme prices

---

## 2026-03-28 — Day 2: Post-Graduation Analysis

### Data Collected
- 55 unique graduated tokens, 200 price checkpoints across 15.8 hours
- Graduation rate: ~3.5/hour (83/day)

### Analysis Results (Post-Graduation Strategy)
Ran comprehensive analysis (`scripts/analyze_phase0.py`, `scripts/analyze_phase0_corrected.py`).

**Finding: The "buy every graduation" strategy does NOT work.**
- 44% of graduations are dead — zero post-graduation trading volume (DexScreener returns stale cached prices)
- Of the 28 active tokens: TP hit rate 7.4% (need >30%), W/L ratio 1.03:1 (need >2:1)
- Social signals showed NO predictive value — tokens with 0 socials outperformed those with socials
- Verdict: **NO-GO for Phase 1**

### Pivot to Pre-Graduation Strategy
User asked: what about catching tokens BEFORE graduation? Research revealed:
- Bonding curve math: every Pump.fun token uses k=3.22e25 constant product, graduates at ~85 real SOL
- If you buy at $5K mcap and it graduates at $69K, that's 13.8x return
- Base rate: only 1-2% of ALL tokens graduate — deeply negative EV
- **Key question: what's P(graduation | mcap > $30K)?** — need data to answer

### Pre-Graduation Observer Deployed
Built `scripts/observe_pregrad.py` (v1):
- Tracks tokens as they cross $5K/$10K/$20K/$30K/$40K/$50K/$60K mcap thresholds
- Records whether each token eventually graduates or dies
- Updated status API and dashboard for pre-grad data
- All 4 processes running on Hetzner

---

## 2026-03-29 to 2026-03-30 — Days 3-4: Pre-Grad Observer v2

### v1 Data Quality Issues
- All 73 "died" tokens showed identical ~120m tracking time — the stale timeout, not actual death time
- No mcap trajectory data between threshold crossings

### v2 Observer Improvements
- Death detection: checks every 2 min (was 5), triggers when mcap drops <$3K or 50% from high
- Death reason recorded for analysis
- Mcap snapshots every 60s for trajectory analysis
- Log file rolls over at midnight UTC
- Max 6h tracking before force-resolving

### Early Results (n=80 resolved)
- $5K: 8.8% graduation rate (breakeven: 7.2%) — marginal positive EV
- $30K: 75.0% graduation rate (breakeven: 43.5%) — strong positive EV
- BUT: small sample, wide confidence intervals

---

## 2026-03-30 to 2026-04-04 — Days 4-9: Data Collection & Analysis

### Sample Growth
| Date | $30K Resolved | Grad Rate |
|------|--------------|-----------|
| Mar 30 | 13 | 61.5% |
| Mar 31 | 22 | 54.5% |
| Apr 1 | 25 | 60.0% |
| Apr 2 | 26 | 61.5% |
| Apr 4 | 32 | 62.5% |

### Full Analysis (Apr 4, n=32 at $30K)
- Built comprehensive analysis script (`scripts/analyze_pregrad.py`) with Wilson CI
- **$30K threshold: 62.5% grad rate, 95% CI [45.3%–77.1%], breakeven 43.5%**
- Worst-case EV: +$2.19/trade, CI lower bound just above breakeven → **GO ✓**
- $5K/$10K/$20K all below breakeven — NO-GO

### Data Quality Investigation (`scripts/investigate_strategy.py`)
- Found 3 anomalous tokens (ANIME, FAP, gnzystrm) with >$69K mcap classified as "died" — likely PumpSwap tokens incorrectly tracked. Excluding them: $30K rate improves to 69.0%
- $40K+ 0% graduation explained: all were these same anomalous tokens

### Strategy A vs B Analysis
- **A: Sell at graduation** ($30K→$69K = 2.3x) — +$6.50/trade guaranteed
- **B: Hold for post-grad momentum** — +$8.10/trade avg, but B beats A only 65% of the time
- Post-graduation: 48% hit TP, 48% hit SL — essentially a coin flip

### Execution Window
- 75% of tokens go $30K→graduation in <5 minutes, 30% in <1 minute
- Manual execution can only catch the slower ones

---

## 2026-04-05 — Day 10: Telegram Alerts & Phase 1 Start

### Telegram Integration
- Wired pre-grad observer into existing probodds Telegram bot
- Alerts fire on $30K+ threshold crossings and graduations
- Includes symbol, mcap, % to graduation, social links, pump.fun link

### Phase 1 Decision
Based on $30K data (n=32, 62.5% grad rate, CI above breakeven): **GO for Phase 1**
- Manual trading via Pump.fun/Photon when Telegram alert fires
- $5/trade, sell at graduation if possible

---

## 2026-04-05 to 2026-04-11 — Days 10-16: Phase 1 Live Trading

### Data Convergence
- $30K graduation rate drifted down as sample grew: 62.5% (n=32) → 50.0% (n=56)
- At 50%, worst-case EV: +$0.75/trade — very thin
- 95% CI lower bound (37%) now BELOW breakeven (43.5%)

### Phase 1 Results
- Placed trades on alerts
- **Net negative P&L**
- The theoretical edge (+$0.75/trade) did not survive execution costs (slippage, gas, timing delays)
- Selection bias: manual execution catches slower tokens that are more likely to reverse

### Final Verdict: ABANDON
The strategy does not have a sufficient edge for manual execution.

---

## 2026-04-11 — Project Closure

### Final Statistics
- **1,372 unique tokens tracked** over 14 days
- **41 graduated** out of 1,352 resolved (3.0% overall)
- **$30K threshold**: 28/56 graduated (50.0%) — above theoretical breakeven but too thin for execution
- **Live trading**: net negative

### Total Losses Across Projects
- Polymarket: -$1,288
- Degen (Phase 1): net negative (small, $5/trade sizing)

### Lessons Learned
1. **Data collection infrastructure was excellent** — the observer system, dashboard, and Telegram alerts all worked flawlessly
2. **The analysis approach was correct** — validate with paper data → small live trades → decide
3. **Theoretical EV != executable EV** — slippage, gas, and timing delays eat thin edges
4. **The execution window problem is fundamental** — 75% of graduating tokens go $30K→$69K in <5 minutes. Manual trading cannot capture the fast ones, which biases your sample toward the slower (worse) tokens
5. **Graduation rates converge lower with more data** — early small samples were optimistic (62.5% at n=32 → 50% at n=56)
6. **Social signals are useless** — consistently showed no predictive value across all analyses

### What Would Be Needed for This to Work
- Sub-second automated execution (Jito bundles, dedicated RPC)
- $5K+ capital to absorb the high variance
- 70%+ graduation rate at the entry threshold (which we never observed)
- Or a completely different filter that improves the base rate

### Status: SHELVED
Observer processes remain running on Hetzner (low resource usage). Data continues to collect passively. No capital deployed.
