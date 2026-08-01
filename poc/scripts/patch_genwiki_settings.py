#!/usr/bin/env python3
"""
patch_genwiki_settings.py — safely patch GenWiki's data.json to either:
  (a) attempt the unsupported local-Ollama hack, or
  (b) configure the official OpenRouter free-tier fallback.

This does a read-modify-write MERGE on the existing data.json (does not
touch unrelated keys like your saved API keys for other providers).

IMPORTANT: Close Obsidian before running this, and reopen it after —
Obsidian caches plugin settings in memory and will overwrite your edit
on its next save if the vault is open while you patch the file.

Usage:
    # Attempt A: local Ollama hack (unsupported, spike-test this first)
    python patch_genwiki_settings.py \
        --vault /path/to/poc-vault/model-a-llama3.1-8b \
        --mode ollama-hack \
        --model llama3.1:8b

    # Fallback B: official OpenRouter free tier
    python patch_genwiki_settings.py \
        --vault /path/to/poc-vault/model-a-openrouter \
        --mode openrouter \
        --model "meta-llama/llama-3.3-70b-instruct:free" \
        --openrouter-key sk-or-v1-xxxxxxxx
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", required=True, help="Path to the Obsidian vault root")
    ap.add_argument("--mode", required=True, choices=["ollama-hack", "openrouter"])
    ap.add_argument("--model", required=True,
                     help="For ollama-hack: an Ollama tag you've pulled, e.g. llama3.1:8b. "
                          "For openrouter: a model ID, e.g. meta-llama/llama-3.3-70b-instruct:free "
                          "(check openrouter.ai/models?order=pricing-low-to-high for the current live list — "
                          "the free catalog rotates).")
    ap.add_argument("--openrouter-key", help="Required for --mode openrouter")
    ap.add_argument("--ollama-url", default="http://localhost:11434/v1",
                     help="Ollama's OpenAI-compatible endpoint (default: http://localhost:11434/v1)")
    args = ap.parse_args()

    if args.mode == "openrouter" and not args.openrouter_key:
        print("ERROR: --openrouter-key is required for --mode openrouter", file=sys.stderr)
        sys.exit(1)

    data_path = Path(args.vault) / ".obsidian" / "plugins" / "genwiki" / "data.json"
    if not data_path.exists():
        print(f"ERROR: {data_path} not found.", file=sys.stderr)
        print("Open the vault in Obsidian and enable GenWiki at least once first, "
              "so it creates its default data.json — then close Obsidian and re-run this.", file=sys.stderr)
        sys.exit(1)

    with open(data_path, "r", encoding="utf-8") as f:
        settings = json.load(f)

    backup_path = data_path.with_suffix(".json.bak")
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
    print(f"Backed up original settings to {backup_path}")

    if args.mode == "ollama-hack":
        settings["provider"] = "openai"
        settings["openaiApiKey"] = "ollama-local-unused-key"  # any non-empty string; Ollama ignores it
        settings["openaiBaseUrl"] = args.ollama_url
        settings["openaiModel"] = args.model
        print("Patched for UNSUPPORTED local-Ollama hack:")
        print(f"  provider     = openai (spoofed)")
        print(f"  openaiBaseUrl = {args.ollama_url}")
        print(f"  openaiModel   = {args.model}")
        print("\nBefore reopening Obsidian, confirm Ollama is running and has this model pulled:")
        print(f"  ollama list   # should show {args.model}")
        print(f"  curl {args.ollama_url}/chat/completions -H 'Content-Type: application/json' -d "
              f'\'{{"model":"{args.model}","messages":[{{"role":"user","content":"say hi"}}]}}\'')
        print("  ^ if that curl doesn't return a normal chat completion JSON, the hack will fail in GenWiki too.")
        print("\nNote: embedding calls will ALSO be routed to this URL. If your Ollama version doesn't serve")
        print("an OpenAI-compatible /v1/embeddings route, embeddings will silently fail (logged to Obsidian's")
        print("developer console) but ingestion itself will still proceed — GenWiki catches embedding errors")
        print("and continues without them. Core ingestion quality is NOT blocked by embedding failures.")
    else:
        settings["provider"] = "openrouter"
        settings["openrouterApiKey"] = args.openrouter_key
        settings["openrouterModel"] = args.model
        print("Patched for OFFICIAL OpenRouter free-tier provider:")
        print(f"  provider        = openrouter")
        print(f"  openrouterModel = {args.model}")
        print("\nReminder: OpenRouter free tier = 20 req/min, 50 req/day (unfunded account).")

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

    print(f"\nWrote {data_path}")
    print("Now reopen Obsidian for this vault and try ingesting ONE small test document before running the full batch.")


if __name__ == "__main__":
    main()
