"""PTRS lookup and de-risking adjustment utilities."""
import json
import os

_table = None

PHASE_ALIASES = {
    "preclinical": "preclinical",
    "pre-clinical": "preclinical",
    "ind": "ind_enabling",
    "ind_enabling": "ind_enabling",
    "phase 1": "phase1",
    "phase1": "phase1",
    "ph1": "phase1",
    "phase 1/2": "phase1_2",
    "phase1/2": "phase1_2",
    "phase1_2": "phase1_2",
    "phase 1_2": "phase1_2",
    "phase 2": "phase2",
    "phase2": "phase2",
    "ph2": "phase2",
    "phase 2b": "phase2b",
    "phase2b": "phase2b",
    "phase 3": "phase3",
    "phase3": "phase3",
    "ph3": "phase3",
    "nda": "nda_submitted",
    "bla": "nda_submitted",
    "nda_submitted": "nda_submitted",
    "nda submitted": "nda_submitted",
    "approved": "nda_submitted",
}

TA_ALIASES = {
    "oncology": "oncology",
    "cancer": "oncology",
    "hematology": "oncology",
    "immunology": "immunology",
    "inflammation": "immunology",
    "autoimmune": "immunology",
    "neurology": "neurology",
    "neuroscience": "neurology",
    "cns": "neurology",
    "psychiatry": "neurology",
    "rare disease": "rare_disease",
    "rare_disease": "rare_disease",
    "orphan": "rare_disease",
    "cardio": "cardio_metabolic",
    "cardiovascular": "cardio_metabolic",
    "metabolic": "cardio_metabolic",
    "cardio_metabolic": "cardio_metabolic",
    "cardio / metabolic": "cardio_metabolic",
    "mash": "cardio_metabolic",
    "nash": "cardio_metabolic",
    "infectious disease": "infectious_disease",
    "infectious_disease": "infectious_disease",
    "infectious": "infectious_disease",
    "antiviral": "infectious_disease",
}

# Additive PTRS adjustments per de-risking signal
_DERISKING_ADJUSTMENTS = {
    "orphan_drug":                  0.02,
    "fast_track":                   0.03,
    "breakthrough_designation":     0.05,
    "patients_dosed_50plus":        0.03,
    "patients_dosed_100plus":       0.05,   # mutually exclusive with 50plus — use higher
    "best_in_class_efficacy":       0.07,
    "fda_registrational_alignment": 0.04,
    "biomarker_defined_population": 0.03,
    "platform_multi_indication":    0.02,
}

# Hard caps per phase to prevent unrealistic PTRS
_PTRS_CAPS = {
    "preclinical":  0.20,
    "ind_enabling": 0.25,
    "phase1":       0.45,
    "phase1b":      0.45,
    "phase1_2":     0.55,
    "phase2":       0.65,
    "phase2b":      0.70,
    "phase3":       0.85,
    "nda_submitted": 0.95,
}

# Valid signal vocabulary (for reference / validation)
VALID_DERISKING_SIGNALS = set(_DERISKING_ADJUSTMENTS.keys())


def _load_table():
    global _table
    if _table is None:
        path = os.path.join(os.path.dirname(__file__), "../ptrs_table.json")
        with open(path) as f:
            _table = json.load(f)
    return _table


def lookup_ptrs(phase: str, therapeutic_area: str) -> float:
    """Return base PTRS for a given phase and therapeutic area. Defaults gracefully."""
    table = _load_table()
    phase_key = PHASE_ALIASES.get((phase or "phase2").lower().strip(), "phase2")
    ta_key = TA_ALIASES.get((therapeutic_area or "oncology").lower().strip(), "oncology")
    return table.get(phase_key, {}).get(ta_key, 0.30)


def get_adjusted_ptrs(phase: str, ta: str, de_risking_signals: list[str]) -> dict:
    """
    Compute PTRS adjusted for de-risking signals.

    Returns:
        {
            "base": float,
            "adjusted": float,
            "breakdown": [{signal, contribution}, ...]
        }
    """
    phase_key = PHASE_ALIASES.get((phase or "phase2").lower().strip(), phase)
    base = lookup_ptrs(phase_key, ta)

    # Filter to valid signals only
    signals = [s for s in (de_risking_signals or []) if s in VALID_DERISKING_SIGNALS]
    has_100plus = "patients_dosed_100plus" in signals

    breakdown = []
    total_adjustment = 0.0

    for signal in signals:
        # patients_dosed_50plus and 100plus are mutually exclusive — use higher
        if signal == "patients_dosed_50plus" and has_100plus:
            continue
        contribution = _DERISKING_ADJUSTMENTS[signal]
        breakdown.append({"signal": signal, "contribution": contribution})
        total_adjustment += contribution

    adjusted = base + total_adjustment
    cap = _PTRS_CAPS.get(phase_key, 0.65)
    adjusted = min(adjusted, cap)

    return {
        "base": round(base, 3),
        "adjusted": round(adjusted, 3),
        "breakdown": breakdown,
    }


def normalize_phase(phase: str) -> str:
    """Return the canonical phase key used in ptrs_table.json."""
    if not phase:
        return "phase2"
    return PHASE_ALIASES.get(phase.lower().strip(), phase.lower().strip())


def normalize_ta(ta: str) -> str:
    """Return the canonical TA key used in ptrs_table.json."""
    if not ta:
        return "oncology"
    return TA_ALIASES.get(ta.lower().strip(), ta.lower().strip())
