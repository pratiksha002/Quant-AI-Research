# Appendix: Unsupported Local-Ollama Hack

**This is not part of the main POC path anymore.** The main POC now uses
Gemini + OpenRouter, both official, both free, no card, no file editing.
Read this only if cloud ingestion turns out to be a hard no later and you
want to revisit local-only ingestion.

## Why this exists
GenWiki v1.0.9's settings UI only supports six cloud providers (Gemini,
Anthropic, OpenAI, DeepSeek, Kimi, OpenRouter) — no Ollama, no custom
base-URL field. But internally, each provider's base URL is a plain
variable with a default (e.g. `openaiBaseUrl` defaults to
`api.openai.com`), and the OpenAI call path only checks that the API key
string is non-empty — it doesn't validate it's a real OpenAI key. That
means hand-editing the plugin's `data.json` to point `openaiBaseUrl` at
a local Ollama server can work, since Ollama exposes an OpenAI-compatible
`/v1/chat/completions` endpoint and ignores the Authorization header.

## Why it's not the default
- **Unsupported**: no UI for it, could silently break on any GenWiki update.
- **Embeddings uncertain**: GenWiki will also route embedding calls to the
  same URL. Whether your installed Ollama version serves an OpenAI-style
  `/v1/embeddings` route isn't guaranteed. The good news: GenWiki catches
  embedding failures and continues without them — ingestion itself won't
  hard-fail, you'd just lose semantic search until/unless embeddings work.
- **Requires local hardware** capable of running an 8B+ model reasonably,
  which the cloud-free-tier path avoids entirely.

## If you want to try it anyway

```bash
# 1. Install Ollama and pull a model
ollama pull llama3.1:8b

# 2. Open the target vault in Obsidian once, enable GenWiki, then CLOSE Obsidian
#    (so it isn't holding the settings file open / about to overwrite your edit)

# 3. Patch the settings
python patch_genwiki_settings.py \
    --vault /path/to/your/vault \
    --mode ollama-hack \
    --model llama3.1:8b

# 4. Sanity-check the endpoint BEFORE reopening Obsidian
curl http://localhost:11434/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"llama3.1:8b","messages":[{"role":"user","content":"say hi"}]}'
# If this doesn't return a normal chat completion JSON, GenWiki won't work either.

# 5. Reopen Obsidian, ingest ONE small test document, check the result before
#    running a full batch.
```

If the curl in step 4 fails, or the ingested page comes back empty/garbled,
that's your signal to fall back to the cloud path rather than debugging
further — the hack isn't worth chasing down for a small POC.

## Restoring original settings
The patch script writes a backup before editing:
`.obsidian/plugins/genwiki/data.json.bak`. Copy it back over `data.json`
(with Obsidian closed) to undo the change.
