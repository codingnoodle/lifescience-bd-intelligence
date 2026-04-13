"""PTRS calculation and portfolio valuation utilities."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from backend.state import Indication, PortfolioValuation

logger = logging.getLogger(__name__)


class PTRSCalculator:
    """Calculate Probability of Technical and Regulatory Success (PTRS)."""

    def __init__(self, ptrs_table_path: Optional[str] = None):
        """
        Initialize PTRS calculator with lookup table.

        Args:
            ptrs_table_path: Path to PTRS JSON file. If None, uses default.
        """
        if ptrs_table_path is None:
            # Default to backend/ptrs_table.json
            backend_dir = Path(__file__).parent.parent
            ptrs_table_path = backend_dir / "ptrs_table.json"

        with open(ptrs_table_path, 'r') as f:
            self.ptrs_table: Dict[str, Dict[str, float]] = json.load(f)

        logger.info(f"Loaded PTRS table from {ptrs_table_path}")

    def get_ptrs(
        self,
        clinical_stage: str,
        therapeutic_area: str
    ) -> Optional[float]:
        """
        Look up PTRS score for a given stage and therapeutic area.

        Args:
            clinical_stage: Development stage (preclinical, phase1, phase2, etc.)
            therapeutic_area: Therapeutic area (oncology, immunology, etc.)

        Returns:
            PTRS score (0-1) or None if not found
        """
        # Normalize inputs
        stage = clinical_stage.lower().replace(" ", "_").replace("-", "_")
        area = therapeutic_area.lower().replace(" ", "_").replace("-", "_")

        # Look up in table
        if stage in self.ptrs_table and area in self.ptrs_table[stage]:
            ptrs = self.ptrs_table[stage][area]
            logger.info(f"PTRS for {stage}/{area}: {ptrs}")
            return ptrs
        else:
            logger.warning(f"PTRS not found for {stage}/{area}")
            return None

    def calculate_risk_adjusted_npv(
        self,
        npv: float,
        ptrs: float
    ) -> float:
        """
        Calculate risk-adjusted NPV.

        rNPV = NPV × PTRS

        Args:
            npv: Net present value (undiscounted for risk)
            ptrs: Probability of technical and regulatory success

        Returns:
            Risk-adjusted NPV
        """
        return npv * ptrs


def calculate_portfolio_value(
    indications: List[Indication],
    discount_rate: float = 0.10,
    optionality_premium_pct: float = 0.15
) -> PortfolioValuation:
    """
    Calculate portfolio-level valuation across multiple indications.

    This implements a real-world BD valuation approach:
    1. Calculate risk-adjusted NPV for each indication
    2. Sum primary + secondary indications
    3. Add optionality premium for having multiple shots on goal
    4. Assess diversification benefit

    Args:
        indications: List of all indications (primary + secondary)
        discount_rate: Discount rate for NPV calculations
        optionality_premium_pct: Premium % for optionality (default 15%)

    Returns:
        PortfolioValuation with portfolio-level metrics
    """
    if not indications:
        return PortfolioValuation(
            total_indications=0,
            portfolio_npv=0.0,
            portfolio_risk_adjusted_npv=0.0
        )

    # Separate primary and secondary indications
    primary_indications = [ind for ind in indications if ind.is_primary]
    secondary_indications = [ind for ind in indications if not ind.is_primary]

    # Calculate NPVs
    primary_npv = sum(
        ind.risk_adjusted_npv_usd or 0.0
        for ind in primary_indications
    )

    secondary_npv = sum(
        ind.risk_adjusted_npv_usd or 0.0
        for ind in secondary_indications
    )

    # Base portfolio value
    base_portfolio_npv = primary_npv + secondary_npv

    # Optionality premium: Having multiple indications increases value
    # because if primary fails, you still have secondary shots on goal
    optionality_premium = 0.0
    if len(secondary_indications) > 0:
        # Premium scales with number of secondary indications
        # But with diminishing returns (sqrt)
        num_secondary = len(secondary_indications)
        optionality_premium = base_portfolio_npv * optionality_premium_pct * (num_secondary ** 0.5)

    # Total portfolio value
    total_portfolio_npv = base_portfolio_npv + optionality_premium

    # Diversification benefit assessment
    diversification_benefit = _assess_diversification(indications)

    return PortfolioValuation(
        total_indications=len(indications),
        primary_indication_npv=primary_npv,
        secondary_indications_npv=secondary_npv,
        portfolio_npv=base_portfolio_npv,
        portfolio_risk_adjusted_npv=total_portfolio_npv,
        optionality_premium=optionality_premium,
        diversification_benefit=diversification_benefit
    )


def _assess_diversification(indications: List[Indication]) -> str:
    """
    Assess qualitative diversification benefit.

    Args:
        indications: List of all indications

    Returns:
        Qualitative assessment string
    """
    if len(indications) <= 1:
        return "No diversification - single indication risk"

    # Check if indications span multiple therapeutic areas
    therapeutic_areas = set(ind.therapeutic_area for ind in indications)

    # Check if indications are at different stages
    stages = set(ind.clinical_stage for ind in indications)

    if len(therapeutic_areas) > 1 and len(stages) > 1:
        return "Strong diversification - multiple therapeutic areas and development stages reduce portfolio risk"
    elif len(therapeutic_areas) > 1:
        return "Moderate diversification - multiple therapeutic areas provide market risk diversification"
    elif len(stages) > 1:
        return "Moderate diversification - staggered development stages provide temporal risk diversification"
    else:
        return "Limited diversification - indications clustered in same area and stage"


def estimate_npv_simple(
    peak_sales: float,
    years_to_peak: int,
    patent_life_years: int,
    cogs_margin: float = 0.70,  # 70% gross margin typical for pharma
    discount_rate: float = 0.10
) -> float:
    """
    Simple NPV estimation for a drug indication.

    This is a simplified model. Real BD teams use complex DCF models.

    Args:
        peak_sales: Estimated peak annual sales (USD)
        years_to_peak: Years until reaching peak sales
        patent_life_years: Years of patent protection remaining
        cogs_margin: Gross margin (1 - COGS/Revenue)
        discount_rate: Discount rate for NPV

    Returns:
        Estimated NPV (USD)
    """
    total_npv = 0.0

    # Ramp up phase (linear growth to peak)
    for year in range(1, years_to_peak + 1):
        revenue = peak_sales * (year / years_to_peak)
        gross_profit = revenue * cogs_margin
        pv = gross_profit / ((1 + discount_rate) ** year)
        total_npv += pv

    # Plateau phase (maintain peak sales)
    plateau_years = patent_life_years - years_to_peak
    for year in range(years_to_peak + 1, patent_life_years + 1):
        gross_profit = peak_sales * cogs_margin
        pv = gross_profit / ((1 + discount_rate) ** year)
        total_npv += pv

    return total_npv
