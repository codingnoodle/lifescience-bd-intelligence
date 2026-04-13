"""Utilities for selecting comparable deal transactions from the benchmark database."""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_BENCHMARKS_PATH = Path(__file__).parent / "deal_benchmarks.json"

_TA_KEYWORDS: list[tuple[str, list[str]]] = [
    ("oncology_hematology",    ["hematol", "leukemia", "lymphoma", "myeloma", "aml", "cml", "t-cell", "b-cell"]),
    ("oncology_adc",           ["adc", "antibody-drug"]),
    ("oncology_io_bispecific", ["bispecific", "pd-1", "pd-l1", "io "]),
    ("oncology",               ["oncol", "tumor", "cancer", "solid"]),
    ("cardiometabolic",        ["cardio", "metabol", "obes", "mash", "glp", "lipid", "ascvd", "cardiovasc"]),
    ("immunology",             ["immuno", "autoimmune", "mast", "inflammatory"]),
    ("neuroscience",           ["neuro", "cns", "psych", "sleep", "alzheim", "parkin", "muscular"]),
    ("rare_disease",           ["rare", "orphan", "genetic", "lsd", "enpp"]),
    ("respiratory",            ["respir", "pulmon", "copd", "asthma", "bronch"]),
    ("infectious_disease",     ["infect", "antivir", "antibiot", "vaccine", "fungal"]),
]

_PHASE_ORDER = ["preclinical", "phase1", "phase1b", "phase1_2", "phase2", "phase2b", "phase3", "marketed"]

def _normalize_phase(phase: str) -> str:
    p = phase.lower().replace(" ", "").replace("-", "_").replace("/", "_")
    for candidate in reversed(_PHASE_ORDER):  # most specific first
        if candidate in p or candidate.replace("_", "") in p:
            return candidate
    return "phase2"

def _ta_bucket(ta: str) -> str:
    ta_lower = ta.lower()
    for bucket, keywords in _TA_KEYWORDS:
        if any(kw in ta_lower for kw in keywords):
            return bucket
    return "oncology"

def _phase_distance(p1: str, p2: str) -> int:
    """Lower = more similar phase."""
    try:
        return abs(_PHASE_ORDER.index(p1) - _PHASE_ORDER.index(p2))
    except ValueError:
        return 99

def get_comparable_deals(ta: str, phase: str, n: int = 5) -> list[dict]:
    """
    Return the n most relevant raw deal records for a given TA + phase.
    Selects by TA bucket match first, then by phase proximity.
    Returns raw deal dicts — NO pre-computed ranges.
    """
    try:
        with open(_BENCHMARKS_PATH) as f:
            data = json.load(f)
    except Exception as e:
        logger.warning(f"Could not load deal_benchmarks.json: {e}")
        return []

    target_bucket = _ta_bucket(ta)
    target_phase = _normalize_phase(phase)

    all_deals = data.get("ma_deals", []) + [
        {**d, "deal_type": "licensing"} for d in data.get("licensing_deals", [])
    ]

    # Score each deal: lower is better
    scored = []
    for deal in all_deals:
        if not deal.get("upfront_bn"):
            continue
        deal_bucket = _ta_bucket(deal.get("ta", ""))
        deal_phase = _normalize_phase(deal.get("phase", ""))
        ta_match = 0 if deal_bucket == target_bucket else (1 if deal_bucket.split("_")[0] == target_bucket.split("_")[0] else 2)
        phase_dist = _phase_distance(target_phase, deal_phase)
        scored.append((ta_match * 10 + phase_dist, deal))

    scored.sort(key=lambda x: x[0])
    return [d for _, d in scored[:n]]


def format_comps_for_prompt(ta: str, phase: str, n: int = 5) -> str:
    """
    Return a formatted block of comparable transactions for injection into agent prompts.
    Provides raw facts only — no pre-computed ranges, no anchoring.
    """
    comps = get_comparable_deals(ta, phase, n=n)
    if not comps:
        return "No comparable transactions found in database — rely on your training knowledge of recent pharma M&A."

    lines = [
        "Comparable transactions (2025–2026, real M&A + licensing data):",
        "Use these as reference points. Assess how similar/different the current asset is to each comp,",
        "then derive your own estimate — do NOT simply copy a comp's value.",
        "",
    ]
    for d in comps:
        deal_type = d.get("deal_type", "M&A")
        upfront = f"${d['upfront_bn']}B upfront"
        total = f" (${d.get('total_bn')}B total)" if d.get("total_bn") else ""
        lines.append(
            f"  • [{deal_type}] {d['buyer']} / {d['asset'][:55]}"
        )
        lines.append(
            f"    TA: {d['ta']} | Phase: {d['phase']} | Modality: {d.get('modality','unknown')}"
        )
        lines.append(f"    Deal: {upfront}{total}")
        lines.append("")

    return "\n".join(lines)
