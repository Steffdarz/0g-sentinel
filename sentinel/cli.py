"""
0G Sentinel CLI — query and verify stored reports.

Usage:
    python -m sentinel.cli run          # start the agent loop
    python -m sentinel.cli run-once     # single cycle
    python -m sentinel.cli list         # list all stored reports
    python -m sentinel.cli get <hash>   # retrieve report by root hash
    python -m sentinel.cli verify <hash> # verify report integrity
"""
import sys
import json
from sentinel.storage.og_storage import list_reports, get_report
from sentinel.agent.sentinel import run_loop, run_once


def cmd_list():
    reports = list_reports()
    if not reports:
        print("No reports stored yet. Run `python -m sentinel.cli run-once` first.")
        return
    print(f"\n{'─'*70}")
    print(f"  {'#':<4} {'Timestamp':<32} {'On-chain':<10} {'Root Hash'}")
    print(f"{'─'*70}")
    for i, m in enumerate(reports, 1):
        on_chain = "YES" if m.get("on_chain") else "local"
        root = m.get("og_root_hash", "")[:24] + "..."
        print(f"  {i:<4} {m['timestamp']:<32} {on_chain:<10} {root}")
    print(f"{'─'*70}")
    print(f"  Total: {len(reports)} reports\n")


def cmd_get(root_hash: str):
    result = get_report(root_hash)
    if not result:
        print(f"Report not found: {root_hash}")
        sys.exit(1)
    meta   = result["metadata"]
    report = result["report"]
    analysis = report.get("analysis", {})

    print(f"\n{'='*60}")
    print(f"  Report: {meta['filename']}")
    print(f"  Time  : {meta['timestamp']}")
    print(f"  Hash  : {meta['og_root_hash']}")
    print(f"  Chain : {'ON-CHAIN' if meta['on_chain'] else 'LOCAL ONLY'}")
    if meta.get("explorer_url"):
        print(f"  Link  : {meta['explorer_url']}")
    print(f"{'─'*60}")
    print(f"  Summary    : {analysis.get('summary', 'N/A')}")
    print(f"  DeFi Health: {analysis.get('defi_health', 'N/A')}")
    print(f"  Risk Level : {analysis.get('risk_level', 'N/A')}")
    print(f"  Insight    : {analysis.get('key_insight', 'N/A')}")
    print(f"\n  Top Movers:")
    for m in analysis.get("top_movers", []):
        arrow = "▲" if m["change_24h"] > 0 else "▼"
        print(f"    {arrow} {m['coin']:<15} {m['change_24h']:>+.2f}%  [{m['signal']}]")
    print(f"{'='*60}\n")


def cmd_verify(root_hash: str):
    import hashlib
    result = get_report(root_hash)
    if not result:
        print(f"Report not found: {root_hash}")
        sys.exit(1)
    meta = result["metadata"]
    local_path = meta["local_path"]

    h = hashlib.sha256()
    with open(local_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    actual_hash = h.hexdigest()
    stored_hash = meta["local_sha256"]

    if actual_hash == stored_hash:
        print(f"[✓] Integrity verified — SHA256 matches: {actual_hash[:24]}...")
        if meta.get("on_chain"):
            print(f"[✓] On-chain Merkle root: {meta['og_root_hash']}")
            print(f"    Verify at: {meta.get('explorer_url', 'N/A')}")
    else:
        print(f"[✗] Integrity FAILED — file may have been tampered with")
        print(f"    Expected : {stored_hash}")
        print(f"    Actual   : {actual_hash}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "run":
        run_loop()
    elif cmd == "run-once":
        result = run_once()
        print(json.dumps(result["metadata"], indent=2))
    elif cmd == "list":
        cmd_list()
    elif cmd == "get" and len(sys.argv) > 2:
        cmd_get(sys.argv[2])
    elif cmd == "verify" and len(sys.argv) > 2:
        cmd_verify(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
