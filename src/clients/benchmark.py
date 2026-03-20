"""
Benchmark-Client — Holt LLM-Daten von OpenRouter, Chatbot Arena und lokalen Benchmarks.
"""

import httpx
from typing import Optional


# Timeout für API-Anfragen
TIMEOUT = 30.0

# ============================================================
# Hardcodierte Benchmark-Daten für populäre Modelle
# Quellen: Offizielle Papers und öffentliche Leaderboards
# Stand: März 2025
# ============================================================
BENCHMARK_DATA: dict[str, dict] = {
    # --- OpenAI ---
    "gpt-4o": {
        "provider": "OpenAI",
        "release_date": "2024-05",
        "parameters": "~200B (geschätzt, MoE)",
        "context_window": 128000,
        "mmlu": 88.7,
        "humaneval": 90.2,
        "math": 76.6,
        "gpqa": 53.6,
        "arc_challenge": 96.7,
        "hellaswag": 95.3,
        "categories": ["reasoning", "coding", "chat", "math"],
    },
    "gpt-4o-mini": {
        "provider": "OpenAI",
        "release_date": "2024-07",
        "parameters": "~8B (geschätzt)",
        "context_window": 128000,
        "mmlu": 82.0,
        "humaneval": 87.0,
        "math": 70.2,
        "gpqa": 40.2,
        "arc_challenge": 93.1,
        "hellaswag": 92.5,
        "categories": ["chat", "coding"],
    },
    "gpt-4-turbo": {
        "provider": "OpenAI",
        "release_date": "2024-04",
        "parameters": "~1.8T (geschätzt, MoE)",
        "context_window": 128000,
        "mmlu": 86.4,
        "humaneval": 87.1,
        "math": 72.6,
        "gpqa": 49.3,
        "arc_challenge": 96.3,
        "hellaswag": 95.3,
        "categories": ["reasoning", "coding", "chat", "math"],
    },
    "o1": {
        "provider": "OpenAI",
        "release_date": "2024-12",
        "parameters": "unbekannt",
        "context_window": 200000,
        "mmlu": 91.8,
        "humaneval": 92.4,
        "math": 96.4,
        "gpqa": 78.0,
        "arc_challenge": 97.2,
        "hellaswag": 95.8,
        "categories": ["reasoning", "math", "coding"],
    },
    "o3-mini": {
        "provider": "OpenAI",
        "release_date": "2025-01",
        "parameters": "unbekannt",
        "context_window": 200000,
        "mmlu": 86.9,
        "humaneval": 92.9,
        "math": 97.9,
        "gpqa": 79.7,
        "arc_challenge": 96.1,
        "hellaswag": 94.2,
        "categories": ["reasoning", "math", "coding"],
    },
    # --- Anthropic ---
    "claude-3.5-sonnet": {
        "provider": "Anthropic",
        "release_date": "2024-10",
        "parameters": "unbekannt",
        "context_window": 200000,
        "mmlu": 88.7,
        "humaneval": 93.7,
        "math": 78.3,
        "gpqa": 65.0,
        "arc_challenge": 96.7,
        "hellaswag": 89.0,
        "categories": ["coding", "reasoning", "chat"],
    },
    "claude-3.5-haiku": {
        "provider": "Anthropic",
        "release_date": "2024-10",
        "parameters": "unbekannt",
        "context_window": 200000,
        "mmlu": 77.6,
        "humaneval": 88.1,
        "math": 69.2,
        "gpqa": 41.6,
        "arc_challenge": 92.8,
        "hellaswag": 85.3,
        "categories": ["chat", "coding"],
    },
    "claude-3-opus": {
        "provider": "Anthropic",
        "release_date": "2024-03",
        "parameters": "unbekannt",
        "context_window": 200000,
        "mmlu": 86.8,
        "humaneval": 84.9,
        "math": 60.1,
        "gpqa": 50.4,
        "arc_challenge": 96.4,
        "hellaswag": 95.4,
        "categories": ["reasoning", "chat", "coding"],
    },
    # --- Google ---
    "gemini-2.0-flash": {
        "provider": "Google",
        "release_date": "2025-02",
        "parameters": "unbekannt",
        "context_window": 1000000,
        "mmlu": 85.2,
        "humaneval": 89.0,
        "math": 73.1,
        "gpqa": 52.8,
        "arc_challenge": 94.5,
        "hellaswag": 93.1,
        "categories": ["chat", "coding", "reasoning"],
    },
    "gemini-1.5-pro": {
        "provider": "Google",
        "release_date": "2024-05",
        "parameters": "unbekannt (MoE)",
        "context_window": 2000000,
        "mmlu": 85.9,
        "humaneval": 84.1,
        "math": 67.7,
        "gpqa": 46.2,
        "arc_challenge": 94.4,
        "hellaswag": 92.5,
        "categories": ["reasoning", "chat", "math"],
    },
    "gemini-2.0-pro": {
        "provider": "Google",
        "release_date": "2025-02",
        "parameters": "unbekannt",
        "context_window": 1000000,
        "mmlu": 87.8,
        "humaneval": 90.5,
        "math": 78.9,
        "gpqa": 58.1,
        "arc_challenge": 96.0,
        "hellaswag": 94.2,
        "categories": ["reasoning", "coding", "math", "chat"],
    },
    # --- Meta ---
    "llama-3.1-405b": {
        "provider": "Meta",
        "release_date": "2024-07",
        "parameters": "405B",
        "context_window": 128000,
        "mmlu": 88.6,
        "humaneval": 89.0,
        "math": 73.8,
        "gpqa": 51.1,
        "arc_challenge": 96.9,
        "hellaswag": 96.3,
        "categories": ["reasoning", "coding", "math", "chat"],
    },
    "llama-3.1-70b": {
        "provider": "Meta",
        "release_date": "2024-07",
        "parameters": "70B",
        "context_window": 128000,
        "mmlu": 83.6,
        "humaneval": 80.5,
        "math": 68.0,
        "gpqa": 46.7,
        "arc_challenge": 94.8,
        "hellaswag": 94.6,
        "categories": ["reasoning", "chat", "coding"],
    },
    "llama-3.1-8b": {
        "provider": "Meta",
        "release_date": "2024-07",
        "parameters": "8B",
        "context_window": 128000,
        "mmlu": 69.4,
        "humaneval": 72.6,
        "math": 51.9,
        "gpqa": 32.8,
        "arc_challenge": 83.4,
        "hellaswag": 82.0,
        "categories": ["chat"],
    },
    "llama-3.3-70b": {
        "provider": "Meta",
        "release_date": "2024-12",
        "parameters": "70B",
        "context_window": 128000,
        "mmlu": 86.0,
        "humaneval": 88.4,
        "math": 77.0,
        "gpqa": 50.5,
        "arc_challenge": 95.1,
        "hellaswag": 94.8,
        "categories": ["reasoning", "coding", "math", "chat"],
    },
    # --- Mistral ---
    "mistral-large": {
        "provider": "Mistral",
        "release_date": "2024-11",
        "parameters": "123B",
        "context_window": 128000,
        "mmlu": 84.0,
        "humaneval": 92.0,
        "math": 71.2,
        "gpqa": 52.3,
        "arc_challenge": 94.2,
        "hellaswag": 93.4,
        "categories": ["coding", "reasoning", "chat"],
    },
    "mistral-small": {
        "provider": "Mistral",
        "release_date": "2025-01",
        "parameters": "24B",
        "context_window": 32000,
        "mmlu": 81.0,
        "humaneval": 85.5,
        "math": 65.8,
        "gpqa": 40.1,
        "arc_challenge": 91.3,
        "hellaswag": 90.6,
        "categories": ["chat", "coding"],
    },
    "mixtral-8x22b": {
        "provider": "Mistral",
        "release_date": "2024-04",
        "parameters": "176B (MoE, 39B aktiv)",
        "context_window": 65536,
        "mmlu": 77.8,
        "humaneval": 75.0,
        "math": 49.8,
        "gpqa": 36.1,
        "arc_challenge": 91.3,
        "hellaswag": 88.7,
        "categories": ["chat", "reasoning"],
    },
    # --- DeepSeek ---
    "deepseek-v3": {
        "provider": "DeepSeek",
        "release_date": "2024-12",
        "parameters": "671B (MoE, 37B aktiv)",
        "context_window": 128000,
        "mmlu": 88.5,
        "humaneval": 82.6,
        "math": 90.2,
        "gpqa": 59.1,
        "arc_challenge": 95.8,
        "hellaswag": 95.0,
        "categories": ["reasoning", "math", "coding", "chat"],
    },
    "deepseek-r1": {
        "provider": "DeepSeek",
        "release_date": "2025-01",
        "parameters": "671B (MoE)",
        "context_window": 128000,
        "mmlu": 90.8,
        "humaneval": 85.3,
        "math": 97.3,
        "gpqa": 71.5,
        "arc_challenge": 96.3,
        "hellaswag": 95.5,
        "categories": ["reasoning", "math", "coding"],
    },
    # --- Qwen ---
    "qwen-2.5-72b": {
        "provider": "Alibaba",
        "release_date": "2024-09",
        "parameters": "72B",
        "context_window": 128000,
        "mmlu": 86.1,
        "humaneval": 86.4,
        "math": 83.1,
        "gpqa": 49.0,
        "arc_challenge": 95.7,
        "hellaswag": 94.1,
        "categories": ["math", "coding", "reasoning", "chat"],
    },
}

# Kategorie -> Benchmark-Mapping für Rankings
CATEGORY_BENCHMARKS = {
    "coding": "humaneval",
    "math": "math",
    "reasoning": "gpqa",
    "chat": "mmlu",
    "general": "mmlu",
}

# Task -> Kategorie-Mapping für Empfehlungen
TASK_CATEGORIES = {
    "code": "coding",
    "coding": "coding",
    "programming": "coding",
    "development": "coding",
    "math": "math",
    "mathematics": "math",
    "calculation": "math",
    "reasoning": "reasoning",
    "analysis": "reasoning",
    "research": "reasoning",
    "logic": "reasoning",
    "science": "reasoning",
    "chat": "chat",
    "conversation": "chat",
    "writing": "chat",
    "creative": "chat",
    "summarization": "chat",
    "translation": "chat",
    "general": "general",
}


async def fetch_openrouter_models() -> list[dict]:
    """Holt die Modellliste von OpenRouter inkl. Pricing."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get("https://openrouter.ai/api/v1/models")
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])


async def fetch_arena_leaderboard() -> Optional[dict]:
    """
    Versucht Chatbot Arena Leaderboard-Daten von Hugging Face zu holen.
    Gibt None zurück wenn nicht verfügbar.
    """
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Versuche die Space-API
            resp = await client.get(
                "https://huggingface.co/api/spaces/lmsys/chatbot-arena-leaderboard"
            )
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return None


def get_benchmark_data(model_name: str) -> Optional[dict]:
    """Gibt Benchmark-Daten für ein Modell zurück (case-insensitive Suche)."""
    name_lower = model_name.lower().strip()

    # Exakter Match
    if name_lower in BENCHMARK_DATA:
        return BENCHMARK_DATA[name_lower]

    # Teilstring-Match
    for key, data in BENCHMARK_DATA.items():
        if name_lower in key or key in name_lower:
            return data

    return None


def get_model_key(model_name: str) -> Optional[str]:
    """Findet den exakten Key für ein Modell (case-insensitive)."""
    name_lower = model_name.lower().strip()

    if name_lower in BENCHMARK_DATA:
        return name_lower

    for key in BENCHMARK_DATA:
        if name_lower in key or key in name_lower:
            return key

    return None


def get_all_models() -> dict[str, dict]:
    """Gibt alle hardcodierten Benchmark-Daten zurück."""
    return BENCHMARK_DATA.copy()


def get_top_models_by_category(category: str, limit: int = 10) -> list[tuple[str, dict, float]]:
    """
    Gibt die Top-Modelle für eine Kategorie zurück.
    Returns: Liste von (model_name, data, score) Tupeln.
    """
    cat = category.lower().strip()
    benchmark_key = CATEGORY_BENCHMARKS.get(cat, "mmlu")

    scored = []
    for name, data in BENCHMARK_DATA.items():
        score = data.get(benchmark_key, 0)
        if score > 0:
            scored.append((name, data, score))

    scored.sort(key=lambda x: x[2], reverse=True)
    return scored[:limit]


def resolve_task_category(task: str) -> str:
    """Löst einen Task-String in eine Kategorie auf."""
    task_lower = task.lower().strip()
    for keyword, cat in TASK_CATEGORIES.items():
        if keyword in task_lower:
            return cat
    return "general"


async def get_openrouter_pricing(model_ids: list[str]) -> dict[str, dict]:
    """
    Holt Pricing-Daten von OpenRouter für bestimmte Modelle.
    Returns: Dict mit model_id -> pricing info.
    """
    try:
        models = await fetch_openrouter_models()
    except Exception:
        return {}

    pricing = {}
    for model in models:
        model_id = model.get("id", "")
        model_name = model.get("name", "")

        for search_id in model_ids:
            search_lower = search_id.lower()
            if search_lower in model_id.lower() or search_lower in model_name.lower():
                p = model.get("pricing", {})
                pricing[model_id] = {
                    "name": model_name,
                    "prompt_cost": p.get("prompt", "N/A"),
                    "completion_cost": p.get("completion", "N/A"),
                    "context_length": model.get("context_length", "N/A"),
                    "top_provider": model.get("top_provider", {}),
                }

    return pricing
