"""
Konfiguration — Einstellungen für den Benchmark MCP Server.
"""

# Keine API-Keys nötig — OpenRouter und HuggingFace sind öffentlich.
# Falls in Zukunft Keys gebraucht werden, hier über .env laden.

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
HUGGINGFACE_API_URL = "https://huggingface.co/api"

# Timeouts
REQUEST_TIMEOUT = 30.0
