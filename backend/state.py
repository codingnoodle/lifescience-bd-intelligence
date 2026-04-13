from typing import TypedDict, Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Legacy Pydantic model — kept for backward compat with ptrs_calculator.py and indications_agent.py
class Indication(BaseModel):
    name: str = ""
    therapeutic_area: str = ""
    clinical_stage: str = ""
    is_primary: bool = False
    launch_year: Optional[int] = None
    ptrs_score: Optional[float] = None
    science_score: Optional[float] = None
    science_rationale: Optional[str] = None
    peak_sales_bn: Optional[float] = None
    market_score: Optional[float] = None
    market_rationale: Optional[str] = None
    npv_usd: Optional[float] = None


class PortfolioValuation(BaseModel):
    """Legacy model for ptrs_calculator.py compat."""
    total_npv: float = 0.0
    indications: List[Indication] = []


class IndicationAnalysis(TypedDict, total=False):
    """Per-indication state enriched sequentially by science then market agents."""
    # Set by research planner
    name: str
    phase: str
    therapeutic_area: str
    launch_year: Optional[int]

    # Science agent writes
    positioning_profile: Dict[str, Any]   # target, moa, line_of_therapy, efficacy_metrics, safety_metrics, differentiation_claims
    de_risking_signals: List[str]          # from fixed vocabulary in ptrs_lookup.py
    ptrs_base: float
    ptrs_adjusted: float
    ptrs_breakdown: List[Dict[str, Any]]  # [{signal, contribution}, ...]
    science_score: float
    science_rationale: str

    # Market agent writes
    comparator: Dict[str, Any]             # {name, sponsor, peak_sales_bn, source}
    metric_comparison: List[Dict[str, Any]]  # [{metric, asset_value, comparator_value, direction}, ...]
    differentiation_verdict: str           # best_in_class / better_in_class / me_too / worse_in_class
    peak_sales_standalone_bn: float        # undiscounted, own patient population
    peak_sales_with_displacement_bn: float # undiscounted, includes SOC capture if applicable
    market_score: float
    market_rationale: str
    comparator_confidence: str             # high / medium / low
    # Computed by synthesizer (per-indication dual values)
    peak_sales_risk_adjusted_bn: float     # peak × PTRS × NPV discount
    peak_sales_if_succeed_bn: float        # peak × NPV discount (no PTRS)


class BDState(TypedDict, total=False):
    """Shared state for the BD intelligence multi-agent system."""

    # Input
    message: str
    filters: Dict[str, Any]

    # Parsed by research planner
    drug_asset_name: str
    indications: List[IndicationAnalysis]
    clarification_needed: Optional[str]
    research_plan: Optional[str]

    # Synthesis outputs
    composite_score: Optional[float]
    science_score: Optional[float]
    market_score: Optional[float]
    recommendation: Optional[str]
    summary: Optional[str]

    # Three-scenario valuation (replaces single deal range)
    scenario_standalone: Optional[Dict[str, Any]]    # {value_bn, derivation_string}
    scenario_displacement: Optional[Dict[str, Any]]  # {value_bn, derivation_string}
    scenario_strategic: Optional[Dict[str, Any]]     # {value_bn, derivation_string}

    # Buyer analysis
    buyers: Optional[List[Dict[str, Any]]]     # [{name, urgency_multiplier, confidence, rationale}]
    bidding_tension: Optional[Dict[str, Any]]  # {score, premium, signals, confidence}

    # Metadata
    messages: List[Dict[str, Any]]
    errors: List[str]
