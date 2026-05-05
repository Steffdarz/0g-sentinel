"""
Analyzer: sends collected market data to 0G Compute (OpenAI-compatible)
for AI-generated insight. Falls back to local heuristic if no key set.
"""
import json
import requests
from sentinel.config import OG_COMPUTE_URL, OG_COMPUTE_KEY


SYSTEM_PROMPT = """You are a concise DeFi market analyst.
Given a raw market data snapshot, produce a structured JSON report with:
- summary: 2-3 sentence market overview
- top_movers: list of {coin, change_24h, signal} for biggest movers (max 5)
- defi_health: "bullish" | "neutral" | "bearish" with one-line reason
- risk_level: "low" | "medium" | "high"
- key_insight: one actionable observation for builders/investors
Respond ONLY with valid JSON, no markdown fences."""


def analyze_with_0g(snapshot: dict) -> dict:
    """Call 0G Compute inference (OpenAI-compatible API)."""
    headers = {
        "Authorization": f"Bearer {OG_COMPUTE_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": json.dumps(snapshot, indent=2)},
        ],
        "temperature": 0.3,
        "max_tokens": 512,
    }
    resp = requests.post(
        f"{OG_COMPUTE_URL}/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    return json.loads(content)


def analyze_local(snapshot: dict) -> dict:
    """Heuristic fallback when 0G Compute key is not configured."""
    prices = snapshot.get("prices", {})
    movers = []
    for coin, data in prices.items():
        change = data.get(f"{coin}_24h_change") or data.get("usd_24h_change", 0)
        movers.append({"coin": coin, "change_24h": round(change, 2),
                       "signal": "buy" if change > 3 else "sell" if change < -3 else "hold"})

    movers.sort(key=lambda x: abs(x["change_24h"]), reverse=True)
    avg_change = sum(m["change_24h"] for m in movers) / max(len(movers), 1)
    health = "bullish" if avg_change > 2 else "bearish" if avg_change < -2 else "neutral"

    return {
        "summary": (
            f"Market snapshot at {snapshot['timestamp']}. "
            f"Average 24h change across tracked assets: {avg_change:.2f}%. "
            f"Trending: {', '.join(snapshot.get('trending_coins', [])[:3])}."
        ),
        "top_movers": movers[:5],
        "defi_health": health,
        "risk_level": "high" if abs(avg_change) > 5 else "medium" if abs(avg_change) > 2 else "low",
        "key_insight": f"Top coin by DeFi dominance: {snapshot['defi_global'].get('top_coin_name', 'N/A')}.",
        "source": "local_heuristic",
    }


def analyze(snapshot: dict) -> dict:
    """Analyze snapshot — use 0G Compute if key is available, else fallback."""
    if OG_COMPUTE_KEY:
        try:
            result = analyze_with_0g(snapshot)
            result["source"] = "0g_compute"
            return result
        except Exception as e:
            print(f"[analyzer] 0G Compute error: {e} — using local fallback")
    return analyze_local(snapshot)
