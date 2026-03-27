#!/usr/bin/env python3
"""
Degen Observer Status API — lightweight FastAPI service exposing:
- Observer & tracker process health (PID, uptime, memory)
- Graduation counts and recent graduations
- Price tracking checkpoint stats
- Data file sizes and freshness

Runs on port 8004, auto-refreshed by dashboard every 10s.
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

DATA_DIR = Path("/opt/probodds/degen/data")

app = FastAPI(title="ProbOdds Degen Observer Status")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://probodds.com", "http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _find_process(name: str) -> dict | None:
    """Find a running python process by script name."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", name], capture_output=True, text=True, timeout=5
        )
        pids = result.stdout.strip().split("\n")
        pids = [p for p in pids if p and p != str(os.getpid())]
        if not pids:
            return None

        pid = int(pids[0])
        # Get process info from /proc
        stat = Path(f"/proc/{pid}/stat").read_text().split()
        start_ticks = int(stat[21])
        uptime_s = float(Path("/proc/uptime").read_text().split()[0])
        clk_tck = os.sysconf("SC_CLK_TCK")
        started_ago = uptime_s - (start_ticks / clk_tck)

        # Memory from /proc/pid/status
        status_lines = Path(f"/proc/{pid}/status").read_text()
        mem_kb = 0
        for line in status_lines.split("\n"):
            if line.startswith("VmRSS:"):
                mem_kb = int(line.split()[1])
                break

        return {
            "pid": pid,
            "uptime_seconds": round(started_ago, 0),
            "memory_mb": round(mem_kb / 1024, 1),
        }
    except Exception:
        return None


def _read_jsonl(path: Path) -> list[dict]:
    """Read all entries from a JSONL file."""
    if not path.exists():
        return []
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def _get_today_files() -> tuple[Path, Path]:
    """Get today's graduation and price tracking files."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return (
        DATA_DIR / f"graduations_{today}.jsonl",
        DATA_DIR / f"price_tracking_{today}.jsonl",
    )


def _file_stats(path: Path) -> dict:
    """Get file size and line count."""
    if not path.exists():
        return {"exists": False, "lines": 0, "size_bytes": 0}
    size = path.stat().st_size
    lines = sum(1 for _ in open(path))
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return {
        "exists": True,
        "lines": lines,
        "size_bytes": size,
        "last_modified": mtime.isoformat(),
    }


def _all_data_files() -> list[dict]:
    """List all data files with stats."""
    if not DATA_DIR.exists():
        return []
    files = []
    for p in sorted(DATA_DIR.glob("*.jsonl")):
        stats = _file_stats(p)
        stats["name"] = p.name
        files.append(stats)
    return files


@app.get("/health")
def health():
    return {"status": "ok", "service": "degen-observer-status-api"}


@app.get("/status")
def status():
    now = datetime.now(timezone.utc)
    grad_file, price_file = _get_today_files()

    # Process status
    observer = _find_process("observe_graduations.py")
    tracker = _find_process("track_prices.py")

    # Today's graduation data
    grads = _read_jsonl(grad_file)
    recent_grads = grads[-5:] if grads else []  # Last 5

    # Today's price tracking data
    price_entries = _read_jsonl(price_file)

    # Compute stats from all graduation files
    all_files = _all_data_files()
    total_grads = 0
    total_price_entries = 0
    for f in all_files:
        if f["name"].startswith("graduations_"):
            total_grads += f["lines"]
        elif f["name"].startswith("price_tracking_"):
            total_price_entries += f["lines"]

    # Latest graduation age
    latest_grad_age = None
    if grads:
        last_ts = grads[-1].get("ts", "")
        try:
            last_dt = datetime.fromisoformat(last_ts)
            latest_grad_age = round((now - last_dt).total_seconds(), 0)
        except (ValueError, TypeError):
            pass

    return {
        "processes": {
            "observer": {
                "status": "running" if observer else "stopped",
                **(observer or {}),
            },
            "tracker": {
                "status": "running" if tracker else "stopped",
                **(tracker or {}),
            },
        },
        "today": {
            "graduations": len(grads),
            "price_checkpoints": len(price_entries),
            "graduation_file": _file_stats(grad_file),
            "price_file": _file_stats(price_file),
            "latest_grad_age_seconds": latest_grad_age,
        },
        "totals": {
            "total_graduations": total_grads,
            "total_price_entries": total_price_entries,
            "data_files": len(all_files),
            "days_collected": len(
                [f for f in all_files if f["name"].startswith("graduations_")]
            ),
        },
        "recent_graduations": [
            {
                "ts": g.get("ts", ""),
                "symbol": g.get("symbol", "?"),
                "name": g.get("name", "?"),
                "mcap": g.get("mcap", 0),
                "dex_price": g.get("dex_price"),
                "has_twitter": g.get("has_twitter", False),
                "has_telegram": g.get("has_telegram", False),
                "has_website": g.get("has_website", False),
                "mint": g.get("mint", ""),
            }
            for g in recent_grads
        ],
        "files": all_files,
        "collected_at": now.isoformat(),
    }
