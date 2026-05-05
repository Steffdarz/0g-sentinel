"""Central configuration — reads from .env in project root."""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from workspace root
load_dotenv(Path(__file__).parent.parent / ".env")

# Wallet
WALLET_ADDRESS    = os.environ["WALLET_ADDRESS"]
WALLET_PRIVATE_KEY = os.environ["WALLET_PRIVATE_KEY"]

# 0G Galileo Testnet
OG_RPC_URL        = os.getenv("OG_RPC_URL", "https://evmrpc-testnet.0g.ai")
OG_CHAIN_ID       = int(os.getenv("OG_CHAIN_ID", "16602"))
OG_FLOW_CONTRACT  = os.getenv("OG_FLOW_CONTRACT", "0x22E03a6A89B950F1c82ec5e74F8eCa321a105296")
OG_INDEXER_URL    = os.getenv("OG_INDEXER_URL", "https://indexer-storage-testnet-turbo.0g.ai")

# 0G Compute (OpenAI-compatible)
OG_COMPUTE_URL    = os.getenv("OG_COMPUTE_URL", "https://api.0g.ai")
OG_COMPUTE_KEY    = os.getenv("OG_COMPUTE_KEY", "")   # Set after broker setup

# Agent settings
AGENT_INTERVAL_SEC = int(os.getenv("AGENT_INTERVAL_SEC", "300"))  # 5 min
REPORTS_DIR        = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
