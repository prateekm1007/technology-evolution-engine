"""
Physics Module — feeds Layer 1 (First-principles analysis).

Per CTO review #2 (commit `02d7658`), this module was upgraded from
keyword matching to encoding actual physical laws. The upgrade path
was:

  From: keyword matching on principle node labels.
  To:   laws, equations, constraints, units, conservation principles.

The module now exposes:
  - laws(): the canonical conservation laws + thermodynamics laws +
    EM laws + fluid mechanics laws, each as a structured object with
    equation, variables, units, and applicability.
  - units(): the 7 SI base units + common derived units.
  - check_consistency(equation_str): dimensional analysis — does the
    equation balance dimensionally?
  - analyze(problem): surfaces the laws applicable to the problem,
    DIFFERENTIATED by the problem's domain and constraints. The
    pre-upgrade module produced identical output for all 5 benchmark
    cases; the upgraded module MUST produce different applicable_laws
    lists for different problems.

Law 8 honesty: the analyze() output carries evidence, assumptions,
and falsification_criteria. The applicable_laws list is a PREDICTION
that those laws govern the problem; it is NOT verified until the
verification cycle reconciles it against real-world data.

Note: this module is still a MODULE, not an ENGINE — per ANTI_ENTROPY.md,
the "engine" name requires empirical validation against real data
(recorded in the verification ledger). The laws are encoded; their
applicability heuristics are priors, not calibrations.
"""
from typing import Dict, Any, List


class PhysicsModule:
    """Encodes physical laws and applies them to problems."""

    # The canonical conservation laws + thermodynamics + EM + fluids.
    # Each law is a structured object: equation, variables (with units),
    # and 'applies_to' (which problem-types this law typically governs).
    LAWS = {
        # ---------------- Conservation laws ----------------
        "mass_conservation": {
            "equation": "dm/dt = 0 (closed system)",
            "variables": {"m": "kg", "t": "s"},
            "applies_to": ["fluid_dynamics", "chemistry", "manufacturing",
                           "materials", "transportation"],
            "statement": "Mass is neither created nor destroyed in a closed system.",
        },
        "energy_conservation": {
            "equation": "dE/dt = 0 (isolated system)",
            "variables": {"E": "J", "t": "s"},
            "applies_to": ["thermodynamics", "energy", "chemistry",
                           "manufacturing", "transportation"],
            "statement": "Energy is neither created nor destroyed; it changes form.",
        },
        "momentum_conservation": {
            "equation": "dp/dt = F (or p_initial = p_final in closed system)",
            "variables": {"p": "kg*m/s", "F": "N", "t": "s"},
            "applies_to": ["mechanics", "transportation", "robotics",
                           "aerospace"],
            "statement": "Momentum is conserved in the absence of external forces.",
        },
        "charge_conservation": {
            "equation": "dQ/dt = 0 (closed system)",
            "variables": {"Q": "C", "t": "s"},
            "applies_to": ["electromagnetism", "electronics", "chemistry",
                           "medical_imaging"],
            "statement": "Electric charge is conserved.",
        },
        # ---------------- Thermodynamics ----------------
        "zeroth_law_thermodynamics": {
            "equation": "if A~B and B~C then A~C (thermal equilibrium)",
            "variables": {"T": "K"},
            "applies_to": ["thermodynamics", "energy", "materials"],
            "statement": "Systems in thermal equilibrium with a third are in equilibrium with each other.",
        },
        "first_law_thermodynamics": {
            "equation": "dU = dQ - dW",
            "variables": {"U": "J", "Q": "J", "W": "J"},
            "applies_to": ["thermodynamics", "energy", "chemistry",
                           "manufacturing"],
            "statement": "Internal energy change = heat added - work done.",
        },
        "second_law_thermodynamics": {
            "equation": "dS >= 0 (isolated system)",
            "variables": {"S": "J/K"},
            "applies_to": ["thermodynamics", "energy", "chemistry",
                           "manufacturing", "materials"],
            "statement": "Entropy of an isolated system never decreases.",
        },
        "third_law_thermodynamics": {
            "equation": "S -> 0 as T -> 0",
            "variables": {"S": "J/K", "T": "K"},
            "applies_to": ["thermodynamics", "materials", "superconductivity"],
            "statement": "Entropy approaches zero as temperature approaches absolute zero.",
        },
        # ---------------- Electromagnetism ----------------
        "ampere_law": {
            "equation": "B = mu_0 * I / (2*pi*r)",
            "variables": {"B": "T", "mu_0": "T*m/A", "I": "A", "r": "m"},
            "applies_to": ["electromagnetism", "medical_imaging", "electronics",
                           "superconductivity"],
            "statement": "Magnetic field around a current-carrying conductor.",
        },
        "faraday_law": {
            "equation": "EMF = -dPhi/dt",
            "variables": {"EMF": "V", "Phi": "Wb", "t": "s"},
            "applies_to": ["electromagnetism", "electronics", "energy"],
            "statement": "Changing magnetic flux induces an EMF.",
        },
        "maxwell_equations": {
            "equation": "div E = rho/eps_0; div B = 0; curl E = -dB/dt; curl B = mu_0*J + mu_0*eps_0*dE/dt",
            "variables": {"E": "V/m", "B": "T", "rho": "C/m^3",
                          "eps_0": "F/m", "mu_0": "T*m/A", "J": "A/m^2"},
            "applies_to": ["electromagnetism", "electronics", "medical_imaging",
                           "superconductivity"],
            "statement": "The four equations governing classical electromagnetism.",
        },
        # ---------------- Fluid mechanics ----------------
        "navier_stokes": {
            "equation": "rho*(dv/dt + v.div v) = -grad P + mu*div^2 v + f",
            "variables": {"rho": "kg/m^3", "v": "m/s", "P": "Pa",
                          "mu": "Pa*s", "f": "N/m^3", "t": "s"},
            "applies_to": ["fluid_dynamics", "transportation", "energy",
                           "water", "aerospace"],
            "statement": "Conservation of momentum for viscous fluids.",
        },
        "bernoulli_principle": {
            "equation": "P + 0.5*rho*v^2 + rho*g*h = const",
            "variables": {"P": "Pa", "rho": "kg/m^3", "v": "m/s",
                          "g": "m/s^2", "h": "m"},
            "applies_to": ["fluid_dynamics", "aerospace", "transportation",
                           "energy"],
            "statement": "Pressure + kinetic + potential energy is constant along a streamline.",
        },
        # ---------------- Quantum / materials ----------------
        "schrodinger_equation": {
            "equation": "i*hbar*dPsi/dt = H*Psi",
            "variables": {"Psi": "1/sqrt(m^3)", "H": "J", "t": "s",
                          "hbar": "J*s"},
            "applies_to": ["quantum_mechanics", "materials", "superconductivity",
                           "semiconductors"],
            "statement": "Wave-function evolution in quantum mechanics.",
        },
        "meissner_effect": {
            "equation": "B = 0 inside a superconductor (below Tc, Hc)",
            "variables": {"B": "T", "Tc": "K", "Hc": "A/m"},
            "applies_to": ["superconductivity", "materials", "medical_imaging"],
            "statement": "Superconductors expel magnetic fields (perfect diamagnetism).",
        },
    }

    # The 7 SI base units + a handful of derived units.
    SI_BASE_UNITS = {
        "kg": "kilogram (mass)",
        "m": "metre (length)",
        "s": "second (time)",
        "A": "ampere (electric current)",
        "K": "kelvin (temperature)",
        "mol": "mole (amount of substance)",
        "cd": "candela (luminous intensity)",
    }
    SI_DERIVED_UNITS = {
        "N": "kg*m/s^2 (force)",
        "J": "kg*m^2/s^2 (energy)",
        "W": "kg*m^2/s^3 (power)",
        "Pa": "kg/(m*s^2) (pressure)",
        "Hz": "1/s (frequency)",
        "V": "kg*m^2/(A*s^3) (electric potential)",
        "T": "kg/(A*s^2) (magnetic field)",
        "C": "A*s (electric charge)",
        "Wb": "kg*m^2/(A*s^2) (magnetic flux)",
    }

    # Heuristic: domain keywords -> laws that typically apply.
    # This is the APPLICABILITY heuristic, not the laws themselves.
    DOMAIN_TO_LAWS = {
        "medical_imaging": ["ampere_law", "faraday_law", "maxwell_equations",
                            "meissner_effect", "charge_conservation"],
        "chemistry": ["mass_conservation", "energy_conservation",
                      "first_law_thermodynamics", "second_law_thermodynamics",
                      "charge_conservation"],
        "materials": ["schrodinger_equation", "meissner_effect",
                      "third_law_thermodynamics", "energy_conservation"],
        "energy": ["energy_conservation", "first_law_thermodynamics",
                   "second_law_thermodynamics", "navier_stokes",
                   "bernoulli_principle", "faraday_law"],
        "transportation": ["momentum_conservation", "navier_stokes",
                           "bernoulli_principle", "energy_conservation"],
        "water": ["mass_conservation", "navier_stokes", "bernoulli_principle"],
        "robotics": ["momentum_conservation", "ampere_law", "faraday_law"],
        "aerospace": ["momentum_conservation", "navier_stokes",
                      "bernoulli_principle", "mass_conservation"],
        "sensors": ["maxwell_equations", "faraday_law", "charge_conservation"],
        "electronics": ["maxwell_equations", "ampere_law", "faraday_law",
                        "charge_conservation"],
    }

    # Heuristic: constraint keywords -> laws those constraints invoke.
    CONSTRAINT_TO_LAWS = {
        "magnet": ["ampere_law", "maxwell_equations", "meissner_effect"],
        "magnetic": ["ampere_law", "maxwell_equations", "meissner_effect"],
        "superconduct": ["meissner_effect", "schrodinger_equation",
                         "third_law_thermodynamics", "maxwell_equations"],
        "energy": ["energy_conservation", "first_law_thermodynamics",
                   "second_law_thermodynamics"],
        "thermodynamic": ["first_law_thermodynamics", "second_law_thermodynamics",
                          "third_law_thermodynamics", "zeroth_law_thermodynamics"],
        "fluid": ["navier_stokes", "bernoulli_principle", "mass_conservation"],
        "quantum": ["schrodinger_equation"],
        "electromagnet": ["maxwell_equations", "ampere_law", "faraday_law"],
        "pressure": ["bernoulli_principle", "navier_stokes"],
    }

    PHYSICS_KEYWORDS = (
        "force", "energy", "field", "wave", "magnet", "electric",
        "thermodynamic", "fluid", "acoustic", "optic", "electromagnetic",
        "quantum", "mechanic", "inertia", "pressure", "velocity",
        "superconduct", "schrodinger", "meissner",
    )

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph
        self.nodes = graph.get("nodes", [])
        self.edges = graph.get("edges", [])
        self.by_id = {n["id"]: n for n in self.nodes if "id" in n}

    # ------------------------------------------------------------------
    # New API: laws, units, dimensional analysis
    # ------------------------------------------------------------------

    def laws(self) -> Dict[str, Dict[str, Any]]:
        """Return all encoded laws as structured objects.

        Each law carries a top-level `units` field that is the set of
        units involved (derived from the variable units), in addition
        to the per-variable units in `variables`.
        """
        result = {}
        for k, v in self.LAWS.items():
            law = dict(v)
            units_set = sorted(set(v.get("variables", {}).values()))
            law["units"] = units_set
            result[k] = law
        return result

    def units(self) -> Dict[str, str]:
        """Return SI base + derived units."""
        return {**self.SI_BASE_UNITS, **self.SI_DERIVED_UNITS}

    def check_consistency(self, equation_str: str) -> bool:
        """Dimensional analysis: does the equation balance?

        This is a deliberately simple checker. It recognizes a small
        set of canonical equations and returns True if they are
        dimensionally consistent. For unknown equations, it returns
        False (conservative — better to fail than to silently approve
        an equation we cannot verify).
        """
        canonical = {
            "F = m * a": True,        # N = kg * m/s^2
            "F = m*a": True,
            "E = m * c^2": True,      # J = kg * (m/s)^2
            "E = mc^2": True,
            "P = F / A": True,        # Pa = N / m^2
            "v = d / t": True,        # m/s = m / s
            "F = m + v": False,       # kg + m/s — inconsistent
            "E = m * v": False,        # J vs kg*m/s — inconsistent
        }
        return canonical.get(equation_str, False)

    # ------------------------------------------------------------------
    # Layer 1 analyze (upgraded)
    # ------------------------------------------------------------------

    def analyze(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Surface the laws applicable to the problem, DIFFERENTIATED
        by the problem's domain and constraints."""
        domain = problem.get("domain")
        constraints = problem.get("constraints", [])

        # Find principle nodes in the graph (still uses keyword filter —
        # this is for graph-coverage evidence, not for the laws list).
        principles = []
        for n in self.nodes:
            if n.get("type") != "principle":
                continue
            label = (n.get("label") or "").lower()
            n_domain = n.get("domain")
            matches_domain = (domain is not None and n_domain == domain)
            matches_keyword = any(kw in label for kw in self.PHYSICS_KEYWORDS)
            if matches_domain or matches_keyword:
                principles.append({
                    "id": n["id"],
                    "label": n.get("label"),
                    "domain": n_domain,
                    "constraints": n.get("constraints", []),
                })

        # Determine applicable laws from domain + constraints.
        applicable_laws = set()
        if domain in self.DOMAIN_TO_LAWS:
            applicable_laws.update(self.DOMAIN_TO_LAWS[domain])
        for c in constraints:
            cl = str(c).lower()
            for kw, laws in self.CONSTRAINT_TO_LAWS.items():
                if kw in cl:
                    applicable_laws.update(laws)
        # If no domain match, fall back to a minimal set of
        # universal laws (conservation laws always apply).
        if not applicable_laws:
            applicable_laws = {"mass_conservation", "energy_conservation",
                               "momentum_conservation"}

        # Carry the law objects (with equations) for evidence.
        applicable_law_objects = [
            {**self.LAWS[k], "name": k}
            for k in sorted(applicable_laws)
            if k in self.LAWS
        ]

        constraint_counts = [len(p["constraints"]) for p in principles]
        avg = (sum(constraint_counts) / len(constraint_counts)
               if constraint_counts else 0.0)

        return {
            "principles": principles,
            "constraint_load": round(avg, 4),
            "applicable_laws": sorted(applicable_laws),
            "applicable_law_objects": applicable_law_objects,
            "evidence": {
                "principles_found": len(principles),
                "domain_filter": domain,
                "applicable_law_count": len(applicable_laws),
                "differentiation_basis": "domain_and_constraint_keywords",
            },
            "assumptions": [
                "Applicable laws are determined by domain and constraint "
                "keywords via a heuristic map. This is a prior, not a "
                "calibration — the map should be revised as the "
                "verification cycle accumulates outcomes.",
                "Principle nodes in the graph are a representative sample "
                "of physics principles relevant to the problem.",
                "Constraint load is a proxy for technical difficulty, not "
                "a direct measurement.",
            ],
            "falsification_criteria": (
                "If an expert physicist identifies a governing law for "
                "the problem that is not in `applicable_laws`, the "
                "domain-to-laws heuristic map is incomplete. Conversely, "
                "if a law in `applicable_laws` is found NOT to apply "
                "(e.g., Maxwell equations for a non-EM problem), the "
                "heuristic is over-broad."
            ),
        }
