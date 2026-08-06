#!/usr/bin/env python3
"""
Phase 5 — Extract real patent abstracts from fetched Google Patents pages.

Reads the page_reader JSON output for each patent, extracts the
abstract + claims text, and saves a normalized text file to
data/ingestion/real/<PATENT_ID>.txt.

The output format matches what PatentParser expects:
    TITLE: <patent title>
    ABSTRACT:
    <abstract text>
    CLAIMS:
    <claims text>

This is a one-off extraction utility, NOT a module. It is NOT imported
by anything.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES_DIR = pathlib.Path("/tmp/phase5_search/pages")
OUT_DIR = ROOT / "data" / "ingestion" / "real"


def extract_text(html_or_text):
    """Strip HTML tags and normalize whitespace."""
    if not html_or_text:
        return ""
    # Remove script/style blocks
    text = re.sub(r"<script[^>]*>.*?</script>", "", html_or_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Strip all HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode HTML entities (basic)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def find_abstract(full_text):
    """Extract the abstract section from a Google Patents page text."""
    # Google Patents typically has "Abstract" as a heading followed by the abstract text.
    # Try several patterns.
    patterns = [
        r"Abstract\s+(.+?)(?:Images|Classifications|Claims|Description|Field|Background|Summary|Detailed)",
        r"ABSTRACT\s+(.+?)(?:Images|Classifications|Claims|Description|Field|Background|Summary|Detailed)",
    ]
    for p in patterns:
        m = re.search(p, full_text, re.DOTALL | re.IGNORECASE)
        if m:
            abstract = m.group(1).strip()
            # Truncate to reasonable length
            if len(abstract) > 2000:
                abstract = abstract[:2000] + "..."
            return abstract
    # Fallback: take first 1500 chars after "Abstract" keyword
    idx = full_text.lower().find("abstract")
    if idx >= 0:
        return full_text[idx + 8:idx + 1500].strip()
    return ""


def find_claims(full_text):
    """Extract first few claims (truncated for parser input)."""
    patterns = [
        r"Claims\s+(.+?)(?:Description|Classifications|Images|Patent|Google)",
        r"CLAIMS\s+(.+?)(?:Description|Classifications|Images|Patent|Google)",
    ]
    for p in patterns:
        m = re.search(p, full_text, re.DOTALL | re.IGNORECASE)
        if m:
            claims = m.group(1).strip()
            # Truncate to first ~3 claims or 2000 chars
            if len(claims) > 2000:
                claims = claims[:2000] + "..."
            return claims
    return ""


def find_title(page_data):
    """Extract patent title from page data."""
    title = page_data.get("title", "")
    if title:
        # Clean up Google Patents title format
        # Often: "USXXXXXXA1 - Patent Title - Google Patents"
        if " - " in title:
            parts = title.split(" - ")
            if len(parts) >= 2:
                return parts[1].strip()
        return title.strip()
    return "Untitled Patent"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pages = sorted(PAGES_DIR.glob("*.json"))
    print(f"Found {len(pages)} patent pages to extract")
    print()

    extracted = []
    for page_path in pages:
        patent_id = page_path.stem
        with open(page_path) as f:
            page_data = json.load(f)

        # page_reader returns nested structure
        data = page_data.get("data", page_data)
        title = find_title(data)
        html = data.get("html", "")
        text = data.get("text", "") or extract_text(html)

        abstract = find_abstract(text)
        claims = find_claims(text)

        if not abstract and not claims:
            print(f"  WARNING: {patent_id} — no abstract or claims found")
            # Save raw text first 500 chars for inspection
            print(f"    text preview: {text[:300]!r}")
            continue

        out_path = OUT_DIR / f"{patent_id}.txt"
        with open(out_path, "w") as f:
            f.write(f"TITLE: {title}\n")
            f.write(f"PATENT_NUMBER: {patent_id}\n")
            f.write(f"ABSTRACT:\n{abstract}\n\n")
            if claims:
                f.write(f"CLAIMS:\n{claims}\n")

        extracted.append({
            "patent_id": patent_id,
            "title": title,
            "abstract_length": len(abstract),
            "claims_length": len(claims),
            "out_path": str(out_path.relative_to(ROOT)),
        })
        print(f"  {patent_id}: {title[:60]}")
        print(f"    abstract: {len(abstract)} chars, claims: {len(claims)} chars")

    # Save extraction manifest
    manifest_path = OUT_DIR / "_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump({
            "extracted_at": extracted[0]["patent_id"] if extracted else None,
            "count": len(extracted),
            "patents": extracted,
        }, f, indent=2)

    print(f"\nExtracted {len(extracted)} patents to {OUT_DIR}")


if __name__ == "__main__":
    main()
