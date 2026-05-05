"""
0G Storage integration.

Uploads reports as JSON files to 0G decentralized storage via the
TypeScript SDK CLI wrapper (since the Python SDK is not yet official).
Falls back to local-only storage during development.

Each upload returns a Merkle root hash that permanently identifies the
report on-chain — anyone can verify it via the 0G Storage Explorer.
"""
import json
import hashlib
import subprocess
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone

from sentinel.config import (
    OG_INDEXER_URL, OG_RPC_URL,
    OG_FLOW_CONTRACT, WALLET_PRIVATE_KEY, REPORTS_DIR
)


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def store_report(report: dict) -> dict:
    """
    Store a report on 0G Storage.
    Returns storage metadata including root hash and local path.
    """
    ts = report.get("timestamp", datetime.now(timezone.utc).isoformat())
    safe_ts = ts.replace(":", "-").replace("+", "").replace(".", "-")
    filename = f"report_{safe_ts}.json"
    local_path = REPORTS_DIR / filename

    # Always write locally first
    with open(local_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    local_hash = _sha256_file(str(local_path))

    # Attempt 0G on-chain upload via Node.js SDK wrapper
    root_hash = None
    tx_hash = None
    on_chain = False

    try:
        root_hash, tx_hash = _upload_to_0g(str(local_path))
        on_chain = True
        print(f"[storage] Uploaded to 0G — root: {root_hash[:16]}...")
    except Exception as e:
        print(f"[storage] On-chain upload skipped ({e}) — local only")
        root_hash = f"local:{local_hash}"

    metadata = {
        "filename": filename,
        "local_path": str(local_path),
        "local_sha256": local_hash,
        "og_root_hash": root_hash,
        "og_tx_hash": tx_hash,
        "on_chain": on_chain,
        "timestamp": ts,
        "explorer_url": (
            f"https://storagescan-galileo.0g.ai/tx/{tx_hash}"
            if tx_hash else None
        ),
    }

    # Save metadata alongside report
    meta_path = local_path.with_suffix(".meta.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata


def _upload_to_0g(filepath: str):
    """
    Call the Node.js 0G Storage upload script.
    Returns (root_hash, tx_hash).
    """
    script_dir = Path(__file__).parent.parent / "scripts"
    upload_script = script_dir / "upload.mjs"

    result = subprocess.run(
        ["node", str(upload_script), filepath],
        capture_output=True, text=True, timeout=120,
        env={
            **os.environ,
            "OG_RPC_URL": OG_RPC_URL,
            "OG_FLOW_CONTRACT": OG_FLOW_CONTRACT,
            "OG_INDEXER_URL": OG_INDEXER_URL,
            "WALLET_PRIVATE_KEY": WALLET_PRIVATE_KEY,
        }
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "upload failed")

    # Script prints JSON: {"rootHash": "...", "txHash": "..."}
    out = json.loads(result.stdout.strip())
    return out["rootHash"], out["txHash"]


def list_reports() -> list:
    """Return all stored report metadata sorted newest-first."""
    metas = []
    for meta_file in sorted(REPORTS_DIR.glob("*.meta.json"), reverse=True):
        with open(meta_file) as f:
            metas.append(json.load(f))
    return metas


def get_report(root_hash: str) -> dict | None:
    """Retrieve a report by its 0G root hash or local SHA256."""
    for meta in list_reports():
        if (meta.get("og_root_hash") == root_hash or
                meta.get("local_sha256") == root_hash or
                root_hash in str(meta.get("og_root_hash", ""))):
            report_path = Path(meta["local_path"])
            if report_path.exists():
                with open(report_path) as f:
                    report = json.load(f)
                return {"metadata": meta, "report": report}
    return None
