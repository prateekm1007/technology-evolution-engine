#!/usr/bin/env python3
"""
section_segmentation.py — Generation 1: Section segmentation for arxiv PDFs.

Per auditor cycle 103: "The Gen 4 breakthrough requires Gen 1 first —
you cannot extract mechanisms from abstracts alone."

Per CEO 6-generation plan:
  Gen 1: World-class ingestion layer (target 8-9/10)
  - Section segmentation: extract abstract, introduction, methods,
    results, discussion from scientific papers.

This module:
  1. Takes a PDF file path
  2. Extracts full text via pdftotext
  3. Segments into sections using header detection (regex + heuristics)
  4. Returns a CanonicalDocument with sections populated

The section segmentation uses common scientific paper header patterns:
  - "Abstract" / "Introduction" / "Methods" / "Results" / "Discussion"
  - "1. Introduction" / "2. Methods" / "3. Results" / "4. Discussion"
  - "MATERIALS AND METHODS" / "RESULTS AND DISCUSSION"

Target benchmark: 98% section segmentation accuracy.
"""
import re
import subprocess
import pathlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class SegmentedDocument:
    """A scientific paper segmented into sections."""
    title: str = ""
    abstract: str = ""
    introduction: str = ""
    methods: str = ""
    results: str = ""
    discussion: str = ""
    conclusions: str = ""
    references: str = ""
    full_text: str = ""
    sections_found: List[str] = field(default_factory=list)
    source_file: str = ""
    
    def get_body_text(self) -> str:
        """Get the body text (methods + results + discussion).
        
        This is the text the NLP pipeline should process for mechanism
        extraction. Abstracts are too short; body sections contain
        the multi-step causal chains.
        """
        parts = []
        if self.methods:
            parts.append(self.methods)
        if self.results:
            parts.append(self.results)
        if self.discussion:
            parts.append(self.discussion)
        if self.conclusions:
            parts.append(self.conclusions)
        return " ".join(parts)


# Common section header patterns in scientific papers
SECTION_PATTERNS = {
    "abstract": [
        r'^\s*Abstract\s*$',
        r'^\s*ABSTRACT\s*$',
        r'^\s*Summary\s*$',
    ],
    "introduction": [
        r'^\s*Introduction\s*$',
        r'^\s*INTRODUCTION\s*$',
        r'^\s*\d+\.?\s*Introduction\s*$',
        r'^\s*\d+\.?\s*INTRODUCTION\s*$',
    ],
    "methods": [
        r'^\s*Methods\s*$',
        r'^\s*METHODS\s*$',
        r'^\s*Materials\s+and\s+Methods\s*$',
        r'^\s*MATERIALS\s+AND\s+METHODS\s*$',
        r'^\s*Experimental\s*$',
        r'^\s*EXPERIMENTAL\s*$',
        r'^\s*Methodology\s*$',
        r'^\s*\d+\.?\s*Methods\s*$',
        r'^\s*\d+\.?\s*Materials\s+and\s+Methods\s*$',
        r'^\s*\d+\.?\s*Experimental\s*$',
    ],
    "results": [
        r'^\s*Results\s*$',
        r'^\s*RESULTS\s*$',
        r'^\s*Results\s+and\s+Discussion\s*$',
        r'^\s*RESULTS\s+AND\s+DISCUSSION\s*$',
        r'^\s*\d+\.?\s*Results\s*$',
        r'^\s*\d+\.?\s*Results\s+and\s+Discussion\s*$',
    ],
    "discussion": [
        r'^\s*Discussion\s*$',
        r'^\s*DISCUSSION\s*$',
        r'^\s*\d+\.?\s*Discussion\s*$',
    ],
    "conclusions": [
        r'^\s*Conclusions?\s*$',
        r'^\s*CONCLUSIONS?\s*$',
        r'^\s*\d+\.?\s*Conclusions?\s*$',
        r'^\s*Conclusion\s*$',
    ],
    "references": [
        r'^\s*References\s*$',
        r'^\s*REFERENCES\s*$',
        r'^\s*Bibliography\s*$',
        r'^\s*\d+\.?\s*References\s*$',
    ],
}


def extract_pdf_text(pdf_path: str) -> str:
    """Extract full text from a PDF using pdftotext."""
    result = subprocess.run(
        ["pdftotext", "-q", str(pdf_path), "-"],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout


def segment_paper(text: str) -> SegmentedDocument:
    """Segment a scientific paper into sections.
    
    Uses header detection: looks for lines that match common section
    header patterns (case-insensitive, with optional numbering).
    
    Returns a SegmentedDocument with populated sections.
    """
    doc = SegmentedDocument(full_text=text)
    
    lines = text.split('\n')
    
    # Find section header positions
    section_starts: List[Tuple[str, int]] = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) > 80:
            continue  # Skip empty or very long lines (not headers)
        
        for section_name, patterns in SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    section_starts.append((section_name, i))
                    break
            else:
                continue
            break
    
    # If no sections found, try a more aggressive approach:
    # look for all-caps short lines that might be headers
    if not section_starts:
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if (line_stripped and len(line_stripped) < 50 and
                line_stripped.isupper() and
                not line_stripped.isdigit()):
                # Check if it matches any known section name
                for section_name, patterns in SECTION_PATTERNS.items():
                    for pattern in patterns:
                        if re.match(pattern, line_stripped, re.IGNORECASE):
                            section_starts.append((section_name, i))
                            break
    
    # Extract title (first non-empty lines before first section)
    if section_starts:
        first_section_line = section_starts[0][1]
        title_lines = []
        for line in lines[:first_section_line]:
            line = line.strip()
            if line and not line.isdigit() and len(line) > 5:
                title_lines.append(line)
        doc.title = " ".join(title_lines[:3])  # Usually first 3 lines
    
    # Extract each section's text
    for idx, (section_name, start_line) in enumerate(section_starts):
        # End line is the start of the next section, or end of document
        if idx + 1 < len(section_starts):
            end_line = section_starts[idx + 1][1]
        else:
            end_line = len(lines)
        
        section_text = "\n".join(lines[start_line + 1:end_line]).strip()
        
        # Assign to the document
        if section_name == "abstract":
            doc.abstract = section_text
        elif section_name == "introduction":
            doc.introduction = section_text
        elif section_name == "methods":
            doc.methods = section_text
        elif section_name == "results":
            # If "Results and Discussion" was matched, assign to both
            if "discussion" in section_text.lower()[:100]:
                doc.results = section_text
                doc.discussion = section_text  # shared
            else:
                doc.results = section_text
        elif section_name == "discussion":
            doc.discussion = section_text
        elif section_name == "conclusions":
            doc.conclusions = section_text
        elif section_name == "references":
            doc.references = section_text
        
        if section_name not in doc.sections_found:
            doc.sections_found.append(section_name)
    
    return doc


def segment_pdf(pdf_path: str) -> SegmentedDocument:
    """Extract and segment a PDF paper.
    
    This is the main entry point for Gen 1 section segmentation.
    """
    text = extract_pdf_text(pdf_path)
    doc = segment_paper(text)
    doc.source_file = str(pdf_path)
    return doc


if __name__ == "__main__":
    # Test on available arxiv PDFs
    import glob
    
    pdfs = glob.glob("/tmp/arxiv_pdfs/*.pdf")[:3]
    
    for pdf_path in pdfs:
        print(f"\n{'='*60}")
        print(f"PDF: {pathlib.Path(pdf_path).name}")
        print(f"{'='*60}")
        
        doc = segment_pdf(pdf_path)
        
        print(f"Title: {doc.title[:80]}...")
        print(f"Sections found: {doc.sections_found}")
        print(f"Abstract: {len(doc.abstract)} chars")
        print(f"Introduction: {len(doc.introduction)} chars")
        print(f"Methods: {len(doc.methods)} chars")
        print(f"Results: {len(doc.results)} chars")
        print(f"Discussion: {len(doc.discussion)} chars")
        print(f"Conclusions: {len(doc.conclusions)} chars")
        print(f"Body text (methods+results+discussion): {len(doc.get_body_text())} chars")
        
        if doc.get_body_text():
            print(f"\nBody text preview (first 300 chars):")
            print(doc.get_body_text()[:300])
