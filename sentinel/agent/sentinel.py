"""
Sentinel agent main loop.
Collects → Analyzes → Stores on 0G → Repeats every AGENT_INTERVAL_SEC.
"""
import json
import time
import signal
import sys
from datetime import datetime, timezone

from sentinel.agent.collector import collect
from sentinel.agent.analyzer  import analyze
from sentinel.storage.og_storage import store_report
from sentinel.config import AGENT_INTERVAL_SEC

_running = True


def _handle_signal(sig, frame):
    global _running
    print("\n[sentinel] Shutting down gracefully...")
    _running = False


def run_once() -> dict:
    """Execute one full collect → analyze → store cycle."""
    print(f"\n[sentinel] Cycle start — {datetime.now(timezone.utc).isoformat()}")

    print("[sentinel] Collecting market data...")
    snapshot = collect()

    print("[sentinel] Analyzing with AI...")
    analysis = analyze(snapshot)

    report = {
        "timestamp":  snapshot["timestamp"],
        "snapshot":   snapshot,
        "analysis":   analysis,
        "agent":      "0G Sentinel v1.0",
    }

    print("[sentinel] Storing report on 0G Storage...")
    metadata = store_report(report)

    print(f"[sentinel] Report stored — hash: {metadata['og_root_hash']}")
    if metadata.get("explorer_url"):
        print(f"[sentinel] Explorer: {metadata['explorer_url']}")

    return {"report": report, "metadata": metadata}


def run_loop():
    """Run the agent in a continuous loop."""
    signal.signal(signal.SIGINT,  _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    print("=" * 60)
    print("  0G SENTINEL — Autonomous Market Intelligence Agent")
    print(f"  Interval: {AGENT_INTERVAL_SEC}s | Network: 0G Galileo Testnet")
    print("=" * 60)

    while _running:
        try:
            result = run_once()
            print(f"[sentinel] Sleeping {AGENT_INTERVAL_SEC}s until next cycle...")
        except Exception as e:
            print(f"[sentinel] Cycle error: {e}")

        for _ in range(AGENT_INTERVAL_SEC):
            if not _running:
                break
            time.sleep(1)

    print("[sentinel] Agent stopped.")
