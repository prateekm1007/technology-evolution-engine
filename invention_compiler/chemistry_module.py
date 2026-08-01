"""
Chemistry Module — feeds Layer 1 (First-principles analysis).

Per CTO review #2 (commit `02d7658`), upgraded from keyword matching
to encoding actual chemistry principles:

  From: keywords (filter graph nodes by label keywords).
  To:   reaction pathways, kinetics, equilibrium, energy states.

The module now exposes:
  - reaction_pathways(): canonical reaction types as structured objects
    with reactants, products, and conditions.
  - kinetics_models(): rate laws (Arrhenius, Michaelis-Menten) as
    structured models with equations and variables.
  - equilibrium_models(): equilibrium-constant formulations.
  - energy_states(): Gibbs free energy and related state functions.
  - analyze(problem): surfaces the pathways/kinetics/equilibrium
    applicable to the problem, DIFFERENTIATED by the problem's domain
    and constraints.

Law 8 honesty: the analyze() output carries evidence, assumptions,
and falsification_criteria.

Note: this is still a MODULE, not an ENGINE — the encoded models are
priors, not calibrations. The kinetics models are not solved against
real data; they identify WHICH model would apply if data were available.
"""
from typing import Dict, Any, List


class ChemistryModule:
    """Encodes chemistry principles and applies them to problems."""

    # Canonical reaction pathways. Each is a structured object.
    REACTION_PATHWAYS = {
        "haber_bosch": {
            "name": "Haber-Bosch ammonia synthesis",
            "reactants": ["N2", "H2"],
            "products": ["NH3"],
            "conditions": {
                "temperature_K": "600-700",
                "pressure_atm": "150-300",
                "catalyst": "Fe or Ru promoted",
            },
            "thermodynamics": "exothermic (dH = -46 kJ/mol NH3)",
            "notes": "Industrial standard since 1913; consumes 1-2% of world energy.",
        },
        "electrochemical_ammonia": {
            "name": "Electrochemical ammonia synthesis (ambient)",
            "reactants": ["N2", "H2O", "electrons"],
            "products": ["NH3", "O2"],
            "conditions": {
                "temperature_K": "298-350",
                "pressure_atm": "1",
                "catalyst": "Li-mediated or transition-metal complex",
            },
            "thermodynamics": "energy input required (electrical)",
            "notes": "Active research area; no commercial process yet. The "
                     "N≡N triple bond (945 kJ/mol) is the binding constraint.",
        },
        "electrolysis_water": {
            "name": "Water electrolysis",
            "reactants": ["H2O"],
            "products": ["H2", "O2"],
            "conditions": {
                "temperature_K": "298-1000",
                "pressure_atm": "1-30",
                "catalyst": "Pt/IrO2 (acidic) or Ni-based (alkaline)",
            },
            "thermodynamics": "energy input required (electrical, dG = +237 kJ/mol)",
            "notes": "Mature technology; efficiency 70-80%.",
        },
        "polymerization": {
            "name": "Polymer synthesis",
            "reactants": ["monomer(s)"],
            "products": ["polymer"],
            "conditions": {
                "temperature_K": "varies (300-500)",
                "pressure_atm": "1-100",
                "catalyst": "Ziegler-Natta, metallocene, or radical initiator",
            },
            "thermodynamics": "exothermic (varies)",
            "notes": "Backbone of plastics industry.",
        },
        "calcination_cement": {
            "name": "Cement calcination",
            "reactants": ["CaCO3"],
            "products": ["CaO", "CO2"],
            "conditions": {
                "temperature_K": "1100-1500",
                "pressure_atm": "1",
                "catalyst": "none",
            },
            "thermodynamics": "endothermic (dH = +178 kJ/mol)",
            "notes": "Source of ~8% of global CO2 emissions.",
        },
        "carbonation_cure": {
            "name": "CO2 carbonation curing (carbon-negative cement)",
            "reactants": ["CaO", "CO2", "H2O"],
            "products": ["CaCO3"],
            "conditions": {
                "temperature_K": "298-373",
                "pressure_atm": "1-10",
                "catalyst": "none",
            },
            "thermodynamics": "exothermic (dH < 0)",
            "notes": "CarbonCure and Solidia commercialize this; sequesters CO2.",
        },
        "photocatalysis_water_splitting": {
            "name": "Photocatalytic water splitting",
            "reactants": ["H2O", "photons"],
            "products": ["H2", "O2"],
            "conditions": {
                "temperature_K": "298",
                "pressure_atm": "1",
                "catalyst": "TiO2, SrTiO3, or multi-junction semiconductor",
            },
            "thermodynamics": "energy input (solar photons, dG = +237 kJ/mol)",
            "notes": "Active research; best efficiency ~1-2% (target: >10%).",
        },
    }

    # Kinetic rate laws as structured models.
    KINETICS_MODELS = {
        "arrhenius": {
            "equation": "k = A * exp(-Ea / (R * T))",
            "variables": {
                "k": "1/s (rate constant)",
                "A": "1/s (pre-exponential factor)",
                "Ea": "J/mol (activation energy)",
                "R": "J/(mol*K) (gas constant, 8.314)",
                "T": "K (temperature)",
            },
            "applies_to": ["thermal_reactions", "catalytic_reactions"],
            "statement": "Rate constant depends exponentially on activation energy and temperature.",
        },
        "michaelis_menten": {
            "equation": "v = Vmax * [S] / (Km + [S])",
            "variables": {
                "v": "mol/(L*s) (reaction rate)",
                "Vmax": "mol/(L*s) (max rate)",
                "[S]": "mol/L (substrate concentration)",
                "Km": "mol/L (Michaelis constant)",
            },
            "applies_to": ["enzyme_kinetics", "biocatalysis"],
            "statement": "Enzyme kinetics saturating with substrate.",
        },
        "langmuir_hinshelwood": {
            "equation": "r = k * KA * KB * PA * PB / (1 + KA*PA + KB*PB)^2",
            "variables": {
                "r": "mol/(m^2*s) (rate)",
                "k": "1/s (rate constant)",
                "KA, KB": "1/Pa (adsorption constants)",
                "PA, PB": "Pa (partial pressures)",
            },
            "applies_to": ["heterogeneous_catalysis", "surface_reactions"],
            "statement": "Bimolecular surface reaction with adsorbed species.",
        },
    }

    # Equilibrium models.
    EQUILIBRIUM_MODELS = {
        "K_eq": {
            "equation": "K_eq = [products]^stoich / [reactants]^stoich",
            "variables": {
                "K_eq": "dimensionless",
                "[products]": "mol/L",
                "[reactants]": "mol/L",
            },
            "applies_to": ["reversible_reactions"],
            "statement": "Equilibrium constant relates product and reactant concentrations.",
        },
        "van_t_hoff": {
            "equation": "d(ln K_eq)/dT = dH / (R * T^2)",
            "variables": {
                "K_eq": "dimensionless",
                "T": "K",
                "dH": "J/mol (enthalpy change)",
                "R": "J/(mol*K)",
            },
            "applies_to": ["temperature_dependent_equilibria"],
            "statement": "Temperature dependence of equilibrium constant.",
        },
    }

    # Energy state models.
    ENERGY_STATES = {
        "gibbs_free_energy": {
            "equation": "G = H - T*S",
            "variables": {
                "G": "J/mol (Gibbs free energy)",
                "H": "J/mol (enthalpy)",
                "T": "K (temperature)",
                "S": "J/(mol*K) (entropy)",
            },
            "applies_to": ["spontaneity_determination"],
            "statement": "A reaction is spontaneous when dG < 0 at constant T,P.",
        },
        "nernst_equation": {
            "equation": "E = E0 - (R*T/nF) * ln(Q)",
            "variables": {
                "E": "V (cell potential)",
                "E0": "V (standard potential)",
                "R": "J/(mol*K)",
                "T": "K",
                "n": "dimensionless (electron count)",
                "F": "C/mol (Faraday constant, 96485)",
                "Q": "dimensionless (reaction quotient)",
            },
            "applies_to": ["electrochemistry", "electrochemical_cells"],
            "statement": "Cell potential under non-standard conditions.",
        },
        "activation_energy": {
            "equation": "Ea = -R * d(ln k)/d(1/T)",
            "variables": {
                "Ea": "J/mol",
                "R": "J/(mol*K)",
                "k": "1/s (rate constant)",
                "T": "K",
            },
            "applies_to": ["kinetics"],
            "statement": "Energy barrier for a reaction to proceed.",
        },
    }

    # Heuristic: domain/constraint -> applicable pathways/models.
    DOMAIN_TO_PATHWAYS = {
        "chemistry": ["electrochemical_ammonia", "haber_bosch"],
        "medical_imaging": [],  # chemistry-light
        "materials": ["polymerization", "calcination_cement", "carbonation_cure"],
        "energy": ["electrolysis_water", "photocatalysis_water_splitting"],
    }
    CONSTRAINT_TO_PATHWAYS = {
        "ammonia": ["electrochemical_ammonia", "haber_bosch"],
        "cement": ["calcination_cement", "carbonation_cure"],
        "carbon_negative": ["carbonation_cure"],
        "co2": ["carbonation_cure"],
        "polymer": ["polymerization"],
        "electrochem": ["electrochemical_ammonia", "electrolysis_water"],
        "photosynth": ["photocatalysis_water_splitting"],
        "water_splitting": ["photocatalysis_water_splitting", "electrolysis_water"],
        "hydrogen": ["electrolysis_water", "photocatalysis_water_splitting"],
    }
    CONSTRAINT_TO_KINETICS = {
        "catalyst": ["arrhenius", "langmuir_hinshelwood"],
        "enzyme": ["michaelis_menten"],
        "electrochem": ["arrhenius"],
        "thermal": ["arrhenius"],
    }
    CONSTRAINT_TO_EQUILIBRIUM = {
        "electrochem": ["nernst_equation"] if False else ["K_eq"],
        "reversible": ["K_eq", "van_t_hoff"],
        "equilibrium": ["K_eq", "van_t_hoff"],
    }
    CONSTRAINT_TO_ENERGY_STATES = {
        "energy": ["gibbs_free_energy", "activation_energy"],
        "electrochem": ["gibbs_free_energy", "nernst_equation", "activation_energy"],
        "catalyst": ["activation_energy", "gibbs_free_energy"],
        "spontaneous": ["gibbs_free_energy"],
    }

    CHEMISTRY_KEYWORDS = (
        "polymer", "membrane", "catalyst", "electrode", "chemical",
        "molecular", "ionic", "oxidation", "reduction", "electrochem",
        "photochem", "synthesis", "alloy", "ceramic", "composite",
        "semiconductor", "electrolyte", "crystal", "ammonia", "cement",
        "carbon", "hydrogen", "polymerization", "calcination",
    )

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph
        self.nodes = graph.get("nodes", [])
        self.edges = graph.get("edges", [])

    # ------------------------------------------------------------------
    # New API
    # ------------------------------------------------------------------

    def reaction_pathways(self) -> List[Dict[str, Any]]:
        return [dict(v) for v in self.REACTION_PATHWAYS.values()]

    def kinetics_models(self) -> Dict[str, Dict[str, Any]]:
        return {k: dict(v) for k, v in self.KINETICS_MODELS.items()}

    def equilibrium_models(self) -> Dict[str, Dict[str, Any]]:
        return {k: dict(v) for k, v in self.EQUILIBRIUM_MODELS.items()}

    def energy_states(self) -> Dict[str, Dict[str, Any]]:
        return {k: dict(v) for k, v in self.ENERGY_STATES.items()}

    # ------------------------------------------------------------------
    # Layer 1 analyze (upgraded)
    # ------------------------------------------------------------------

    def analyze(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Surface applicable pathways, kinetics, equilibrium, and
        energy states — DIFFERENTIATED by problem domain and constraints."""
        domain = problem.get("domain")
        constraints = [str(c).lower() for c in problem.get("constraints", [])]

        # Aggregate applicable pathways from domain + constraints.
        applicable_pathways = set()
        if domain in self.DOMAIN_TO_PATHWAYS:
            applicable_pathways.update(self.DOMAIN_TO_PATHWAYS[domain])
        for c in constraints:
            for kw, paths in self.CONSTRAINT_TO_PATHWAYS.items():
                if kw in c:
                    applicable_pathways.update(paths)
        # Constraint keywords on the problem text itself.
        problem_text = (problem.get("problem") or "").lower()
        for kw, paths in self.CONSTRAINT_TO_PATHWAYS.items():
            if kw in problem_text:
                applicable_pathways.update(paths)

        # Kinetics.
        applicable_kinetics = set()
        for c in constraints:
            for kw, models in self.CONSTRAINT_TO_KINETICS.items():
                if kw in c:
                    applicable_kinetics.update(models)

        # Equilibrium.
        applicable_equilibrium = set()
        for c in constraints:
            for kw, models in self.CONSTRAINT_TO_EQUILIBRIUM.items():
                if kw in c:
                    applicable_equilibrium.update(models)

        # Energy states.
        applicable_energy = set()
        for c in constraints:
            for kw, models in self.CONSTRAINT_TO_ENERGY_STATES.items():
                if kw in c:
                    applicable_energy.update(models)
        # Always include Gibbs free energy — it's the canonical energy-state.
        if not applicable_energy:
            applicable_energy = {"gibbs_free_energy"}

        # Surface graph nodes too (for evidence of graph coverage).
        nodes = []
        for n in self.nodes:
            label = (n.get("label") or "").lower()
            n_domain = n.get("domain")
            matches_domain = (domain is not None and n_domain == domain)
            matches_keyword = any(kw in label for kw in self.CHEMISTRY_KEYWORDS)
            ntype = n.get("type", "")
            is_material_like = ntype in ("component", "principle", "process")
            if (matches_domain or matches_keyword) and is_material_like:
                nodes.append({
                    "id": n["id"],
                    "label": n.get("label"),
                    "type": ntype,
                    "domain": n_domain,
                    "constraints": n.get("constraints", []),
                })

        # Carry structured objects for evidence.
        pathway_objs = [
            {**self.REACTION_PATHWAYS[k], "name": k}
            for k in sorted(applicable_pathways)
            if k in self.REACTION_PATHWAYS
        ]
        kinetics_objs = [
            {**self.KINETICS_MODELS[k], "name": k}
            for k in sorted(applicable_kinetics)
            if k in self.KINETICS_MODELS
        ]
        equilibrium_objs = [
            {**self.EQUILIBRIUM_MODELS[k], "name": k}
            for k in sorted(applicable_equilibrium)
            if k in self.EQUILIBRIUM_MODELS
        ]
        energy_objs = [
            {**self.ENERGY_STATES[k], "name": k}
            for k in sorted(applicable_energy)
            if k in self.ENERGY_STATES
        ]

        return {
            "materials_and_processes": nodes,
            "applicable_pathways": sorted(applicable_pathways),
            "applicable_pathway_objects": pathway_objs,
            "applicable_kinetics": sorted(applicable_kinetics),
            "applicable_kinetics_objects": kinetics_objs,
            "applicable_equilibrium": sorted(applicable_equilibrium),
            "applicable_equilibrium_objects": equilibrium_objs,
            "applicable_energy_states": sorted(applicable_energy),
            "applicable_energy_state_objects": energy_objs,
            "evidence": {
                "nodes_found": len(nodes),
                "domain_filter": domain,
                "pathway_count": len(applicable_pathways),
                "kinetics_count": len(applicable_kinetics),
                "equilibrium_count": len(applicable_equilibrium),
                "energy_state_count": len(applicable_energy),
                "differentiation_basis": "domain_and_constraint_keywords",
            },
            "assumptions": [
                "Applicable pathways/kinetics/equilibrium are determined by "
                "domain and constraint keywords via heuristic maps. These "
                "identify WHICH model would apply; they do not SOLVE the "
                "model against real data.",
                "Reaction pathway conditions (T, P, catalyst) are documented "
                "ranges, not optimized values for the specific problem.",
            ],
            "falsification_criteria": (
                "If a chemistry literature search for the problem surfaces "
                "a pathway, kinetics model, or equilibrium model not in this "
                "engine's output, the heuristic map is incomplete."
            ),
        }
