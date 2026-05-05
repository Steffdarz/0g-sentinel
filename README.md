# 0G Sentinel — Autonomous Market Intelligence Agent

> **0G APAC Hackathon 2026 — Track 3: Agentic Economy**

0G Sentinel is an autonomous AI agent that continuously collects live DeFi market data, generates structured intelligence reports, and stores each report immutably on the **0G decentralised storage network**. Every report is cryptographically anchored on-chain via a Merkle root, making market analysis auditable and tamper-evident by anyone with the root hash.

---

## Problem

DeFi market intelligence is ephemeral. Price feeds, TVL snapshots, and trend analyses are consumed and discarded — there is no persistent, verifiable record of what the market looked like at any given moment. This makes it impossible to:

- Audit the data a trading agent acted on
- Verify that a published analysis matches the raw data
- Build trust in AI-generated market insights

---

## Solution

0G Sentinel introduces **on-chain data provenance for AI agents**:

```
Live APIs  →  Sentinel Agent  →  Analysis  →  0G Storage  →  On-chain Merkle Root
```

Each cycle the agent:

1. **Collects** live market data (prices, DeFi TVL, trending coins) from CoinGecko
2. **Analyzes** the snapshot — producing a structured JSON report with DeFi health, top movers, and a key insight
3. **Uploads** the report to 0G decentralised storage via the `@0gfoundation/0g-ts-sdk`
4. **Records** the on-chain Merkle root hash and transaction hash for public verification

Anyone can verify a report by querying the 0G Storage indexer with the Merkle root hash.

---

## Architecture

```
sentinel/
├── agent/
│   ├── collector.py    # CoinGecko market data (no API key required)
│   ├── analyzer.py     # AI analysis — 0G Compute or local heuristic
│   └── sentinel.py     # Main agent loop (collect → analyze → store)
├── storage/
│   └── og_storage.py   # 0G Storage integration via Node.js subprocess
├── scripts/
│   ├── upload.mjs      # ESM script wrapping @0gfoundation/0g-ts-sdk
│   └── package.json
└── cli.py              # CLI: run, run-once, list, get, verify
```

**Key design decisions:**

| Component | Choice | Reason |
|---|---|---|
| Storage SDK | `@0gfoundation/0g-ts-sdk` v1.2.6 | Official ESM SDK, active maintenance |
| Node.js subprocess | `upload.mjs` | SDK is ESM-only; Python calls via subprocess |
| Analysis | Local heuristic + 0G Compute (optional) | Works without Compute key; upgradeable |
| Data source | CoinGecko public API | No rate-limit key required for demo |

---

## Live Demo

**On-chain report verified on 0G Galileo testnet:**

```
Root Hash : 0xc79eee3b52ef26e8a3573e4fb78e3699d7e300c82b4384c0091d7974535573ff
Tx Hash   : 0xcd02b6e4c9b2f1625766608ff6a6552ff1fe47f6ed1cab256386eed9a05cede0
Explorer  : https://storagescan-galileo.0g.ai/tx/0xcd02b6e4c9b2f1625766608ff6a6552ff1fe47f6ed1cab256386eed9a05cede0
```

**Sample report output (`sentinel.cli get <hash>`):**

```
============================================================
  Report: report_2026-05-05T06-13-31.json
  Time  : 2026-05-05T06:13:31 UTC
  Hash  : 0xc79eee3b52ef26...
  Chain : ON-CHAIN
  Link  : https://storagescan-galileo.0g.ai/tx/0xcd02b6e4...
────────────────────────────────────────────────────────────
  Summary    : Average 24h change: -0.28%. Trending: wojak, Pudgy Penguins, Toncoin.
  DeFi Health: neutral
  Risk Level : low
  Insight    : Top coin by DeFi dominance: Lido Staked Ether.

  Top Movers:
    ▼ uniswap         -2.73%  [hold]
    ▲ chainlink       +2.14%  [hold]
    ▼ arbitrum        -1.46%  [hold]
    ▼ aave            -1.44%  [hold]
    ▲ bitcoin         +1.18%  [hold]
============================================================
```

---

## Quickstart

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the 0G Storage SDK)
- An EVM wallet with testnet OG tokens ([faucet](https://hub.0g.ai/faucet))

### Install

```bash
# Python dependencies
pip install requests python-dotenv eth-account

# Node.js SDK (from sentinel/scripts/)
cd sentinel/scripts && npm install
```

### Configure `.env`

```env
WALLET_ADDRESS=0x...
WALLET_PRIVATE_KEY=0x...
OG_RPC_URL=https://evmrpc-testnet.0g.ai
OG_CHAIN_ID=16602
OG_FLOW_CONTRACT=0x22E03a6A89B950F1c82ec5e74F8eCa321a105296
OG_INDEXER_URL=https://indexer-storage-testnet-turbo.0g.ai

# Optional: 0G Compute key for AI-powered analysis
# OG_COMPUTE_KEY=app-sk-...
```

### Run

```bash
# Single cycle — collect, analyze, upload
python3 -m sentinel.cli run-once

# Continuous loop (default 5-minute interval)
python3 -m sentinel.cli run

# List all stored reports
python3 -m sentinel.cli list

# Retrieve a specific report by root hash
python3 -m sentinel.cli get <root_hash>

# Verify local file integrity against on-chain hash
python3 -m sentinel.cli verify <root_hash>
```

---

## 0G Storage Integration Details

The agent uploads each report as follows:

1. **Merkle tree** — `ZgFile.fromFilePath()` computes the Merkle tree over the file content
2. **On-chain submission** — `Indexer.upload()` submits the file to the 0G Galileo storage nodes, returning a transaction hash
3. **Verification** — The Merkle root hash is deterministic; anyone can re-derive it from the raw JSON and confirm it matches the on-chain record

The upload script (`upload.mjs`) isolates SDK-specific logic so the Python agent can stay clean and portable. SDK verbose logs are redirected to `stderr`; only the final JSON `{ rootHash, txHash }` is emitted to `stdout`.

---

## 0G Compute Integration (Stretch Goal)

When `OG_COMPUTE_KEY` is set, the analyzer calls the 0G Compute OpenAI-compatible endpoint using `meta-llama/Llama-3.3-70B-Instruct` for AI-generated market insights. Set up via [compute-marketplace.0g.ai](https://compute-marketplace.0g.ai).

Without a key the agent uses a local heuristic analyzer — the on-chain storage pipeline runs identically in both modes.

---

## Why 0G Storage?

| Property | Centralised Storage | 0G Storage |
|---|---|---|
| Tamper-evident | No | Yes — Merkle root on-chain |
| Permissionless read | No | Yes — root hash is enough |
| Verifiable provenance | No | Yes — tx on block explorer |
| Cost | SaaS subscription | Gas only |

0G Storage is purpose-built for high-throughput AI data. By anchoring every intelligence report on 0G, any downstream agent or user can trustlessly verify that the analysis they're acting on hasn't been altered.

---

## Roadmap

- [ ] Live 0G Compute inference integration
- [ ] Multi-source data feeds (DeFiLlama, Chainlink price feeds)
- [ ] On-chain alerting — post critical market events to an on-chain queue
- [ ] Agent-to-agent report sharing via root hash broadcast
- [ ] Web dashboard querying reports from 0G Storage in real-time

---

## Hackathon Submission

- **Event**: 0G APAC Hackathon 2026
- **Track**: Track 3 — Agentic Economy
- **Network**: 0G Galileo Testnet (Chain ID 16602)
- **Wallet**: `0x6164641bE1E09C67C9335BB38448A139e93B8722`
- **Live tx**: [0xcd02b6e4...](https://storagescan-galileo.0g.ai/tx/0xcd02b6e4c9b2f1625766608ff6a6552ff1fe47f6ed1cab256386eed9a05cede0)

---

## License

MIT
