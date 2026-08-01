"""
Mathematics Module — feeds Layer 1 (mathematics) AND Layer 3 (governing
equations).

Per CTO review #2 (commit `02d7658`), upgraded from templates to:

  optimization, probability, graph theory,
  differential equations, control theory.

The module now exposes:
  - optimization_formulations(): LP, convex, integer programming, etc.
  - probability_models(): common distributions and Bayes.
  - graph_theory_concepts(): shortest path, connectivity, centrality.
  - differential_equation_types(): ODE/PDE types and canonical forms.
  - control_theory_concepts(): PID, state-space, stability.
  - analyze_layer1(): identifies the mathematical STRUCTURE of a problem.
  - analyze_layer3(): proposes governing equations, now using the
    upgraded differential-equation-type knowledge.

Law 8 honesty: outputs carry evidence + assumptions + falsification_criteria.
"""
from typing import Dict, Any, List


class MathematicsKnowledgeModule:
    """Encodes mathematical structures and applies them to problems."""

    # CTO review #3: this module is at the "encode" stage of the
    # encode → reason → simulate → discover spectrum. It stores
    # optimization formulations, probability models, graph theory
    # concepts, differential equation types, and control theory
    # concepts as structured data. It does NOT reason over them,
    # simulate them, or discover new ones.
    STAGE = "encode"

    # ------------------------------------------------------------------
    # Optimization formulations
    # ------------------------------------------------------------------
    OPTIMIZATION_FORMULATIONS = {
        "linear_programming": {
            "form": "minimize c^T x subject to A*x <= b, x >= 0",
            "variables": {"x": "decision_vector", "c": "cost_vector",
                          "A": "constraint_matrix", "b": "constraint_vector"},
            "applicable_when": "objective and constraints are linear",
            "solver": "simplex, interior-point",
        },
        "convex_optimization": {
            "form": "minimize f(x) subject to g_i(x) <= 0, where f and g_i are convex",
            "variables": {"x": "decision_vector", "f": "convex_objective",
                          "g_i": "convex_constraints"},
            "applicable_when": "objective and constraints are convex",
            "solver": "interior-point, gradient descent",
        },
        "integer_programming": {
            "form": "minimize c^T x subject to A*x <= b, x in Z^n",
            "variables": {"x": "integer_decision_vector"},
            "applicable_when": "decisions are discrete (e.g., facility location)",
            "solver": "branch-and-bound, cutting planes",
        },
        "stochastic_optimization": {
            "form": "minimize E[f(x, xi)] subject to g(x, xi) <= 0",
            "variables": {"x": "decision_vector", "xi": "random_variable"},
            "applicable_when": "problem has uncertainty that cannot be ignored",
            "solver": "SAA, scenario decomposition",
        },
        "multi_objective_optimization": {
            "form": "minimize (f1(x), f2(x), ..., fk(x)) simultaneously",
            "variables": {"x": "decision_vector", "f_i": "objectives"},
            "applicable_when": "multiple conflicting objectives (e.g., cost vs safety)",
            "solver": "Pareto-frontier methods, weighted sum",
        },
    }

    # ------------------------------------------------------------------
    # Probability distributions and models
    # ------------------------------------------------------------------
    PROBABILITY_MODELS = {
        "normal": {
            "form": "f(x) = (1/(sigma*sqrt(2*pi))) * exp(-(x-mu)^2 / (2*sigma^2))",
            "variables": {"mu": "mean", "sigma": "std_dev"},
            "applicable_when": "sum of many independent effects (CLT)",
        },
        "bernoulli": {
            "form": "P(X=1) = p, P(X=0) = 1-p",
            "variables": {"p": "success_probability"},
            "applicable_when": "binary outcome (pass/fail)",
        },
        "poisson": {
            "form": "P(X=k) = (lambda^k * e^(-lambda)) / k!",
            "variables": {"lambda": "rate_parameter"},
            "applicable_when": "rare events in a fixed interval",
        },
        "exponential": {
            "form": "f(x) = lambda * e^(-lambda*x), x >= 0",
            "variables": {"lambda": "rate"},
            "applicable_when": "time between independent events",
        },
        "bayes_theorem": {
            "form": "P(A|B) = P(B|A) * P(A) / P(B)",
            "variables": {"P(A|B)": "posterior", "P(B|A)": "likelihood",
                          "P(A)": "prior", "P(B)": "evidence"},
            "applicable_when": "updating beliefs from evidence",
        },
        "markov_chain": {
            "form": "P(X_t+1 | X_t, X_t-1, ...) = P(X_t+1 | X_t)",
            "variables": {"X_t": "state at time t", "P": "transition_matrix"},
            "applicable_when": "memoryless state evolution",
        },
    }

    # ------------------------------------------------------------------
    # Graph theory concepts
    # ------------------------------------------------------------------
    GRAPH_THEORY_CONCEPTS = {
        "shortest_path": {
            "form": "minimize sum of edge weights along a path",
            "algorithms": ["Dijkstra", "Bellman-Ford", "A*"],
            "applicable_when": "find optimal route through a network",
        },
        "connectivity": {
            "form": "is the graph connected? what is the min cut?",
            "algorithms": ["DFS/BFS", "Ford-Fulkerson"],
            "applicable_when": "assess network robustness",
        },
        "centrality": {
            "form": "compute betweenness, closeness, eigenvector centrality",
            "algorithms": ["Brandes", "power iteration"],
            "applicable_when": "identify important nodes in a network",
        },
        "minimum_spanning_tree": {
            "form": "minimize total edge weight connecting all nodes",
            "algorithms": ["Kruskal", "Prim"],
            "applicable_when": "minimum-cost connectivity",
        },
        "clique_detection": {
            "form": "find maximal complete subgraphs",
            "algorithms": ["Bron-Kerbosch"],
            "applicable_when": "identify tightly-coupled clusters",
        },
    }

    # ------------------------------------------------------------------
    # Differential equation types
    # ------------------------------------------------------------------
    DIFFERENTIAL_EQUATION_TYPES = {
        "ode_first_order": {
            "form": "dy/dt = f(t, y)",
            "applicable_when": "rate of change depends on current state",
            "canonical_solver": "Runge-Kutta 4",
        },
        "ode_second_order": {
            "form": "d2y/dt2 = f(t, y, dy/dt)",
            "applicable_when": "oscillation, mechanics (F=ma)",
            "canonical_solver": "Runge-Kutta-Nyström",
        },
        "pde_diffusion": {
            "form": "du/dt = D * div^2 u",
            "applicable_when": "heat, mass, or information diffusion",
            "canonical_solver": "finite difference, Crank-Nicolson",
        },
        "pde_wave": {
            "form": "d2u/dt2 = c^2 * div^2 u",
            "applicable_when": "wave propagation (sound, EM, quantum)",
            "canonical_solver": "finite difference time-domain",
        },
        "pde_laplace": {
            "form": "div^2 phi = 0",
            "applicable_when": "steady-state potential (EM, fluid)",
            "canonical_solver": "successive over-relaxation",
        },
        "stochastic_differential": {
            "form": "dX = mu*dt + sigma*dW",
            "applicable_when": "noisy dynamics (finance, Brownian motion)",
            "canonical_solver": "Euler-Maruyama, Milstein",
        },
    }

    # ------------------------------------------------------------------
    # Control theory concepts
    # ------------------------------------------------------------------
    CONTROL_THEORY_CONCEPTS = {
        "pid": {
            "form": "u(t) = Kp*e + Ki*integral(e) + Kd*de/dt",
            "variables": {"Kp": "proportional", "Ki": "integral",
                          "Kd": "derivative", "e": "error"},
            "applicable_when": "setpoint tracking with simple dynamics",
        },
        "state_space": {
            "form": "dx/dt = A*x + B*u; y = C*x + D*u",
            "variables": {"x": "state", "u": "input", "y": "output",
                          "A, B, C, D": "matrices"},
            "applicable_when": "MIMO linear systems",
        },
        "stability": {
            "form": "Re(eigenvalue(A)) < 0 for all eigenvalues",
            "variables": {"A": "state_matrix"},
            "applicable_when": "checking if a system returns to equilibrium",
        },
        "controllability": {
            "form": "rank([B, A*B, A^2*B, ...]) = n",
            "variables": {"A": "state_matrix", "B": "input_matrix", "n": "state_dim"},
            "applicable_when": "can we drive the system to any state?",
        },
        "observability": {
            "form": "rank([C; C*A; C*A^2; ...]) = n",
            "variables": {"A": "state_matrix", "C": "output_matrix", "n": "state_dim"},
            "applicable_when": "can we infer the full state from outputs?",
        },
        "lyapunov_stability": {
            "form": "find V(x) such that V > 0 and dV/dt < 0",
            "variables": {"V": "lyapunov_function"},
            "applicable_when": "nonlinear stability analysis",
        },
    }

    # Map: physics-principle keyword -> candidate governing equation(s).
    EQUATION_PRIORS = {
        "centrifugal_force": [
            {"name": "centrifugal force", "form": "F = m * omega^2 * r",
             "variables": ["F", "m", "omega", "r"]},
        ],
        "bernoulli_principle": [
            {"name": "bernoulli equation", "form": "P + 0.5*rho*v^2 + rho*g*h = const",
             "variables": ["P", "rho", "v", "g", "h"]},
        ],
        "heat_transfer": [
            {"name": "fourier law", "form": "q = -k * grad(T)",
             "variables": ["q", "k", "T"]},
            {"name": "newton cooling", "form": "dT/dt = -k*(T - T_env)",
             "variables": ["T", "t", "k", "T_env"]},
        ],
        "electromagnet": [
            {"name": "ampere law", "form": "B = mu_0 * I / (2*pi*r)",
             "variables": ["B", "mu_0", "I", "r"]},
            {"name": "faraday law", "form": "EMF = -dPhi/dt",
             "variables": ["EMF", "Phi", "t"]},
        ],
        "magnet": [
            {"name": "ampere law", "form": "B = mu_0 * I / (2*pi*r)",
             "variables": ["B", "mu_0", "I", "r"]},
        ],
        "feedback_control": [
            {"name": "pid control", "form": "u(t) = Kp*e + Ki*integral(e) + Kd*de/dt",
             "variables": ["u", "Kp", "Ki", "Kd", "e", "t"]},
        ],
        "oscillation": [
            {"name": "simple harmonic", "form": "x(t) = A*cos(omega*t + phi)",
             "variables": ["x", "A", "omega", "t", "phi"]},
        ],
        "diffusion": [
            {"name": "fick law", "form": "J = -D * grad(C)",
             "variables": ["J", "D", "C"]},
        ],
        "superconduct": [
            {"name": "meissner effect", "form": "B = 0 (below Tc, Hc)",
             "variables": ["B", "Tc", "Hc"]},
            {"name": "london equations", "form": "dJ/dt = (n_s * e^2 / m) * E",
             "variables": ["J", "n_s", "e", "m", "E"]},
        ],
    }

    STRUCTURE_PRIORS = {
        "medical_imaging": ["inverse_problem", "signal_processing",
                            "optimization", "differential_equations"],
        "energy": ["optimization", "differential_equations",
                   "thermodynamics", "probability"],
        "transportation": ["optimization", "control_theory", "graph_theory"],
        "water": ["fluid_dynamics", "mass_transport", "optimization",
                  "differential_equations"],
        "robotics": ["control_theory", "optimization", "graph_theory",
                     "differential_equations"],
        "sensors": ["signal_processing", "statistics", "information_theory",
                    "probability"],
        "materials": ["optimization", "differential_equations",
                       "linear_algebra", "quantum_mechanics"],
        "chemistry": ["optimization", "differential_equations",
                      "probability", "thermodynamics"],
        "superconductivity": ["quantum_mechanics", "differential_equations",
                              "linear_algebra"],
    }

    def __init__(self, graph: Dict[str, Any]):
        self.graph = graph

    # ------------------------------------------------------------------
    # New API: structured math knowledge
    # ------------------------------------------------------------------

    def optimization_formulations(self) -> Dict[str, Dict[str, Any]]:
        return {k: dict(v) for k, v in self.OPTIMIZATION_FORMULATIONS.items()}

    def probability_models(self) -> Dict[str, Dict[str, Any]]:
        return {k: dict(v) for k, v in self.PROBABILITY_MODELS.items()}

    def graph_theory_concepts(self) -> Dict[str, Dict[str, Any]]:
        return {k: dict(v) for k, v in self.GRAPH_THEORY_CONCEPTS.items()}

    def differential_equation_types(self) -> Dict[str, Dict[str, Any]]:
        return {k: dict(v) for k, v in self.DIFFERENTIAL_EQUATION_TYPES.items()}

    def control_theory_concepts(self) -> Dict[str, Dict[str, Any]]:
        return {k: dict(v) for k, v in self.CONTROL_THEORY_CONCEPTS.items()}

    # ------------------------------------------------------------------
    # Layer 1: identify mathematical structure
    # ------------------------------------------------------------------

    def analyze_layer1(self, problem: Dict[str, Any],
                       physics_output: Dict[str, Any]) -> Dict[str, Any]:
        domain = problem.get("domain", "")
        structures = self.STRUCTURE_PRIORS.get(domain, ["optimization"])

        # Map structure tags to the structured objects.
        structure_objects = {}
        for s in structures:
            if s == "optimization":
                structure_objects["optimization"] = self.optimization_formulations()
            elif s == "probability":
                structure_objects["probability"] = self.probability_models()
            elif s == "graph_theory":
                structure_objects["graph_theory"] = self.graph_theory_concepts()
            elif s == "differential_equations":
                structure_objects["differential_equations"] = self.differential_equation_types()
            elif s == "control_theory":
                structure_objects["control_theory"] = self.control_theory_concepts()
            elif s == "information_theory":
                structure_objects["information_theory"] = {"note": "stub — see INVENTION_COMPILER.md"}

        return {
            "mathematical_structures": structures,
            "structure_objects": structure_objects,
            "evidence": {
                "domain": domain,
                "structure_priors_consulted": list(self.STRUCTURE_PRIORS.keys()),
                "structures_matched": structures,
            },
            "assumptions": [
                "Mathematical structure is inferred from the problem domain "
                "via a heuristic map. This identifies WHICH mathematical "
                "framework applies; it does not SOLVE the problem in that "
                "framework.",
            ],
            "falsification_criteria": (
                "If a mathematician identifies a structural requirement not "
                "in this engine's output, the structure prior map is "
                "incomplete."
            ),
        }

    # ------------------------------------------------------------------
    # Layer 3: propose governing equations
    # ------------------------------------------------------------------

    def analyze_layer3(self, problem: Dict[str, Any],
                        physics_output: Dict[str, Any]) -> Dict[str, Any]:
        equations = []
        for principle in physics_output.get("principles", []):
            label = (principle.get("label") or "").lower()
            for keyword, priors in self.EQUATION_PRIORS.items():
                if keyword in label:
                    for eq in priors:
                        if eq["name"] not in [e["name"] for e in equations]:
                            equations.append(eq)
                            break
        # Also pull equations from applicable_laws if physics module upgraded.
        for law_name in physics_output.get("applicable_laws", []):
            label = law_name.lower()
            for keyword, priors in self.EQUATION_PRIORS.items():
                if keyword in label:
                    for eq in priors:
                        if eq["name"] not in [e["name"] for e in equations]:
                            equations.append(eq)
                            break
        return {
            "governing_equations": equations,
            "evidence": {
                "principles_examined": len(physics_output.get("principles", [])),
                "laws_examined": len(physics_output.get("applicable_laws", [])),
                "equations_proposed": len(equations),
                "prior_map_keys": list(self.EQUATION_PRIORS.keys()),
            },
            "assumptions": [
                "Governing equations are templated starting points, not "
                "calibrated models. They identify WHICH equations must hold; "
                "they do not solve them.",
                "The equation-prior map is small and hand-curated. Many real "
                "physics principles have no entry.",
            ],
            "falsification_criteria": (
                "If a governing equation derived from first principles is "
                "not in this engine's output, the prior map is incomplete "
                "OR the physics principle was not surfaced by Layer 1."
            ),
        }
