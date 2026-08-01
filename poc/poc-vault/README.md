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
