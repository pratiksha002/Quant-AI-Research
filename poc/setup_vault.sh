#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# POC vault scaffold — Ingestion Quality Test (cloud free-tier providers)
# Run this on YOUR machine (not in a sandboxed environment) after installing
# Obsidian and the GenWiki plugin, and after getting free API keys for
# Gemini (aistudio.google.com) and OpenRouter (openrouter.ai).
# This script does NOT install those — see README.md.
# ---------------------------------------------------------------------------
set -euo pipefail

VAULT_ROOT="${1:-poc-vault}"

echo "Creating POC vault scaffold at ./${VAULT_ROOT} ..."

declare -A PROVIDER_NOTES=(
  ["model-a-gemini"]="Provider = Gemini. Paste your Gemini API key in GenWiki settings. Pick Flash or Flash-Lite for higher free-tier limits than Pro. Supports embeddings (semantic search)."
  ["model-b-openrouter"]="Provider = OpenRouter. Paste your OpenRouter API key in GenWiki settings. Enter a current :free model ID (catalog rotates — check openrouter.ai/models). No embeddings support in GenWiki for this provider; falls back to keyword search."
)

for MODEL_DIR in model-a-gemini model-b-openrouter; do
  BASE="${VAULT_ROOT}/${MODEL_DIR}"
  mkdir -p "${BASE}/inbox"
  mkdir -p "${BASE}/wiki/sources"
  mkdir -p "${BASE}/wiki/entities"
  mkdir -p "${BASE}/wiki/concepts"
  mkdir -p "${BASE}/_database"
  mkdir -p "${BASE}/source-docs-raw"      # original 15-20 test docs, untouched, for the review script
  touch "${BASE}/log.md"
  echo '{}' > "${BASE}/_database/index.json"

  cat > "${BASE}/README.md" <<EOF
# ${MODEL_DIR}

This is an isolated vault for testing ingestion quality with ${MODEL_DIR}.

${PROVIDER_NOTES[$MODEL_DIR]}

1. Open this folder as a new vault in Obsidian.
2. Install/enable the GenWiki plugin for this vault.
3. In GenWiki settings, configure the provider as noted above.
4. Copy the SAME 15-20 test documents (from your corpus checklist) into
   source-docs-raw/ AND into inbox/ (source-docs-raw stays untouched as the
   ground truth for the review script; inbox/ is what GenWiki consumes).
5. Ingest in batches of 5, committing to git after each batch (see below).
   Watch your daily request cap, especially OpenRouter's 50/day limit.
EOF

  (
    cd "${BASE}"
    git init -q
    git add -A
    git commit -q -m "Initial empty vault scaffold (${MODEL_DIR})"
  )
done

cat > "${VAULT_ROOT}/README.md" <<'EOF'
# POC: Ingestion Quality Test (cloud free-tier providers)

Two isolated vaults, same 15-20 documents, two different GenWiki providers
(Gemini free tier vs OpenRouter free tier), so you can diff results side
by side. See the top-level README.md (one level up) for full setup steps.

## Workflow per vault
1. Drop 5 documents into inbox/ (and the same 5 into source-docs-raw/).
2. Let GenWiki ingest them.
3. Commit: `git add -A && git commit -m "batch 1: <doc names>"`
4. Review the new/changed files in wiki/entities/ and wiki/concepts/
   against source-docs-raw/ using the rubric.
5. Optionally run scripts/review_helper.py for a heuristic first pass
   before your manual review.
6. Repeat for the next batch of 5.

## After both vaults are done
Fill in rubric_tracker.xlsx (repo root) — one row per document per model —
and check the Summary sheet for which provider wins on average.
EOF

echo "Done. Structure:"
find "${VAULT_ROOT}" -maxdepth 3 | sort
