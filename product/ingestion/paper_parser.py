"""
Paper Parser — Phase 3 Step 3.

Extracts structured information from scientific paper text:
  - equations (lines containing '=' that look like mathematical formulas)
  - assumptions (lines under an 'Assumptions:' header)
  - limitations (lines under a 'Limitations:' header)
  - title, abstract, authors (when detectable)
  - provenance (when provided)

The extraction is deliberately shallow — keyword/regex based, no NLP.
This matches the PatentParser's approach. Real papers with complex
formatting (LaTeX, tables, multi-column) will need deeper parsing,
but this proves the contract works on realistic paper text.

Per the CTO directive: "Build paper_parser.py against one real paper.
One arXiv abstract, prove equations/assumptions/limitations extraction
works (even shallowly) before committing to 10-20."
"""
import re
import hashlib
from typing import Dict, Any, List


class PaperParser:
    """Extracts structured information from scientific paper text."""

    # Patterns for equation detection.
    # An equation is a line that:
    # - contains '='
    # - does NOT contain common prose patterns (is, was, were, etc.)
    # - contains at least one mathematical-looking token (variable names,
    #   subscripts, parentheses, operators)
    EQUATION_PATTERN = re.compile(
        r'^[A-Za-z_]\w*(?:\([^)]*\))?\s*[=≈≤≥<>]\s*\S+',
        re.MULTILINE
    )

    # Section headers that contain assumptions.
    ASSUMPTION_HEADERS = ['assumptions', 'assumption', 'assumed']

    # Section headers that contain limitations.
    LIMITATION_HEADERS = ['limitations', 'limitation', 'caveats', 'caveat']

    # Section headers for abstract.
    ABSTRACT_HEADERS = ['abstract', 'summary']

    def parse(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a paper text and return structured extraction.

        Args:
            d: dict with 'text' (required), 'id', 'title',
               'provenance' (optional).

        Returns:
            dict with: paper_id, title, abstract, equations, assumptions,
            limitations, materials, components, constraints, provenance,
            word_count, parse_confidence.
        """
        text = d.get("text", "")
        paper_id = d.get("id", "PAPER-" + hashlib.sha256(
            text.encode()).hexdigest()[:12].upper())

        title = d.get("title") or self._extract_title(text)
        abstract = self._extract_section(text, self.ABSTRACT_HEADERS)
        equations = self._extract_equations(text)
        assumptions = self._extract_section_items(text, self.ASSUMPTION_HEADERS)
        limitations = self._extract_section_items(text, self.LIMITATION_HEADERS)

        # Also extract materials and components (reuse keyword approach
        # from PatentParser — same vocabulary, different source).
        materials = self._extract_materials(text)
        components = self._extract_components(text)
        constraints = self._extract_constraints(text)

        result = {
            "paper_id": paper_id,
            "title": title,
            "abstract": abstract,
            "equations": equations,
            "assumptions": assumptions,
            "limitations": limitations,
            "materials": materials,
            "components": components,
            "constraints": constraints,
            "word_count": len(text.split()),
            "parse_confidence": self._confidence(text, equations, assumptions, limitations),
        }

        # Attach provenance if provided.
        if "provenance" in d:
            result["provenance"] = d["provenance"]
        else:
            result["provenance"] = {
                "source": paper_id,
                "source_type": "paper",
                "title": title,
                "extracted_by": "product.ingestion.paper_parser",
                "confidence": result["parse_confidence"],
            }

        return result

    def _extract_title(self, text: str) -> str:
        """Extract title from the first non-empty line."""
        for line in text.strip().split("\n"):
            line = line.strip()
            if line.startswith("Title:"):
                return line[6:].strip()
            if len(line) > 10 and not line.isupper():
                return line
        return "Untitled"

    def _extract_section(self, text: str, headers: List[str]) -> str:
        """Extract the text under a section header."""
        for header in headers:
            pattern = re.compile(
                rf"{header}[\s:]*\n(.*?)(?=\n[A-Z][a-z]+:|\Z)",
                re.IGNORECASE | re.DOTALL
            )
            m = pattern.search(text)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_section_items(self, text: str,
                                headers: List[str]) -> List[str]:
        """Extract list items under a section header (bullet points
        or numbered items).

        F-030 fix: stop at the first non-bullet line after the section
        header. Before the fix, the section regex captured everything
        from the header to the end of text (or the next header),
        including prose lines after the bullet points.
        """
        section_text = self._extract_section(text, headers)
        if not section_text:
            return []
        items = []
        in_bullets = False
        for line in section_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Check if this line starts with a bullet marker.
            is_bullet = bool(re.match(r"^[-*•]\s*", line)) or \
                        bool(re.match(r"^\d+\.\s*", line))
            if is_bullet:
                in_bullets = True
                # Strip bullet markers.
                line = re.sub(r"^[-*•]\s*", "", line)
                line = re.sub(r"^\d+\.\s*", "", line)
                if len(line) > 5:
                    items.append(line)
            elif in_bullets:
                # F-030 fix: we were in bullets, and this line is NOT
                # a bullet — it's prose after the bullet points. Stop.
                break
            elif len(line) > 5:
                # Lines before any bullets — could be section intro text.
                # Include them (they might be meaningful context).
                items.append(line)
        return items

    def _extract_equations(self, text: str) -> List[str]:
        """Extract lines that look like mathematical equations.

        F-030 fix: handle inline equations (prose lead-in followed
        by equation). Before the fix, lines containing prose indicators
        like ' is ' were skipped entirely — missing equations like
        'The cooling power is P_cool = P_rad - P_atm'.
        """
        equations = []
        for line in text.split("\n"):
            line = line.strip()
            if not line or len(line) > 200:
                continue
            # Must contain '=' or '≈'.
            if "=" not in line and "≈" not in line:
                continue
            # Must have at least one mathematical-looking token.
            has_math = bool(re.search(
                r"[A-Za-z_]\w*\s*[({]", line  # variable followed by ( or {
            )) or bool(re.search(r"[+\-*/^]", line))  # operators
            if not has_math:
                continue
            # F-030 fix: if the line has a prose lead-in (contains
            # ' is ', ' was ', etc. before the '='), extract just the
            # equation part — the substring from the variable name
            # before '=' to the end of the line.
            lower = line.lower()
            eq_pos = line.find("=")
            if eq_pos < 0:
                eq_pos = line.find("≈")
            # Look backwards from '=' for a variable-like token.
            before_eq = line[:eq_pos]
            # Find the last variable-like token before '='.
            var_match = re.search(
                r"([A-Za-z_]\w*(?:\([^)]*\))?)\s*$", before_eq)
            if var_match:
                # Check if there's prose before the variable.
                prose_before = before_eq[:var_match.start()].lower().strip()
                prose_indicators = [" is ", " was ", " were ", " are ",
                                   " means ", " equals ", " represents ",
                                   "given by", "given as", "defined as",
                                   "computed as", "calculated as"]
                has_prose_lead = any(ind in prose_before
                                     for ind in prose_indicators)
                if has_prose_lead:
                    # Extract just the equation part (variable = rest).
                    equation = line[var_match.start():].strip()
                    equations.append(equation)
                else:
                    # No prose lead — the whole line is the equation.
                    equations.append(line)
            else:
                equations.append(line)
        return equations

    def _extract_materials(self, text: str) -> List[str]:
        """Extract material keywords from text (same as PatentParser)."""
        ms = ['polymer', 'ceramic', 'metal', 'alloy', 'composite',
              'silicon', 'graphene', 'carbon', 'titanium', 'aluminum',
              'steel', 'copper', 'glass', 'membrane', 'substrate',
              'semiconductor', 'silver']
        tl = text.lower()
        return [m for m in ms if m in tl]

    def _extract_components(self, text: str) -> List[str]:
        """Extract component keywords from text.

        Phase 5.C (per auditor's V4 finding on F-038): expanded the
        keyword list with scientific vocabulary grounded in the actual
        arXiv abstracts ingested in Phase 5.B. The previous list was
        patent-oriented (pump, sensor, coating, etc.) and missed
        scientific component vocabulary that arXiv papers use
        (sorbent, metamaterial, electrolyte, anode, cathode). This
        expansion is a DATA modification, not an architectural one —
        the auditor explicitly authorized it as a fix for F-038.

        Terms were selected by:
        1. Scanning all 10 arXiv abstracts ingested in Phase 5.B for
           candidate component vocabulary.
        2. Filtering to terms that appear in 1+ papers AND are
           actually components (not materials, not principles, not
           generic words like 'cell' or 'ion').
        3. Excluding terms with high false-positive risk (e.g., 'mof'
           would match 'monolithic' as a substring; 'cell' would
           match 'cellular').

        Per F-001 lesson: keyword matching that works on fixtures but
        not real text is the failure mode this expansion is designed
        to fix. The expansion is grounded in real arXiv text, not
        speculative vocabulary.
        """
        # Original patent-oriented component vocabulary (Phase 3 Step 3).
        cks = ['pump', 'sensor', 'coating', 'membrane', 'exchanger',
               'substrate', 'valve', 'motor', 'circuit', 'electrode',
               'battery', 'panel', 'filter', 'chamber', 'nozzle',
               'actuator', 'controller',
               # Phase 5.C additions — scientific component vocabulary
               # grounded in actual arXiv abstracts. Each term verified
               # to appear in at least 1 of the 10 Phase 5.B papers.
               'anode',           # battery papers — anode component
               'cathode',         # battery papers — cathode component
               'electrolyte',    # battery papers — electrolyte component
               'sorbent',          # AWH + DAC papers — sorbent material/component
               'metamaterial',   # radiative cooling papers — structural component
               'adsorbent',       # AWH + DAC papers — adsorbent material
               'charger',         # EV-charging papers — charging component
               'metal-organic framework',  # multi-word, no false-positive risk
               ]
        tl = text.lower()
        return [c for c in cks if c in tl]

    def _extract_constraints(self, text: str) -> Dict[str, str]:
        """Extract constraint keywords (same as PatentParser)."""
        cm = {
            'energy': ['power', 'energy', 'watt', 'voltage'],
            'temperature': ['temperature', 'thermal', 'heat', 'cooling'],
            'size': ['dimension', 'size', 'volume', 'weight'],
            'cost': ['cost', 'price', 'expense'],
            'safety': ['safety', 'toxic', 'hazard'],
            'manufacturing': ['manufactur', 'fabricat', 'production',
                              'deposition', 'sintering'],
        }
        tl = text.lower()
        return {c: 'present' for c, ks in cm.items()
                if any(k in tl for k in ks)}

    def _confidence(self, text: str, equations: List[str],
                    assumptions: List[str],
                    limitations: List[str]) -> float:
        """Compute a parse confidence score."""
        score = 0.0
        if len(text) > 200:
            score += 0.2
        if len(text) > 500:
            score += 0.2
        if equations:
            score += 0.2
        if assumptions:
            score += 0.2
        if limitations:
            score += 0.2
        return min(score, 1.0)
