# POC Corpus Checklist (15–20 documents)

Fill in real document names as you pick them. This selection is deliberately
adversarial — it's meant to expose failure modes early, not to look tidy.

| # | Category | Purpose | Doc name (fill in) | Picked? |
|---|---|---|---|---|
| 1 | Straightforward | Baseline — should extract cleanly | | ☐ |
| 2 | Straightforward | Baseline | | ☐ |
| 3 | Straightforward | Baseline | | ☐ |
| 4 | Straightforward | Baseline | | ☐ |
| 5 | Overlapping topic | Tests correct merge vs. wrongful duplication | | ☐ |
| 6 | Overlapping topic | Same as above, different doc | | ☐ |
| 7 | Overlapping topic | Same as above, different doc | | ☐ |
| 8 | Same concept, different wording | Tests entity deduplication | | ☐ |
| 9 | Same concept, different wording | Same as above, different doc | | ☐ |
| 10 | Long document | Tests degradation on length (book chapter) | | ☐ |
| 11 | Long document | Same as above, different doc | | ☐ |
| 12 | Scanned/OCR | Tests the OCR failure mode explicitly | | ☐ |
| 13 | Messy/poorly formatted | Tests graceful degradation | | ☐ |

Add 2–7 more of whichever category you're least confident about, up to ~20 total.

## Reminders
- Use the **same exact document set** for both models (Model A and Model B) — copy, don't re-pick.
- Convert PDFs to plain text for the review script: `pdftotext -layout file.pdf file.txt`
  (keep the original PDF too — that's what actually goes into GenWiki's inbox).
- Batches of 5 at a time, committing to git after each batch (see setup_vault.sh output).
