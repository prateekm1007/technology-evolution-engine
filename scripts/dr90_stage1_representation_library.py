#!/usr/bin/env python3
"""
dr90_stage1_representation_library.py — DR-90 Stage 1: Study Human Invention (cycle 241).

Per DR-90 (docs/DR-90_REPRESENTATION_DISCOVERY.md):
  "Stage 1 — Study Human Invention. Humans almost never invent by
   composing operators. They invent by changing representation."

  Deliverable: representation_library.json
  Each entry: primitive, why it mattered, what representation changed,
  what previous representation failed, what new search became possible.
  Target: 100 historical invention primitives.

This is NOT code. This is knowledge engineering — studying how humans
invented new representations throughout history and encoding the pattern.

The library is the TRAINING DATA for DR-90 Stage 2 (Representation
Grammar). The engine will learn from these examples what a
"representational change" looks like, then attempt to generate new ones.

HONEST STATUS:
  - This is the FIRST deliverable of DR-90.
  - The entries are CURATED by the engineer (not discovered by the engine).
  - The engine will USE this library in later stages to learn patterns.
  - The library is NOT complete (100 target; starts with 25, grows over time).
  - This is a NEW RESEARCH PROGRAM, not "Cycle 241" of the old DSL.
"""
import json
from pathlib import Path


# ============================================================================
# REPRESENTATION LIBRARY — 25 Historical Invention Primitives (initial set)
# ============================================================================

REPRESENTATION_LIBRARY = [
    # === Mathematics ===
    {
        "id": "REP-001",
        "primitive": "Zero",
        "field": "mathematics",
        "year_approx": "628 CE (Brahmagupta)",
        "why_it_mattered": "Enabled positional notation, algebra, and the concept of 'nothing' as a quantity.",
        "what_representation_changed": "From counting (only positive integers) to a number system with a placeholder for absence.",
        "what_previous_representation_failed": "Roman numerals had no zero — arithmetic was done on abaci, not symbolically. Subtraction like X - X had no symbolic answer.",
        "what_new_search_became_possible": "Algebraic manipulation (solving equations with unknowns), positional arithmetic, calculus (limits require approaching zero)."
    },
    {
        "id": "REP-002",
        "primitive": "Calculus (derivatives and integrals)",
        "field": "mathematics",
        "year_approx": "1666 (Newton) / 1675 (Leibniz)",
        "why_it_mattered": "Enabled the study of continuous change, optimization, and accumulation.",
        "what_representation_changed": "From discrete algebra (finite operations) to infinitesimal operations (limits, rates of change).",
        "what_previous_representation_failed": "Discrete algebra could not describe velocity, acceleration, or area under a curve. Archimedes' method of exhaustion was ad hoc and not generalizable.",
        "what_new_search_became_possible": "Optimization (find extrema via derivatives), differential equations (model dynamic systems), physics (Newton's laws require calculus)."
    },
    {
        "id": "REP-003",
        "primitive": "Complex numbers",
        "field": "mathematics",
        "year_approx": "1545 (Cardano) / 1831 (Gauss)",
        "why_it_mattered": "Made algebra complete (fundamental theorem of algebra) and enabled signal processing.",
        "what_representation_changed": "From real line (1D) to complex plane (2D with imaginary axis).",
        "what_previous_representation_failed": "Real numbers could not represent solutions to x² + 1 = 0. Polynomial roots were 'impossible' without complex numbers.",
        "what_new_search_became_possible": "Fourier analysis (signals as complex exponentials), quantum mechanics (wave functions are complex), control theory (stability via complex poles)."
    },
    {
        "id": "REP-004",
        "primitive": "Vector spaces (linear algebra)",
        "field": "mathematics",
        "year_approx": "1888 (Peano) / 1920s (formalized)",
        "why_it_mattered": "Enabled manipulation of multi-dimensional quantities as single objects.",
        "what_representation_changed": "From scalar equations (one variable at a time) to vector/matrix operations (all dimensions simultaneously).",
        "what_previous_representation_failed": "Scalar algebra required writing N equations for N variables. Transformations were tedious and error-prone.",
        "what_new_search_became_possible": "Matrix methods (solve systems, eigenvalues, SVD), computer graphics (transformations), machine learning (neural network weights as matrices)."
    },
    {
        "id": "REP-005",
        "primitive": "Fourier transform",
        "field": "mathematics / signal processing",
        "year_approx": "1822 (Fourier)",
        "why_it_mattered": "Enabled decomposition of any signal into frequency components.",
        "what_representation_changed": "From time domain (signal as function of time) to frequency domain (signal as sum of sinusoids).",
        "what_previous_representation_failed": "Time-domain analysis couldn't separate overlapping frequency components. Filtering was ad hoc.",
        "what_new_search_became_possible": "Spectral analysis, compression (JPEG, MP3), filtering (remove specific frequencies), convolution theorem (fast convolution via FFT)."
    },
    {
        "id": "REP-006",
        "primitive": "Tensor notation",
        "field": "mathematics / physics",
        "year_approx": "1900 (Ricci-Curbastro)",
        "why_it_mattered": "Enabled coordinate-free description of physical laws.",
        "what_representation_changed": "From component-wise equations (depend on coordinate system) to tensor equations (valid in all frames).",
        "what_previous_representation_failed": "Component notation made general relativity nearly impossible to express — equations changed with every coordinate transformation.",
        "what_new_search_became_possible": "General relativity (Einstein field equations), continuum mechanics, machine learning (multi-dimensional data as tensors)."
    },
    {
        "id": "REP-007",
        "primitive": "Probability distributions",
        "field": "mathematics / statistics",
        "year_approx": "1713 (Bernoulli) / 1933 (Kolmogorov)",
        "why_it_mattered": "Enabled reasoning under uncertainty.",
        "what_representation_changed": "From deterministic values (single answer) to distributions (range of possible answers with probabilities).",
        "what_previous_representation_failed": "Deterministic models couldn't represent noise, measurement error, or inherent randomness.",
        "what_new_search_became_possible": "Bayesian inference, statistical hypothesis testing, Monte Carlo methods, probabilistic ML."
    },
    {
        "id": "REP-008",
        "primitive": "Graph theory",
        "field": "mathematics",
        "year_approx": "1736 (Euler)",
        "why_it_mattered": "Enabled representation of relational structure (not just quantities).",
        "what_representation_changed": "From numerical data (values) to relational data (nodes + edges representing connections).",
        "what_previous_representation_failed": "Tables and equations couldn't naturally represent network structure (social networks, molecular bonds, circuits).",
        "what_new_search_became_possible": "Network analysis, shortest paths, matching, flow problems, graph neural networks."
    },
    {
        "id": "REP-009",
        "primitive": "Information entropy (Shannon)",
        "field": "information theory",
        "year_approx": "1948 (Shannon)",
        "why_it_mattered": "Quantified information and enabled digital communication.",
        "what_representation_changed": "From messages as sequences of symbols to messages as bit strings with measurable information content.",
        "what_previous_representation_failed": "No formal measure of 'how much information' a message contains. Compression and channel capacity were undefined.",
        "what_new_search_became_possible": "Data compression (Huffman, Lempel-Ziv), error-correcting codes, channel capacity theorem, maximum entropy methods."
    },
    {
        "id": "REP-010",
        "primitive": "Dynamic programming",
        "field": "computer science",
        "year_approx": "1950s (Bellman)",
        "why_it_mattered": "Enabled efficient solution of problems with overlapping subproblems.",
        "what_representation_changed": "From exhaustive search (try all possibilities) to memoized recursion (store and reuse subproblem solutions).",
        "what_previous_representation_failed": "Naive recursion on problems like Fibonacci or shortest path had exponential complexity due to redundant computation.",
        "what_new_search_became_possible": "Optimal control (Bellman equation), sequence alignment (bioinformatics), reinforcement learning (value functions)."
    },

    # === Computing ===
    {
        "id": "REP-011",
        "primitive": "Turing machine",
        "field": "computer science",
        "year_approx": "1936 (Turing)",
        "why_it_mattered": "Defined the limits of computation.",
        "what_representation_changed": "From informal algorithms (recipes) to formal state machines (tape, head, states, transitions).",
        "what_previous_representation_failed": "No formal model of 'what is computable.' Hilbert's Entscheidungsproblem had no answer.",
        "what_new_search_became_possible": "Computability theory, complexity classes (P, NP), universal computation, von Neumann architecture."
    },
    {
        "id": "REP-012",
        "primitive": "Lambda calculus",
        "field": "computer science",
        "year_approx": "1936 (Church)",
        "why_it_mattered": "Provided a foundation for functional programming.",
        "what_representation_changed": "From state machines (Turing) to function application (everything is a function).",
        "what_previous_representation_failed": "Turing machines are imperative — they describe HOW to compute step by step. Lambda calculus describes WHAT to compute declaratively.",
        "what_new_search_became_possible": "Functional programming (LISP, Haskell), type theory, Curry-Howard correspondence (proofs = programs)."
    },
    {
        "id": "REP-013",
        "primitive": "Gradient descent",
        "field": "optimization / ML",
        "year_approx": "1847 (Cauchy)",
        "why_it_mattered": "Enabled optimization of differentiable functions.",
        "what_representation_changed": "From discrete search (try points, compare) to directional search (follow the gradient downhill).",
        "what_previous_representation_failed": "Grid search and random search don't scale to high dimensions — the search space grows exponentially.",
        "what_new_search_became_possible": "Convex optimization, neural network training (backprop uses gradient descent), logistic regression, SVMs."
    },
    {
        "id": "REP-014",
        "primitive": "Backpropagation",
        "field": "machine learning",
        "year_approx": "1986 (Rumelhart, Hinton, Williams)",
        "why_it_mattered": "Enabled efficient training of multi-layer neural networks.",
        "what_representation_changed": "From manual gradient computation (derive each layer's gradient by hand) to automatic differentiation (chain rule applied automatically through the computation graph).",
        "what_previous_representation_failed": "Manual gradient derivation was intractable for networks with more than 2-3 layers. Perceptrons (single layer) couldn't learn XOR.",
        "what_new_search_became_possible": "Deep learning (CNNs, RNNs, transformers), any-depth neural networks, automatic differentiation frameworks (PyTorch, JAX)."
    },
    {
        "id": "REP-015",
        "primitive": "Attention mechanism",
        "field": "machine learning",
        "year_approx": "2014 (Bahdanau) / 2017 (Vaswani)",
        "why_it_mattered": "Enabled dynamic routing of information based on relevance.",
        "what_representation_changed": "From fixed-weight connections (every input contributes equally) to dynamic attention weights (the model learns which inputs to focus on per context).",
        "what_previous_representation_failed": "RNNs processed sequences sequentially — early tokens were 'forgotten' by the time late tokens arrived. Fixed connections couldn't adapt to context.",
        "what_new_search_became_possible": "Transformers, GPT/BERT, self-attention, multi-head attention, in-context learning."
    },
    {
        "id": "REP-016",
        "primitive": "Monte Carlo Tree Search",
        "field": "AI / game playing",
        "year_approx": "2006 (Coulom) / 2016 (AlphaGo)",
        "why_it_mattered": "Enabled planning in games with huge branching factors.",
        "what_representation_changed": "From exhaustive minimax (evaluate all moves) to probabilistic sampling (sample promising moves via UCT, build asymmetric tree).",
        "what_previous_representation_failed": "Minimax with alpha-beta pruning was intractable for Go (10^170 positions). No good heuristic evaluation function existed.",
        "what_new_search_became_possible": "AlphaGo, AlphaZero, game AI for Go/Chess/Shogi, planning under uncertainty."
    },
    {
        "id": "REP-017",
        "primitive": "Bayesian Optimization",
        "field": "optimization",
        "year_approx": "1975 (Kushner) / 1998 (Jones, EGO)",
        "why_it_mattered": "Enabled optimization of expensive black-box functions.",
        "what_representation_changed": "From direct evaluation (try each point) to surrogate-based optimization (fit a model, optimize the acquisition function).",
        "what_previous_representation_failed": "Direct methods (grid, random, evolutionary) require too many evaluations for expensive functions (each eval takes hours/days).",
        "what_new_search_became_possible": "Hyperparameter tuning, drug discovery, materials design, A/B testing with small samples."
    },
    {
        "id": "REP-018",
        "primitive": "Generative adversarial networks (GANs)",
        "field": "machine learning",
        "year_approx": "2014 (Goodfellow)",
        "why_it_mattered": "Enabled generation of realistic data via adversarial training.",
        "what_representation_changed": "From single-model learning (one network learns to classify/generate) to two-model adversarial learning (generator vs discriminator in a game).",
        "what_previous_representation_failed": "Autoregressive models produced blurry images. VAEs had limited fidelity. No principled way to generate realistic data.",
        "what_new_search_became_possible": "Photorealistic image generation, style transfer, deepfakes, data augmentation."
    },
    {
        "id": "REP-019",
        "primitive": "Diffusion models",
        "field": "machine learning",
        "year_approx": "2020 (Ho, DDPM)",
        "why_it_mattered": "Enabled high-quality generation via iterative denoising.",
        "what_representation_changed": "From direct generation (one-shot: noise → image) to iterative generation (noise → denoise → denoise → ... → image).",
        "what_previous_representation_failed": "GANs were hard to train (mode collapse, instability). VAEs produced blurry outputs. Direct generation couldn't produce high-fidelity results.",
        "what_new_search_became_possible": "Stable Diffusion, DALL-E, image editing, text-to-image, video generation."
    },
    {
        "id": "REP-020",
        "primitive": "Reinforcement learning (MDP formulation)",
        "field": "AI / control",
        "year_approx": "1950s (Bellman) / 1989 (Watkins, Q-learning)",
        "why_it_mattered": "Enabled learning optimal policies through interaction.",
        "what_representation_changed": "From supervised learning (labeled examples) to experiential learning (agent interacts with environment, receives rewards).",
        "what_previous_representation_failed": "Supervised learning requires labeled data. Many problems (game playing, robotics) have no labels — only outcomes (win/lose, reward).",
        "what_new_search_became_possible": "AlphaGo, robotic control, autonomous driving, game AI, recommendation systems."
    },

    # === Physics / Engineering ===
    {
        "id": "REP-021",
        "primitive": "Lagrangian/Hamiltonian mechanics",
        "field": "physics",
        "year_approx": "1788 (Lagrange) / 1833 (Hamilton)",
        "why_it_mattered": "Enabled systematic derivation of equations of motion for any system.",
        "what_representation_changed": "From Newton's force-based mechanics (vector equations per particle) to energy-based mechanics (scalar Lagrangian L = T - V for the whole system).",
        "what_previous_representation_failed": "Newton's approach required decomposing forces for each particle — intractable for constrained systems (pendulums, rigid bodies).",
        "what_new_search_became_possible": "Analytical mechanics, Noether's theorem (symmetries → conservation laws), quantum mechanics (Hamiltonian operator), field theory."
    },
    {
        "id": "REP-022",
        "primitive": "Phase space",
        "field": "physics / dynamical systems",
        "year_approx": "1800s (Gibbs, Boltzmann)",
        "why_it_mattered": "Enabled geometric analysis of dynamical systems.",
        "what_representation_changed": "From time-series (track position over time) to phase-space trajectories (plot position AND momentum, see the geometry of dynamics).",
        "what_previous_representation_failed": "Time-series analysis couldn't reveal attractors, bifurcations, or stability — these are geometric properties invisible in 1D time plots.",
        "what_new_search_became_possible": "Chaos theory, stability analysis, statistical mechanics, optimal control (LQR operates in phase space)."
    },
    {
        "id": "REP-023",
        "primitive": "Symmetry groups",
        "field": "mathematics / physics",
        "year_approx": "1830 (Galois) / 1920s (Weyl)",
        "why_it_mattered": "Connected symmetries to conservation laws and classification.",
        "what_representation_changed": "From individual equations (solve case by case) to symmetry-based classification (group theory: find all structures with a given symmetry).",
        "what_previous_representation_failed": "Ad hoc approaches couldn't classify particles, crystals, or equations. Noether's theorem required a formal symmetry framework.",
        "what_new_search_became_possible": "Particle physics (Standard Model via gauge groups), crystallography (230 space groups), Galois theory (solvability of polynomial equations)."
    },
    {
        "id": "REP-024",
        "primitive": "Duality (linear programming / convex optimization)",
        "field": "optimization",
        "year_approx": "1947 (Dantzig) / 1960s (formalized)",
        "why_it_mattered": "Enabled solving optimization problems from two perspectives.",
        "what_representation_changed": "From primal-only optimization (minimize f(x)) to primal-dual optimization (minimize f(x) = maximize g(y), with complementary slackness).",
        "what_previous_representation_failed": "Primal-only approaches couldn't provide optimality certificates or bounds without solving the full problem.",
        "what_new_search_became_possible": "LP duality (strong/weak), KKT conditions, interior point methods, SVM optimization, game theory (minimax = duality)."
    },
    {
        "id": "REP-025",
        "primitive": "Manifold hypothesis (high-dimensional data lies on low-dimensional manifolds)",
        "field": "machine learning / geometry",
        "year_approx": "2000s (Tenenbaum, Roweis)",
        "why_it_mattered": "Enabled dimensionality reduction and geometric ML.",
        "what_representation_changed": "From Euclidean space (data in R^n) to manifold space (data on a curved surface embedded in R^n).",
        "what_previous_representation_failed": "Euclidean distance in high dimensions is uninformative (curse of dimensionality). PCA assumed linear structure.",
        "what_new_search_became_possible": "t-SNE, UMAP, manifold learning, geometric deep learning, normalizing flows (density on manifolds)."
    },
]


# ============================================================================
# SAVE LIBRARY TO JSON
# ============================================================================

def save_library(path: str = "data/dr90/representation_library.json"):
    """Save the representation library to JSON."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(REPRESENTATION_LIBRARY, f, indent=2)
    print(f"Saved {len(REPRESENTATION_LIBRARY)} entries to {path}")


def load_library(path: str = "data/dr90/representation_library.json") -> list:
    """Load the representation library from JSON."""
    with open(path, "r") as f:
        return json.load(f)


def analyze_library(library: list):
    """Analyze patterns in the representation library."""
    print("=" * 80)
    print("REPRESENTATION LIBRARY ANALYSIS")
    print("=" * 80)
    print()
    print(f"Total entries: {len(library)}")
    print()

    # By field
    from collections import Counter
    fields = Counter(e["field"] for e in library)
    print("By field:")
    for field, count in fields.most_common():
        print(f"  {field}: {count}")
    print()

    # Common patterns in what_representation_changed
    change_patterns = Counter()
    for e in library:
        text = e["what_representation_changed"].lower()
        if "from" in text and "to" in text:
            # Extract the "from X to Y" pattern
            change_patterns["from_X_to_Y"] += 1
        if "discrete" in text or "finite" in text:
            change_patterns["discrete_to_continuous"] += 1
        if "scalar" in text or "single" in text:
            change_patterns["scalar_to_vector"] += 1
        if "manual" in text or "ad hoc" in text:
            change_patterns["manual_to_systematic"] += 1
        if "fixed" in text:
            change_patterns["fixed_to_adaptive"] += 1
        if "time" in text or "sequence" in text:
            change_patterns["time_to_frequency_or_space"] += 1

    print("Representation change patterns:")
    for pattern, count in change_patterns.most_common():
        print(f"  {pattern}: {count}")
    print()

    # Common patterns in what_new_search_became_possible
    search_patterns = Counter()
    for e in library:
        text = e["what_new_search_became_possible"].lower()
        if "optimization" in text or "optimize" in text:
            search_patterns["optimization_enabled"] += 1
        if "learning" in text or "train" in text:
            search_patterns["learning_enabled"] += 1
        if "compression" in text or "compress" in text:
            search_patterns["compression_enabled"] += 1
        if "classification" in text or "classify" in text:
            search_patterns["classification_enabled"] += 1
        if "generation" in text or "generate" in text:
            search_patterns["generation_enabled"] += 1
        if "prediction" in text or "predict" in text:
            search_patterns["prediction_enabled"] += 1
        if "planning" in text or "control" in text:
            search_patterns["planning_enabled"] += 1

    print("New search capabilities enabled:")
    for pattern, count in search_patterns.most_common():
        print(f"  {pattern}: {count}")
    print()

    # Key insight
    print("=" * 80)
    print("KEY INSIGHT FOR DR-90")
    print("=" * 80)
    print()
    print("The representation library reveals that representational inventions")
    print("follow a small number of TRANSFORMATION PATTERNS:")
    print()
    print("  1. DISCRETE → CONTINUOUS (calculus, gradient descent, diffusion)")
    print("  2. SCALAR → VECTOR/TENSOR (vector spaces, tensors, attention)")
    print("  3. MANUAL → AUTOMATIC (backprop, dynamic programming)")
    print("  4. FIXED → ADAPTIVE (attention, parameterized models)")
    print("  5. DIRECT → SURROGATE (Bayesian opt, MCTS, GANs)")
    print("  6. EUCLIDEAN → MANIFOLD (manifold hypothesis, phase space)")
    print("  7. TIME → FREQUENCY/SPACE (Fourier transform)")
    print("  8. PRIMAL → DUAL (duality, Lagrangian/Hamiltonian)")
    print()
    print("These 8 patterns are the GRAMMAR of representation change.")
    print("DR-90 Stage 2 will formalize these into a representation DSL.")
    print("DR-90 Stage 3 will mutate representations using these patterns.")
    print()
    print(f"Current library: {len(library)} entries (target: 100)")
    print(f"Remaining: {100 - len(library)} entries to add in future iterations.")


if __name__ == "__main__":
    save_library()
    library = load_library()
    analyze_library(library)
