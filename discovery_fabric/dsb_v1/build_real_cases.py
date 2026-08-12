"""Build the 10 real historical cases for DSB V1."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from case_schema import compute_answer_hash, validate_case

CASES_DIR = Path(__file__).parent / "cases" / "real"
CASES_DIR.mkdir(parents=True, exist_ok=True)


def make_case(case_id, domain, name_internal, cutoff_date, exposed_facts,
              withheld_facts, breakthrough_relationship, forbidden_terms,
              future_terminology, answer_mechanism, constraint_release,
              historical_source):
    return {
        "case_id": case_id,
        "case_type": "real",
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
        "fabricated": False,
    }


CASES = [
    # ---- DSB-R-001: Lithium-ion battery ----
    # Exposed: lithium metal batteries are unsafe + non-aqueous electrolytes exist + general challenge
    # Withheld: LiCoO2 intercalates Li (Whittingham 1976) + graphite intercalates Li + the combination
    make_case(
        case_id="DSB-R-001",
        domain="materials",
        name_internal="lithium_ion_battery",
        cutoff_date="1990-12-31T23:59:59Z",
        exposed_facts=[
            "Lithium metal batteries are unsafe due to dendrite formation during cycling.",
            "Non-aqueous electrolytes exist that can conduct lithium ions between electrodes.",
            "Rechargeable battery electrodes must support reversible ion insertion and extraction.",
            "The challenge is to build a safe rechargeable high-energy-density battery.",
        ],
        withheld_facts=[
            "Lithium cobalt oxide (LiCoO2) has been shown to reversibly intercalate lithium ions at a high potential (Whittingham, 1976).",
            "Graphite has been shown to reversibly intercalate lithium ions at a low potential.",
            "Combining a LiCoO2 cathode with a graphite anode in a non-aqueous electrolyte yields a rechargeable battery with high energy density and no lithium metal dendrite risk (Yoshino, 1985; Sony commercialized 1991).",
        ],
        breakthrough_relationship=(
            "Combining a lithium-intercalation cathode (LiCoO2) with a lithium-intercalation "
            "anode (graphite) in a non-aqueous electrolyte yields a safe, rechargeable, "
            "high-energy-density battery without lithium metal dendrites."
        ),
        forbidden_terms=[
            "lithium-ion", "li-ion", "licoo2", "graphite anode", "yoshino",
            "goodenough", "whittingham", "sony 1991",
        ],
        future_terminology=[
            "lithium-ion battery", "Li-ion", "LiCoO2-graphite", "rocking-chair battery",
        ],
        answer_mechanism=(
            "Both electrodes reversibly intercalate lithium ions at different potentials. "
            "On discharge, lithium ions migrate from the graphite anode to the LiCoO2 cathode "
            "through the non-aqueous electrolyte; on charge, they migrate back. No lithium "
            "metal is ever plated, eliminating dendrite formation."
        ),
        constraint_release=(
            "Releases the safety constraint imposed by lithium metal dendrites, enabling "
            "rechargeable high-energy batteries."
        ),
        historical_source="Whittingham 1976; Goodenough 1980; Yoshino 1985; Sony commercialization 1991; Nobel Chemistry 2019.",
    ),

    # ---- DSB-R-002: PCR ----
    # Exposed: DNA polymerase + heat denaturation + oligonucleotide synthesis (the components)
    # Withheld: the cyclic temperature protocol + the use of thermostable polymerase + the exponential amplification
    make_case(
        case_id="DSB-R-002",
        domain="biology",
        name_internal="pcr",
        cutoff_date="1984-12-31T23:59:59Z",
        exposed_facts=[
            "DNA polymerase enzymes extend short oligonucleotide primers along a DNA template.",
            "Heating double-stranded DNA denatures it into single strands; cooling allows re-annealing.",
            "Synthetic oligonucleotides of arbitrary sequence can be chemically manufactured.",
            "Measuring a specific DNA sequence requires producing enough copies to detect.",
        ],
        withheld_facts=[
            "Thermophilic bacteria such as Thermus aquaticus produce heat-stable DNA polymerases (Taq) that survive repeated heating (Chien 1976; Saiki 1988).",
            "Cycling the temperature through denaturation, annealing, and extension steps with a thermostable polymerase and two flanking primers doubles the target sequence each cycle, yielding exponential amplification (Mullis 1983; Saiki 1985).",
        ],
        breakthrough_relationship=(
            "Cyclically heating and cooling a DNA sample with flanking primers and a thermostable "
            "DNA polymerase exponentially amplifies a specific DNA sequence, yielding million-fold "
            "copy numbers without cellular cloning."
        ),
        forbidden_terms=[
            "pcr", "polymerase chain reaction", "taq", "thermus aquaticus",
            "mullis", "saiki 1985", "thermal cycler",
        ],
        future_terminology=[
            "PCR", "Taq polymerase", "thermal cycling", "primer extension amplification",
        ],
        answer_mechanism=(
            "Each temperature cycle (denature → anneal → extend) doubles the number of target "
            "copies. Using a thermostable polymerase means the enzyme survives denaturation, "
            "so the cycle can be repeated without adding fresh enzyme. N cycles yield 2^N copies."
        ),
        constraint_release=(
            "Releases the constraint of needing cellular cloning to produce detectable DNA "
            "quantities, enabling in-vitro exponential amplification."
        ),
        historical_source="Mullis 1983 (idea); Saiki et al. 1985 (first implementation); Nobel Chemistry 1993.",
    ),

    # ---- DSB-R-003: Graphene ----
    # Exposed: graphite is layered + theory says 2D crystals are unstable + mechanical cleavage is known
    # Withheld: scotch-tape repeated peeling isolates single layers + the actual isolation
    make_case(
        case_id="DSB-R-003",
        domain="materials",
        name_internal="graphene",
        cutoff_date="2003-12-31T23:59:59Z",
        exposed_facts=[
            "Graphite is a crystalline form of carbon arranged in stacked two-dimensional layers held together by weak van der Waals forces.",
            "Theory predicts that strictly two-dimensional crystals are thermodynamically unstable at finite temperature due to long-wavelength fluctuations (Landau-Peierls).",
            "Mechanical cleavage of layered materials is a known technique for thinning samples.",
            "Carbon nanotubes — rolled-up single atomic sheets of carbon — are known to exist and have useful electronic properties.",
        ],
        withheld_facts=[
            "Repeated mechanical exfoliation of graphite using adhesive tape can isolate single-atom-thick carbon layers visible under an optical microscope on a silicon wafer (Novoselov & Geim, 2004).",
            "Single-layer graphene is metastable but persists at room temperature and exhibits exceptionally high electron mobility and the quantum Hall effect at room temperature.",
        ],
        breakthrough_relationship=(
            "Repeated mechanical exfoliation of graphite using adhesive tape isolates stable "
            "single-atom-thick carbon sheets (graphene) at room temperature, contradicting the "
            "Landau-Peierls prediction."
        ),
        forbidden_terms=[
            "graphene", "scotch tape", "novoselov", "geim", "exfoliated monolayer",
            "single-layer graphite",
        ],
        future_terminology=[
            "graphene", "scotch-tape method", "mechanical exfoliation of graphite", "2D materials",
        ],
        answer_mechanism=(
            "Adhesive tape applied to graphite and peeled away removes a thin layer. Repeating "
            "this on the residue progressively thins the sample. On a silicon wafer with the "
            "right oxide thickness, even a single atomic layer produces a faint optical contrast "
            "that allows it to be located under a microscope."
        ),
        constraint_release=(
            "Releases the theoretical constraint that 2D crystals cannot exist at finite "
            "temperature, opening the field of two-dimensional materials."
        ),
        historical_source="Novoselov & Geim 2004 (Science); Nobel Physics 2010.",
    ),

    # ---- DSB-R-004: AlexNet (deep CNN on GPU) ----
    # Exposed: CNNs + GPUs + ImageNet + ReLU + Dropout
    # Withheld: the specific deep+wide CNN architecture trained on GPU with ReLU+dropout beats SVMs by 10pp
    make_case(
        case_id="DSB-R-004",
        domain="ml",
        name_internal="alexnet",
        cutoff_date="2011-12-31T23:59:59Z",
        exposed_facts=[
            "Convolutional neural networks can learn translation-invariant visual features but have been limited to shallow architectures and small datasets.",
            "Graphics processing units (GPUs) provide massive parallel floating-point throughput suitable for matrix multiplication.",
            "Large labeled image datasets such as ImageNet contain over one million images across one thousand categories.",
            "Rectified linear units (ReLUs) avoid the vanishing-gradient problem of sigmoid activations.",
            "Dropout is a regularization technique that prevents co-adaptation of hidden units during training.",
            "Support vector machines and shallow hand-engineered features dominate ImageNet benchmarks at approximately 25 percent top-5 error.",
        ],
        withheld_facts=[
            "Training a deep (eight-layer) convolutional network with ReLU activations and dropout on two GPUs using ImageNet reduces top-5 error from approximately 26 percent to approximately 15 percent (Krizhevsky, Sutskever, Hinton, 2012).",
        ],
        breakthrough_relationship=(
            "A deep (5+ layer) convolutional neural network with ReLU activations and dropout, "
            "trained on GPUs on a million-image dataset, reduces image-classification top-5 error "
            "by approximately 10 percentage points over the previous shallow-feature state of the art."
        ),
        forbidden_terms=[
            "alexnet", "krizhevsky", "sutskever", "hinton 2012", "imagenet 2012 winner",
        ],
        future_terminology=[
            "AlexNet", "deep learning revolution", "GPU-trained CNN", "ImageNet 2012",
        ],
        answer_mechanism=(
            "Depth allows the network to learn a hierarchy of features from edges to object parts. "
            "ReLU enables training of deep networks without vanishing gradients. Dropout prevents "
            "overfitting on the million-image dataset. GPU parallelism makes training the large "
            "model tractable in weeks rather than months."
        ),
        constraint_release=(
            "Releases the depth constraint on trainable CNNs imposed by vanishing gradients and "
            "training cost, enabling deep learning."
        ),
        historical_source="Krizhevsky, Sutskever, Hinton 2012 (NeurIPS); widely cited as the start of the deep learning era.",
    ),

    # ---- DSB-R-005: Perovskite solar cells ----
    # Exposed: DSSCs exist at ~11% + perovskites are known materials + liquid electrolyte limits DSSC stability
    # Withheld: perovskites as solid-state absorbers in place of dye + liquid electrolyte → ~25% efficiency
    make_case(
        case_id="DSB-R-005",
        domain="materials",
        name_internal="perovskite_solar",
        cutoff_date="2008-12-31T23:59:59Z",
        exposed_facts=[
            "Dye-sensitized solar cells (DSSCs) achieve approximately 11 percent power conversion efficiency using a ruthenium dye on titanium dioxide with a liquid iodide electrolyte.",
            "Organic-inorganic lead halide perovskites (such as CH3NH3PbI3) are known crystalline materials with strong light absorption and long carrier diffusion lengths.",
            "The liquid electrolyte in DSSCs limits long-term stability and creates packaging challenges.",
            "Solid-state hole-transport materials such as spiro-OMeTAD exist but solid-state DSSCs have lower efficiency than liquid versions.",
        ],
        withheld_facts=[
            "Using a lead-halide perovskite as the absorber in a solid-state sensitized architecture (replacing both the dye and the liquid electrolyte) yields a stable cell with efficiency rising from 3.8 percent (Kojima 2009) to over 25 percent by 2020.",
        ],
        breakthrough_relationship=(
            "Replacing the dye and liquid electrolyte in a sensitized solar cell with a lead-halide "
            "perovskite absorber and a solid-state hole transporter yields a high-efficiency (>20 percent) "
            "stable solution-processable photovoltaic."
        ),
        forbidden_terms=[
            "perovskite solar cell", "kojima 2009", "solid-state perovskite", "mapbi3 solar",
        ],
        future_terminology=[
            "perovskite solar cell", "PSC", "lead-halide perovskite photovoltaic",
        ],
        answer_mechanism=(
            "The perovskite absorbs light and generates free carriers (rather than excitons bound "
            "to a dye). Its long carrier diffusion length allows efficient charge collection in a "
            "thin film. Solid-state architecture eliminates the stability-limiting liquid electrolyte."
        ),
        constraint_release=(
            "Releases the efficiency-stability trade-off of liquid-electrolyte DSSCs, enabling "
            "solution-processable high-efficiency photovoltaics."
        ),
        historical_source="Kojima et al. 2009 (first perovskite-sensitized cell, 3.8%); Lee et al. 2012; Snaith group; efficiency >25% by 2020.",
    ),

    # ---- DSB-R-006: mRNA vaccines ----
    # Exposed: modified nucleosides reduce immunogenicity + LNP delivery + spike protein target
    # Withheld: the specific combination → 95% efficacy in months
    make_case(
        case_id="DSB-R-006",
        domain="biology",
        name_internal="mrna_vaccine",
        cutoff_date="2019-12-31T23:59:59Z",
        exposed_facts=[
            "In vitro transcribed mRNA triggers innate immune sensors (TLR7/8) that degrade the mRNA and prevent therapeutic translation.",
            "Replacing uridine with pseudouridine or N1-methylpseudouridine in synthetic mRNA reduces TLR recognition and increases translation (modified-nucleoside chemistry).",
            "Lipid nanoparticles (LNPs) efficiently deliver nucleic acids into the cytoplasm of cells in vivo.",
            "Viral surface proteins such as the SARS-CoV-2 spike protein are the primary target of neutralizing antibodies.",
            "Conventional vaccine platforms (live-attenuated, inactivated, subunit) require months to years of manufacturing scale-up.",
        ],
        withheld_facts=[
            "Encapsulating N1-methylpseudouridine-modified mRNA encoding the SARS-CoV-2 spike protein in an LNP and injecting it intramuscularly induces neutralizing antibodies at protective titers within weeks (Polack et al. 2020; 95 percent efficacy in Phase 3).",
        ],
        breakthrough_relationship=(
            "Encapsulating N1-methylpseudouridine-modified mRNA encoding a viral spike protein in "
            "a lipid nanoparticle, injected intramuscularly, induces protective neutralizing "
            "antibodies within weeks at over 90 percent efficacy."
        ),
        forbidden_terms=[
            "mrna vaccine", "biontech", "pfizer-biontech", "polack 2020", "moderna",
        ],
        future_terminology=[
            "mRNA vaccine", "modified-mRNA LNP vaccine", "COVID-19 mRNA vaccine",
        ],
        answer_mechanism=(
            "Modified mRNA evades innate immunity long enough to be translated by host ribosomes "
            "into the viral spike protein. The LNP delivers the mRNA into the cytoplasm. The "
            "translated spike triggers adaptive B-cell and T-cell responses. Manufacturing is "
            "sequence-defined and scalable in weeks."
        ),
        constraint_release=(
            "Releases the time-to-scale constraint of conventional vaccine platforms, enabling "
            "pandemic-speed vaccine development."
        ),
        historical_source="Kariko/Weissman 2005 (modified nucleosides); Polack et al. 2020 (Pfizer-BioNTech Phase 3); Nobel Medicine 2023.",
    ),

    # ---- DSB-R-007: CRISPR-Cas9 gene editing ----
    # Exposed: bacterial CRISPR is adaptive immunity + Cas9 is a nuclease + ZFN/TALENs are hard to redesign
    # Withheld: guide RNA + Cas9 → programmable DNA cleavage in human cells
    make_case(
        case_id="DSB-R-007",
        domain="biology",
        name_internal="crispr_cas9",
        cutoff_date="2011-12-31T23:59:59Z",
        exposed_facts=[
            "Bacterial CRISPR loci encode an adaptive immune system that stores snippets of phage DNA as spacers between repeat sequences.",
            "The Cas9 protein from Streptococcus pyogenes is a DNA endonuclease guided by a dual RNA (crRNA + tracrRNA) complex.",
            "Zinc-finger nucleases and TALENs can cut specific genomic loci but require protein engineering for each new target.",
            "Double-strand DNA breaks stimulate endogenous repair pathways (NHEJ or HDR) that can disrupt or replace a gene.",
        ],
        withheld_facts=[
            "Fusing the crRNA and tracrRNA into a single guide RNA (sgRNA) and co-expressing it with Cas9 in human cells achieves programmable sequence-specific DNA cleavage at any locus defined by a 20-nucleotide guide (Jinek, Charpentier, Doudna, 2012).",
        ],
        breakthrough_relationship=(
            "A single guide RNA fused from crRNA and tracrRNA directs the Cas9 nuclease to cut "
            "any genomic locus defined by a 20-nucleotide target sequence, enabling programmable "
            "gene editing in cells."
        ),
        forbidden_terms=[
            "crispr-cas9", "crispr/cas9", "jinek 2012", "doudna", "charpentier", "sgRNA",
        ],
        future_terminology=[
            "CRISPR-Cas9", "sgRNA", "programmed CRISPR editing", "CRISPR gene editing",
        ],
        answer_mechanism=(
            "The 20-nucleotide spacer of the sgRNA base-pairs with the genomic target adjacent "
            "to a PAM sequence. Cas9 then cleaves both DNA strands. The resulting double-strand "
            "break is repaired by NHEJ (knockout) or HDR (knock-in) using a co-delivered template."
        ),
        constraint_release=(
            "Releases the protein-engineering constraint of ZFNs/TALENs, enabling any lab to "
            "target any locus by changing only the sgRNA sequence."
        ),
        historical_source="Jinek et al. 2012 (Science); Cong/Zhang 2013 (human cells); Nobel Chemistry 2020.",
    ),

    # ---- DSB-R-008: Checkpoint immunotherapy (anti-PD-1) ----
    # Exposed: PD-1 suppresses T-cells + CTLA-4 blockade works in melanoma + tumor microenvironment suppresses T-cells
    # Withheld: anti-PD-1 antibody → durable responses in cancer patients
    make_case(
        case_id="DSB-R-008",
        domain="biology",
        name_internal="checkpoint_anti_pd1",
        cutoff_date="2011-12-31T23:59:59Z",
        exposed_facts=[
            "PD-1 is a receptor expressed on activated T-cells that dampens T-cell activity when engaged by its ligands.",
            "Blocking the CTLA-4 checkpoint with an antibody (ipilimumab) produces durable responses in melanoma patients.",
            "Many tumors upregulate immunosuppressive ligands in their local environment, correlating with T-cell exhaustion and poor prognosis.",
            "Cancer vaccines that activate T-cells have largely failed in clinical trials because activated T-cells become functionally silenced inside tumors.",
        ],
        withheld_facts=[
            "An antibody that blocks PD-1 (nivolumab, pembrolizumab) releases T-cell suppression in the tumor microenvironment and produces durable responses in melanoma, lung, and kidney cancer patients (Brahmer 2012; Topalian 2012).",
        ],
        breakthrough_relationship=(
            "An antibody blocking the PD-1 receptor on T-cells releases T-cell suppression in "
            "the tumor microenvironment, producing durable responses in multiple cancer types."
        ),
        forbidden_terms=[
            "anti-pd-1", "nivolumab", "pembrolizumab", "brahmer 2012", "topalian 2012",
            "checkpoint immunotherapy", "keytruda", "opdivo",
        ],
        future_terminology=[
            "PD-1 inhibitor", "checkpoint immunotherapy", "immune checkpoint blockade",
        ],
        answer_mechanism=(
            "PD-1 engagement by tumor PD-L1 suppresses T-cell effector function. Blocking PD-1 "
            "with an antibody releases the brake, allowing tumor-specific T-cells to kill tumor "
            "cells. This works across tumor types that use PD-L1 as an immune-evasion mechanism."
        ),
        constraint_release=(
            "Releases the constraint that tumor-specific T-cells are functionally suppressed "
            "in the tumor microenvironment."
        ),
        historical_source="Brahmer et al. 2012 (nivolumab, NEJM); Topalian et al. 2012; Nobel Medicine 2018 (Allison/Honjo).",
    ),

    # ---- DSB-R-009: iPSCs (induced pluripotent stem cells) ----
    # Exposed: ES cells are pluripotent + differentiation is considered irreversible + TFs control cell fate
    # Withheld: 4 TFs (Oct4, Sox2, Klf4, c-Myc) reprogram somatic cells to pluripotency
    make_case(
        case_id="DSB-R-009",
        domain="biology",
        name_internal="ipsc",
        cutoff_date="2005-12-31T23:59:59Z",
        exposed_facts=[
            "Embryonic stem cells are pluripotent — they can differentiate into all three germ layers.",
            "Cellular differentiation has historically been considered largely irreversible in somatic cells.",
            "Somatic cell nuclear transfer (cloning) can reprogram a differentiated nucleus to pluripotency, but requires an oocyte and is inefficient.",
            "Specific transcription factors (including Oct4, Sox2, Klf4, and c-Myc) are enriched in embryonic stem cells and are necessary for maintaining pluripotency.",
        ],
        withheld_facts=[
            "Ectopic co-expression of four transcription factors (Oct4, Sox2, Klf4, c-Myc) in differentiated mouse fibroblasts reprograms them to induced pluripotent stem cells (Takahashi & Yamanaka, 2006).",
        ],
        breakthrough_relationship=(
            "Ectopic co-expression of four embryonic transcription factors (Oct4, Sox2, Klf4, "
            "c-Myc) in differentiated somatic cells reprograms them to a pluripotent state "
            "without requiring an oocyte."
        ),
        forbidden_terms=[
            "ipsc", "ipscs", "induced pluripotent", "takahashi", "yamanaka",
            "reprogramming factors",
        ],
        future_terminology=[
            "iPSC", "induced pluripotent stem cell", "Yamanaka factors", "reprogramming TFs",
        ],
        answer_mechanism=(
            "The four transcription factors bind and activate the endogenous pluripotency "
            "network, overriding the differentiation program. After reprogramming, the exogenous "
            "factors can be removed and the cells maintain pluripotency autonomously."
        ),
        constraint_release=(
            "Releases the constraint that cellular differentiation is irreversible and that "
            "reprogramming requires an oocyte."
        ),
        historical_source="Takahashi & Yamanaka 2006 (Cell); Nobel Medicine 2012.",
    ),

    # ---- DSB-R-010: GANs ----
    # Exposed: generative models produce blurry outputs + discriminative models classify well + adversarial training is from game theory
    # Withheld: training a generator against a discriminator produces sharp realistic samples
    make_case(
        case_id="DSB-R-010",
        domain="ml",
        name_internal="gan",
        cutoff_date="2013-12-31T23:59:59Z",
        exposed_facts=[
            "Generative models that maximize likelihood (such as deep Boltzmann machines and variational autoencoders) tend to produce blurry samples because they average over modes.",
            "Discriminative neural networks achieve high accuracy on classification tasks.",
            "Two-player zero-sum games in game theory have equilibrium solutions where neither player benefits from changing strategy.",
            "Neural networks can approximate complex distributions given sufficient capacity and training data.",
        ],
        withheld_facts=[
            "Training two networks simultaneously — a generator that maps noise to samples and a discriminator that distinguishes real from generated samples — in an adversarial zero-sum game produces a generator that outputs sharp, realistic samples (Goodfellow et al. 2014).",
        ],
        breakthrough_relationship=(
            "Training a generator network against a discriminator network in an adversarial "
            "zero-sum game produces a generator that maps noise to sharp, realistic samples "
            "without requiring an explicit likelihood."
        ),
        forbidden_terms=[
            "gan", "generative adversarial", "goodfellow 2014", "adversarial generator-discriminator",
        ],
        future_terminology=[
            "GAN", "generative adversarial network", "adversarial training",
        ],
        answer_mechanism=(
            "The generator learns to fool the discriminator; the discriminator learns to detect "
            "fakes. At equilibrium, the generator produces samples indistinguishable from real "
            "data. Bypassing explicit likelihood avoids the mode-averaging that causes blurriness."
        ),
        constraint_release=(
            "Releases the likelihood-averaging constraint of explicit generative models, enabling "
            "sharp sample generation."
        ),
        historical_source="Goodfellow et al. 2014 (NeurIPS).",
    ),
]


def main():
    print(f"Building {len(CASES)} real cases for DSB V1...")
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
    print(f"\nAll real cases saved to {CASES_DIR}")


if __name__ == "__main__":
    main()
