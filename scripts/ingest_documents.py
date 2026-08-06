#!/usr/bin/env python3
"""
ingest_documents.py — DR-39: Canonical document parsing layer.

Per docs/EXTRACTION_ARCHITECTURE.md step 2:
  Accept PDF and text inputs → produce a canonical structured document
  object with sections, paragraphs, citations, tables, provenance.

This module wraps the existing section_segmentation.py and adds:
  - paragraph-level segmentation
  - citation extraction
  - table detection (basic)
  - provenance (source_id, retrieval_timestamp)
  - deterministic JSON output

Exit criterion: A random scientific PDF becomes a structured document
with readable sections and source provenance.
"""
import sys
import json
import re
import hashlib
import subprocess
import pathlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

# Import existing section segmentation
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from scripts.section_segmentation import segment_pdf, segment_paper, extract_pdf_text


@dataclass
class Paragraph:
    """A paragraph within a section."""
    text: str
    char_start: int
    char_end: int
    index: int  # paragraph number within section


@dataclass
class Citation:
    """A citation reference extracted from text."""
    raw_text: str
    char_start: int
    char_end: int
    citation_type: str = "unknown"  # inline, bracket, footnote


@dataclass
class Equation:
    """An equation extracted from text (DR-39, cycle 124)."""
    raw_text: str
    char_start: int
    char_end: int
    section: str = ""
    equation_type: str = "unknown"  # formula, inline, display


@dataclass
class Table:
    """A table detected in the text."""
    raw_text: str
    char_start: int
    char_end: int
    section: str = ""
    row_count: int = 0
    col_count: int = 0


@dataclass
class CanonicalDocument:
    """The canonical document representation (DR-39).
    
    This is the structured output that feeds downstream extraction:
    entities, relations, mechanisms, discoveries.
    """
    # Identity
    source_id: str = ""  # arxiv_id, filename, or URL
    source_type: str = ""  # "pdf", "text", "url"
    title: str = ""
    
    # Content
    abstract: str = ""
    introduction: str = ""
    methods: str = ""
    results: str = ""
    discussion: str = ""
    conclusions: str = ""
    references: str = ""
    full_text: str = ""
    
    # Structure
    sections: Dict[str, str] = field(default_factory=dict)
    paragraphs: Dict[str, List[Paragraph]] = field(default_factory=dict)
    citations: List[Citation] = field(default_factory=dict)
    tables: List[Table] = field(default_factory=list)
    equations: List[Equation] = field(default_factory=list)  # cycle 124
    
    # Provenance (DR-43)
    retrieval_timestamp: str = ""
    provenance_hash: str = ""
    source_file: str = ""
    
    def get_body_text(self) -> str:
        """Get methods + results + discussion + conclusions."""
        parts = []
        for section_name in ("methods", "results", "discussion", "conclusions"):
            text = getattr(self, section_name, "")
            if text:
                parts.append(text)
        return " ".join(parts)
    
    def to_dict(self) -> Dict:
        """Serializable representation."""
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "title": self.title[:200],
            "sections_found": list(self.sections.keys()),
            "abstract_chars": len(self.abstract),
            "body_chars": len(self.get_body_text()),
            "paragraph_count": sum(len(p) for p in self.paragraphs.values()),
            "citation_count": len(self.citations),
            "table_count": len(self.tables),
            "equation_count": len(self.equations),
            "retrieval_timestamp": self.retrieval_timestamp,
            "provenance_hash": self.provenance_hash[:16],
        }


def extract_paragraphs(section_text: str) -> List[Paragraph]:
    """Split a section into paragraphs."""
    if not section_text:
        return []
    
    paragraphs = []
    # Split on double newlines (paragraph breaks)
    parts = re.split(r'\n\s*\n', section_text)
    
    char_offset = 0
    for i, part in enumerate(parts):
        part = part.strip()
        if not part or len(part) < 20:
            char_offset += len(part) + 2
            continue
        
        paragraphs.append(Paragraph(
            text=part,
            char_start=char_offset,
            char_end=char_offset + len(part),
            index=i,
        ))
        char_offset += len(part) + 2
    
    return paragraphs


def extract_citations(text: str) -> List[Citation]:
    """Extract citation references from text."""
    citations = []
    
    # Pattern 1: [1], [2,3], [Smith et al., 2020]
    for match in re.finditer(r'\[([^\]]{2,80})\]', text):
        content = match.group(1)
        # Check if it looks like a citation (has a number or "et al")
        if re.search(r'\d|et al|et\. al', content):
            citations.append(Citation(
                raw_text=match.group(),
                char_start=match.start(),
                char_end=match.end(),
                citation_type="bracket",
            ))
    
    # Pattern 2: (Author, 2020) or (Author et al., 2020)
    for match in re.finditer(r'\(([A-Z][a-z]+(?:\s+et\s+al\.?)?,\s*\d{4})\)', text):
        citations.append(Citation(
            raw_text=match.group(),
            char_start=match.start(),
            char_end=match.end(),
            citation_type="parenthetical",
        ))
    
    return citations


def detect_tables(text: str) -> List[Table]:
    """Detect tables in text (basic heuristic)."""
    tables = []
    
    # Look for tab-separated data or aligned columns
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        # A table row has multiple tabs or aligned columns
        if line.count('\t') >= 2 or (line.count('|') >= 2):
            table_lines = [line]
            start_char = sum(len(l) + 1 for l in lines[:i])
            
            # Collect consecutive table lines
            j = i + 1
            while j < len(lines) and (lines[j].count('\t') >= 2 or lines[j].count('|') >= 2):
                table_lines.append(lines[j])
                j += 1
            
            if len(table_lines) >= 2:  # At least 2 rows
                table_text = '\n'.join(table_lines)
                # Estimate columns
                col_count = max(line.count('\t'), line.count('|')) + 1
                tables.append(Table(
                    raw_text=table_text[:500],
                    char_start=start_char,
                    char_end=start_char + len(table_text),
                    row_count=len(table_lines),
                    col_count=col_count,
                ))
            i = j
        else:
            i += 1
    
    return tables


def extract_equations(text: str) -> List[Equation]:
    """Extract equations from text (DR-39, cycle 124).
    
    Detects:
    1. Display equations: lines that are mostly math (contain = and math symbols)
    2. Inline equations: short formula snippets within sentences
    3. Numbered equations: (1), (2), etc. at end of equation lines
    
    Target benchmark: 95% equation extraction accuracy.
    """
    equations = []
    lines = text.split('\n')
    char_offset = 0
    
    # Math symbols that indicate equation content
    math_symbols = set('=±×÷≤≥≠≈∑∏∫∂∇√αβγδεζηθλμνξπρσφψωΔΣΠΩ∞')
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            char_offset += len(line) + 1
            continue
        
        # Check if this line is a display equation
        # Heuristics:
        # 1. Contains '=' 
        # 2. Has math symbols or variables
        # 3. Is relatively short (< 200 chars)
        # 4. Doesn't start with a capital letter + space (prose)
        
        has_equals = '=' in line_stripped
        has_math = any(c in math_symbols for c in line_stripped)
        is_short = len(line_stripped) < 200
        starts_prose = bool(re.match(r'^[A-Z][a-z]+\s', line_stripped))
        has_equation_number = bool(re.search(r'\(\d+\)\s*$', line_stripped))
        
        # Display equation: has =, is short, doesn't look like prose
        if has_equals and is_short and not starts_prose:
            # Check it's not just a simple assignment like "x = 5"
            # (which might be inline, not display)
            eq_type = "display" if has_equation_number or has_math else "inline"
            
            # Filter out lines that are just URLs or file paths
            if 'http' in line_stripped or '.py' in line_stripped:
                char_offset += len(line) + 1
                continue
            
            equations.append(Equation(
                raw_text=line_stripped[:200],
                char_start=char_offset,
                char_end=char_offset + len(line_stripped),
                equation_type=eq_type,
            ))
        
        # Also catch inline equations: short math expressions in parentheses
        # e.g., "(y = mx + b)" or "(E = mc²)"
        inline_matches = re.finditer(r'\(([^)]{3,80}=[^)]{3,80})\)', line_stripped)
        for match in inline_matches:
            eq_text = match.group(1).strip()
            if any(c in math_symbols or c.isdigit() for c in eq_text):
                equations.append(Equation(
                    raw_text=eq_text[:200],
                    char_start=char_offset + match.start(),
                    char_end=char_offset + match.end(),
                    equation_type="inline",
                ))
        
        char_offset += len(line) + 1
    
    return equations


def compute_provenance_hash(text: str) -> str:
    """Compute a hash of the source content for provenance."""
    return hashlib.sha256(text.encode()).hexdigest()


def ingest_pdf(pdf_path: str, source_id: str = "") -> CanonicalDocument:
    """Ingest a PDF file into a CanonicalDocument.
    
    This is the main entry point for DR-39.
    """
    pdf_path = pathlib.Path(pdf_path)
    
    # Use existing section segmentation
    segmented = segment_pdf(str(pdf_path))
    
    # Create canonical document
    doc = CanonicalDocument(
        source_id=source_id or pdf_path.stem,
        source_type="pdf",
        title=segmented.title[:200],
        abstract=segmented.abstract,
        introduction=segmented.introduction,
        methods=segmented.methods,
        results=segmented.results,
        discussion=segmented.discussion,
        conclusions=segmented.conclusions,
        references=segmented.references,
        full_text=segmented.full_text,
        sections={s: getattr(segmented, s, "") for s in segmented.sections_found},
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
        provenance_hash=compute_provenance_hash(segmented.full_text),
        source_file=str(pdf_path),
    )
    
    # Extract paragraphs for each section
    for section_name in doc.sections:
        section_text = doc.sections[section_name]
        doc.paragraphs[section_name] = extract_paragraphs(section_text)
    
    # Extract citations from full text
    doc.citations = extract_citations(doc.full_text)
    
    # Detect tables
    doc.tables = detect_tables(doc.full_text)
    
    # Extract equations (cycle 124)
    doc.equations = extract_equations(doc.full_text)
    
    return doc


def ingest_text(text: str, source_id: str = "text_input") -> CanonicalDocument:
    """Ingest plain text into a CanonicalDocument."""
    segmented = segment_paper(text)
    
    doc = CanonicalDocument(
        source_id=source_id,
        source_type="text",
        title=segmented.title[:200],
        abstract=segmented.abstract,
        introduction=segmented.introduction,
        methods=segmented.methods,
        results=segmented.results,
        discussion=segmented.discussion,
        conclusions=segmented.conclusions,
        references=segmented.references,
        full_text=segmented.full_text,
        sections={s: getattr(segmented, s, "") for s in segmented.sections_found},
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
        provenance_hash=compute_provenance_hash(text),
    )
    
    for section_name in doc.sections:
        doc.paragraphs[section_name] = extract_paragraphs(doc.sections[section_name])
    doc.citations = extract_citations(doc.full_text)
    doc.tables = detect_tables(doc.full_text)
    doc.equations = extract_equations(doc.full_text)
    
    return doc


if __name__ == "__main__":
    # Test on available PDFs
    import glob
    
    pdfs = glob.glob("/tmp/arxiv_pdfs/*.pdf")[:3]
    for pdf_path in pdfs:
        doc = ingest_pdf(pdf_path)
        info = doc.to_dict()
        print(f"\n{info['source_id']}:")
        print(f"  Title: {info['title'][:60]}...")
        print(f"  Sections: {info['sections_found']}")
        print(f"  Body chars: {info['body_chars']}")
        print(f"  Paragraphs: {info['paragraph_count']}")
        print(f"  Citations: {info['citation_count']}")
        print(f"  Tables: {info['table_count']}")
        print(f"  Provenance hash: {info['provenance_hash']}")
