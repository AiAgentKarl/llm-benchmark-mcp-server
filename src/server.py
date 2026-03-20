"""
LLM Benchmark MCP Server — Vergleicht LLMs anhand von Benchmarks, Preisen und Kategorien.

Gibt AI-Agents Zugriff auf:
- Benchmark-Daten (MMLU, HumanEval, MATH, GPQA)
- Modellvergleiche (Side-by-Side)
- Preisvergleiche (via OpenRouter)
- Modellempfehlungen nach Aufgabe und Budget
"""

from mcp.server.fastmcp import FastMCP
from src.tools.benchmark import register_tools

mcp = FastMCP(
    "llm-benchmark",
    instructions=(
        "LLM Benchmark Server — Vergleicht Language Models anhand von "
        "Benchmarks, Preisen und Kategorien. Enthält Daten zu GPT-4, Claude, "
        "Gemini, Llama, Mistral, DeepSeek und mehr. Kann Modelle empfehlen, "
        "Preise vergleichen und Rankings nach Kategorie (Coding, Math, "
        "Reasoning, Chat) erstellen."
    ),
)

# Tools registrieren
register_tools(mcp)


def main():
    """Startet den MCP-Server über stdio-Transport."""
    mcp.run()


if __name__ == "__main__":
    main()
