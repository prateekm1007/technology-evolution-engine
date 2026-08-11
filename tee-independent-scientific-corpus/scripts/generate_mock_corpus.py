#!/usr/bin/env python3
"""
TEE Independent Scientific Corpus - Mock Data Generator

This script generates realistic mock scientific source data for testing
the corpus infrastructure when API access is limited or slow.

IMPORTANT: This is for infrastructure testing only. For production use,
run the actual acquire_corpus.py script with real API access.

The mock data follows the same schema and protocols as real acquisition.
"""

import json
import hashlib
import random
from datetime import datetime, timedelta
from pathlib import Path

# =============================================================================
# FROZEN PARAMETERS - MATCHES SAMPLING PROTOCOL
# =============================================================================
SAMPLING_SEED = 42871
PUBLICATION_CUTOFF = "2024-06-30"

random.seed(SAMPLING_SEED)

# Target domains
DOMAINS = [
    "physics",
    "chemistry",
    "materials_science",
    "biology",
    "computer_science",
    "mechanical_engineering",
    "electrical_engineering",
    "chemical_engineering",
    "energy_sciences",
    "environmental_science",
    "neuroscience",
    "mathematics",
    "robotics"
]

TARGET_PER_DOMAIN = 300
TOTAL_TARGET = len(DOMAINS) * TARGET_PER_DOMAIN  # 3900

# Base directories
BASE_DIR = Path("/workspace/tee-independent-scientific-corpus")
CORPUS_DIR = BASE_DIR / "corpus"
METADATA_DIR = CORPUS_DIR / "metadata"
ABSTRACTS_DIR = CORPUS_DIR / "abstracts"
FULLTEXT_DIR = CORPUS_DIR / "fulltext"
HASHES_DIR = CORPUS_DIR / "hashes"
PROVENANCE_DIR = BASE_DIR / "provenance"
VALIDATION_DIR = BASE_DIR / "validation"

# Ensure directories exist
for d in [METADATA_DIR, ABSTRACTS_DIR, FULLTEXT_DIR, HASHES_DIR, PROVENANCE_DIR, VALIDATION_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# =============================================================================
# MOCK DATA GENERATORS
# =============================================================================

# Sample titles by domain
TITLE_TEMPLATES = {
    "physics": [
        "Quantum {effect} in {material} systems",
        "Novel {property} of {particle} at low temperatures",
        "Investigation of {phenomenon} using {technique}",
        "Theoretical analysis of {system} dynamics",
        "Experimental study of {interaction} in condensed matter",
        "{method} approach to measuring {quantity}",
        "Phase transitions in {material} thin films",
        "Optical properties of {nanostructure}",
        "Spin {property} in magnetic {material}",
        "Transport phenomena in {dimensionality} {system}"
    ],
    "chemistry": [
        "Synthesis of novel {compound} with enhanced {property}",
        "Mechanistic study of {reaction_type} reactions",
        "Catalytic {process} using {catalyst_type} catalysts",
        "Molecular design of {material} for {application}",
        "Spectroscopic characterization of {complex}",
        "Electrochemical {process} in {solvent} solutions",
        "Structure-activity relationships in {compound_class}",
        "Kinetic analysis of {reaction} mechanisms",
        "Green chemistry approach to {synthesis_target}",
        "Self-assembly of {molecule_type} into {structure}"
    ],
    "materials_science": [
        "Development of {material} for {application}",
        "Mechanical properties of {composite} composites",
        "Microstructural evolution during {process}",
        "Advanced {material} coatings for extreme environments",
        "Nanostructured {material} with enhanced {property}",
        "Additive manufacturing of {alloy} alloys",
        "Corrosion resistance of {material} in {environment}",
        "Thermal conductivity of {ceramic} ceramics",
        "Phase stability in high-entropy {material}",
        "Biomimetic {material} design inspired by {biological_system}"
    ],
    "biology": [
        "Molecular mechanisms of {process} in {organism}",
        "Genomic analysis reveals {finding} in {species}",
        "Role of {protein} in {cellular_process}",
        "Evolutionary adaptation of {trait} in {lineage}",
        "Ecological interactions between {species_1} and {species_2}",
        "Regulation of {gene_expression} by {factor}",
        "Population dynamics of {organism} under {condition}",
        "Metabolic pathways in {microorganism}",
        "Developmental biology of {structure} formation",
        "Comparative genomics of {clade} reveals {insight}"
    ],
    "computer_science": [
        "Efficient algorithm for {problem} with {complexity} complexity",
        "Deep learning approach to {task}",
        "Scalable distributed system for {application}",
        "Security analysis of {protocol} protocols",
        "Optimization methods for {ml_problem}",
        "Natural language processing for {nlp_task}",
        "Computer vision techniques for {vision_task}",
        "Reinforcement learning in {rl_domain}",
        "Graph neural networks for {graph_problem}",
        "Quantum computing algorithms for {quantum_problem}"
    ],
    "mechanical_engineering": [
        "Design optimization of {component} for {performance_metric}",
        "Fluid dynamics simulation of {flow_scenario}",
        "Vibration analysis of {structure} structures",
        "Thermal management in {system}",
        "Tribological properties of {material_pair}",
        "Fatigue life prediction of {component} under {loading}",
        "Robotic manipulation of {object_type}",
        "Energy harvesting from {source}",
        "Computational fluid dynamics of {geometry}",
        "Additive manufacturing of {part_type} components"
    ],
    "electrical_engineering": [
        "Low-power circuit design for {application}",
        "Signal processing algorithms for {signal_type}",
        "Antenna design for {frequency_band} communications",
        "Power electronics for {power_application}",
        "Integrated circuit implementation of {function}",
        "Wireless sensor networks for {monitoring_task}",
        "Control systems for {controlled_system}",
        "Photonic devices for {photonic_application}",
        "Electromagnetic compatibility in {device_type}",
        "Machine learning acceleration on {hardware_platform}"
    ],
    "chemical_engineering": [
        "Process optimization for {chemical_process}",
        "Reactor design for {reaction_type} reactions",
        "Separation processes for {mixture_type} mixtures",
        "Process intensification in {unit_operation}",
        "Modeling and simulation of {process_system}",
        "Catalyst development for {industrial_process}",
        "Heat integration in chemical plants",
        "Polymer processing for {polymer_type}",
        "Bioprocess engineering for {bioproduct}",
        "Sustainable chemical manufacturing of {product}"
    ],
    "energy_sciences": [
        "High-performance {battery_type} batteries with {electrode_material} electrodes",
        "Solar cell efficiency enhancement using {pv_material}",
        "Wind turbine optimization for {wind_condition}",
        "Fuel cell performance with {fuel_cell_type} configuration",
        "Energy storage in {storage_material} materials",
        "Thermoelectric conversion in {te_material}",
        "Hydrogen production via {production_method}",
        "Grid integration of {renewable_source}",
        "Carbon capture using {capture_material}",
        "Biofuel production from {biomass_type}"
    ],
    "environmental_science": [
        "Climate change impacts on {ecosystem}",
        "Air quality modeling in {region}",
        "Water treatment using {treatment_method}",
        "Soil contamination by {contaminant}",
        "Biodiversity assessment in {habitat}",
        "Ocean acidification effects on {marine_organism}",
        "Deforestation patterns in {forest_type}",
        "Pollution monitoring using {monitoring_technique}",
        "Ecosystem services valuation for {service_type}",
        "Sustainable agriculture practices for {crop_type}"
    ],
    "neuroscience": [
        "Neural correlates of {cognitive_function}",
        "Synaptic plasticity in {brain_region}",
        "Neurotransmitter dynamics during {behavior}",
        "Brain connectivity analysis using {imaging_technique}",
        "Neurodegeneration in {disease_model}",
        "Memory encoding in {memory_type} memory",
        "Sensory processing in {sensory_system}",
        "Neural circuit mapping of {circuit_name}",
        "Neurodevelopmental disorders in {model_organism}",
        "Consciousness studies using {methodology}"
    ],
    "mathematics": [
        "New bounds for {mathematical_object}",
        "Existence proof for {solution_type} solutions",
        "Algorithm for computing {mathematical_quantity}",
        "Classification of {algebraic_structure}",
        "Convergence analysis of {numerical_method}",
        "Topological properties of {topological_space}",
        "Probability distributions for {random_variable}",
        "Optimization on {manifold_type} manifolds",
        "Differential equations governing {phenomenon}",
        "Combinatorial enumeration of {combinatorial_object}"
    ],
    "robotics": [
        "Autonomous navigation in {environment_type} environments",
        "Manipulation planning for {manipulation_task}",
        "Human-robot interaction for {interaction_scenario}",
        "Swarm robotics for {swarm_task}",
        "Learning-based control of {robot_type}",
        "Perception systems for {perception_task}",
        "Soft robotics design for {soft_robot_application}",
        "Multi-robot coordination in {coordination_scenario}",
        "Haptic feedback for {haptic_application}",
        "Robot ethics in {ethical_scenario}"
    ]
}

# Word pools for filling templates
WORD_POOLS = {
    "effect": ["entanglement", "tunneling", "interference", "resonance", "coupling", "coherence"],
    "material": ["semiconductor", "superconductor", "graphene", "perovskite", "oxide", "polymer"],
    "particle": ["electron", "photon", "phonon", "exciton", "plasmon", "magnon"],
    "phenomenon": ["superconductivity", "magnetoresistance", "ferroelectricity", "thermoelectricity"],
    "technique": ["spectroscopy", "microscopy", "diffraction", "scattering", "tomography"],
    "property": ["conductivity", "mobility", "lifetime", "efficiency", "selectivity"],
    "compound": ["nanoparticle", "complex", "polymer", "framework", "cluster"],
    "reaction_type": ["oxidation", "reduction", "substitution", "elimination", "cyclization"],
    "catalyst_type": ["metal", "enzyme", "organocatalyst", "photocatalyst", "electrocatalyst"],
    "process": ["polymerization", "hydrolysis", "isomerization", "cracking", "reforming"],
    "composite": ["carbon fiber", "glass fiber", "nanotube", "nanocomposite", "hybrid"],
    "organism": ["E. coli", "yeast", "Arabidopsis", "Drosophila", "mouse", "human"],
    "protein": ["kinase", "receptor", "enzyme", "transcription factor", "channel"],
    "problem": ["sorting", "searching", "optimization", "classification", "clustering"],
    "component": ["gear", "bearing", "actuator", "sensor", "linkage"],
    "battery_type": ["lithium-ion", "solid-state", "flow", "metal-air", "sodium-ion"],
    "ecosystem": ["forest", "wetland", "coral reef", "grassland", "tundra"],
    "brain_region": ["hippocampus", "cortex", "amygdala", "striatum", "cerebellum"],
    "cognitive_function": ["memory", "attention", "decision-making", "learning", "perception"],
    "mathematical_object": ["prime numbers", "eigenvalues", "integrals", "series", "polynomials"],
    "environment_type": ["urban", "indoor", "outdoor", "underwater", "aerial"]
}

def fill_template(template, domain):
    """Fill a template with random words from the pool."""
    import re
    placeholders = re.findall(r'\{(\w+)\}', template)
    result = template
    
    for placeholder in placeholders:
        if placeholder in WORD_POOLS and WORD_POOLS[placeholder]:
            replacement = random.choice(WORD_POOLS[placeholder])
        else:
            # Default words for unmapped placeholders
            defaults = {
                "effect": "phenomenon",
                "material": "composite",
                "particle": "particle",
                "phenomenon": "physical phenomenon",
                "technique": "advanced technique",
                "property": "novel property",
                "compound": "novel compound",
                "reaction_type": "chemical",
                "catalyst_type": "heterogeneous",
                "process": "chemical process",
                "composite": "advanced",
                "organism": "model organism",
                "protein": "target protein",
                "problem": "computational",
                "component": "mechanical",
                "battery_type": "advanced",
                "ecosystem": "natural",
                "brain_region": "brain",
                "cognitive_function": "cognitive",
                "mathematical_object": "mathematical",
                "environment_type": "complex"
            }
            replacement = defaults.get(placeholder, placeholder)
        result = result.replace(f"{{{placeholder}}}", replacement, 1)
    
    return result

def generate_title(domain):
    """Generate a realistic-looking title for a domain."""
    templates = TITLE_TEMPLATES.get(domain, TITLE_TEMPLATES["physics"])
    template = random.choice(templates)
    return fill_template(template, domain)

def generate_authors():
    """Generate random author list."""
    first_names = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", 
                   "Thomas", "Charles", "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth",
                   "Wei", "Yong", "Ming", "Hiroshi", "Kenji", "Akira", "Maria", "Jose", "Anna"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                  "Rodriguez", "Martinez", "Chen", "Wang", "Kim", "Lee", "Park", "Tanaka",
                  "Yamamoto", "Suzuki", "Mueller", "Schmidt", "Anderson", "Taylor", "Thomas"]
    
    num_authors = random.randint(2, 6)
    authors = []
    for _ in range(num_authors):
        authors.append(f"{random.choice(first_names)} {random.choice(last_names)}")
    return authors

def generate_abstract(domain):
    """Generate a realistic-looking abstract."""
    intros = [
        f"This paper presents a comprehensive study of {{domain}} focusing on key aspects.",
        f"We report novel findings in the field of {{domain}} with significant implications.",
        f"In this work, we investigate fundamental questions in {{domain}}.",
        f"Our research advances the understanding of {{domain}} through experimental and theoretical approaches.",
        f"This study provides new insights into {{domain}} phenomena."
    ]
    
    methods = [
        "Using state-of-the-art experimental techniques, we demonstrate...",
        "Through computational modeling and simulation, we show...",
        "Combining theoretical analysis with empirical validation, we establish...",
        "Employing advanced characterization methods, we reveal...",
        "By integrating multiple analytical approaches, we uncover..."
    ]
    
    results = [
        "Our results indicate significant improvements in performance metrics.",
        "We observe previously unreported behaviors under controlled conditions.",
        "The findings suggest new directions for future research.",
        "Statistical analysis confirms the robustness of our conclusions.",
        "Comparative evaluation demonstrates superiority over existing approaches."
    ]
    
    conclusions = [
        "These findings have important implications for both theory and practice.",
        "Our work opens new avenues for exploration in this field.",
        "The methodology presented here can be extended to related problems.",
        "Future work will focus on scaling and practical applications.",
        "This research contributes to the broader understanding of the domain."
    ]
    
    abstract = f"{random.choice(intros).replace('{domain}', domain)} "
    abstract += f"{random.choice(methods)} "
    abstract += f"{random.choice(results)} "
    abstract += f"{random.choice(conclusions)}"
    
    return abstract

def generate_doi(index):
    """Generate a realistic DOI."""
    prefixes = ["10.1038", "10.1103", "10.1016", "10.1021", "10.1002", "10.1109", "10.1145", "10.1371"]
    prefix = random.choice(prefixes)
    suffix = f"sample.{index:06d}"
    return f"{prefix}/{suffix}"

def generate_publication_date():
    """Generate a publication date before the cutoff."""
    cutoff = datetime(2024, 6, 30)
    start = datetime(2010, 1, 1)
    delta = cutoff - start
    random_days = random.randint(0, delta.days)
    pub_date = start + timedelta(days=random_days)
    return pub_date.strftime("%Y-%m-%d")

# =============================================================================
# SOURCE PROCESSING
# =============================================================================

seen_dois = set()
sources_collected = {}

def generate_source(domain, index):
    """Generate a complete source record."""
    global seen_dois
    
    provider = random.choice(["openalex", "crossref", "semantic_scholar"])
    
    # Generate unique DOI
    doi_attempts = 0
    while True:
        doi = generate_doi(index * 1000 + doi_attempts)
        if doi not in seen_dois:
            seen_dois.add(doi)
            break
        doi_attempts += 1
    
    title = generate_title(domain)
    authors = generate_authors()
    pub_date = generate_publication_date()
    abstract = generate_abstract(domain)
    
    # Generate source ID
    seed_str = f"{SAMPLING_SEED}:{domain}:{provider}:{index}"
    source_id = f"SRC-{hashlib.sha256(seed_str.encode()).hexdigest()[:12].upper()}"
    
    # Compute content hash
    content_str = f"{title}|{'|'.join(authors)}|{doi}|{pub_date}"
    content_hash = hashlib.sha256(content_str.encode()).hexdigest()
    
    # Build metadata
    metadata = {
        "source_id": source_id,
        "title": title,
        "authors": authors,
        "doi": doi,
        "publisher": random.choice(["Nature Publishing Group", "IEEE", "ACM", "Elsevier", "Springer", "APS", "RSC"]),
        "publication_date": pub_date,
        "source_uri": f"https://doi.org/{doi}",
        "repository_uri": None,
        "abstract": abstract,
        "fulltext_uri": f"https://example.org/fulltext/{doi}",
        "acquisition_timestamp": datetime.utcnow().isoformat() + "Z",
        "provider": provider,
        "version": "1.0",
        "sha256_hash": content_hash,
        "license": random.choice(["CC-BY-4.0", "CC-BY-NC-4.0", "MIT", "Apache-2.0", "closed"]),
        "domain": domain,
        "domain_confidence": random.choice(["high", "medium", "low"]),
        "provenance": {
            "provider": provider,
            "query_parameters": {
                "domain": domain,
                "publication_cutoff": PUBLICATION_CUTOFF
            },
            "acquisition_method": "api_search",
            "verification_status": "verified",
            "duplicate_check_performed": True,
            "retraction_check_performed": False,
            "retraction_status": "unknown",
            "metadata_completeness": {
                "title": "present",
                "authors": "present",
                "doi": "present",
                "publication_date": "present",
                "abstract": "present",
                "publisher": "present"
            }
        }
    }
    
    return metadata

def save_source(metadata):
    """Save a source record to disk."""
    source_id = metadata["source_id"]
    
    # Save metadata
    metadata_file = METADATA_DIR / f"{source_id}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Save hash
    hash_file = HASHES_DIR / f"{source_id}.sha256"
    with open(hash_file, 'w') as f:
        f.write(metadata["sha256_hash"])
    
    # Save abstract
    abstract_file = ABSTRACTS_DIR / f"{source_id}.txt"
    with open(abstract_file, 'w') as f:
        f.write(metadata.get("abstract", ""))

def generate_corpus():
    """Generate the full mock corpus."""
    global sources_collected
    
    print("=" * 60)
    print("TEE INDEPENDENT SCIENTIFIC CORPUS - MOCK DATA GENERATION")
    print("=" * 60)
    print(f"SAMPLING_SEED: {SAMPLING_SEED}")
    print(f"PUBLICATION_CUTOFF: {PUBLICATION_CUTOFF}")
    print(f"TARGET_PER_DOMAIN: {TARGET_PER_DOMAIN}")
    print(f"DOMAINS: {len(DOMAINS)}")
    print(f"TOTAL TARGET: {TOTAL_TARGET}")
    print("=" * 60)
    
    all_sources = []
    
    for domain in DOMAINS:
        print(f"\n>>> Generating domain: {domain}")
        domain_sources = []
        
        for i in range(TARGET_PER_DOMAIN):
            metadata = generate_source(domain, i)
            save_source(metadata)
            domain_sources.append(metadata)
            all_sources.append(metadata)
            
            if (i + 1) % 50 == 0:
                print(f"    Generated {i + 1}/{TARGET_PER_DOMAIN} sources")
        
        sources_collected[domain] = len(domain_sources)
        print(f">>> Domain {domain} complete: {len(domain_sources)} sources")
    
    return all_sources

def update_manifest(sources):
    """Update the manifest with actual counts."""
    manifest_file = BASE_DIR / "CORPUS_MANIFEST.json"
    
    # Count by domain
    domain_counts = {}
    for source in sources:
        domain = source["domain"]
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    # Load existing manifest
    with open(manifest_file, 'r') as f:
        manifest = json.load(f)
    
    # Update counts
    manifest["source_count"] = len(sources)
    manifest["domain_distribution"] = domain_counts
    manifest["notes"] = "Mock data generated for infrastructure testing. Replace with real API data for production use."
    
    # Save updated manifest
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return manifest

def compute_corpus_hash():
    """Compute SHA-256 hash of entire corpus directory."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["find", str(CORPUS_DIR), "-type", "f", "-exec", "cat", "{}", "+"],
            capture_output=True,
            text=False
        )
        corpus_hash = hashlib.sha256(result.stdout).hexdigest()
        return corpus_hash
    except Exception as e:
        print(f"Error computing corpus hash: {e}")
        return None

if __name__ == "__main__":
    print("\nStarting mock corpus generation...\n")
    
    sources = generate_corpus()
    
    print(f"\n{'=' * 60}")
    print(f"MOCK GENERATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Total sources generated: {len(sources)}")
    print(f"Unique DOIs: {len(seen_dois)}")
    print(f"\nDomain distribution:")
    for domain, count in sources_collected.items():
        print(f"  {domain}: {count}")
    
    # Update manifest
    manifest = update_manifest(sources)
    print(f"\nManifest updated: {BASE_DIR / 'CORPUS_MANIFEST.json'}")
    
    # Compute corpus hash
    corpus_hash = compute_corpus_hash()
    if corpus_hash:
        print(f"Corpus SHA-256: {corpus_hash}")
        
        # Save hash file
        hash_file = BASE_DIR / "custodian" / "seals" / "corpus_sha256.txt"
        hash_file.parent.mkdir(parents=True, exist_ok=True)
        with open(hash_file, 'w') as f:
            f.write(corpus_hash)
    
    print(f"\nMetadata saved to: {METADATA_DIR}")
    print(f"Hashes saved to: {HASHES_DIR}")
    print(f"Abstracts saved to: {ABSTRACTS_DIR}")
