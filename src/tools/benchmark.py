"""
Benchmark-Tools — MCP-Tools für LLM-Vergleich, Benchmarks und Preise.
"""

from src.clients.benchmark import (
    get_benchmark_data,
    get_model_key,
    get_all_models,
    get_top_models_by_category,
    resolve_task_category,
    get_openrouter_pricing,
    CATEGORY_BENCHMARKS,
)


def register_tools(mcp):
    """Registriert alle Benchmark-Tools beim MCP-Server."""

    @mcp.tool()
    async def compare_models(model_names: list[str]) -> str:
        """
        Vergleicht LLMs nebeneinander mit Benchmarks, Kontext und Kategorien.

        Args:
            model_names: Liste von Modellnamen zum Vergleichen (z.B. ["gpt-4o", "claude-3.5-sonnet", "gemini-2.0-pro"])
        """
        if not model_names:
            return "Fehler: Mindestens ein Modellname erforderlich."

        if len(model_names) > 10:
            return "Fehler: Maximal 10 Modelle gleichzeitig vergleichbar."

        results = []
        found_models = []

        for name in model_names:
            key = get_model_key(name)
            data = get_benchmark_data(name)
            if data and key:
                found_models.append((key, data))
            else:
                results.append(f"'{name}' — Nicht in der Datenbank gefunden.")

        if not found_models:
            all_models = get_all_models()
            available = ", ".join(sorted(all_models.keys()))
            return f"Keine der angegebenen Modelle gefunden.\n\nVerfügbare Modelle:\n{available}"

        # Header
        results.append("=" * 70)
        results.append("LLM BENCHMARK-VERGLEICH")
        results.append("=" * 70)

        # Vergleichstabelle
        benchmarks = ["mmlu", "humaneval", "math", "gpqa", "arc_challenge", "hellaswag"]
        bench_labels = {
            "mmlu": "MMLU",
            "humaneval": "HumanEval",
            "math": "MATH",
            "gpqa": "GPQA",
            "arc_challenge": "ARC-C",
            "hellaswag": "HellaSwag",
        }

        for model_name, data in found_models:
            results.append(f"\n--- {model_name} ---")
            results.append(f"  Provider:    {data.get('provider', 'N/A')}")
            results.append(f"  Release:     {data.get('release_date', 'N/A')}")
            results.append(f"  Parameter:   {data.get('parameters', 'N/A')}")
            results.append(f"  Kontext:     {data.get('context_window', 'N/A'):,} Tokens")
            results.append(f"  Kategorien:  {', '.join(data.get('categories', []))}")
            results.append("  Benchmarks:")
            for bench in benchmarks:
                score = data.get(bench, None)
                label = bench_labels.get(bench, bench)
                if score is not None:
                    results.append(f"    {label:12s}: {score:.1f}%")

        # Direktvergleich wenn mehrere Modelle
        if len(found_models) > 1:
            results.append("\n" + "=" * 70)
            results.append("DIREKTVERGLEICH")
            results.append("=" * 70)

            for bench in benchmarks:
                label = bench_labels.get(bench, bench)
                scores = []
                for model_name, data in found_models:
                    score = data.get(bench, 0)
                    scores.append((model_name, score))
                scores.sort(key=lambda x: x[1], reverse=True)
                winner = scores[0]
                results.append(f"\n  {label}: Bestes Modell = {winner[0]} ({winner[1]:.1f}%)")
                for model_name, score in scores:
                    bar = "#" * int(score / 2)
                    results.append(f"    {model_name:25s} {score:6.1f}% |{bar}")

        return "\n".join(results)

    @mcp.tool()
    async def get_model_details(model_name: str) -> str:
        """
        Gibt detaillierte Infos zu einem bestimmten LLM zurück.

        Args:
            model_name: Name des Modells (z.B. "gpt-4o", "claude-3.5-sonnet", "deepseek-r1")
        """
        key = get_model_key(model_name)
        data = get_benchmark_data(model_name)

        if not data or not key:
            all_models = get_all_models()
            available = ", ".join(sorted(all_models.keys()))
            return f"Modell '{model_name}' nicht gefunden.\n\nVerfügbare Modelle:\n{available}"

        # OpenRouter-Pricing holen
        pricing = await get_openrouter_pricing([key])

        lines = []
        lines.append("=" * 60)
        lines.append(f"MODELLDETAILS: {key}")
        lines.append("=" * 60)
        lines.append(f"Provider:       {data.get('provider', 'N/A')}")
        lines.append(f"Release:        {data.get('release_date', 'N/A')}")
        lines.append(f"Parameter:      {data.get('parameters', 'N/A')}")
        lines.append(f"Kontextfenster: {data.get('context_window', 'N/A'):,} Tokens")
        lines.append(f"Kategorien:     {', '.join(data.get('categories', []))}")

        lines.append("\nBenchmark-Ergebnisse:")
        benchmarks = {
            "mmlu": ("MMLU (Wissen)", "Allgemeinwissen über 57 Fachgebiete"),
            "humaneval": ("HumanEval (Code)", "Python-Programmieraufgaben"),
            "math": ("MATH", "Mathematische Problemlösung"),
            "gpqa": ("GPQA (Experten)", "Fragen auf PhD-Niveau"),
            "arc_challenge": ("ARC-Challenge", "Naturwissenschaftliches Reasoning"),
            "hellaswag": ("HellaSwag", "Satzergänzung und Common Sense"),
        }

        for bench_key, (label, desc) in benchmarks.items():
            score = data.get(bench_key, None)
            if score is not None:
                bar = "#" * int(score / 2.5)
                lines.append(f"  {label:25s}: {score:6.1f}% |{bar}")
                lines.append(f"  {'':25s}  ({desc})")

        # Stärken/Schwächen
        bench_scores = {k: data.get(k, 0) for k in ["mmlu", "humaneval", "math", "gpqa"]}
        best_bench = max(bench_scores, key=bench_scores.get)
        worst_bench = min(bench_scores, key=bench_scores.get)

        bench_names = {"mmlu": "Allgemeinwissen", "humaneval": "Coding", "math": "Mathematik", "gpqa": "Experten-Reasoning"}
        lines.append(f"\nStärke:   {bench_names.get(best_bench, best_bench)} ({bench_scores[best_bench]:.1f}%)")
        lines.append(f"Schwäche: {bench_names.get(worst_bench, worst_bench)} ({bench_scores[worst_bench]:.1f}%)")

        # Pricing von OpenRouter
        if pricing:
            lines.append("\nPreise (via OpenRouter):")
            for pid, pdata in pricing.items():
                prompt_cost = pdata.get("prompt_cost", "N/A")
                completion_cost = pdata.get("completion_cost", "N/A")
                lines.append(f"  {pdata.get('name', pid)}:")
                lines.append(f"    Input:  ${prompt_cost}/Token")
                lines.append(f"    Output: ${completion_cost}/Token")
        else:
            lines.append("\nPreise: Über OpenRouter nicht verfügbar. Nutze get_pricing() für Preisvergleich.")

        return "\n".join(lines)

    @mcp.tool()
    async def recommend_model(task: str, budget: str = "medium") -> str:
        """
        Empfiehlt das beste LLM für eine Aufgabe und ein Budget.

        Args:
            task: Art der Aufgabe (z.B. "coding", "math", "reasoning", "chat", "creative writing")
            budget: Budget-Level — "low" (günstigste), "medium" (bestes Preis-Leistung), "high" (beste Qualität)
        """
        category = resolve_task_category(task)
        benchmark_key = CATEGORY_BENCHMARKS.get(category, "mmlu")
        top_models = get_top_models_by_category(category, limit=20)

        if not top_models:
            return f"Keine Modelle für Kategorie '{category}' gefunden."

        # Budget-basierte Filterung
        # Low = kleine/günstige Modelle, Medium = mittlere, High = beste
        budget_lower = budget.lower().strip()

        budget_models = {
            "low": [
                "gpt-4o-mini", "claude-3.5-haiku", "mistral-small",
                "llama-3.1-8b", "gemini-2.0-flash",
            ],
            "medium": [
                "gpt-4o", "claude-3.5-sonnet", "gemini-2.0-pro",
                "llama-3.3-70b", "deepseek-v3", "mistral-large",
                "qwen-2.5-72b", "llama-3.1-70b",
            ],
            "high": [
                "o1", "o3-mini", "claude-3-opus", "gpt-4-turbo",
                "llama-3.1-405b", "deepseek-r1", "gemini-2.0-pro",
            ],
        }

        allowed = budget_models.get(budget_lower, budget_models["medium"])

        # Filtere Top-Modelle nach Budget
        filtered = [(name, data, score) for name, data, score in top_models if name in allowed]

        if not filtered:
            # Fallback: alle Modelle
            filtered = top_models[:5]

        lines = []
        lines.append("=" * 60)
        lines.append(f"MODELLEMPFEHLUNG")
        lines.append(f"Aufgabe:  {task} (Kategorie: {category})")
        lines.append(f"Budget:   {budget}")
        lines.append(f"Benchmark: {benchmark_key.upper()}")
        lines.append("=" * 60)

        # Top-Empfehlung
        best = filtered[0]
        lines.append(f"\n>>> EMPFEHLUNG: {best[0]} <<<")
        lines.append(f"    Score: {best[2]:.1f}% ({benchmark_key.upper()})")
        lines.append(f"    Provider: {best[1].get('provider', 'N/A')}")
        lines.append(f"    Kontext: {best[1].get('context_window', 'N/A'):,} Tokens")

        # Alternativen
        if len(filtered) > 1:
            lines.append("\nAlternativen:")
            for name, data, score in filtered[1:5]:
                lines.append(f"  {name:25s} — {score:.1f}% ({data.get('provider', 'N/A')})")

        # Budget-Tipps
        lines.append("\nBudget-Tipps:")
        if budget_lower == "low":
            lines.append("  - GPT-4o-mini und Gemini Flash bieten starke Leistung zu niedrigen Kosten")
            lines.append("  - Open-Source-Modelle (Llama, Mistral) sind kostenlos selbst hostbar")
        elif budget_lower == "medium":
            lines.append("  - DeepSeek V3 bietet Premium-Leistung zu günstigen Preisen")
            lines.append("  - Claude 3.5 Sonnet hat das beste Preis-Leistungs-Verhältnis bei Coding")
        else:
            lines.append("  - Reasoning-Modelle (o1, DeepSeek R1) sind bei komplexen Aufgaben überlegen")
            lines.append("  - Für Multi-Step-Reasoning lohnt sich das Premium-Budget")

        return "\n".join(lines)

    @mcp.tool()
    async def list_top_models(category: str = "general", limit: int = 10) -> str:
        """
        Listet die Top-LLMs nach Kategorie sortiert auf.

        Args:
            category: Kategorie — "coding", "math", "reasoning", "chat", "general"
            limit: Anzahl der Modelle (Standard: 10, Maximum: 20)
        """
        limit = min(max(1, limit), 20)
        top = get_top_models_by_category(category, limit)

        if not top:
            available_cats = ", ".join(CATEGORY_BENCHMARKS.keys())
            return f"Kategorie '{category}' nicht gefunden.\n\nVerfügbare Kategorien: {available_cats}"

        benchmark_key = CATEGORY_BENCHMARKS.get(category.lower(), "mmlu")

        lines = []
        lines.append("=" * 65)
        lines.append(f"TOP {limit} LLMs — Kategorie: {category.upper()}")
        lines.append(f"Sortiert nach: {benchmark_key.upper()}")
        lines.append("=" * 65)

        for rank, (name, data, score) in enumerate(top, 1):
            provider = data.get("provider", "N/A")
            params = data.get("parameters", "N/A")
            ctx = data.get("context_window", 0)
            bar = "#" * int(score / 2.5)
            lines.append(f"\n  #{rank:2d}  {name}")
            lines.append(f"       Provider: {provider} | Parameter: {params} | Kontext: {ctx:,}")
            lines.append(f"       {benchmark_key.upper()}: {score:.1f}% |{bar}")

        # Legende
        lines.append("\n" + "-" * 65)
        lines.append("Benchmark-Erklärungen:")
        bench_desc = {
            "mmlu": "MMLU — Allgemeinwissen über 57 Fachgebiete",
            "humaneval": "HumanEval — Python-Code-Generierung",
            "math": "MATH — Mathematische Problemlösung (Highschool bis Wettbewerb)",
            "gpqa": "GPQA — Expertenfragen auf PhD-Niveau",
        }
        desc = bench_desc.get(benchmark_key, benchmark_key)
        lines.append(f"  {desc}")

        return "\n".join(lines)

    @mcp.tool()
    async def get_pricing(model_names: list[str]) -> str:
        """
        Vergleicht die Preise von LLMs über OpenRouter.

        Args:
            model_names: Liste von Modellnamen (z.B. ["gpt-4o", "claude-3.5-sonnet", "gemini-pro"])
        """
        if not model_names:
            return "Fehler: Mindestens ein Modellname erforderlich."

        pricing = await get_openrouter_pricing(model_names)

        lines = []
        lines.append("=" * 70)
        lines.append("LLM PREISVERGLEICH (via OpenRouter)")
        lines.append("=" * 70)

        if not pricing:
            lines.append("\nKeine Preisdaten von OpenRouter verfügbar.")
            lines.append("Mögliche Gründe:")
            lines.append("  - API nicht erreichbar")
            lines.append("  - Modellnamen stimmen nicht mit OpenRouter-IDs überein")
            lines.append("\nTipp: Nutze die exakten OpenRouter-Modell-IDs (z.B. 'openai/gpt-4o')")

            # Fallback: Geschätzte Preise
            lines.append("\nGeschätzte Preise (Stand März 2025, $/1M Tokens):")
            estimated = {
                "gpt-4o": ("$2.50 Input", "$10.00 Output"),
                "gpt-4o-mini": ("$0.15 Input", "$0.60 Output"),
                "o1": ("$15.00 Input", "$60.00 Output"),
                "o3-mini": ("$1.10 Input", "$4.40 Output"),
                "claude-3.5-sonnet": ("$3.00 Input", "$15.00 Output"),
                "claude-3.5-haiku": ("$0.80 Input", "$4.00 Output"),
                "claude-3-opus": ("$15.00 Input", "$75.00 Output"),
                "gemini-2.0-flash": ("$0.10 Input", "$0.40 Output"),
                "gemini-2.0-pro": ("$1.25 Input", "$5.00 Output"),
                "gemini-1.5-pro": ("$1.25 Input", "$5.00 Output"),
                "deepseek-v3": ("$0.27 Input", "$1.10 Output"),
                "deepseek-r1": ("$0.55 Input", "$2.19 Output"),
                "llama-3.1-405b": ("$1.00 Input", "$1.00 Output"),
                "llama-3.1-70b": ("$0.40 Input", "$0.40 Output"),
                "llama-3.1-8b": ("$0.05 Input", "$0.05 Output"),
                "mistral-large": ("$2.00 Input", "$6.00 Output"),
                "mistral-small": ("$0.10 Input", "$0.30 Output"),
                "qwen-2.5-72b": ("$0.35 Input", "$0.40 Output"),
            }

            for name in model_names:
                key = None
                name_lower = name.lower()
                for k in estimated:
                    if name_lower in k or k in name_lower:
                        key = k
                        break
                if key:
                    inp, out = estimated[key]
                    lines.append(f"  {key:25s}: {inp:15s} | {out}")

            return "\n".join(lines)

        # OpenRouter-Daten formatieren
        entries = []
        for model_id, pdata in pricing.items():
            prompt = pdata.get("prompt_cost", "0")
            completion = pdata.get("completion_cost", "0")

            # In $/1M Tokens umrechnen
            try:
                prompt_per_m = float(prompt) * 1_000_000
                completion_per_m = float(completion) * 1_000_000
            except (ValueError, TypeError):
                prompt_per_m = 0
                completion_per_m = 0

            entries.append({
                "id": model_id,
                "name": pdata.get("name", model_id),
                "input_per_m": prompt_per_m,
                "output_per_m": completion_per_m,
                "context": pdata.get("context_length", "N/A"),
            })

        # Nach Input-Preis sortieren
        entries.sort(key=lambda x: x["input_per_m"])

        for e in entries:
            lines.append(f"\n  {e['name']}")
            lines.append(f"    ID:      {e['id']}")
            lines.append(f"    Input:   ${e['input_per_m']:.2f} / 1M Tokens")
            lines.append(f"    Output:  ${e['output_per_m']:.2f} / 1M Tokens")
            lines.append(f"    Kontext: {e['context']}")

        # Kostenschätzung
        lines.append("\n" + "-" * 70)
        lines.append("Kostenschätzung (1.000 Anfragen à 500 Input + 500 Output Tokens):")
        for e in entries:
            cost = (e["input_per_m"] * 500 + e["output_per_m"] * 500) / 1_000_000 * 1000
            lines.append(f"  {e['name']:35s}: ~${cost:.2f}")

        return "\n".join(lines)
