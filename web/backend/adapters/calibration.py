"""CalibrationStore - no hidden constants."""
PRIORS = {
    "pass_through_rate": (0.6, "assumed cost pass-through; fit to BOM evidence"),
    "viability_threshold": (0.5, "assumed; fit to licensing/decision outcomes"),
    "viability_gain": (0.5, "activation->viability scaling; fit to replay"),
    "propagation_rate": (0.35, "edge transmission; fit to historical replay"),
    "equilibrium_damping": (0.5, "relaxation damping; numerical choice"),
    "equilibrium_max_iter": (12, "iteration cap; numerical choice"),
    "equilibrium_eps": (1e-3, "convergence tolerance; numerical choice"),
    "competition_purpose_weight": (0.8, "shared-purpose competition; fit to market data"),
    "competition_niche_weight": (0.2, "same-niche competition; fit to market data"),
    "confidence_base": (0.6, "heuristic confidence floor; calibrate via reliability diagram"),
}
class CalibrationStore:
    def __init__(self): self.fitted = {}
    def get(self, name): return self.fitted.get(name, PRIORS[name][0])
    def status(self): return {n: {"value": self.get(n), "calibrated": n in self.fitted, "provenance": PRIORS[n][1]} for n in PRIORS}
    def calibrate_from_ledger(self, ledger):
        outcomes = [e for e in ledger if e.get("outcome") not in (None, "pending")]
        if len(outcomes) < 20: return {"fitted": False, "reason": f"insufficient evidence ({len(outcomes)}/20)"}
        return {"fitted": True, "n": len(outcomes)}
C = CalibrationStore()
