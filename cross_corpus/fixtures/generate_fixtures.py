"""
Fixture generator for the cross-corpus pilot (Issue #4).

Produces 500 papers + 500 patent-family members across 10 domains. The
fixtures are SYNTHETIC-BUT-FAITHFUL: they use realistic field shapes (DOIs,
DOCDB family ids, EPO citation roles, INPADOC priority chains, atomic claims)
so the engine exercises its full ingest/graph/motif/null/forensic stack.

Each domain gets:
  - 50 papers
  - 50 patents grouped into ~30 DOCDB families
  - planted instances of each of the 10 motifs (so tests can verify detection)

Planting strategy:
  - m01 (constraint_release): 1 paper (old, with constraint) + 1 patent (X-cites
    old paper) + 1 paper (newer, same mechanism, drops constraint).
  - m02 (paper_patent_gap): 1 paper with mechanism+domain that has NO later patent.
  - m03 (patent_science_gap): 1 patent with mech+mat that has NO later paper.
  - m04 (paper_failure_patent_workaround): 1 paper with reported_failure + 1
    patent with same mech+mat, no citation.
  - m05 (old_science_new_patent): 1 paper >5yrs before patent on same mech, no cite.
  - m06 (two_papers_two_families): 2 papers in different domains + 2 families.
  - m07 (three_papers_one_patent): 3 independent papers + 1 patent.
  - m08 (one_paper_three_families): 1 paper + 3 families with different mats.
  - m09 (jurisdictional_divergence): 1 family with 2 members, divergent claims.
  - m10 (unexplained_bridge): 1 paper + 1 patent sharing >=2 features, no cite.

All planted instances are detectable; the rest of the corpus is background noise.
"""
from __future__ import annotations
import json
import random
from pathlib import Path
from datetime import date, timedelta

# Fix a seed so the corpus is reproducible
SEED = 4242

DOMAINS = [
    "battery_electrochemistry",
    "perovskite_photovoltaics",
    "crispr_gene_editing",
    "mrna_therapeutics",
    "solid_state_lighting",
    "carbon_capture",
    "hydrogen_electrocatalysis",
    "neuromorphic_computing",
    "topological_insulators",
    "additive_manufacturing",
]

DOMAIN_MECHANISMS = {
    "battery_electrochemistry": ["intercalation", "conversion", "alloying", "solid_electrolyte_interphase"],
    "perovskite_photovoltaics": ["bandgap_engineering", "defect_passivation", "interface_engineering"],
    "crispr_gene_editing": ["double_strand_break", "base_editing", "prime_editing"],
    "mrna_therapeutics": ["lipid_nanoparticle_delivery", "cap_analog", "modified_nucleoside"],
    "solid_state_lighting": ["quantum_confinement", "phosphor_conversion", "radiative_recombination"],
    "carbon_capture": ["amine_scrubbing", "membrane_separation", "metal_organic_framework_adsorption"],
    "hydrogen_electrocatalysis": ["hydrogen_evolution_reaction", "oxygen_evolution_reaction", "proton_conductivity"],
    "neuromorphic_computing": ["spike_timing_dependent_plasticity", "memristive_switching", "analog_weight_storage"],
    "topological_insulators": ["surface_state_conduction", "bulk_band_inversion", "spin_momentum_locking"],
    "additive_manufacturing": ["laser_powder_bed_fusion", "directed_energy_deposition", "binder_jetting"],
}

DOMAIN_MATERIALS = {
    "battery_electrochemistry": ["LiCoO2", "Li7La3Zr2O12", "LiFePO4", "graphite", "Si_anode"],
    "perovskite_photovoltaics": ["MAPbI3", "FAPbBr3", "CsPbI3", "Spiro_OMeTAD"],
    "crispr_gene_editing": ["Cas9", "Cas12a", "CasX", "guide_RNA"],
    "mrna_therapeutics": ["ionizable_lipid", "PEG_lipid", "m5C_modified_mRNA"],
    "solid_state_lighting": ["GaN", "YAG_Ce", "CsPbBr3_QD", "InGaN_QW"],
    "carbon_capture": ["MEA", "zeolite_13X", "Mg_MOF_74", "ZIF_8"],
    "hydrogen_electrocatalysis": ["Pt_C", "NiFe_LD", "MoS2", "IrO2"],
    "neuromorphic_computing": ["HfO2_RRAM", "TaOx_MEM", "WO3_PCM"],
    "topological_insulators": ["Bi2Se3", "Bi2Te3", "Sb2Te3", "HgTe_QW"],
    "additive_manufacturing": ["IN718_powder", "Ti6Al4V_powder", "316L_powder", "AlSi10Mg_powder"],
}


def _d(offset_days: int, base: date = date(2024, 1, 1)) -> str:
    return (base + timedelta(days=offset_days)).isoformat()


def _gen_priority_chain(d: str) -> list[str]:
    return [f"PRIORITY_CHAIN:{d}"]


def gen_corpus(out_dir: Path, seed: int = SEED):
    rng = random.Random(seed)
    papers: list[dict] = []
    patents: list[dict] = []
    paper_seq = 0
    patent_seq = 0
    family_seq = 0

    for domain in DOMAINS:
        mechs = DOMAIN_MECHANISMS[domain]
        mats = DOMAIN_MATERIALS[domain]
        # ---- ~48 background papers per domain spread across 2015-2024 ----
        for i in range(48):
            paper_seq += 1
            pub = _d(rng.randint(-365 * 9, -1))  # 2015 to 2023-12-31
            mech = rng.choice(mechs)
            mat = rng.choice(mats)
            papers.append({
                "paper_id": f"paper:{domain}:bg{paper_seq}",
                "doi": f"10.1000/{domain}.{paper_seq}",
                "title": f"Background study {paper_seq} in {domain}",
                "abstract": f"Studies {mech} using {mat}.",
                "publication_date": pub,
                "authors": [f"Author_{rng.randint(1, 500)}"],
                "domain": domain,
                "mechanisms": [mech],
                "materials": [mat],
                "processes": [],
                "claims": [{
                    "subject": f"material:{mat}",
                    "predicate": "achieves_property",
                    "obj": f"property:{mech}_performance",
                    "value": f"{rng.uniform(0.1, 0.9):.2f}",
                    "negated": False,
                }],
                "citations": [],
                "reported_failures": [],
                "ingestion_source": "synthetic_fixture",
            })

        # ---- ~45 background patent families per domain (2-3 members each) ----
        for i in range(45):
            family_seq += 1
            fid = f"fam:DOCDB:{domain[0:3]}{family_seq:06d}"
            prio = _d(rng.randint(-365 * 8, -30))
            # 2-3 members per family
            n_members = rng.randint(2, 3)
            jurisdictions_pool = ["EP", "US", "JP", "CN", "KR"]
            chosen_juris = rng.sample(jurisdictions_pool, rng.randint(1, 3))
            mech = rng.choice(mechs)
            mat = rng.choice(mats)
            for j in range(n_members):
                patent_seq += 1
                jur = chosen_juris[j % len(chosen_juris)]
                patents.append({
                    "patent_id": f"patent:{jur}:{domain}:bg{patent_seq}",
                    "docdb_family_id": fid,
                    "publication_date": _d(rng.randint(0, 365 * 2)),
                    "priority_date": prio,
                    "jurisdictions": [jur],
                    "inventors": [f"Inventor_{rng.randint(1, 200)}"],
                    "assignee": f"Corp_{rng.randint(1, 50)}",
                    "title": f"Patent {patent_seq} on {mech}",
                    "abstract": f"Claims {mech} with {mat}.",
                    "domain": domain,
                    "mechanisms": [mech],
                    "materials": [mat],
                    "processes": [f"PRIORITY_CHAIN:{prio}", "process_X"],
                    "claims": [{
                        "subject": f"material:{mat}",
                        "predicate": "achieves_property",
                        "obj": f"property:{mech}_performance",
                        "value": f"{rng.uniform(0.5, 0.99):.2f}",
                        "negated": False,
                    }],
                    "citations": [],
                    "ingestion_source": "synthetic_fixture",
                })

        # ---- planted motifs ----
        _plant_m01(papers, patents, domain, mechs, mats, rng, paper_seq, patent_seq)
        _plant_m02(papers, patents, domain, mechs, mats, rng)
        _plant_m03(papers, patents, domain, mechs, mats, rng)
        _plant_m04(papers, patents, domain, mechs, mats, rng)
        _plant_m05(papers, patents, domain, mechs, mats, rng)
        _plant_m09(papers, patents, domain, mechs, mats, rng)
        _plant_m10(papers, patents, domain, mechs, mats, rng)

    # m06/m07/m08 are cross-domain — plant after all domains exist
    _plant_m06(papers, patents, rng)
    _plant_m07(papers, patents, rng)
    _plant_m08(papers, patents, rng)

    # Write
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "papers.jsonl").open("w") as f:
        for p in papers:
            f.write(json.dumps(p, sort_keys=True) + "\n")
    with (out_dir / "patents.jsonl").open("w") as f:
        for p in patents:
            f.write(json.dumps(p, sort_keys=True) + "\n")
    return {"papers": len(papers), "patents": len(patents)}


# ---------- motif planters ----------

def _plant_m01(papers, patents, domain, mechs, mats, rng, pseq_start, pat_start):
    mech = rng.choice(mechs)
    mat = rng.choice(mats)
    old_pub = _d(rng.randint(-365 * 8, -365 * 4))
    pat_prio = _d(rng.randint(-365 * 2, -365))
    new_pub = _d(rng.randint(-180, -30))
    old_id = f"paper:{domain}:m01_old"
    pat_id = f"patent:EP:{domain}:m01_pat"
    new_id = f"paper:{domain}:m01_new"
    papers.append({
        "paper_id": old_id,
        "publication_date": old_pub,
        "domain": domain,
        "mechanisms": [mech],
        "materials": [mat],
        "claims": [{
            "subject": f"material:{mat}", "predicate": "requires_temperature_le",
            "obj": "property:operating_temp", "value": "200C", "negated": False,
        }],
        "citations": [], "reported_failures": [],
        "title": "M01 old", "abstract": "old constraint", "authors": [],
        "processes": [], "ingestion_source": "synthetic_fixture",
    })
    papers.append({
        "paper_id": new_id,
        "publication_date": new_pub,
        "domain": domain,
        "mechanisms": [mech],
        "materials": [mat],
        "claims": [{
            "subject": f"material:{mat}", "predicate": "achieves_property",
            "obj": f"property:{mech}_performance", "value": "0.9", "negated": False,
        }],
        "citations": [], "reported_failures": [],
        "title": "M01 new", "abstract": "drops constraint", "authors": [],
        "processes": [], "ingestion_source": "synthetic_fixture",
    })
    patents.append({
        "patent_id": pat_id,
        "docdb_family_id": f"fam:DOCDB:m01{domain}",
        "publication_date": _d(rng.randint(-365, -30)),
        "priority_date": pat_prio,
        "jurisdictions": ["EP"],
        "inventors": [], "assignee": "Corp_M01",
        "domain": domain, "mechanisms": [mech], "materials": [mat],
        "processes": [f"PRIORITY_CHAIN:{pat_prio}"],
        "claims": [],
        "citations": [{
            "source_id": pat_id, "target_id": old_id, "source_kind": "patent",
            "target_kind": "paper", "role": "X",
            "citation_date": pat_prio,
        }],
        "title": "M01 pat", "abstract": "", "ingestion_source": "synthetic_fixture",
    })


def _plant_m02(papers, patents, domain, mechs, mats, rng):
    mech = rng.choice(mechs)
    mat = rng.choice(mats)
    paper_id = f"paper:{domain}:m02_gap"
    papers.append({
        "paper_id": paper_id,
        "publication_date": _d(rng.randint(-365 * 3, -365)),
        "domain": domain, "mechanisms": [mech], "materials": [mat],
        "claims": [{
            "subject": f"material:{mat}", "predicate": "achieves_property",
            "obj": f"property:{mech}_performance", "value": "0.8", "negated": False,
        }],
        "citations": [], "reported_failures": [],
        "title": "M02 gap", "abstract": "", "authors": [],
        "processes": [], "ingestion_source": "synthetic_fixture",
    })


def _plant_m03(papers, patents, domain, mechs, mats, rng):
    mech = rng.choice(mechs)
    mat = rng.choice(mats)
    prio = _d(rng.randint(-365 * 4, -365 * 2))
    pat_id = f"patent:US:{domain}:m03_gap"
    patents.append({
        "patent_id": pat_id,
        "docdb_family_id": f"fam:DOCDB:m03{domain}",
        "publication_date": _d(rng.randint(-365 * 2, -365)),
        "priority_date": prio,
        "jurisdictions": ["US"], "inventors": [], "assignee": "Corp_M03",
        "domain": domain, "mechanisms": [mech], "materials": [mat],
        "processes": [f"PRIORITY_CHAIN:{prio}"],
        "claims": [{
            "subject": f"material:{mat}", "predicate": "achieves_property",
            "obj": f"property:{mech}_performance", "value": "0.95", "negated": False,
        }],
        "citations": [],
        "title": "M03 gap", "abstract": "", "ingestion_source": "synthetic_fixture",
    })


def _plant_m04(papers, patents, domain, mechs, mats, rng):
    mech = rng.choice(mechs)
    mat = rng.choice(mats)
    paper_id = f"paper:{domain}:m04_fail"
    pat_id = f"patent:EP:{domain}:m04_work"
    papers.append({
        "paper_id": paper_id,
        "publication_date": _d(rng.randint(-365 * 4, -365 * 2)),
        "domain": domain, "mechanisms": [mech], "materials": [mat],
        "claims": [], "citations": [],
        "reported_failures": [f"failure of {mat} under {mech}"],
        "title": "M04 fail", "abstract": "", "authors": [],
        "processes": [], "ingestion_source": "synthetic_fixture",
    })
    prio = _d(rng.randint(-365, -30))
    patents.append({
        "patent_id": pat_id,
        "docdb_family_id": f"fam:DOCDB:m04{domain}",
        "publication_date": _d(rng.randint(-30, -1)),
        "priority_date": prio,
        "jurisdictions": ["EP"], "inventors": [], "assignee": "Corp_M04",
        "domain": domain, "mechanisms": [mech], "materials": [mat],
        "processes": [f"PRIORITY_CHAIN:{prio}"],
        "claims": [{
            "subject": f"material:{mat}", "predicate": "achieves_property",
            "obj": f"property:{mech}_performance", "value": "0.9", "negated": False,
        }],
        "citations": [],  # does NOT cite the failure paper
        "title": "M04 work", "abstract": "", "ingestion_source": "synthetic_fixture",
    })


def _plant_m05(papers, patents, domain, mechs, mats, rng):
    mech = rng.choice(mechs)
    mat = rng.choice(mats)
    paper_id = f"paper:{domain}:m05_old"
    pat_id = f"patent:JP:{domain}:m05_enabling"
    old_pub = _d(-365 * 10)
    pat_prio = _d(-365 * 2)
    papers.append({
        "paper_id": paper_id,
        "publication_date": old_pub,
        "domain": domain, "mechanisms": [mech], "materials": [mat],
        "claims": [{
            "subject": f"material:{mat}", "predicate": "describes_mechanism",
            "obj": f"mechanism:{mech}", "negated": False,
        }],
        "citations": [], "reported_failures": [],
        "title": "M05 foundational", "abstract": "", "authors": [],
        "processes": [], "ingestion_source": "synthetic_fixture",
    })
    patents.append({
        "patent_id": pat_id,
        "docdb_family_id": f"fam:DOCDB:m05{domain}",
        "publication_date": _d(-365),
        "priority_date": pat_prio,
        "jurisdictions": ["JP"], "inventors": [], "assignee": "Corp_M05",
        "domain": domain, "mechanisms": [mech], "materials": [mat],
        "processes": [f"PRIORITY_CHAIN:{pat_prio}"],
        "claims": [],
        "citations": [],  # does NOT cite foundational
        "title": "M05 enabling", "abstract": "", "ingestion_source": "synthetic_fixture",
    })


def _plant_m09(papers, patents, domain, mechs, mats, rng):
    mech = rng.choice(mechs)
    mat = rng.choice(mats)
    prio = _d(rng.randint(-365 * 3, -365 * 2))
    fid = f"fam:DOCDB:m09{domain}"
    # EP member: many claims
    ep_id = f"patent:EP:{domain}:m09_big"
    patents.append({
        "patent_id": ep_id,
        "docdb_family_id": fid,
        "publication_date": _d(-365),
        "priority_date": prio,
        "jurisdictions": ["EP"], "inventors": [], "assignee": "Corp_M09",
        "domain": domain, "mechanisms": [mech], "materials": [mat],
        "processes": [f"PRIORITY_CHAIN:{prio}"],
        "claims": [
            {"subject": f"material:{mat}", "predicate": "achieves_property",
             "obj": f"property:{mech}_perf", "value": "0.9", "negated": False},
            {"subject": f"material:{mat}", "predicate": "operates_at_temperature",
             "obj": "property:temp_range", "value": "20-80C", "negated": False},
            {"subject": f"material:{mat}", "predicate": "exhibits_stability",
             "obj": "property:cycle_life", "value": ">1000", "negated": False},
        ],
        "citations": [],
        "title": "M09 big", "abstract": "", "ingestion_source": "synthetic_fixture",
    })
    # US member: only 1 claim
    us_id = f"patent:US:{domain}:m09_small"
    patents.append({
        "patent_id": us_id,
        "docdb_family_id": fid,
        "publication_date": _d(-300),
        "priority_date": prio,
        "jurisdictions": ["US"], "inventors": [], "assignee": "Corp_M09",
        "domain": domain, "mechanisms": [mech], "materials": [mat],
        "processes": [f"PRIORITY_CHAIN:{prio}"],
        "claims": [
            {"subject": f"material:{mat}", "predicate": "achieves_property",
             "obj": f"property:{mech}_perf", "value": "0.7", "negated": False},
        ],
        "citations": [],
        "title": "M09 small", "abstract": "", "ingestion_source": "synthetic_fixture",
    })


def _plant_m10(papers, patents, domain, mechs, mats, rng):
    mech = rng.choice(mechs)
    mat1 = rng.choice(mats)
    mat2 = rng.choice([m for m in mats if m != mat1])
    paper_id = f"paper:{domain}:m10_p"
    pat_id = f"patent:CN:{domain}:m10_pat"
    pub = _d(rng.randint(-365 * 3, -365 * 2))
    prio = _d(rng.randint(-365 * 2, -365))
    papers.append({
        "paper_id": paper_id,
        "publication_date": pub,
        "domain": domain, "mechanisms": [mech, "secondary_mech"],
        "materials": [mat1, mat2],
        "claims": [], "citations": [], "reported_failures": [],
        "title": "M10 paper", "abstract": "", "authors": [],
        "processes": [], "ingestion_source": "synthetic_fixture",
    })
    patents.append({
        "patent_id": pat_id,
        "docdb_family_id": f"fam:DOCDB:m10{domain}",
        "publication_date": _d(rng.randint(-365, -30)),
        "priority_date": prio,
        "jurisdictions": ["CN"], "inventors": [], "assignee": "Corp_M10",
        "domain": domain, "mechanisms": [mech, "secondary_mech"],
        "materials": [mat1, mat2],
        "processes": [f"PRIORITY_CHAIN:{prio}"],
        "claims": [], "citations": [],
        "title": "M10 pat", "abstract": "", "ingestion_source": "synthetic_fixture",
    })


def _plant_m06(papers, patents, rng):
    # Two papers in different domains on a shared cross-domain mechanism,
    # plus two patent families (one per domain).
    d1, d2 = "battery_electrochemistry", "neuromorphic_computing"
    mech = "memristive_switching"  # shared
    p1 = f"paper:{d1}:m06_p1"
    p2 = f"paper:{d2}:m06_p2"
    papers.append({
        "paper_id": p1,
        "publication_date": _d(-365 * 3),
        "domain": d1, "mechanisms": [mech], "materials": ["HfO2_RRAM"],
        "claims": [], "citations": [], "reported_failures": [],
        "title": "M06 p1", "abstract": "", "authors": [],
        "processes": [], "ingestion_source": "synthetic_fixture",
    })
    papers.append({
        "paper_id": p2,
        "publication_date": _d(-365 * 2),
        "domain": d2, "mechanisms": [mech], "materials": ["TaOx_MEM"],
        "claims": [], "citations": [], "reported_failures": [],
        "title": "M06 p2", "abstract": "", "authors": [],
        "processes": [], "ingestion_source": "synthetic_fixture",
    })
    for d, mat in [(d1, "HfO2_RRAM"), (d2, "TaOx_MEM")]:
        prio = _d(-365 * 2)
        fid = f"fam:DOCDB:m06{d}"
        patents.append({
            "patent_id": f"patent:EP:{d}:m06_pat",
            "docdb_family_id": fid,
            "publication_date": _d(-365),
            "priority_date": prio,
            "jurisdictions": ["EP"], "inventors": [], "assignee": "Corp_M06",
            "domain": d, "mechanisms": [mech], "materials": [mat],
            "processes": [f"PRIORITY_CHAIN:{prio}"],
            "claims": [], "citations": [],
            "title": "M06 pat", "abstract": "", "ingestion_source": "synthetic_fixture",
        })


def _plant_m07(papers, patents, rng):
    # 3 independent papers in same domain on same mech, different mats
    domain = "perovskite_photovoltaics"
    mech = "defect_passivation"
    mats = ["MAPbI3", "FAPbBr3", "CsPbI3"]
    for i, mat in enumerate(mats):
        papers.append({
            "paper_id": f"paper:{domain}:m07_p{i+1}",
            "publication_date": _d(-365 * (3 + i)),
            "domain": domain, "mechanisms": [mech], "materials": [mat],
            "claims": [], "citations": [], "reported_failures": [],
            "title": f"M07 p{i+1}", "abstract": "", "authors": [],
            "processes": [], "ingestion_source": "synthetic_fixture",
        })
    # 1 patent in same domain/mech
    prio = _d(-365)
    patents.append({
        "patent_id": f"patent:US:{domain}:m07_pat",
        "docdb_family_id": f"fam:DOCDB:m07{domain}",
        "publication_date": _d(-30),
        "priority_date": prio,
        "jurisdictions": ["US"], "inventors": [], "assignee": "Corp_M07",
        "domain": domain, "mechanisms": [mech], "materials": ["Spiro_OMeTAD"],
        "processes": [f"PRIORITY_CHAIN:{prio}"],
        "claims": [], "citations": [],
        "title": "M07 pat", "abstract": "", "ingestion_source": "synthetic_fixture",
    })


def _plant_m08(papers, patents, rng):
    # 1 paper + 3 families with different mats
    domain = "carbon_capture"
    mech = "amine_scrubbing"
    paper_id = f"paper:{domain}:m08_p"
    papers.append({
        "paper_id": paper_id,
        "publication_date": _d(-365 * 3),
        "domain": domain, "mechanisms": [mech], "materials": ["MEA"],
        "claims": [], "citations": [], "reported_failures": [],
        "title": "M08 p", "abstract": "", "authors": [],
        "processes": [], "ingestion_source": "synthetic_fixture",
    })
    for i, mat in enumerate(["zeolite_13X", "Mg_MOF_74", "ZIF_8"]):
        prio = _d(-365 * 2 + i * 30)
        fid = f"fam:DOCDB:m08{i}{domain}"
        patents.append({
            "patent_id": f"patent:EP:{domain}:m08_pat{i}",
            "docdb_family_id": fid,
            "publication_date": _d(-365 + i * 30),
            "priority_date": prio,
            "jurisdictions": ["EP"], "inventors": [], "assignee": f"Corp_M08_{i}",
            "domain": domain, "mechanisms": [mech], "materials": [mat],
            "processes": [f"PRIORITY_CHAIN:{prio}"],
            "claims": [], "citations": [],
            "title": f"M08 pat{i}", "abstract": "", "ingestion_source": "synthetic_fixture",
        })


if __name__ == "__main__":
    out = Path(__file__).parent
    counts = gen_corpus(out)
    print(f"Generated: {counts}")
