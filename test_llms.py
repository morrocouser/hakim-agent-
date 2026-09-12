#!/usr/bin/env python3
"""
Test direct des LLM configurés sur OpenRouter pour AXIOM v4.0
Mesure la latence, la validité des réponses et les performances réelles.
"""

import sys
import io
import time
import json
from pathlib import Path

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from axiom.claude.client import LocalAPIClient
from axiom.models.schemas import ModelName

# Couleurs ANSI
R = "\033[91m"; G = "\033[92m"; Y = "\033[93m"; C = "\033[96m"
W = "\033[97m"; M = "\033[95m"; DIM = "\033[2m"; BOLD = "\033[1m"; RST = "\033[0m"

MODELS_TO_TEST = [
    ("SMALL  (Score 0.0 - 2.5)", ModelName.SMALL,  "Dis uniquement 'OK'"),
    ("MEDIUM (Score 2.6 - 4.5)", ModelName.MEDIUM, "Donne une définition courte de Python en 1 phrase."),
    ("LARGE  (Score 4.6 - 6.5)", ModelName.LARGE,  "Écris une fonction Python simple qui calcule la somme de deux nombres."),
    ("BEST   (Score 6.6 - 10.0)", ModelName.BEST,   "Explique brièvement le principe d'une architecture Event-Driven."),
]

async def main():
    print(f"\n{BOLD}{C}===================================================={RST}")
    print(f"{BOLD}{C}    TEST EN DIRECT DES LLM OPENROUTER -- AXIOM v4.0  {RST}")
    print(f"{BOLD}{C}===================================================={RST}\n")

    try:
        client = LocalAPIClient()
    except Exception as e:
        print(f"{R}[KO] Impossible d'initialiser le client OpenRouter: {e}{RST}")
        return

    if not client.is_configured():
        print(f"{R}[KO] Clé OPENROUTER_API_KEY non configurée.{RST}")
        return

    print(f"  {G}[✓]{RST} Clé API OpenRouter détectée\n")

    passed = 0
    failed = 0

    for tier_label, model_enum, prompt in MODELS_TO_TEST:
        model_name = model_enum.value
        print(f"----------------------------------------------------")
        print(f" {BOLD}{W}Modèle Tier: {tier_label}{RST}")
        print(f" {DIM}ID OpenRouter: {C}{model_name}{RST}")
        print(f" {DIM}Prompt: \"{prompt}\"{RST}")

        t0 = time.perf_counter()
        try:
            response = await client.chat(
                model=model_name,
                system="Tu es un assistant IA précis.",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            elapsed = (time.perf_counter() - t0) * 1000
            passed += 1

            # Clean output display
            clean_resp = response.strip().replace("\n", " ")
            if len(clean_resp) > 120:
                clean_resp = clean_resp[:120] + "..."

            print(f" {G}[OK] Réponse reçue en {elapsed:.1f}ms{RST}")
            print(f" {M}➜ Output:{RST} {clean_resp}\n")

        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            failed += 1
            print(f" {R}[KO] Échec après {elapsed:.1f}ms{RST}")
            print(f" {R}  Erreur: {e}{RST}\n")

    print(f"{BOLD}{C}===================================================={RST}")
    print(f" Résultat final : {G}{passed} modèles opérationnels{RST} / {R}{failed} échecs{RST}")
    print(f"{BOLD}{C}===================================================={RST}\n")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
