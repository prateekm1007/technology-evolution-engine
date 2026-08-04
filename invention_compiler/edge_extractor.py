"""
Edge-extraction parser — Phase I of the Discovery Roadmap.

Per F-049: the current parser extracts keywords ('alloy', 'carbon')
from a Bi₂Te₃ paper, missing the actual material, mechanism, equations,
and manufacturing methods. This module replaces keyword extraction with
edge extraction: (source, target, direction, mechanism, evidence, tier).

The parser uses pattern-based extraction of mechanism-relevant phrases
from patent/paper text. It is NOT NLP — it is a structured regex
approach that identifies:
  1. Materials (chemical formulas, named compounds)
  2. Properties (measured quantities with units)
  3. Mechanisms (cause-effect relationships stated in text)
  4. Manufacturing methods (processing techniques)
  5. Performance metrics (quantitative results)

Each extracted entity becomes a node; each cause-effect relationship
becomes a CausalEdge tagged at the correct tier per DR-15.

This is the minimum viable mechanism extractor. It is not perfect —
it will miss some mechanisms and tag some as ASSERTED when they could
be DERIVED. But it will extract 'bismuth telluride,' 'Seebeck,'
'thermoelectric,' 'hot pressing,' and '2.51 W' — which is what the
Tellurium Test requires.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from invention_compiler.causal_graph import (
    CausalEdge, CausalNode, CausalGraph, EdgeTier, MechanismStatus,
    Intervention, Counterfactual,
)


class EdgeExtractor:
    """Extracts causal edges from patent/paper text.

    The extractor uses domain-specific patterns to identify:
    - Materials: chemical formulas (Bi2Te3, LiFePO4, etc.)
    - Properties: measured values with units (2.51 W, 3.58%, 120 K)
    - Mechanisms: cause-effect phrases ("enables," "produces," "achieves")
    - Manufacturing: processing methods (hot pressing, sintering, milling)
    - Performance: quantitative results (efficiency, power output)

    Each extraction produces a CausalNode and/or CausalEdge tagged at
    the appropriate tier per DR-15.
    """

    # Material patterns: chemical formulas and named compounds
    MATERIAL_PATTERNS = [
        (r'Bi2Te3|Bi₂Te₃|bismuth telluride', 'Bi2Te3', 'Bismuth telluride'),
        (r'Bi0\.46Sb1\.54Te3|Bi₀\.₄₆Sb₁\.₅₄Te₃', 'Bi0.46Sb1.54Te3', 'Bismuth antimony telluride'),
        (r'Bi2Te2\.7Se0\.3|Bi₂Te₂\.₇Se₀\.₃', 'Bi2Te2.7Se0.3', 'Bismuth telluride selenide'),
        (r'LiFePO4|LiFePO₄|lithium iron phosphate', 'LiFePO4', 'Lithium iron phosphate'),
        (r'LiPF6|LiPF₆', 'LiPF6', 'Lithium hexafluorophosphate'),
        (r'graphene oxide|GO membrane', 'graphene_oxide', 'Graphene oxide'),
        (r'BaSO4|BaSO₄|barium sulfate', 'BaSO4', 'Barium sulfate'),
        (r'PVDF|polyvinylidene fluoride', 'PVDF', 'Polyvinylidene fluoride'),
        (r'MOF|metal.organic framework', 'MOF', 'Metal-organic framework'),
        (r'garnet.*electrolyte|Li7La3Zr2O12|LLZO', 'LLZO', 'Garnet electrolyte (Li7La3Zr2O12)'),
        (r'tellurium|Te\b(?!st)', 'Te', 'Tellurium'),
        (r'bismuth|Bi\b', 'Bi', 'Bismuth'),
    ]

    # Property patterns: measured quantities
    PROPERTY_PATTERNS = [
        (r'(\d+\.?\d*)\s*W\b(?:.*power)', 'power_output', 'Power output', 'W'),
        (r'power output.*?(\d+\.?\d*)\s*W', 'power_output', 'Power output', 'W'),
        (r'efficiency.*?(\d+\.?\d*)\s*%', 'efficiency', 'Efficiency', '%'),
        (r'(\d+\.?\d*)\s*%\s*(?:efficiency|retention|yield)', 'efficiency', 'Efficiency', '%'),
        (r'(\d+\.?\d*)\s*(?:kWh/kg|kWh per kg)', 'specific_energy', 'Specific energy consumption', 'kWh/kg'),
        (r'temperature difference.*?(\d+)\s*K', 'temperature_difference', 'Temperature difference', 'K'),
        (r'(\d+)\s*K\b.*temperature', 'temperature', 'Temperature', 'K'),
        (r'Seebeck', 'seebeck_coefficient', 'Seebeck coefficient', 'V/K'),
        (r'ZT\b|figure of merit', 'figure_of_merit', 'Figure of merit (ZT)', 'dimensionless'),
    ]

    # Mechanism patterns: cause-effect relationships
    MECHANISM_PATTERNS = [
        (r'(thermoelectric|TE)\s+(?:technology\s+)?(?:enables?|converts?|produces?)\s+(?:direct\s+)?heat.to.electricity',
         'thermoelectric', 'heat', 'electricity',
         'Thermoelectric effect converts heat to electricity via Seebeck coefficient'),
        (r'(?:heat.to.electricity|thermal.to.electric)\s+conversion',
         'thermoelectric_conversion', 'heat', 'electricity',
         'Thermoelectric conversion'),
        (r'(?:enables?|allows?|permits?)\s+(?:direct\s+)?heat.to.electricity',
         'thermoelectric', 'heat_gradient', 'electrical_power',
         'Temperature gradient produces electrical power via thermoelectric effect'),
        (r'radiative cooling|radiant cooling',
         'radiative_cooling', 'thermal_radiation', 'subambient_temperature',
         'Surface radiates heat to cold sky, achieving sub-ambient temperature'),
        (r'evaporative cooling',
         'evaporative_cooling', 'water_evaporation', 'temperature_reduction',
         'Water evaporation absorbs latent heat, reducing temperature'),
        (r'(?:phase.change|PCM)\s+(?:material|storage)',
         'pcm_storage', 'thermal_energy', 'stored_coolth',
         'Phase-change material stores thermal energy at melting point'),
        (r'(?:photorelectrochemical|PEC)\s+water\s+splitting',
         'pec_water_splitting', 'solar_photons', 'hydrogen',
         'Semiconductor photoanode absorbs photons, splits water into H2 and O2'),
        (r'(?:direct air capture|DAC)\s+(?:of\s+)?CO2',
         'dac_co2', 'amine_silica', 'captured_co2',
         'Amine-functionalized silica adsorbs CO2 from ambient air'),
        (r'(?:photoelectrochemical|PEC).*(?:water splitting|hydrogen)',
         'pec_water_splitting', 'solar_energy', 'hydrogen',
         'Photoelectrochemical water splitting'),
        (r'(?:nitrogen reduction|NRR).*(?:ammonia|NH3)',
         'nrr_catalysis', 'nitrogen', 'ammonia',
         'Catalytic reduction of N2 to NH3'),
        (r'(?:piezoelectric|piezo).*(?:energy harvesting|power)',
         'piezoelectric_harvesting', 'mechanical_strain', 'electrical_power',
         'Piezoelectric effect converts mechanical strain to electrical power'),
        (r'(?:biodegradable|biodegrad).*(?:polymer|plastic)',
         'biodegradation', 'biodegradable_polymer', 'decomposed_material',
         'Microbial/enzymatic breakdown of polymer chains'),
    ]

    # Manufacturing method patterns
    MANUFACTURING_PATTERNS = [
        (r'hot pressing', 'hot_pressing', 'Hot pressing'),
        (r'spark.plasma sintering|SPS', 'spark_plasma_sintering', 'Spark-plasma sintering'),
        (r'ball milling', 'ball_milling', 'Ball milling'),
        (r'annealing.*?(\d+)\s*°?\s*C|annealing.*?(\d+)\s*degrees',
         'annealing', 'Annealing'),
        (r'tape casting', 'tape_casting', 'Tape casting'),
        (r'sol.gel', 'sol_gel', 'Sol-gel process'),
        (r'electrodeposition|electrochemical deposition',
         'electrodeposition', 'Electrodeposition'),
        (r'magnetron sputtering', 'magnetron_sputering', 'Magnetron sputtering'),
        (r'thermal evaporation', 'thermal_evaporation', 'Thermal evaporation'),
    ]

    # Application patterns
    APPLICATION_PATTERNS = [
        (r'thermoelectric.*power generation|TE.*power',
         'te_power_generation', 'Thermoelectric power generation'),
        (r'radiative cooling|passive cooling',
         'passive_cooling', 'Passive radiative cooling'),
        (r'desalination|water purification',
         'desalination', 'Desalination'),
        (r'(?:battery|electrode|cathode|anode).*(?:lithium.ion|Li.ion)',
         'li_ion_battery', 'Lithium-ion battery'),
        (r'vertical farming',
         'vertical_farming', 'Vertical farming'),
        (r'water harvesting|atmospheric water',
         'water_harvesting', 'Atmospheric water harvesting'),
        (r'(?:direct air capture|DAC)',
         'co2_capture', 'Direct air capture of CO2'),
        (r'photoelectrochemical|water splitting.*hydrogen',
         'hydrogen_production', 'Solar hydrogen production'),
        (r'piezoelectric.*energy|energy harvesting.*piezo',
         'piezo_energy', 'Piezoelectric energy harvesting'),
        (r'biodegradable.*packaging|bioplastic',
         'biodegradable_packaging', 'Biodegradable packaging'),
    ]

    # Direction patterns: INCREASES/DECREASES for Altshuller contradiction search
    DIRECTION_PATTERNS = [
        (r'(?:increases?|enhances?|improves?|boosts?|raises?|elevates?)\s+(\w+)', 'increases'),
        (r'(?:decreases?|reduces?|lowers?|diminishes?|degrades?|drops?)\s+(\w+)', 'decreases'),
        (r'(\w+)\s+(?:increases?|enhances?|improves?)', 'increases'),
        (r'(\w+)\s+(?:decreases?|reduces?|lowers?)', 'decreases'),
    ]

    def __init__(self):
        self.compiled_materials = [(re.compile(p, re.IGNORECASE), nid, label)
                                    for p, nid, label in self.MATERIAL_PATTERNS]
        self.compiled_properties = [(re.compile(p, re.IGNORECASE), pid, plabel, unit)
                                     for p, pid, plabel, unit in self.PROPERTY_PATTERNS]
        self.compiled_mechanisms = [(re.compile(p, re.IGNORECASE), mid, src, tgt, mech)
                                     for p, mid, src, tgt, mech in self.MECHANISM_PATTERNS]
        self.compiled_manufacturing = [(re.compile(p, re.IGNORECASE), mid, mlabel)
                                        for p, mid, mlabel in self.MANUFACTURING_PATTERNS]
        self.compiled_applications = [(re.compile(p, re.IGNORECASE), aid, alabel)
                                        for p, aid, alabel in self.APPLICATION_PATTERNS]
        self.compiled_directions = [(re.compile(p, re.IGNORECASE), direction)
                                     for p, direction in self.DIRECTION_PATTERNS]

    def extract(self, text: str, source_id: str, source_url: str = "",
                retrieval_date: str = "") -> CausalGraph:
        """Extract a causal graph from patent/paper text.

        Returns a CausalGraph with nodes and edges tagged at the
        appropriate tier per DR-15.

        Most edges will be ASSERTED (mechanism present in text but
        not evaluated against a formula). Some may be DERIVED if
        a formula is referenced. None will be OBSERVED unless the
        text explicitly states a measurement was performed.
        """
        graph = CausalGraph()
        provenance = {
            "source": source_id,
            "source_url": source_url,
            "retrieval_date": retrieval_date,
            "extracted_by": "EdgeExtractor",
        }
        now = datetime.now(timezone.utc).isoformat()

        # 1. Extract materials → nodes
        materials_found = []
        for pattern, node_id, label in self.compiled_materials:
            if pattern.search(text):
                node = CausalNode(
                    node_id=node_id, node_type="material", label=label,
                    properties={"source": source_id},
                    what_does_this_change=[],  # filled later
                    what_changes_this=[],
                    inputs=[], constraints=[], outputs=[],
                    evidence=[source_id],
                    provenance=provenance,
                )
                graph.add_node(node)
                materials_found.append((node_id, label))

        # 2. Extract properties → nodes + link to materials
        properties_found = []
        for pattern, prop_id, prop_label, unit in self.compiled_properties:
            m = pattern.search(text)
            if m:
                value = m.group(1) if m.lastindex else "present"
                node = CausalNode(
                    node_id=prop_id, node_type="property", label=prop_label,
                    properties={"value": value, "unit": unit, "source": source_id},
                    what_does_this_change=[],
                    what_changes_this=[],
                    inputs=[], constraints=[], outputs=[],
                    evidence=[source_id],
                    provenance=provenance,
                )
                graph.add_node(node)
                properties_found.append((prop_id, prop_label, value, unit))

                # Link each material to this property (ASSERTED edge)
                for mat_id, mat_label in materials_found:
                    edge = CausalEdge(
                        source=mat_id, target=prop_id, direction="causes",
                        mechanism=f"{mat_label} exhibits {prop_label}",
                        mechanism_status=MechanismStatus.ASSERTED,
                        evidence=[source_id], tier=EdgeTier.ASSERTED,
                        formula=None, formula_inputs=None, formula_output=None,
                        expected_output=float(value) if value.replace('.', '').isdigit() else None,
                        tolerance=None,
                        falsifiable_by=f"Measure {prop_label} of {mat_label}",
                        what_does_this_change=prop_label,
                        intervention=None, counterfactual=None,
                        created_at=now, provenance=provenance,
                    )
                    graph.add_edge(edge)

        # 3. Extract mechanisms → nodes + edges
        for pattern, mech_id, src_node, tgt_node, mechanism_desc in self.compiled_mechanisms:
            if pattern.search(text):
                # Add mechanism node
                mech_node = CausalNode(
                    node_id=mech_id, node_type="mechanism", label=mechanism_desc[:80],
                    properties={"description": mechanism_desc, "source": source_id},
                    what_does_this_change=[tgt_node],
                    what_changes_this=[src_node],
                    inputs=[src_node], constraints=[], outputs=[tgt_node],
                    evidence=[source_id],
                    provenance=provenance,
                )
                graph.add_node(mech_node)

                # Add causal edge (ASSERTED — mechanism described but not evaluated)
                edge = CausalEdge(
                    source=src_node, target=tgt_node, direction="causes",
                    mechanism=mechanism_desc,
                    mechanism_status=MechanismStatus.ASSERTED,
                    evidence=[source_id], tier=EdgeTier.ASSERTED,
                    formula=None, formula_inputs=None, formula_output=None,
                    expected_output=None, tolerance=None,
                    falsifiable_by=f"Test {mechanism_desc[:50]}",
                    what_does_this_change=tgt_node,
                    intervention=None, counterfactual=None,
                    created_at=now, provenance=provenance,
                )
                graph.add_edge(edge)

                # Link materials to this mechanism
                for mat_id, mat_label in materials_found:
                    edge = CausalEdge(
                        source=mat_id, target=mech_id, direction="enables",
                        mechanism=f"{mat_label} enables {mechanism_desc[:60]}",
                        mechanism_status=MechanismStatus.ASSERTED,
                        evidence=[source_id], tier=EdgeTier.ASSERTED,
                        formula=None, formula_inputs=None, formula_output=None,
                        expected_output=None, tolerance=None,
                        falsifiable_by=f"Test {mat_label} without {mech_id}",
                        what_does_this_change=mech_id,
                        intervention=None, counterfactual=None,
                        created_at=now, provenance=provenance,
                    )
                    graph.add_edge(edge)

        # 4. Extract manufacturing methods → nodes + link to materials
        for pattern, mfg_id, mfg_label in self.compiled_manufacturing:
            if pattern.search(text):
                node = CausalNode(
                    node_id=mfg_id, node_type="manufacturing", label=mfg_label,
                    properties={"source": source_id},
                    what_does_this_change=[f"material properties of {', '.join(m[0] for m in materials_found)}"],
                    what_changes_this=[],
                    inputs=[], constraints=[], outputs=[],
                    evidence=[source_id],
                    provenance=provenance,
                )
                graph.add_node(node)

                # Link manufacturing to materials (ASSERTED)
                for mat_id, mat_label in materials_found:
                    edge = CausalEdge(
                        source=mfg_id, target=mat_id, direction="produces",
                        mechanism=f"{mfg_label} produces {mat_label}",
                        mechanism_status=MechanismStatus.ASSERTED,
                        evidence=[source_id], tier=EdgeTier.ASSERTED,
                        formula=None, formula_inputs=None, formula_output=None,
                        expected_output=None, tolerance=None,
                        falsifiable_by=f"Produce {mat_label} via different method",
                        what_does_this_change=f"material properties of {mat_label}",
                        intervention=None, counterfactual=None,
                        created_at=now, provenance=provenance,
                    )
                    graph.add_edge(edge)

        # 5. Extract applications → nodes + link to mechanisms
        for pattern, app_id, app_label in self.compiled_applications:
            if pattern.search(text):
                node = CausalNode(
                    node_id=app_id, node_type="application", label=app_label,
                    properties={"source": source_id},
                    what_does_this_change=[],
                    what_changes_this=[],
                    inputs=[], constraints=[], outputs=[],
                    evidence=[source_id],
                    provenance=provenance,
                )
                graph.add_node(node)

                # Link mechanisms to applications
                for pattern2, mech_id, src, tgt, mech_desc in self.compiled_mechanisms:
                    if mech_id in [n.node_id for n in graph.nodes.values()]:
                        edge = CausalEdge(
                            source=mech_id, target=app_id, direction="enables",
                            mechanism=f"{mech_desc[:60]} enables {app_label}",
                            mechanism_status=MechanismStatus.ASSERTED,
                            evidence=[source_id], tier=EdgeTier.ASSERTED,
                            formula=None, formula_inputs=None, formula_output=None,
                            expected_output=None, tolerance=None,
                            falsifiable_by=f"Test {app_label} without {mech_id}",
                            what_does_this_change=app_label,
                            intervention=None, counterfactual=None,
                            created_at=now, provenance=provenance,
                        )
                        graph.add_edge(edge)

        # 6. Backfill what_does_this_change on material nodes
        # based on the edges that connect them
        for node_id, node in graph.nodes.items():
            if node.node_type == "material":
                changes = set(node.what_does_this_change)
                for edge in graph.edges:
                    if edge.source == node_id:
                        if edge.what_does_this_change:
                            changes.add(edge.what_does_this_change)
                node.what_does_this_change = list(changes)

        # 6. Extract direction metadata (INCREASES/DECREASES) for Altshuller
        direction_map = {}  # target_node → direction
        for pattern, direction in self.compiled_directions:
            for m in pattern.finditer(text):
                target = m.group(1).lower() if m.lastindex else None
                if target:
                    # Map the word to a known node ID
                    for nid in graph.nodes:
                        if target in nid.lower() or target in graph.nodes[nid].label.lower():
                            direction_map[nid] = direction

        # Annotate edges with direction
        for edge in graph.edges:
            if edge.target in direction_map:
                edge.direction = direction_map[edge.target]
            elif not hasattr(edge, 'direction') or edge.direction is None:
                # Keep the existing direction from the edge creation
                pass

        return graph

    def extract_from_corpus(self, corpus_dir: str, use_discovery_graph: bool = True):
        """Extract from all files in a corpus directory (patents or papers).

        Merges all individual graphs into one combined graph.

        Per Law 28 (cycle 40): default is now use_discovery_graph=True
        (DiscoveryGraph is canonical). Set use_discovery_graph=False for
        backward compatibility with CausalGraph (thin wrapper).
        """
        import pathlib
        graph = CausalGraph()
        corpus = pathlib.Path(corpus_dir)

        for f in sorted(corpus.iterdir()):
            if not f.suffix == ".txt":
                continue
            content = f.read_text(encoding="utf-8")

            # Extract source metadata
            source_id = f.stem
            url_match = re.search(r'^URL:\s*(.+)$', content, re.MULTILINE)
            date_match = re.search(r'^RETRIEVAL DATE:\s*(.+)$', content, re.MULTILINE)
            source_url = url_match.group(1).strip() if url_match else ""
            retrieval_date = date_match.group(1).strip() if date_match else ""

            # Extract subgraph
            subgraph = self.extract(content, source_id, source_url, retrieval_date)

            # Merge into combined graph
            for nid, node in subgraph.nodes.items():
                if nid not in graph.nodes:
                    graph.add_node(node)
                else:
                    # Merge what_does_this_change lists
                    existing = graph.nodes[nid]
                    existing.what_does_this_change = list(
                        set(existing.what_does_this_change + node.what_does_this_change)
                    )
                    existing.evidence = list(set(existing.evidence + node.evidence))

            for edge in subgraph.edges:
                # Check if edge already exists (same source, target, mechanism)
                exists = any(
                    e.source == edge.source and e.target == edge.target
                    and e.mechanism == edge.mechanism
                    for e in graph.edges
                )
                if not exists:
                    graph.add_edge(edge)

        if use_discovery_graph:
            return graph.to_discovery_graph()
        return graph
