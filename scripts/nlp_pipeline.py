#!/usr/bin/env python3
"""
nlp_pipeline.py — Generation 2-3: spaCy-based entity and relation extraction.

Per CEO 6-generation plan:
  Gen 2: Move from strings to objects (entity extraction with NER)
  Gen 3: Move from regex to dependency-graph-based relation extraction

This module replaces the regex-based EdgeExtractor with a spaCy NLP pipeline
that:
  1. Extracts entities with types (material, mechanism, property, application)
  2. Extracts relations using dependency parsing (not regex)
  3. Assigns confidence scores to each relation
  4. Builds a canonical document representation

The key architectural change (per CEO):
  DO NOT BUILD:  regexes → knowledge graph
  BUILD:         documents → structure → entities → relations → mechanisms

Target benchmarks:
  Entity recall: 95%, precision: 95%, linking: 90%
  Relation F1: 90%, precision: 95%, recall: 90%
"""
import sys
import json
import re
import pathlib
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field

# spaCy is the foundation for Gen 2-3
import spacy
from spacy.tokens import Doc, Span


# ---------------------------------------------------------------------------
# Entity type mapping — map spaCy entity types to TEE canonical types
# ---------------------------------------------------------------------------

ENTITY_TYPE_MAP = {
    # Materials
    "CHEMICAL": "material",
    "MATERIAL": "material",
    "PRODUCT": "material",
    # Mechanisms
    "PROCESS": "mechanism",
    "EVENT": "mechanism",
    # Properties
    "QUANTITY": "property",
    "MEASUREMENT": "property",
    # Applications
    "ORG": "application",
    "PRODUCT": "application",
    # General
    "CONCEPT": "concept",
    "ENTITY": "entity",
}

# Scientific entity patterns (supplement spaCy NER for domain-specific terms)
# Per cycle 101: refined to reduce false positives. The previous patterns
# were too broad (matching "for", "with", "the" as materials).
SCIENTIFIC_PATTERNS = {
    "material": [
        # Material names (specific, not single common words)
        r"\b(?:graphene\s+oxide|carbon\s+nanotube|silicon\s+wafer|PVDF|PDMS|hydroxyapatite|hydrogel|nanofiber\s+membrane|composite\s+material|biomaterial|biopolymer|elastomer)\b",
        # Biological materials (multi-word or specific)
        r"\b(?:spider\s+silk|hagfish\s+slime|chiton\s+radula|pitcher\s+plant|lotus\s+leaf|bone\s+tissue|blood[\s-]brain\s+barrier)\b",
        # Chemical formulas (must have at least 2 elements or a number)
        r"\b(?:[A-Z][a-z]?[0-9]+){2,}\b",
        r"\b[A-Z][a-z]?[A-Z][a-z]?[0-9]*\b",
    ],
    "mechanism": [
        r"\b(?:oxidation|reduction|diffusion|adsorption|desorption|crystallization|nucleation|polymerization|crosslinking|biomineralization|precipitation|catalysis|electrospinning|selective\s+permeability|controlled\s+release)\b",
        r"\b(?:phase\s+transition|energy\s+dissipation|charge\s+transport|ion\s+transport|electron\s+transfer|heat\s+transfer)\b",
    ],
    "property": [
        r"\b(?:thermal\s+conductivity|electrical\s+conductivity|tensile\s+strength|fracture\s+toughness|contact\s+angle|surface\s+tension|porosity|permeability|viscosity|density|hardness|elasticity)\b",
        r"\b\d+(?:\.\d+)?\s*(?:nm|μm|mm|cm|m|kg|g|mg|°C|K|Pa|kPa|MPa|GPa|V|W|J|mol|M|Hz|kHz|MHz|GHz)\b",
    ],
    "application": [
        r"\b(?:lithium[\s-]ion\s+battery|fuel\s+cell|solar\s+cell|drug\s+delivery|tissue\s+engineering|water\s+filtration|desalination|self[\s-]healing\s+concrete|magnetic\s+storage|data\s+storage)\b",
    ],
}

# Stopwords to exclude from entity matching
ENTITY_STOPWORDS = {
    "the", "a", "an", "for", "with", "and", "or", "but", "in", "on", "at",
    "to", "of", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "they", "them",
    "while", "which", "who", "whom", "whose", "what", "where", "when",
    "how", "why", "from", "by", "as", "into", "through", "during",
    "before", "after", "above", "below", "up", "down", "out", "off",
    "over", "under", "again", "further", "then", "once",
    # Cycle 107: extended with common English words that SciSpacy extracts
    # as entities but are not scientific concepts.
    "all", "can", "more", "such", "some", "main", "area", "low", "high",
    "well", "set", "few", "not", "no", "yes", "only", "very", "just",
    "also", "than", "too", "most", "other", "many", "much", "any",
    "each", "both", "same", "different", "new", "old", "first", "last",
    "next", "previous", "one", "two", "three", "four", "five",
    "samples", "sample", "study", "studies", "research", "work",
    "results", "result", "data", "method", "methods", "approach",
    "system", "systems", "process", "processes", "effect", "effects",
    "change", "changes", "increase", "decrease", "reduction", "reducing",
    "addition", "removal", "presence", "absence", "formation",
    "determine", "determined", "obtained", "observed", "measured",
    "recorded", "detected", "reported", "shown", "found", "given",
    "based", "using", "used", "use", "uses", "allow", "allows",
    "enable", "enables", "enabled", "leading", "lead", "leads",
    "provide", "provides", "provided", "require", "requires",
    "include", "includes", "included", "involving", "involve",
    "involved", "consisting", "consist", "consists",
    "project", "prevent", "prevents", "prevented",
    "however", "therefore", "moreover", "furthermore", "nevertheless",
    "accordingly", "consequently", "thus", "hence", "whereas",
    "although", "though", "despite", "regardless",
    "figure", "fig", "table", "equation", "eq", "section",
    "abstract", "introduction", "conclusion", "references",
    "author", "authors", "et", "al",
    # Common verbs that are not mechanisms
    "show", "shown", "showed", "demonstrate", "demonstrated",
    "reveal", "revealed", "indicate", "indicated", "suggest",
    "suggested", "confirm", "confirmed", "support", "supported",
    "exhibit", "exhibited", "display", "displayed",
    # Common adjectives that are not properties
    "significant", "significantly", "remarkable", "remarkably",
    "excellent", "good", "bad", "poor", "great", "small", "large",
    "big", "tiny", "huge", "wide", "narrow", "thin", "thick",
    "fast", "slow", "rapid", "quick", "stable", "unstable",
    # Common nouns that are not scientific entities
    "time", "times", "way", "ways", "case", "cases", "part", "parts",
    "type", "types", "kind", "kinds", "form", "forms", "number",
    "numbers", "value", "values", "level", "levels", "rate", "rates",
    "range", "ranges", "point", "points", "line", "lines", "side",
    "sides", "end", "ends", "top", "bottom", "middle", "center",
    "left", "right", "front", "back", "inside", "outside",
    # Cycle 108: additional noise words that pass POS filter but aren't scientific
    "does", "due", "even", "find", "full", "give", "had", "hand",
    "has", "hours", "details", "contract", "development", "dry",
    "experiments", "experimental_conditions", "homogenization",
    "gold", "air",  # too generic without context
    "materials",  # section header, not an entity
    "purchased",  # verb form tagged as noun
    "diameters",  # generic property, not a specific material
    "nanoparticles",  # too generic without qualifier
    # Cycle 109: lab methodology terms shared across all wet-lab papers.
    # These are NOT domain-specific mechanisms — they're experimental
    # vocabulary that any lab paper uses. Removing them ensures shared
    # entities are domain-specific scientific concepts, not lab protocols.
    "room_temperature", "supernatant", "surfaces", "treatment",
    "preparation", "statistical_analysis", "parameters", "hour",
    "influence", "investigation", "kept", "locations", "non",
    "our", "per", "see", "situ", "turn", "uniformity", "usa",
    "version", "volume", "rpm", "pure", "rpm",
    # Lab equipment and supplies (shared across all labs)
    "sigma-aldrich", "sigma_aldrich", "merck", "fisher",
    "corning", "vwr", "beckman", "eppendorf",
    # Lab procedures (shared across all wet-lab papers)
    "centrifugation", "centrifuge", "sonication", "sonicator",
    "incubation", "incubator", "washing", "rinsing",
    "sterilization", "autoclaving", "filtering", "drying",
    "mixing", "stirring", "heating", "cooling",
    "characterization", "characterized", "analyzed", "measured",
    "calculated", "estimated", "determined", "evaluated",
    "assessed", "examined", "investigated", "studied",
    # Statistical terms (shared across all quantitative papers)
    "mean", "average", "median", "standard_deviation",
    "standard_error", "confidence_interval", "p-value", "p_value",
    "correlation", "regression", "anova", "t-test", "t_test",
    "significance", "significant_difference",
    # Measurement units (shared across all papers)
    "nm", "μm", "mm", "cm", "ml", "μl", "l", "mg", "μg", "g",
    "kg", "hz", "khz", "mhz", "ghz", "pa", "kpa", "mpa", "gpa",
    "v", "mv", "w", "mw", "j", "kj", "mol", "mmol", "μm",
    # Paper structure words
    "scheme", "schemes", "step", "steps", "procedure", "procedures",
    "protocol", "protocols", "setup", "setup", "configuration",
    "framework", "model", "models", "simulation", "simulations",
    # Cycle 109: remaining generic terms
    "temperature", "pressure", "concentration", "weight",
}


@dataclass
class ExtractedEntity:
    """A canonical entity object (Gen 2 target)."""
    text: str
    label: str  # canonical type: material, mechanism, property, application
    start: int
    end: int
    confidence: float
    aliases: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedRelation:
    """A canonical relation object (Gen 3 target)."""
    subject: ExtractedEntity
    relation: str  # e.g., "improves", "causes", "enables"
    obj: ExtractedEntity
    confidence: float
    source_sentence: str
    dependency_path: List[str]  # the dependency graph path connecting subject→object


@dataclass
class CanonicalDocument:
    """The canonical document representation (Gen 1 output → Gen 2-3 input)."""
    text: str
    entities: List[ExtractedEntity] = field(default_factory=list)
    relations: List[ExtractedRelation] = field(default_factory=list)
    sections: Dict[str, str] = field(default_factory=dict)
    equations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class NLPPipeline:
    """spaCy-based NLP pipeline for entity and relation extraction.
    
    This replaces the regex-based EdgeExtractor with a dependency-graph-
    based approach that scales to arbitrary text.
    
    Per cycle 103: upgraded with:
    1. SciSpacy for scientific NER (filters ORG/PERSON/GPE)
    2. String-matching coreference resolution (connects per-sentence relations)
    """
    
    def __init__(self, model_name: str = "en_core_sci_sm"):
        """Initialize the spaCy NLP pipeline.
        
        Per cycle 103: uses SciSpacy (en_core_sci_sm) by default for
        scientific domain NER. Falls back to en_core_web_sm if unavailable.
        """
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            # Fallback to general model if SciSpacy not available
            self.nlp = spacy.load("en_core_web_sm")
        self._compile_patterns()
        self._entity_aliases = {}  # coreference: canonical name → aliases
    
    def _resolve_coreference(self, doc: Doc, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Resolve coreference using string matching (cycle 103).
        
        Per auditor cycle 102: the Gen 4 gap is coreference resolution.
        Per-sentence relations are isolated pairs; the chain builder can't
        connect "nanofibers" in sentence 1 with "nanofibers" in sentence 2
        without knowing they're the same entity.
        
        This implementation uses string matching: if two entities have the
        same text (or one is a substring of the other), they are the same
        entity. This is simpler than neural coref but effective for
        scientific text where entity names are consistent.
        
        The key output: merged entities with aliases, so the chain builder
        can connect relations across sentences.
        """
        # Group entities by normalized text (lowercase, no articles)
        by_normalized = {}
        for ent in entities:
            normalized = ent.text.lower().strip()
            # Remove common articles/prepositions
            normalized = re.sub(r'^(the|a|an)\s+', '', normalized)
            
            if normalized in by_normalized:
                # Merge: keep the one with highest confidence, add alias
                existing = by_normalized[normalized]
                if ent.confidence > existing.confidence:
                    by_normalized[normalized] = ent
                    ent.aliases = existing.aliases + [existing.text]
                else:
                    existing.aliases.append(ent.text)
            else:
                by_normalized[normalized] = ent
        
        # Also check for substring matches (e.g., "nanofiber" matches "nanofiber membrane")
        merged = list(by_normalized.values())
        final = []
        used = set()
        
        for i, ent in enumerate(merged):
            if i in used:
                continue
            ent_normalized = ent.text.lower().strip()
            
            for j, other in enumerate(merged[i+1:], i+1):
                if j in used:
                    continue
                other_normalized = other.text.lower().strip()
                
                # Check if one is a substring of the other (and both are >3 chars)
                if (len(ent_normalized) > 3 and len(other_normalized) > 3 and
                    (ent_normalized in other_normalized or other_normalized in ent_normalized)):
                    # Merge: keep the longer one (more specific), add shorter as alias
                    if len(other.text) > len(ent.text):
                        other.aliases.append(ent.text)
                        final.append(other)
                        used.add(j)
                        used.add(i)
                    else:
                        ent.aliases.append(other.text)
                        final.append(ent)
                        used.add(i)
                        used.add(j)
                    break
            else:
                final.append(ent)
                used.add(i)
        
        return final
    
    def _compile_patterns(self):
        """Compile scientific entity patterns for supplementary NER."""
        self.compiled_patterns = {}
        for entity_type, patterns in SCIENTIFIC_PATTERNS.items():
            self.compiled_patterns[entity_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract entities from text using spaCy NER + scientific patterns.
        
        Gen 2 target: move from strings to objects.
        Per cycle 103: uses SciSpacy + coreference resolution.
        """
        doc = self.nlp(text)
        entities = []
        seen_spans = set()
        
        # 1. spaCy NER (general entities)
        for ent in doc.ents:
            # Per cycle 107: filter generic English words from SciSpacy output.
            ent_text_lower = ent.text.lower().strip()
            # Per cycle 109: also check underscore version (entity IDs use
            # underscores, but entity text uses spaces). Check both formats.
            ent_text_underscore = ent_text_lower.replace(" ", "_")
            if ent_text_lower in ENTITY_STOPWORDS or ent_text_underscore in ENTITY_STOPWORDS:
                continue
            # Skip single words that are too short (< 4 chars) and not chemical formulas
            if len(ent_text_lower) < 4 and not re.match(r'^[A-Z][a-z]?[0-9]', ent.text):
                continue
            
            # Per cycle 108: POS-tag filtering. Only accept entities whose
            # root token is a noun (NOUN) or proper noun (PROPN). Reject
            # verbs (VERB), adjectives (ADJ), adverbs (ADV), etc.
            # This removes "does", "due", "acknowledge", "charged" etc.
            # that passed the stopword filter but are not nouns.
            root_token = ent.root
            if root_token.pos_ not in ("NOUN", "PROPN", "X"):
                # "X" allows unknown POS (some scientific terms)
                continue
            # Also check: if the entity is multi-word, at least one token
            # should be a noun (e.g., "spherical gold" — "gold" is a noun)
            if len(ent) > 1:
                has_noun = any(t.pos_ in ("NOUN", "PROPN") for t in ent)
                if not has_noun:
                    continue
            
            # With SciSpacy, entities are labeled "ENTITY" (scientific)
            # With en_core_web_sm, they're labeled ORG/PERSON/GPE/etc.
            # Map both to canonical types
            canonical_type = ENTITY_TYPE_MAP.get(ent.label_, "entity")
            # Per cycle 103: with SciSpacy, all entities are scientific.
            # Classify them by pattern matching.
            if ent.label_ == "ENTITY":
                # Try to classify using scientific patterns
                ent_text_lower = ent.text.lower()
                classified = False
                for entity_type, patterns in self.compiled_patterns.items():
                    for pattern in patterns:
                        if pattern.search(ent_text_lower):
                            canonical_type = entity_type
                            classified = True
                            break
                    if classified:
                        break
                if not classified:
                    # Default SciSpacy entities to "material" (most common in science)
                    canonical_type = "material"
            
            entity = ExtractedEntity(
                text=ent.text,
                label=canonical_type,
                start=ent.start_char,
                end=ent.end_char,
                confidence=0.8,  # spaCy NER confidence (placeholder)
            )
            entities.append(entity)
            seen_spans.add((ent.start_char, ent.end_char))
        
        # 2. Scientific pattern matching (domain-specific entities)
        for entity_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    start, end = match.span()
                    match_text = match.group()
                    # Skip stopwords and very short matches
                    if match_text.lower().strip() in ENTITY_STOPWORDS:
                        continue
                    if len(match_text) < 3:
                        continue
                    # Skip if this span overlaps with a spaCy entity
                    if any(s <= start < e or s < end <= e for s, e in seen_spans):
                        continue
                    entity = ExtractedEntity(
                        text=match_text,
                        label=entity_type,
                        start=start,
                        end=end,
                        confidence=0.7,  # pattern match (lower than NER)
                    )
                    entities.append(entity)
                    seen_spans.add((start, end))
        
        # 3. Coreference resolution (cycle 103)
        # Merge entities that refer to the same thing across sentences
        entities = self._resolve_coreference(doc, entities)
        
        return entities
    
    def extract_relations(self, text: str, entities: List[ExtractedEntity]) -> List[ExtractedRelation]:
        """Extract relations using dependency parsing.
        
        Gen 3 target: move from regex to dependency-graph-based extraction.
        
        The approach:
        1. Parse the text with spaCy dependency parser
        2. For each sentence, find entity pairs
        3. Find the dependency path connecting them
        4. Extract the relation verb from the path
        5. Assign confidence based on path length and verb specificity
        """
        doc = self.nlp(text)
        relations = []
        
        # Create a lookup from character offset to entity
        ent_by_pos = {}
        for ent in entities:
            for pos in range(ent.start, ent.end):
                ent_by_pos[pos] = ent
        
        for sent in doc.sents:
            # Find entities in this sentence
            sent_entities = []
            for ent in entities:
                if ent.start >= sent.start_char and ent.end <= sent.end_char:
                    sent_entities.append(ent)
            
            # For each pair of entities in the sentence, find the relation.
            # Per cycle 101: only extract relations between entities of
            # different types (material→mechanism, mechanism→property, etc.)
            # to reduce false positives. Same-type pairs are usually noise.
            for i, subj in enumerate(sent_entities):
                for obj in sent_entities[i+1:]:
                    # Skip same-type pairs (material→material is usually noise)
                    if subj.label == obj.label:
                        continue
                    # Skip if either entity is generic "entity" type
                    if subj.label == "entity" or obj.label == "entity":
                        continue
                    relation = self._find_relation(subj, obj, sent, doc)
                    if relation:
                        relations.append(relation)
        
        return relations
    
    def _find_relation(self, subj: ExtractedEntity, obj: ExtractedEntity,
                       sent: Span, doc: Doc) -> Optional[ExtractedRelation]:
        """Find the relation between two entities using dependency parsing.
        
        The relation verb is the lowest common ancestor of the two entities
        in the dependency tree.
        """
        # Find the token spans for subject and object
        subj_tokens = [t for t in sent if subj.start <= t.idx < subj.end]
        obj_tokens = [t for t in sent if obj.start <= t.idx < obj.end]
        
        if not subj_tokens or not obj_tokens:
            return None
        
        # Find the lowest common ancestor (LCA) in the dependency tree
        subj_head = subj_tokens[0].head
        obj_head = obj_tokens[0].head
        
        # Walk up the dependency tree to find LCA
        subj_ancestors = list(subj_head.ancestors) + [subj_head]
        obj_ancestors = list(obj_head.ancestors) + [obj_head]
        
        lca = None
        for sa in subj_ancestors:
            for oa in obj_ancestors:
                if sa == oa:
                    lca = sa
                    break
            if lca:
                break
        
        if not lca:
            return None
        
        # The relation is the LCA verb (or its head if it's not a verb)
        relation_token = lca
        if relation_token.pos_ not in ("VERB", "AUX", "NOUN"):
            # Find the nearest verb ancestor
            for ancestor in [lca] + list(lca.ancestors):
                if ancestor.pos_ in ("VERB", "AUX"):
                    relation_token = ancestor
                    break
        
        relation_text = relation_token.lemma_.lower()
        
        # Skip trivial relations
        if relation_text in ("be", "have", "do", "make", "use", "show"):
            return None
        
        # Per cycle 103: skip citation/metadata relations
        # These come from "X Wang · 2016 · Cited by 347" being parsed as entities
        citation_patterns = {"cite", "cited", "wang", "author", "year", "et", "al"}
        if relation_text in citation_patterns:
            return None
        # Skip if either entity text contains citation metadata
        citation_indicators = ["·", "cited by", "et al", "wang", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"]
        for indicator in citation_indicators:
            if indicator in subj.text.lower() or indicator in obj.text.lower():
                return None
        # Skip entities that are just numbers or years
        if re.match(r'^\d{4}$', subj.text) or re.match(r'^\d{4}$', obj.text):
            return None
        # Skip very long entities (usually parsed metadata, not real entities)
        if len(subj.text) > 50 or len(obj.text) > 50:
            return None
        
        # Build the dependency path
        path = []
        for token in subj_tokens:
            path.append(f"{token.text}({token.dep_})")
        path.append(f"→ {relation_token.text}({relation_token.dep_}) ←")
        for token in obj_tokens:
            path.append(f"{token.text}({token.dep_})")
        
        # Confidence: shorter paths = higher confidence
        path_length = abs(subj_head.i - relation_token.i) + abs(obj_head.i - relation_token.i)
        confidence = max(0.5, 1.0 - (path_length * 0.1))
        
        return ExtractedRelation(
            subject=subj,
            relation=relation_text,
            obj=obj,
            confidence=round(confidence, 2),
            source_sentence=sent.text,
            dependency_path=path,
        )
    
    def process_document(self, text: str) -> CanonicalDocument:
        """Process a document through the full Gen 2-3 pipeline.
        
        documents → structure → entities → relations
        """
        entities = self.extract_entities(text)
        relations = self.extract_relations(text, entities)
        
        return CanonicalDocument(
            text=text,
            entities=entities,
            relations=relations,
            sections={"full_text": text},
        )
    
    def process_to_graph(self, text: str) -> Dict:
        """Process text and return a graph-compatible structure.
        
        This is the interface to the existing CausalGraph system.
        Per cycle 104: entity names are cleaned (whitespace → underscores)
        to ensure the chain builder can match entities across sentences.
        Per cycle 110: entity linking via canonical forms — entities with
        shared core terms are linked (e.g., "permeability" and
        "membrane_permeability" both canonicalize to "permeability").
        """
        doc = self.process_document(text)
        
        # Build entity linking map: raw entity ID → canonical ID
        # Canonical form: the shortest entity that contains the core term.
        # E.g., "membrane_permeability" → "permeability" (core term)
        #       "permeability_values" → "permeability" (core term)
        #       "lower_permeability" → "permeability" (core term)
        entity_link_map = {}
        all_entity_ids = []
        
        for ent in doc.entities:
            clean_id = re.sub(r'\s+', '_', ent.text.strip()).lower()
            all_entity_ids.append(clean_id)
        
        # Build canonical forms: for each entity, find its canonical form
        # by stripping common prefixes/suffixes to get the core term.
        # Per cycle 110: this is cross-paper entity linking. The canonical
        # form is the core term, even if it doesn't exist as a standalone
        # entity in this paper. E.g., "membrane_permeability" → "permeability"
        # even if "permeability" alone wasn't extracted.
        for eid in all_entity_ids:
            canonical = eid
            # Remove common modifiers (strip prefixes)
            for prefix in ["lower_", "higher_", "zero_", "physical_", "membrane_",
                          "water_", "surface_", "thermal_", "electrical_",
                          "ionic_", "bulk_", "intrinsic_", "apparent_"]:
                if eid.startswith(prefix):
                    remainder = eid[len(prefix):]
                    if len(remainder) >= 4:
                        canonical = remainder
                        break
            # Remove common suffixes
            for suffix in ["_values", "_p", "_size", "_sizes", "_spaces", "_with",
                          "_measurements", "_measurement", "_constant", "_level",
                          "_levels", "_ratio", "_index"]:
                if eid.endswith(suffix) and canonical.endswith(suffix):
                    remainder = canonical[:-len(suffix)]
                    if len(remainder) >= 4:
                        canonical = remainder
                        break
            entity_link_map[eid] = canonical
        
        # Build nodes using canonical IDs (deduplicate)
        seen_canonical = set()
        nodes = []
        for ent in doc.entities:
            clean_id = re.sub(r'\s+', '_', ent.text.strip()).lower()
            canonical = entity_link_map.get(clean_id, clean_id)
            if canonical in seen_canonical:
                continue
            seen_canonical.add(canonical)
            nodes.append({
                "node_id": canonical,
                "node_type": ent.label,
                "label": ent.text,
                "confidence": ent.confidence,
            })
        
        # Build edges using canonical IDs
        edges = []
        for rel in doc.relations:
            clean_source = re.sub(r'\s+', '_', rel.subject.text.strip()).lower()
            clean_target = re.sub(r'\s+', '_', rel.obj.text.strip()).lower()
            canonical_source = entity_link_map.get(clean_source, clean_source)
            canonical_target = entity_link_map.get(clean_target, clean_target)
            edges.append({
                "source": canonical_source,
                "target": canonical_target,
                "direction": "causes",
                "mechanism": rel.relation,
                "confidence": rel.confidence,
                "source_sentence": rel.source_sentence,
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "entity_count": len(nodes),
            "relation_count": len(edges),
            "pipeline": "nlp_v2_spaCy",
            "entity_linking_applied": True,
        }


if __name__ == "__main__":
    # Test the pipeline on a sample text
    pipeline = NLPPipeline()
    
    test_text = """
    Graphene oxide membranes exhibit selective permeability for water molecules.
    The nanoporous structure enables rapid water transport while blocking ions.
    Electrospinning produces nanofiber membranes with controlled pore size.
    The pore size governs the selective permeability of the membrane.
    """
    
    result = pipeline.process_to_graph(test_text)
    
    print("=== NLP Pipeline Test ===")
    print(f"Entities: {result['entity_count']}")
    for node in result["nodes"]:
        print(f"  {node['node_type']:12s} {node['label']:30s} (conf={node['confidence']})")
    
    print(f"\nRelations: {result['relation_count']}")
    for edge in result["edges"]:
        print(f"  {edge['source']:25s} --{edge['mechanism']:15s}--> {edge['target']:25s} (conf={edge['confidence']})")
