#!/usr/bin/env python3
"""
Pre-Graduation Observer v2 — Improved Data Collection
=======================================================
Monitors Pump.fun bonding curve tokens BEFORE graduation to answer:
  "What % of tokens at $10K/$20K/$30K/$40K/$50K mcap actually graduate?"

v2 improvements over v1:
- Smarter death detection: checks stale tokens every 2 min (not 5 min)
- Death declared when token drops 50% from high OR below $3K floor
- Actual time of death recorded (not just "stale timeout" at 120m)
- Records death_reason for analysis
- Mcap snapshots every 60s for trajectory analysis
- Log file rolls over at midnight UTC
- Max tracking time of 6 hours before force-resolving

Data saved to data/pregrad_{date}.jsonl for analysis.
"""
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Telegram alerts — reuses the probodds bot
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
# Alert when tokens cross this threshold or higher
ALERT_THRESHOLD = 30000

LOG_FILE = DATA_DIR / f"pregrad_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"

# Mcap thresholds to track (tokens crossing these levels)
THRESHOLDS = [5000, 10000, 20000, 30000, 40000, 50000, 60000]

# How often to poll the live API (seconds)
POLL_INTERVAL = 15

# How many tokens to fetch per poll
FETCH_LIMIT = 200

# How often to check stale tracked tokens via detail API (every N polls)
# At 15s poll interval, 8 polls = every 2 minutes
DETAIL_CHECK_INTERVAL = 8

# A token is considered "stale" if not seen in live API for this many minutes
STALE_MIN_BEFORE_CHECK = 5

# Death conditions
DEATH_MCAP_FLOOR = 3000
DEATH_DROP_PCT = 50
MAX_TRACKING_HOURS = 6

# How often to log mcap snapshots for trajectory (every N polls = ~60s)
SNAPSHOT_INTERVAL = 4


def send_telegram(message):
    """Send a Telegram message via the bot API. Non-blocking, best-effort."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        })
        subprocess.run(
            ["curl", "-s", "-X", "POST", url,
             "-H", "Content-Type: application/json",
             "-d", payload],
            capture_output=True, text=True, timeout=10
        )
    except Exception:
        pass  # alerts are best-effort, never crash the observer


def curl_json(url, timeout=15):
    """Fetch JSON via curl (avoids Python SSL issues)."""
    try:
        result = subprocess.run(
            ["curl", "-s", "-H", "User-Agent: Mozilla/5.0", url],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return None
        if not result.stdout.strip():
            return None
        return json.loads(result.stdout)
    except (json.JSONDecodeError, subprocess.TimeoutExpired, Exception):
        return None


def log_entry(entry):
    """Append entry to JSONL log, rolling over at midnight UTC."""
    global LOG_FILE
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    LOG_FILE = DATA_DIR / f"pregrad_{today}.jsonl"
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _declare_death(info, mint, now_iso, mcap, reason, elapsed_min):
    """Log a death event and mark token as died."""
    info["died"] = True
    entry = {
        "ts": now_iso,
        "event": "died",
        "mint": mint,
        "symbol": info["symbol"],
        "name": info["name"],
        "first_seen_mcap": info["first_seen_mcap"],
        "highest_mcap": info["highest_mcap"],
        "final_mcap": mcap,
        "thresholds_crossed": info["thresholds_crossed"],
        "time_tracked_min": round(elapsed_min, 1),
        "death_reason": reason,
        "has_twitter": info["has_twitter"],
        "has_telegram": info["has_telegram"],
        "has_website": info["has_website"],
    }
    log_entry(entry)
    return entry


def _declare_graduation(info, mint, now_iso, elapsed_min, note=None):
    """Log a graduation event and mark token as graduated."""
    info["graduated"] = True
    entry = {
        "ts": now_iso,
        "event": "graduated",
        "mint": mint,
        "symbol": info["symbol"],
        "name": info["name"],
        "first_seen_mcap": info["first_seen_mcap"],
        "highest_mcap": info["highest_mcap"],
        "thresholds_crossed": info["thresholds_crossed"],
        "time_tracked_min": round(elapsed_min, 1),
        "has_twitter": info["has_twitter"],
        "has_telegram": info["has_telegram"],
        "has_website": info["has_website"],
    }
    if note:
        entry["note"] = note
    log_entry(entry)
    return entry


def _check_death(info, mcap):
    """Check if a token meets death conditions. Returns reason or None."""
    if mcap < DEATH_MCAP_FLOOR:
        return f"below ${DEATH_MCAP_FLOOR}"
    high = info["highest_mcap"]
    if high >= 10000:
        drop = (1 - mcap / high) * 100 if high > 0 else 0
        if drop >= DEATH_DROP_PCT:
            return f"dropped {drop:.0f}% from ${high:,.0f}"
    return None


def main():
    print("=" * 60)
    print("  PRE-GRADUATION OBSERVER v2")
    print("=" * 60)
    print(f"  Log:              {LOG_FILE}")
    print(f"  Poll interval:    {POLL_INTERVAL}s")
    print(f"  Thresholds:       {THRESHOLDS}")
    print(f"  Death floor:      ${DEATH_MCAP_FLOOR:,}")
    print(f"  Death drop:       {DEATH_DROP_PCT}% from high")
    print(f"  Detail check:     every {DETAIL_CHECK_INTERVAL * POLL_INTERVAL}s")
    print(f"  Snapshot:         every {SNAPSHOT_INTERVAL * POLL_INTERVAL}s")
    print(f"  Max tracking:     {MAX_TRACKING_HOURS}h")
    tg_status = "ENABLED" if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID else "DISABLED"
    print(f"  Telegram alerts:  {tg_status} (>= ${ALERT_THRESHOLD/1000:.0f}K)")
    print(f"  Press Ctrl+C to stop\n")

    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        send_telegram("🟢 <b>Degen Pre-Grad Observer</b> started\nAlerts for tokens crossing $30K+")

    tracking = {}
    poll_count = 0
    events_logged = 0

    while True:
        try:
            now = datetime.now(timezone.utc)
            now_iso = now.isoformat()
            poll_count += 1

            data = curl_json(
                f"https://frontend-api-v3.pump.fun/coins/currently-live?limit={FETCH_LIMIT}"
            )
            if not data or not isinstance(data, list):
                if poll_count % 10 == 0:
                    print(f"  [{now.strftime('%H:%M:%S')}] API returned no data, retrying...")
                time.sleep(POLL_INTERVAL)
                continue

            graduated_mints = set()
            on_curve = {}
            for t in data:
                mint = t.get("mint", "")
                if not mint:
                    continue
                if t.get("complete") is True:
                    graduated_mints.add(mint)
                else:
                    on_curve[mint] = t

            # ── Process on-curve tokens ──
            for mint, t in on_curve.items():
                mcap = t.get("usd_market_cap", 0) or 0
                rsol = (t.get("real_sol_reserves", 0) or 0) / 1e9
                symbol = t.get("symbol", "?")
                name = (t.get("name", "?") or "?")[:40]

                if mcap < THRESHOLDS[0]:
                    continue

                if mint not in tracking:
                    tracking[mint] = {
                        "symbol": symbol,
                        "name": name,
                        "first_seen_ts": now_iso,
                        "first_seen_mcap": mcap,
                        "thresholds_crossed": {},
                        "highest_mcap": mcap,
                        "last_seen_mcap": mcap,
                        "last_seen_ts": now_iso,
                        "graduated": False,
                        "died": False,
                        "has_twitter": bool(t.get("twitter")),
                        "has_telegram": bool(t.get("telegram")),
                        "has_website": bool(t.get("website")),
                    }
                    print(f"  [{now.strftime('%H:%M:%S')}] NEW: {symbol:>10} at ${mcap:,.0f}")

                info = tracking[mint]
                if info["graduated"] or info["died"]:
                    continue

                info["last_seen_mcap"] = mcap
                info["last_seen_ts"] = now_iso
                if mcap > info["highest_mcap"]:
                    info["highest_mcap"] = mcap

                # Threshold crossings
                for threshold in THRESHOLDS:
                    thresh_key = str(threshold)
                    if thresh_key not in info["thresholds_crossed"] and mcap >= threshold:
                        info["thresholds_crossed"][thresh_key] = {
                            "ts": now_iso, "mcap": mcap, "rsol": round(rsol, 2),
                        }
                        entry = {
                            "ts": now_iso, "event": "threshold_crossed",
                            "mint": mint, "symbol": symbol, "name": name,
                            "threshold": threshold, "mcap": mcap,
                            "rsol": round(rsol, 2),
                            "has_twitter": info["has_twitter"],
                            "has_telegram": info["has_telegram"],
                            "has_website": info["has_website"],
                        }
                        log_entry(entry)
                        events_logged += 1
                        pct = mcap / 69000 * 100
                        print(f"  [{now.strftime('%H:%M:%S')}] ↑ {symbol:>10} crossed ${threshold/1000:.0f}K (now ${mcap:,.0f}, {pct:.0f}% to grad)")

                        # Telegram alert for high thresholds
                        if threshold >= ALERT_THRESHOLD:
                            social = []
                            if info["has_twitter"]: social.append("TW")
                            if info["has_telegram"]: social.append("TG")
                            if info["has_website"]: social.append("WB")
                            social_str = ", ".join(social) if social else "none"
                            send_telegram(
                                f"🚀 <b>{symbol}</b> crossed <b>${threshold/1000:.0f}K</b>\n"
                                f"mcap: ${mcap:,.0f} ({pct:.0f}% to grad)\n"
                                f"rSOL: {round(rsol, 1)}\n"
                                f"social: [{social_str}]\n"
                                f"<a href='https://pump.fun/coin/{mint}'>pump.fun</a>"
                            )

                # Check death from live-feed mcap
                reason = _check_death(info, mcap)
                if reason:
                    elapsed = (now - datetime.fromisoformat(info["first_seen_ts"])).total_seconds() / 60
                    _declare_death(info, mint, now_iso, mcap, reason, elapsed)
                    events_logged += 1
                    print(f"  [{now.strftime('%H:%M:%S')}] 💀 {symbol:>10} DIED ({reason})")

            # ── Graduation detection ──
            for mint in list(tracking.keys()):
                info = tracking[mint]
                if info["graduated"] or info["died"]:
                    continue
                if mint in graduated_mints:
                    elapsed = (now - datetime.fromisoformat(info["first_seen_ts"])).total_seconds() / 60
                    _declare_graduation(info, mint, now_iso, elapsed)
                    events_logged += 1
                    thresholds_str = ", ".join(
                        f"${int(k)/1000:.0f}K" for k in sorted(info["thresholds_crossed"].keys(), key=int)
                    )
                    print(f"  [{now.strftime('%H:%M:%S')}] 🎓 {info['symbol']:>10} GRADUATED! [{thresholds_str}]")

                    send_telegram(
                        f"🎓 <b>{info['symbol']}</b> GRADUATED!\n"
                        f"Thresholds: [{thresholds_str}]\n"
                        f"Tracked for {elapsed:.0f}m\n"
                        f"<a href='https://pump.fun/coin/{mint}'>pump.fun</a>"
                    )

            # ── Mcap snapshots for trajectory ──
            if poll_count % SNAPSHOT_INTERVAL == 0:
                for mint, info in tracking.items():
                    if info["graduated"] or info["died"]:
                        continue
                    if mint in on_curve:
                        mcap = on_curve[mint].get("usd_market_cap", 0) or 0
                        rsol = (on_curve[mint].get("real_sol_reserves", 0) or 0) / 1e9
                        log_entry({
                            "ts": now_iso, "event": "snapshot",
                            "mint": mint, "symbol": info["symbol"],
                            "mcap": mcap, "rsol": round(rsol, 2),
                            "highest_mcap": info["highest_mcap"],
                            "elapsed_min": round(
                                (now - datetime.fromisoformat(info["first_seen_ts"])).total_seconds() / 60, 1
                            ),
                        })

            # ── Stale token detail checks ──
            if poll_count % DETAIL_CHECK_INTERVAL == 0:
                stale_checked = 0
                for mint in list(tracking.keys()):
                    info = tracking[mint]
                    if info["graduated"] or info["died"]:
                        continue

                    last_seen = datetime.fromisoformat(info["last_seen_ts"])
                    stale_min = (now - last_seen).total_seconds() / 60
                    elapsed_hours = (now - datetime.fromisoformat(info["first_seen_ts"])).total_seconds() / 3600
                    elapsed_min = elapsed_hours * 60

                    if stale_min < STALE_MIN_BEFORE_CHECK and elapsed_hours < MAX_TRACKING_HOURS:
                        continue

                    detail = curl_json(f"https://frontend-api-v3.pump.fun/coins/{mint}")
                    time.sleep(0.3)
                    stale_checked += 1

                    if detail and isinstance(detail, dict):
                        if detail.get("complete") is True:
                            _declare_graduation(info, mint, now_iso, elapsed_min, note="detected_via_detail_check")
                            events_logged += 1
                            print(f"  [{now.strftime('%H:%M:%S')}] 🎓 {info['symbol']:>10} GRADUATED (detail check)")
                        else:
                            mcap = detail.get("usd_market_cap", 0) or 0
                            info["last_seen_mcap"] = mcap
                            info["last_seen_ts"] = now_iso
                            if mcap > info["highest_mcap"]:
                                info["highest_mcap"] = mcap

                            reason = _check_death(info, mcap)
                            if not reason and elapsed_hours >= MAX_TRACKING_HOURS:
                                reason = f"stale {elapsed_hours:.1f}h, mcap=${mcap:,.0f}"
                            if reason:
                                _declare_death(info, mint, now_iso, mcap, reason, elapsed_min)
                                events_logged += 1
                                print(f"  [{now.strftime('%H:%M:%S')}] 💀 {info['symbol']:>10} DIED ({reason})")
                    else:
                        if elapsed_hours >= MAX_TRACKING_HOURS:
                            _declare_death(info, mint, now_iso, info["last_seen_mcap"],
                                          f"no API response after {elapsed_hours:.1f}h", elapsed_min)
                            events_logged += 1
                            print(f"  [{now.strftime('%H:%M:%S')}] 💀 {info['symbol']:>10} DIED (no API response)")

                    if stale_checked >= 5:
                        break

            # ── Status ──
            if poll_count % 20 == 0:
                active = sum(1 for i in tracking.values() if not i["graduated"] and not i["died"])
                grads = sum(1 for i in tracking.values() if i["graduated"])
                deaths = sum(1 for i in tracking.values() if i["died"])
                log_lines = sum(1 for _ in open(LOG_FILE)) if LOG_FILE.exists() else 0
                print(f"  [{now.strftime('%H:%M:%S')}] Poll #{poll_count} | Active: {active} | Grads: {grads} | Died: {deaths} | Events: {log_lines}")

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print(f"\n\n  Stopped. {poll_count} polls, {events_logged} events logged.")
            if LOG_FILE.exists():
                lines = sum(1 for _ in open(LOG_FILE))
                print(f"  Log: {LOG_FILE} ({lines} entries)")

            active = sum(1 for i in tracking.values() if not i["graduated"] and not i["died"])
            grads = sum(1 for i in tracking.values() if i["graduated"])
            deaths = sum(1 for i in tracking.values() if i["died"])
            print(f"\n  Summary: {len(tracking)} tracked, {grads} graduated, {deaths} died, {active} still active")

            if tracking:
                print(f"\n  Conditional graduation rates (resolved only):")
                for threshold in THRESHOLDS:
                    thresh_key = str(threshold)
                    crossed = [i for i in tracking.values() if thresh_key in i["thresholds_crossed"]]
                    resolved = [i for i in crossed if i["graduated"] or i["died"]]
                    if resolved:
                        gc = sum(1 for i in resolved if i["graduated"])
                        print(f"    ${threshold/1000:.0f}K: {gc}/{len(resolved)} graduated ({gc/len(resolved)*100:.0f}%)")
            break
        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    main()
