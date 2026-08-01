# POC: Ingestion Quality (Obsidian + GenWiki + Cloud Free Tier)

Goal: prove — or disprove — that this pipeline can turn a small, adversarial
document set into a clean, correctly-linked, non-hallucinated knowledge
graph, before committing to the full 4-phase build. Nothing here touches
agents, orchestration, or the later Groq routing layer — that's intentional.

**Provider decision**: GenWiki v1.0.9 has no supported local/Ollama option
(verified against its actual source, not just docs). Rather than relying on
an unsupported hack, this POC uses two **officially supported, $0, no-card**
cloud providers so setup stays simple and nothing breaks on a plugin update:

| | Model A: Google Gemini | Model B: OpenRouter (free) |
|---|---|---|
| Cost | $0, no credit card | $0, no credit card |
| Rate limits | ~15 RPM, roughly hundreds-to-~1,500 requests/day depending on the exact Gemini model — check your actual console after signup, published numbers shift | 20 RPM, 50 requests/day (unfunded account) |
| Embeddings / semantic search | Supported | **Not supported by GenWiki** — falls back to keyword search only |
| Setup | Paste API key into GenWiki settings UI | Paste API key into GenWiki settings UI |

Gemini is the stronger of the two — it's the only free option that gets you
GenWiki's full feature set (semantic search included). OpenRouter is kept
as the second comparison point specifically because it represents the
"budget / degraded" path, which is useful to see side by side.

**Real tradeoff, stated plainly**: your test documents leave your machine
in both cases (sent to Google's or OpenRouter's servers respectively). If
that's acceptable for your 15–20 test documents, proceed as below.

The unsupported local-Ollama hack (`scripts/patch_genwiki_settings.py`,
`ollama-hack` mode) is kept in this kit as an optional appendix — see
`scripts/README_ollama_hack.md` — in case you want fully local ingestion
later and are willing to accept it's unofficial and may break on updates.

## What's in this folder

| File | Purpose |
|---|---|
| `setup_vault.sh` | Scaffolds two isolated, git-initialized vaults (one per provider) |
| `corpus_checklist.md` | Template for picking your 15–20 adversarial test documents |
| `rubric_tracker.xlsx` | Where you log scores per document per model; auto-computes averages + a go/no-go recommendation |
| `scripts/review_helper.py` | Heuristic script that flags likely omissions and hallucination candidates before you manually review |
| `scripts/patch_genwiki_settings.py` | Optional — scripted settings setup for either provider, or the unsupported Ollama hack |
| `scripts/README_ollama_hack.md` | Optional appendix — how to spike-test the unsupported local hack if you want it later |

## Step-by-step

### 1. Get free API keys (2 minutes each, no credit card)
- **Gemini**: aistudio.google.com → "Get API key" → create a free key.
- **OpenRouter**: openrouter.ai → sign up → Settings → Keys → create a key.
  Then pick a current free model from openrouter.ai/models?order=pricing-low-to-high
  (filter for `:free` — the exact catalog rotates, so grab whatever's live,
  e.g. something like `meta-llama/llama-3.3-70b-instruct:free` if still available).

### 2. Install Obsidian + GenWiki
- **Obsidian**: obsidian.md → download → install.
- **GenWiki**: inside Obsidian → Settings → Community plugins → Browse →
  search "GenWiki" → Install → Enable.

### 3. Scaffold the vaults
```bash
chmod +x setup_vault.sh
./setup_vault.sh poc-vault
```
This creates `poc-vault/model-a-gemini/` and `poc-vault/model-b-openrouter/`,
each with its own git repo, `inbox/`, `wiki/`, and a `source-docs-raw/`
folder for the untouched originals.

### 4. Configure each vault's provider
Open each vault in Obsidian (one at a time), go to GenWiki's settings tab:
- **model-a-gemini**: Provider = Gemini, paste your Gemini API key, pick a
  model (Flash or Flash-Lite recommended for higher free-tier limits over Pro).
- **model-b-openrouter**: Provider = OpenRouter, paste your OpenRouter key,
  enter the `:free` model ID you picked in Step 1.

No file editing needed — this is all in the plugin's own settings panel.

### 5. Pick your corpus
Fill in `corpus_checklist.md` with real documents — 15–20 total, following
the categories listed (straightforward, overlapping-topic, same-concept-
different-wording, long, scanned/OCR, messy). Use the **identical** set for
both vaults.

### 6. Ingest in batches of 5, commit after each batch
```bash
cd poc-vault/model-a-gemini
git add -A && git commit -m "batch 1: <doc names>"
```
Watch your daily request count, especially for OpenRouter's 50/day cap —
15–20 docs at roughly 1–3 GenWiki calls each should comfortably fit in one
day per vault, but don't run both vaults' full batches back-to-back on the
same OpenRouter key without checking.

### 7. Run the heuristic review helper (optional but recommended)
```bash
# Convert any PDFs to text first, e.g.:
pdftotext -layout poc-vault/model-a-gemini/source-docs-raw/paper.pdf \
                  poc-vault/model-a-gemini/source-docs-raw/paper.txt

python scripts/review_helper.py \
  --source-dir poc-vault/model-a-gemini/source-docs-raw \
  --wiki-dir   poc-vault/model-a-gemini/wiki \
  --out        model-a-report.csv
```
Repeat for model-b-openrouter. This won't tell you the truth — it just
narrows down what to look at manually.

### 8. Score in `rubric_tracker.xlsx`
One row per document per model already scaffolded (yellow = fill in).
The **Summary** tab auto-computes per-model averages and a plain-language
go/no-go recommendation once both models are scored. Since OpenRouter has
no embeddings support here, expect its Link Quality scores to lean more on
GenWiki's keyword-based linking rather than semantic matches — that's a
real, expected difference, not a bug.

### 9. Decide
- **Proceed** → move into the full Phase 1 bulk load from the main plan,
  using whichever provider won (Gemini, most likely, given full feature
  support — but let the data say so).
- **Iterate** → if merge/dedup scores are weak (2–3), that's likely a
  prompt-tuning problem worth one more short loop before scaling to
  hundreds of documents.
- **Stop and reconsider** → any hallucinations, or failure handling that
  silently corrupts the graph, is a real blocker — not something to route
  around at scale.
- **Revisit local-only** → if sending documents to any cloud provider turns
  out to be a hard no once you see it in practice, that's when to seriously
  evaluate the Ollama hack (appendix) or a different ingestion tool
  entirely, rather than defaulting to it now.

## Timeline
3–5 days, working in batches of 5 documents per vault.
