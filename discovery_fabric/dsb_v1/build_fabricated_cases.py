"""Build the 10 matched fabricated counterfactual cases for DSB V1.

Each fabricated case has the SAME structural template as its matched real case:
  - Same domain
  - Same exposed-facts pattern (general context + one side of a relationship)
  - Same withheld-facts pattern (the other side + a combination)
  - Same cutoff_date
  - A "breakthrough_relationship" that is PLAUSIBLE but did NOT historically happen

The point: if the scorer gives high marks to fabricated counterfactuals, the
scorer is too lenient — the system would be producing "discoveries" that
aren't real.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from case_schema import compute_answer_hash, validate_case

CASES_DIR = Path(__file__).parent / "cases" / "fabricated"
CASES_DIR.mkdir(parents=True, exist_ok=True)


def make_case(case_id, domain, name_internal, cutoff_date, exposed_facts,
              withheld_facts, breakthrough_relationship, forbidden_terms,
              future_terminology, answer_mechanism, constraint_release,
              historical_source):
    return {
        "case_id": case_id,
        "case_type": "fabricated",
        "domain": domain,
        "name_internal": name_internal,
        "cutoff_date": cutoff_date,
        "exposed_facts": exposed_facts,
        "withheld_facts": withheld_facts,
        "breakthrough_relationship": breakthrough_relationship,
        "answer_hash": compute_answer_hash(breakthrough_relationship),
        "forbidden_terms": forbidden_terms,
        "future_terminology": future_terminology,
        "answer_mechanism": answer_mechanism,
        "constraint_release": constraint_release,
        "historical_source": historical_source,
        "fabricated": True,
    }


CASES = [
    # ---- DSB-F-001: matched to DSB-R-001 (Li-ion) ----
    # Fabricated: sodium-ion analog claimed before any Na-ion chemistry was actually developed
    make_case(
        case_id="DSB-F-001",
        domain="materials",
        name_internal="fabricated_sodium_ion",
        cutoff_date="1990-12-31T23:59:59Z",
        exposed_facts=[
            "Sodium metal batteries are unsafe due to dendrite formation during cycling.",
            "Non-aqueous electrolytes exist that can conduct sodium ions between electrodes.",
            "Rechargeable battery electrodes must support reversible ion insertion and extraction.",
            "The challenge is to build a safe rechargeable low-cost battery using earth-abundant elements.",
        ],
        withheld_facts=[
            "Sodium cobalt oxide (NaCoO2) has been shown to reversibly intercalate sodium ions at high potential.",
            "Hard carbon has been shown to reversibly intercalate sodium ions at low potential.",
            "Combining a NaCoO2 cathode with a hard-carbon anode in a non-aqueous electrolyte yields a rechargeable sodium battery with no sodium metal dendrite risk.",
        ],
        breakthrough_relationship=(
            "Combining a sodium-intercalation cathode (NaCoO2) with a sodium-intercalation anode "
            "(hard carbon) in a non-aqueous electrolyte yields a safe rechargeable low-cost "
            "battery without sodium metal dendrites."
        ),
        forbidden_terms=[
            "sodium-ion battery", "na-ion", "naco02", "hard carbon anode",
        ],
        future_terminology=[
            "sodium-ion battery", "Na-ion", "NaCoO2-hard-carbon",
        ],
        answer_mechanism=(
            "Both electrodes reversibly intercalate sodium ions at different potentials. Sodium "
            "migrates between electrodes without sodium metal plating."
        ),
        constraint_release=(
            "Releases the safety constraint of sodium metal dendrites using earth-abundant elements."
        ),
        historical_source="FABRICATED. No historical breakthrough of this kind occurred in the 1990-1995 window. Sodium-ion batteries were developed much later (~2010s) using different chemistries.",
    ),

    # ---- DSB-F-002: matched to DSB-R-002 (PCR) ----
    # Fabricated: ligase chain reaction claimed as the exponential amplification
    make_case(
        case_id="DSB-F-002",
        domain="biology",
        name_internal="fabricated_ligase_cycling",
        cutoff_date="1984-12-31T23:59:59Z",
        exposed_facts=[
            "DNA ligase enzymes join adjacent oligonucleotide probes hybridized to a template.",
            "Heating denatures DNA; cooling allows re-annealing of probes.",
            "Synthetic oligonucleotides of arbitrary sequence can be chemically manufactured.",
            "Measuring a specific DNA sequence requires producing enough copies to detect.",
        ],
        withheld_facts=[
            "Cyclically heating and cooling a sample with two adjacent probe pairs and a thermostable ligase doubles the ligated product each cycle, yielding exponential amplification.",
        ],
        breakthrough_relationship=(
            "Cyclically heating and cooling a DNA sample with adjacent oligonucleotide probes "
            "and a thermostable ligase exponentially amplifies a specific sequence via ligation."
        ),
        forbidden_terms=[
            "ligase chain reaction", "lcr", "thermostable ligase amplification",
        ],
        future_terminology=[
            "Ligase Chain Reaction", "LCR",
        ],
        answer_mechanism=(
            "Each cycle denatures the ligated product, allowing new probes to anneal and ligate, "
            "doubling copies each cycle."
        ),
        constraint_release=(
            "Releases the constraint of cellular cloning for DNA detection."
        ),
        historical_source="FABRICATED. While LCR was eventually developed (early 1990s), the breakthrough combination as described here (thermostable ligase + cyclic amplification pre-1985) did not historically occur in this form.",
    ),

    # ---- DSB-F-003: matched to DSB-R-003 (graphene) ----
    # Fabricated: boron nitride monolayer via tape exfoliation claimed before 2004
    make_case(
        case_id="DSB-F-003",
        domain="materials",
        name_internal="fabricated_boron_nitride_monolayer",
        cutoff_date="2003-12-31T23:59:59Z",
        exposed_facts=[
            "Hexagonal boron nitride is a crystalline material arranged in stacked two-dimensional layers held together by weak van der Waals forces.",
            "Theory predicts that strictly two-dimensional crystals are thermodynamically unstable at finite temperature.",
            "Mechanical cleavage of layered materials is a known technique for thinning samples.",
            "Boron nitride nanotubes — rolled-up h-BN sheets — are known to exist.",
        ],
        withheld_facts=[
            "Repeated mechanical exfoliation of hexagonal boron nitride using adhesive tape isolates stable single-atom-thick boron nitride sheets at room temperature.",
        ],
        breakthrough_relationship=(
            "Repeated mechanical exfoliation of hexagonal boron nitride using adhesive tape "
            "isolates stable single-atom-thick boron nitride sheets at room temperature."
        ),
        forbidden_terms=[
            "hexagonal boron nitride monolayer", "h-bn 2d", "white graphene",
        ],
        future_terminology=[
            "h-BN monolayer", "white graphene", "2D boron nitride",
        ],
        answer_mechanism=(
            "Adhesive tape removes a thin layer; repetition thins to a monolayer visible by "
            "optical contrast on silicon."
        ),
        constraint_release=(
            "Releases the theoretical constraint that 2D crystals cannot exist at finite temperature."
        ),
        historical_source="FABRICATED as a pre-2004 breakthrough. h-BN monolayers were actually isolated AFTER graphene (2008 onward), not before.",
    ),

    # ---- DSB-F-004: matched to DSB-R-004 (AlexNet) ----
    # Fabricated: spiking neural network on neuromorphic chip beats SVMs
    make_case(
        case_id="DSB-F-004",
        domain="ml",
        name_internal="fabricated_neuromorphic_snn",
        cutoff_date="2011-12-31T23:59:59Z",
        exposed_facts=[
            "Spiking neural networks model neurons as discrete-time event emitters and are biologically plausible.",
            "Neuromorphic chips (such as SpiNNaker and TrueNorth prototypes) implement spiking neurons directly in silicon.",
            "Large labeled image datasets such as ImageNet contain over one million images across one thousand categories.",
            "Event-driven computation is energy-efficient but historically hard to train using gradient methods.",
            "Support vector machines and shallow hand-engineered features dominate ImageNet benchmarks at approximately 25 percent top-5 error.",
        ],
        withheld_facts=[
            "Training a deep spiking neural network with surrogate-gradient backpropagation on a neuromorphic chip reduces ImageNet top-5 error from 26 percent to 15 percent.",
        ],
        breakthrough_relationship=(
            "A deep spiking neural network trained with surrogate gradients on a neuromorphic "
            "chip reduces ImageNet top-5 error by approximately 10 percentage points over the "
            "previous state of the art."
        ),
        forbidden_terms=[
            "neuromorphic snn imagenet", "surrogate-gradient spiking",
        ],
        future_terminology=[
            "neuromorphic deep learning", "surrogate-gradient SNN",
        ],
        answer_mechanism=(
            "Surrogate gradients allow backpropagation through discrete spikes. Neuromorphic "
            "silicon provides massive parallelism for spike-based computation."
        ),
        constraint_release=(
            "Releases the energy-efficiency constraint of GPU training."
        ),
        historical_source="FABRICATED. As of 2012, neuromorphic SNNs had not achieved AlexNet-level ImageNet performance. This remained true through 2024.",
    ),

    # ---- DSB-F-005: matched to DSB-R-005 (perovskite) ----
    # Fabricated: organic photovoltaic reaching 25% via tandem architecture
    make_case(
        case_id="DSB-F-005",
        domain="materials",
        name_internal="fabricated_organic_tandem_25",
        cutoff_date="2008-12-31T23:59:59Z",
        exposed_facts=[
            "Organic photovoltaics (OPVs) based on conjugated polymer donors and fullerene acceptors achieve approximately 5 percent power conversion efficiency.",
            "Tandem architectures stack two cells with complementary absorption spectra to better use the solar spectrum.",
            "Transparent conducting oxides enable series-connected tandem sub-cells.",
            "Solution-processable semiconductors are attractive for low-cost large-area photovoltaics.",
        ],
        withheld_facts=[
            "A tandem organic photovoltaic with a wide-bandgap front cell and a narrow-bandgap back cell reaches over 20 percent efficiency.",
        ],
        breakthrough_relationship=(
            "A tandem organic photovoltaic combining a wide-bandgap front cell with a narrow-bandgap "
            "back cell exceeds 20 percent power conversion efficiency."
        ),
        forbidden_terms=[
            "organic tandem solar cell", "opv tandem 20",
        ],
        future_terminology=[
            "tandem OPV", "all-organic tandem photovoltaic",
        ],
        answer_mechanism=(
            "The front cell absorbs high-energy photons; the back cell absorbs the rest. The "
            "tandem architecture reduces thermalization losses."
        ),
        constraint_release=(
            "Releases the single-junction efficiency limit of organic photovoltaics."
        ),
        historical_source="FABRICATED. OPV tandem cells did not exceed 20 percent efficiency in the 2008-2012 window. Even by 2024, all-organic tandems had not reached 20 percent.",
    ),

    # ---- DSB-F-006: matched to DSB-R-006 (mRNA vaccine) ----
    # Fabricated: self-amplifying RNA vaccine producing 95% efficacy pre-2020
    make_case(
        case_id="DSB-F-006",
        domain="biology",
        name_internal="fabricated_self_amplifying_rna",
        cutoff_date="2019-12-31T23:59:59Z",
        exposed_facts=[
            "Self-amplifying RNA (saRNA) contains non-structural protein genes from an alphavirus that replicate the RNA in the cytoplasm.",
            "Lipid nanoparticles can deliver self-amplifying RNA into cells.",
            "Viral surface proteins such as the SARS-CoV-2 spike protein are the primary target of neutralizing antibodies.",
            "Conventional vaccine platforms require months to years of manufacturing scale-up.",
        ],
        withheld_facts=[
            "Encapsulating self-amplifying RNA encoding the SARS-CoV-2 spike protein in an LNP induces neutralizing antibodies at 95 percent efficacy after a single low-dose injection.",
        ],
        breakthrough_relationship=(
            "Encapsulating self-amplifying RNA encoding a viral spike protein in a lipid nanoparticle "
            "induces protective neutralizing antibodies at over 90 percent efficacy after a single "
            "low-dose injection."
        ),
        forbidden_terms=[
            "self-amplifying rna vaccine", "sarna lnpi",
        ],
        future_terminology=[
            "saRNA vaccine", "single-dose self-amplifying RNA",
        ],
        answer_mechanism=(
            "The alphavirus replicase amplifies the RNA in the cytoplasm, producing many copies "
            "of the antigen-encoding RNA from a single delivered molecule."
        ),
        constraint_release=(
            "Releases the dose-volume constraint of conventional mRNA vaccines via in-vivo amplification."
        ),
        historical_source="FABRICATED. As of 2020-2021, no saRNA vaccine achieved 95 percent efficacy with a single low dose. saRNA clinical results remained modest through 2024.",
    ),

    # ---- DSB-F-007: matched to DSB-R-007 (CRISPR-Cas9) ----
    # Fabricated: Argonaute-based gene editing (NgAgo) as the breakthrough
    make_case(
        case_id="DSB-F-007",
        domain="biology",
        name_internal="fabricated_argonato_gene_editing",
        cutoff_date="2011-12-31T23:59:59Z",
        exposed_facts=[
            "Prokaryotic Argonaute proteins use small DNA guides to cleave complementary DNA targets.",
            "Thermophilic bacteria such as Natronobacterium gregoryi produce heat-stable Argonautes.",
            "Zinc-finger nucleases and TALENs can cut specific genomic loci but require protein engineering for each new target.",
            "Double-strand DNA breaks stimulate endogenous repair pathways.",
        ],
        withheld_facts=[
            "Using a 24-nucleotide single-stranded DNA guide with NgAgo achieves programmable DNA cleavage in human cells at any genomic locus.",
        ],
        breakthrough_relationship=(
            "A short single-stranded DNA guide directing the NgAgo protein to cleave any genomic "
            "locus enables programmable gene editing in human cells."
        ),
        forbidden_terms=[
            "ngago gene editing", "natronobacterium gregoryi argonaute",
        ],
        future_terminology=[
            "Argonaute gene editing", "gDNA-guided editing",
        ],
        answer_mechanism=(
            "The 24-nt ssDNA guide base-pairs with the target; NgAgo cleaves both strands. "
            "Editing by changing only the guide ssDNA."
        ),
        constraint_release=(
            "Releases the protein-engineering constraint of ZFNs/TALENs."
        ),
        historical_source="FABRICATED. The NgAgo gene-editing claim (2016) was eventually retracted. As of 2024, Argonaute-based editing has not achieved robust programmable editing in human cells.",
    ),

    # ---- DSB-F-008: matched to DSB-R-008 (anti-PD-1) ----
    # Fabricated: IDO inhibitor as breakthrough (these actually FAILED in clinic)
    make_case(
        case_id="DSB-F-008",
        domain="biology",
        name_internal="fabricated_ido_inhibitor",
        cutoff_date="2011-12-31T23:59:59Z",
        exposed_facts=[
            "Indoleamine 2,3-dioxygenase (IDO) degrades tryptophan in the tumor microenvironment, suppressing T-cell function.",
            "Small-molecule inhibitors of IDO exist and are orally bioavailable.",
            "Tumors upregulate IDO as an immune-evasion mechanism.",
            "Cancer vaccines that activate T-cells have largely failed because activated T-cells are suppressed in the tumor microenvironment.",
        ],
        withheld_facts=[
            "An IDO inhibitor combined with a checkpoint antibody produces durable responses in melanoma and lung cancer patients at over 50 percent response rates.",
        ],
        breakthrough_relationship=(
            "An IDO inhibitor combined with a checkpoint antibody releases T-cell suppression "
            "via tryptophan restoration, producing durable responses in multiple cancer types."
        ),
        forbidden_terms=[
            "epacadostat", "ido inhibitor combination",
        ],
        future_terminology=[
            "IDO combination immunotherapy",
        ],
        answer_mechanism=(
            "IDO inhibition restores tryptophan in the tumor microenvironment, releasing T-cells "
            "from metabolic suppression. Combined with checkpoint blockade, durable responses "
            "result."
        ),
        constraint_release=(
            "Releases the metabolic T-cell suppression in the tumor microenvironment."
        ),
        historical_source="FABRICATED. The IDO inhibitor epacadostat FAILED its Phase 3 trial (ECHO-301, 2018) and was a famous negative result in oncology.",
    ),

    # ---- DSB-F-009: matched to DSB-R-009 (iPSC) ----
    # Fabricated: 2-TF (Oct4 + Sox2 only) reprogramming claimed
    make_case(
        case_id="DSB-F-009",
        domain="biology",
        name_internal="fabricated_two_factor_reprogramming",
        cutoff_date="2005-12-31T23:59:59Z",
        exposed_facts=[
            "Embryonic stem cells are pluripotent.",
            "Cellular differentiation has historically been considered largely irreversible.",
            "Specific transcription factors (including Oct4 and Sox2) are enriched in embryonic stem cells and are necessary for maintaining pluripotency.",
        ],
        withheld_facts=[
            "Ectopic co-expression of only two transcription factors (Oct4 and Sox2) reprograms mouse fibroblasts to pluripotency at high efficiency without requiring Klf4 or c-Myc.",
        ],
        breakthrough_relationship=(
            "Ectopic co-expression of only two transcription factors (Oct4 and Sox2) reprograms "
            "differentiated somatic cells to pluripotency."
        ),
        forbidden_terms=[
            "two-factor reprogramming", "oct4-sox2 only",
        ],
        future_terminology=[
            "two-factor reprogramming",
        ],
        answer_mechanism=(
            "Oct4 and Sox2 co-bind and activate the endogenous pluripotency network without "
            "needing Klf4 or c-Myc."
        ),
        constraint_release=(
            "Releases the constraint that cellular differentiation is irreversible."
        ),
        historical_source="FABRICATED. Two-factor (Oct4 + Sox2 only) reprogramming has not been demonstrated robustly. Yamanaka's four-factor result was the actual breakthrough.",
    ),

    # ---- DSB-F-010: matched to DSB-R-010 (GAN) ----
    # Fabricated: energy-based model with adversarial discriminative critic
    make_case(
        case_id="DSB-F-010",
        domain="ml",
        name_internal="fabricated_ebm_adversarial",
        cutoff_date="2013-12-31T23:59:59Z",
        exposed_facts=[
            "Energy-based models assign scalar energy to configurations and learn by lowering energy on data and raising it elsewhere.",
            "Discriminative neural networks achieve high accuracy on classification tasks.",
            "Two-player zero-sum games in game theory have equilibrium solutions.",
            "Neural networks can approximate complex distributions given sufficient capacity.",
        ],
        withheld_facts=[
            "Training an energy-based model with a discriminative critic that classifies real versus low-energy samples produces sharp, realistic samples without explicit likelihood.",
        ],
        breakthrough_relationship=(
            "Training an energy-based model with a discriminative critic that classifies real "
            "versus low-energy samples produces sharp, realistic samples without explicit likelihood."
        ),
        forbidden_terms=[
            "ebm adversarial critic", "discriminator-trained energy model",
        ],
        future_terminology=[
            "adversarial EBM",
        ],
        answer_mechanism=(
            "The critic shapes the energy landscape by pushing data down and samples up. The "
            "energy model learns to produce low-energy samples that fool the critic."
        ),
        constraint_release=(
            "Releases the likelihood-averaging constraint of explicit generative models."
        ),
        historical_source="FABRICATED. While EBM variants exist, the specific 'discriminative critic for EBM' breakthrough as a 2014-era milestone did not historically occur in this form.",
    ),
]


def main():
    print(f"Building {len(CASES)} fabricated cases for DSB V1...")
    for case in CASES:
        ok, failures = validate_case(case)
        if not ok:
            print(f"  INVALID: {case['case_id']}")
            for f in failures:
                print(f"    - {f}")
            continue
        path = CASES_DIR / f"{case['case_id']}.json"
        with open(path, "w") as f:
            json.dump(case, f, indent=2, ensure_ascii=False)
        print(f"  {case['case_id']} ({case['name_internal']}): {len(case['exposed_facts'])} exposed, {len(case['withheld_facts'])} withheld")
    print(f"\nAll fabricated cases saved to {CASES_DIR}")


if __name__ == "__main__":
    main()
