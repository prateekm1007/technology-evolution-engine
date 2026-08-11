#!/usr/bin/env python3
"""
Phase 5.B — Extract real arXiv paper abstracts from fetched pages.

Reads the page_reader JSON output for each arXiv paper, extracts the
abstract, and saves a normalized text file to
data/ingestion/real/<ARXIV_ID>.txt.

The output format matches what PaperParser expects:
    Title: <paper title>
    Abstract:
    <abstract text>

One-off extraction utility, NOT a module. NOT imported by anything.
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES_DIR = pathlib.Path("/tmp/phase5b_search/pages")
OUT_DIR = ROOT / "data" / "ingestion" / "real"


def extract_text(html_or_text):
    if not html_or_text:
        return ""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html_or_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    text = re.sub(r"\s+", " ", text).strip()
    return text


def find_abstract(full_text):
    """arXiv abstracts are in a 'Abstract:' section."""
    # arXiv's canonical format: "Abstract: <text>" followed by "Comments:" or "Subjects:" or "Cite as:"
    patterns = [
        r"Abstract:\s*(.+?)(?:Comments:|Subjects:|Cite as:|MSC|ACM|Submission|BibTeX|References)",
        r"Abstract\s*(.+?)(?:Comments:|Subjects:|Cite as:|MSC|ACM|Submission|BibTeX|References)",
    ]
    for p in patterns:
        m = re.search(p, full_text, re.DOTALL | re.IGNORECASE)
        if m:
            abstract = m.group(1).strip()
            if len(abstract) > 2000:
                abstract = abstract[:2000] + "..."
            return abstract
    # Fallback: first 1500 chars after "Abstract"
    idx = full_text.lower().find("abstract")
    if idx >= 0:
        return full_text[idx + 8:idx + 1500].strip()
    return ""


def find_title(page_data, full_text):
    """Extract paper title."""
    title = page_data.get("title", "")
    if title and "[" not in title[:5]:
        # Clean arXiv title format: "[arXiv:ID] Title" or "Title - arXiv"
        title = re.sub(r"^\[\s*arXiv:\S+\s*\]\s*", "", title)
        title = re.sub(r"\s*-\s*arXiv\s*$", "", title)
        return title.strip()
    # Fallback: look for "Title:" header
    m = re.search(r"Title:\s*(.+?)(?:Authors:|Abstract:|Comments:)", full_text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return "Untitled Paper"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pages = sorted(PAGES_DIR.glob("*.json"))
    print(f"Found {len(pages)} arXiv pages to extract")
    print()

    extracted = []
    for page_path in pages:
        arxiv_id = page_path.stem
        with open(page_path) as f:
            page_data = json.load(f)

        data = page_data.get("data", page_data)
        html = data.get("html", "")
        text = data.get("text", "") or extract_text(html)

        title = find_title(data, text)
        abstract = find_abstract(text)

        if not abstract or len(abstract) < 100:
            print(f"  WARNING: {arxiv_id} — abstract too short ({len(abstract)} chars)")
            print(f"    text preview: {text[:300]!r}")
            continue

        out_path = OUT_DIR / f"arxiv_{arxiv_id}.txt"
        with open(out_path, "w") as f:
            f.write(f"Title: {title}\n")
            f.write(f"arXiv_id: {arxiv_id}\n")
            f.write(f"Abstract:\n{abstract}\n")

        extracted.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "abstract_length": len(abstract),
            "out_path": str(out_path.relative_to(ROOT)),
        })
        print(f"  {arxiv_id}: {title[:70]}")
        print(f"    abstract: {len(abstract)} chars")

    # Save manifest
    manifest_path = OUT_DIR / "_manifest_arxiv.json"
    with open(manifest_path, "w") as f:
        json.dump({
            "extracted_count": len(extracted),
            "papers": extracted,
        }, f, indent=2)

    print(f"\nExtracted {len(extracted)} arXiv papers to {OUT_DIR}")


if __name__ == "__main__":
    main()
