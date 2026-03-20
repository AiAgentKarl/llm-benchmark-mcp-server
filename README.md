# LLM Benchmark MCP Server

MCP server that gives AI agents access to LLM benchmark data, pricing comparisons, and model recommendations.

## Features

- **compare_models** — Side-by-side benchmark comparison of LLMs (MMLU, HumanEval, MATH, GPQA, ARC, HellaSwag)
- **get_model_details** — Detailed info about a specific model including strengths/weaknesses
- **recommend_model** — Get the best model recommendation for your task and budget
- **list_top_models** — Top models ranked by category (coding, math, reasoning, chat)
- **get_pricing** — Pricing comparison via OpenRouter API

## Supported Models

GPT-4o, GPT-4o-mini, GPT-4 Turbo, o1, o3-mini, Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus, Gemini 2.0 Flash, Gemini 2.0 Pro, Gemini 1.5 Pro, Llama 3.1 (8B/70B/405B), Llama 3.3 70B, Mistral Large, Mistral Small, Mixtral 8x22B, DeepSeek V3, DeepSeek R1, Qwen 2.5 72B

## Installation

```bash
pip install llm-benchmark-mcp-server
```

## Usage with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "llm-benchmark": {
      "command": "benchmark-server"
    }
  }
}
```

Or via uvx (no install needed):

```json
{
  "mcpServers": {
    "llm-benchmark": {
      "command": "uvx",
      "args": ["llm-benchmark-mcp-server"]
    }
  }
}
```

## Example Queries

- "Compare GPT-4o vs Claude 3.5 Sonnet vs Gemini 2.0 Pro"
- "Which model is best for coding on a low budget?"
- "Show me the top 10 models for math"
- "What does GPT-4o cost compared to Claude?"
- "Give me details about DeepSeek R1"

## Data Sources

- **Benchmarks**: Hardcoded from official papers and public leaderboards (MMLU, HumanEval, MATH, GPQA, ARC-Challenge, HellaSwag)
- **Pricing**: Live data from [OpenRouter API](https://openrouter.ai/api/v1/models)
- **Arena Rankings**: [Chatbot Arena Leaderboard](https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard) (when available)

## License

MIT
