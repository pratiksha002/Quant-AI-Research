#!/usr/bin/env python3
"""
review_helper.py — heuristic first-pass check for the ingestion-quality POC.

This does NOT replace manual review against the rubric. It flags candidates
for you to look at faster: terms that appear in the source docs but seem
missing from the generated wiki, and terms that appear in the wiki but
can't be found anywhere in the source docs (possible hallucination
candidates). All matching is plain-text heuristics (capitalized phrases +
standalone numbers), not semantic understanding, so treat every flag as
"go check this," not "this is definitely wrong."

Usage:
    python review_helper.py \
        --source-dir poc-vault/model-a-llama3.1-8b/source-docs-raw \
        --wiki-dir   poc-vault/model-a-llama3.1-8b/wiki \
        --out        model-a-report.csv

Notes:
    - Source docs should be plain text or Markdown. If you're working from
      PDFs, convert first, e.g.: `pdftotext -layout paper.pdf paper.txt`
    - Run once per vault (once per model) and compare the two CSVs.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

CAP_PHRASE_RE = re.compile(r"\b(?:[A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,3})\b")
NUMBER_RE = re.compile(r"\b\d{2,}(?:\.\d+)?%?\b")  # 2+ digit numbers, optional decimal/%
STOPWORD_CAPS = {
    "The", "This", "That", "These", "Those", "A", "An", "In", "On", "At",
    "It", "As", "Is", "Are", "Was", "Were", "For", "With", "And", "Or",
    "But", "If", "Then", "So", "To", "Of", "By", "From", "I",
}


def read_text_files(directory: Path) -> dict:
    texts = {}
    if not directory.exists():
        return texts
    for f in directory.rglob("*"):
        if f.is_file() and f.suffix.lower() in {".md", ".txt"}:
            try:
                texts[str(f)] = f.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                print(f"  ! could not read {f}: {e}", file=sys.stderr)
    return texts


def extract_terms(text: str) -> set:
    terms = set()
    for m in CAP_PHRASE_RE.findall(text):
        m = m.strip()
        if m and m not in STOPWORD_CAPS and len(m) > 2:
            terms.add(m)
    for m in NUMBER_RE.findall(text):
        terms.add(m)
    return terms


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source-dir", required=True, help="Folder of original source docs (plain text/Markdown)")
    ap.add_argument("--wiki-dir", required=True, help="Folder of GenWiki-generated pages (wiki/)")
    ap.add_argument("--out", default="review_report.csv", help="Output CSV path")
    args = ap.parse_args()

    source_dir = Path(args.source_dir)
    wiki_dir = Path(args.wiki_dir)

    source_texts = read_text_files(source_dir)
    wiki_texts = read_text_files(wiki_dir)

    if not source_texts:
        print(f"No .md/.txt files found under {source_dir}. If these are PDFs, convert them first "
              f"(e.g. `pdftotext -layout file.pdf file.txt`).", file=sys.stderr)
    if not wiki_texts:
        print(f"No .md/.txt files found under {wiki_dir}. Has GenWiki ingested anything yet?", file=sys.stderr)

    combined_source = "\n".join(source_texts.values())
    combined_wiki = "\n".join(wiki_texts.values())

    source_terms = extract_terms(combined_source)
    wiki_terms = extract_terms(combined_wiki)

    # Terms in source but not found anywhere in the generated wiki (possible omissions)
    missing_from_wiki = sorted(t for t in source_terms if t not in combined_wiki)

    # Terms in wiki but not found anywhere in the source corpus (possible hallucination candidates)
    not_in_source = sorted(t for t in wiki_terms if t not in combined_source)

    rows = []
    max_len = max(len(missing_from_wiki), len(not_in_source), 1)
    for i in range(max_len):
        rows.append({
            "possible_omission_from_wiki": missing_from_wiki[i] if i < len(missing_from_wiki) else "",
            "possible_hallucination_candidate_in_wiki": not_in_source[i] if i < len(not_in_source) else "",
        })

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["possible_omission_from_wiki", "possible_hallucination_candidate_in_wiki"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Source docs read: {len(source_texts)}")
    print(f"Wiki pages read:  {len(wiki_texts)}")
    print(f"Source terms extracted: {len(source_terms)}")
    print(f"Wiki terms extracted:   {len(wiki_terms)}")
    print(f"Possible omissions (in source, not in wiki):        {len(missing_from_wiki)}")
    print(f"Possible hallucination candidates (in wiki, not in source): {len(not_in_source)}")
    print(f"Full lists written to: {args.out}")
    print("\nReminder: these are plain-text heuristics (capitalized phrases + numbers).")
    print("Every row is a prompt to go check the actual page, not a verdict.")


if __name__ == "__main__":
    main()
