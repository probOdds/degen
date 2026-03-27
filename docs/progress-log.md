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
