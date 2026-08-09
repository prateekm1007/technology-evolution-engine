#!/usr/bin/env python3
"""extractor.py — GLiREL relation extraction wrapper.

Wraps GLiREL's predict_relations() and normalizes output to the
evidence-graph schema (extraction_schema.json).

Does NOT make B-2 adjudication decisions. This is extraction only.
"""
import json
import time
from dataclasses import dataclass, asdict
from typing import Optional
from span_mapper import CharSpan, token_positions_to_char_spans, verify_span


@dataclass
class EvidenceEdge:
    """A single evidence edge extracted by GLiREL."""
    source_id: str
    document_id: str
    head_text: str
    head_start: int
    head_end: int
    relation: str
    tail_text: str
    tail_start: int
    tail_end: int
    model_score: float
    model_identifier: str
    threshold: float
    top_k: int
    ner_source: str

    def to_dict(self) -> dict:
        return asdict(self)

    def verify_spans(self, source_text: str) -> bool:
        """Verify both head and tail spans."""
        return (verify_span(self.head_text, self.head_start, self.head_end, source_text)
                and verify_span(self.tail_text, self.tail_start, self.tail_end, source_text))


class GLiRELExtractor:
    """Wraps GLiREL model for relation extraction with span verification."""

    def __init__(self, model_identifier: str, model=None, tokenizer=None):
        self.model_identifier = model_identifier
        self.model = model
        self.tokenizer = tokenizer
        self._load_time = None

    @classmethod
    def from_pretrained(cls, model_identifier: str = "jackboyla/glirel_beta"):
        """Load GLiREL model from HuggingFace."""
        from glirel import GLiREL
        import time
        t0 = time.time()
        model = GLiREL.from_pretrained(model_identifier)
        t1 = time.time()
        instance = cls(model_identifier, model)
        instance._load_time = t1 - t0
        # Get tokenizer from model
        if hasattr(model, 'tokenizer'):
            instance.tokenizer = model.tokenizer
        elif hasattr(model, 'enc'):
            instance.tokenizer = getattr(model.enc, 'tokenizer', None)
        return instance

    def extract_relations(
        self,
        source_id: str,
        source_text: str,
        entity_list: list,
        relation_labels: list,
        threshold: float = 0.0,
        top_k: int = 5,
        ner_source: str = "controlled",
    ) -> list:
        """Extract relations from source_text given entities and relation labels.

        Args:
            source_id: "A" or "B"
            source_text: the source text
            entity_list: list of {label, text, start, end} dicts (NER output)
            relation_labels: list of relation label strings to query
            threshold: minimum score threshold
            top_k: max relations to return
            ner_source: where entities came from ("controlled", "gliner", "spacy")

        Returns:
            list of EvidenceEdge objects (only spans that pass verification)
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        # GLiREL expects entity_list with 'label' and 'text' and position info
        # The exact format depends on GLiREL version; we normalize here
        glirel_entities = []
        for ent in entity_list:
            glirel_entities.append({
                "label": ent.get("label", "ENTITY"),
                "text": ent["text"],
                "start": ent["start"],
                "end": ent["end"],
            })

        # Run GLiREL
        t0 = time.time()
        try:
            raw_relations = self.model.predict_relations(
                source_text,
                labels=relation_labels,
                threshold=threshold,
                top_k=top_k,
                entity_list=glirel_entities,
            )
        except Exception as e:
            print(f"GLiREL predict_relations error: {e}")
            raw_relations = []
        t1 = time.time()
        self._last_inference_time = t1 - t0

        # Normalize to EvidenceEdge
        edges = []
        for rel in raw_relations:
            # GLiREL output format varies; handle common patterns
            head_text = rel.get("head_text", rel.get("head", {}).get("text", ""))
            tail_text = rel.get("tail_text", rel.get("tail", {}).get("text", ""))
            relation = rel.get("label", rel.get("relation", ""))
            score = rel.get("score", 0.0)

            # Get spans from entity_list (GLiREL returns text, we match to entities)
            head_span = self._find_entity_span(head_text, entity_list, source_text)
            tail_span = self._find_entity_span(tail_text, entity_list, source_text)

            if head_span is None or tail_span is None:
                # Skip if we can't find the span
                continue

            edge = EvidenceEdge(
                source_id=source_id,
                document_id=f"source_{source_id}",
                head_text=head_span.text,
                head_start=head_span.start,
                head_end=head_span.end,
                relation=relation,
                tail_text=tail_span.text,
                tail_start=tail_span.start,
                tail_end=tail_span.end,
                model_score=float(score),
                model_identifier=self.model_identifier,
                threshold=threshold,
                top_k=top_k,
                ner_source=ner_source,
            )

            # Verify spans
            if edge.verify_spans(source_text):
                edges.append(edge)
            # else: skip invalid spans

        return edges

    def _find_entity_span(self, text: str, entity_list: list, source_text: str) -> Optional[CharSpan]:
        """Find the character span for an entity text in the entity_list."""
        # First, try exact match in entity_list
        for ent in entity_list:
            if ent["text"] == text:
                return CharSpan(text=ent["text"], start=ent["start"], end=ent["end"])

        # Fallback: find in source_text
        idx = source_text.find(text)
        if idx >= 0:
            return CharSpan(text=text, start=idx, end=idx + len(text))

        return None

    def get_model_info(self) -> dict:
        """Return model metadata."""
        import torch
        info = {
            "model_identifier": self.model_identifier,
            "load_time_seconds": self._load_time,
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
        }
        if torch.cuda.is_available():
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["gpu_vram_total"] = torch.cuda.get_device_properties(0).total_memory
            info["gpu_memory_allocated"] = torch.cuda.memory_allocated()
            info["gpu_memory_reserved"] = torch.cuda.memory_reserved()
        # Try to get parameter count
        if hasattr(self.model, 'model') and hasattr(self.model.model, 'parameters'):
            info["param_count"] = sum(p.numel() for p in self.model.model.parameters())
        return info
