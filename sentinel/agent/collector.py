"""
Data collector: fetches live market data from public APIs.
No API key required — uses CoinGecko public endpoints.
"""
import requests
from datetime import datetime, timezone


COINGECKO_BASE = "https://api.coingecko.com/api/v3"

TRACKED_COINS = [
    "bitcoin", "ethereum", "solana", "avalanche-2", "chainlink",
    "uniswap", "aave", "arbitrum", "optimism", "the-graph",
]

TRACKED_VS = "usd"


def fetch_prices() -> dict:
    """Fetch current prices and 24h stats for tracked coins."""
    ids = ",".join(TRACKED_COINS)
    url = (
        f"{COINGECKO_BASE}/simple/price"
        f"?ids={ids}"
        f"&vs_currencies={TRACKED_VS}"
        f"&include_24hr_change=true"
        f"&include_24hr_vol=true"
        f"&include_market_cap=true"
    )
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_defi_global() -> dict:
    """Fetch global DeFi stats (total TVL, volume, etc.)."""
    url = f"{COINGECKO_BASE}/global/decentralized_finance_defi"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json().get("data", {})


def fetch_trending() -> list:
    """Fetch trending coins on CoinGecko."""
    url = f"{COINGECKO_BASE}/search/trending"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    coins = resp.json().get("coins", [])
    return [c["item"]["name"] for c in coins[:7]]


def collect() -> dict:
    """Run all collectors and return a unified snapshot."""
    timestamp = datetime.now(timezone.utc).isoformat()
    prices    = fetch_prices()
    defi      = fetch_defi_global()
    trending  = fetch_trending()

    return {
        "timestamp": timestamp,
        "prices": prices,
        "defi_global": {
            "defi_market_cap":    defi.get("defi_market_cap"),
            "eth_market_cap":     defi.get("eth_market_cap"),
            "defi_to_eth_ratio":  defi.get("defi_to_eth_ratio"),
            "trading_volume_24h": defi.get("trading_volume_24h"),
            "defi_dominance":     defi.get("defi_dominance"),
            "top_coin_name":      defi.get("top_coin_name"),
        },
        "trending_coins": trending,
    }
