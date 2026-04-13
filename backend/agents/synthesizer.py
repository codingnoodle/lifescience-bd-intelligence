"""
Synthesis agent — buyer mapping, bidding tension, three-scenario valuation.
Owns: buyer-side reasoning (who will buy, how urgently, bidding dynamics, final deal price).
Reads fully enriched indication dicts from science + market agents.
"""
import json
import logging
import os
from datetime import date
from langchain_core.messages import HumanMessage
from backend.config import sonnet
from backend.utils.buyer_context import format_buyer_context_for_prompt, BUYER_PATENT_CLIFFS, FLUSH_BUYERS

logger = logging.getLogger(__name__)
CURRENT_YEAR = date.today().year


def _tavily_search(query: str) -> str:
    try:
        from tavily import TavilyClient
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "Tavily not configured."
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=8,
            include_domains=[
                "fiercepharma.com", "biopharmadive.com", "evaluate.com",
                "globenewswire.com", "businesswire.com", "sec.gov",
                "seekingalpha.com", "reuters.com", "bloomberg.com",
            ],
        )
        results = response.get("results", [])
        lines = [f"- {r.get('title', '')}: {r.get('content', '')[:400]}" for r in results]
        return "\n".join(lines) if lines else "No results."
    except Exception as e:
        logger.error(f"Tavily synthesizer search error: {e}")
        return f"Search unavailable: {e}"


def _npv_discount(launch_year: int | None) -> float:
    """NPV time-value discount factor. Returns multiplier 0-1."""
    if not launch_year:
        launch_year = CURRENT_YEAR + 5
    years_out = max(0, launch_year - CURRENT_YEAR)
    return round(1.0 / ((1.10) ** years_out), 3)


SYNTHESIZER_PROMPT = """You are a pharma BD executive and deal banker writing a valuation memo.
You receive fully analyzed indication data (science + market) and must determine:
(a) who will buy this asset, (b) how urgently, (c) what they will pay.

Asset: {asset_name}

=== INDICATION PORTFOLIO (enriched by science + market agents) ===
{indications_detail}

=== BUYER URGENCY CONTEXT ===
{buyer_context}

=== BUYER FRANCHISE FIT (Tavily search) ===
{franchise_data}

=== BUYER DEAL VELOCITY (Tavily search) ===
{deal_velocity_data}

=== ANALYST / MARKET SENTIMENT (Tavily search) ===
{sentiment_data}

=== TA M&A VELOCITY (Tavily search) ===
{ta_velocity_data}

---

Perform these steps:

STEP 1 — BUYER MAPPING
Identify the top 3 most likely acquirers by combining:
a. Franchise fit: which pharma companies have active commercial franchises in this TA?
b. Patent cliff urgency: use the urgency multipliers from the buyer context above.
   When a buyer appears in BOTH cliff and flush tables, effective = max(cliff, flush), capped at 1.6x.
c. Deal velocity: if a buyer had 3+ deals >$1B in the past 12 months, add +0.2x to their urgency.
d. Defensive buyers: does any company need to DEFEND their franchise from this asset's disruption?
   A company whose drug IS the SOC comparator identified by the market agent should be considered a defensive buyer.

STEP 2 — BIDDING TENSION
Score 0 to 1 from four signals (each up to 0.25):
- Analyst coverage: 3+ distinct analyst mentions in search → 0.25
- Stock / deal movement: recent price spike or data readout buzz → 0.25
- Capable buyer count: 3+ buyers with urgency ≥1.1 → 0.25
- TA deal velocity: 5+ deals >$1B in the past 12 months in this TA → 0.25

Map score to bidding premium:
- 0.0–0.3 → 0% premium
- 0.3–0.6 → 15% premium
- 0.6–0.8 → 25% premium
- 0.8–1.0 → 35% premium

STEP 3 — THREE-SCENARIO VALUATION
Each scenario outputs TWO values side-by-side:
- "if_success_bn": what the asset is worth IF the drug succeeds (no PTRS)
- "risk_adjusted_bn": expected value with PTRS probability discount
The gap between them shows the risk level — a GP sees at a glance how much value depends on clinical success.

IMPORTANT: peak_sales figures from the market agent are ANNUAL revenues. A pharma asset generates revenue
for 8-12 years post-launch. Use a revenue_multiplier to convert annual peak to total commercial value:
- revenue_multiplier = 4.0 for standard commercial life (NPV of ~10 years of revenue at 10% discount)
- revenue_multiplier = 5.0 for orphan/rare disease (longer exclusivity, less competition)
- revenue_multiplier = 3.0 for highly competitive markets (faster erosion)

NPV discount factors for time to launch (pre-computed):

{npv_table}

a. Standalone NPV (intrinsic value on the asset's own patient population):
   commercial_value = peak_sales_standalone_bn × revenue_multiplier
   if_success    = Σ(commercial_value × npv_discount)
   risk_adjusted = Σ(commercial_value × ptrs_adjusted × npv_discount)

b. Platform / displacement (commercial value including SOC capture):
   commercial_value = peak_sales_with_displacement_bn × revenue_multiplier
   if_success    = Σ(commercial_value × npv_discount)
   risk_adjusted = Σ(commercial_value × ptrs_adjusted × npv_discount)
   If multiple indications or platform potential, add 15-25% optionality premium to both.

c. Strategic deal price (what the winning bidder actually pays):
   Use a deal_multiple on annual peak displacement — this is how BD bankers price deals.
   deal_multiple = base_multiple(phase) + urgency_adj + bidding_adj + differentiation_adj

   Base deal multiple by phase:
     Preclinical: 0.5–1.0x  |  Phase 1: 1.0–1.5x  |  Phase 1/2: 1.5–2.5x
     Phase 2: 2.0–3.5x      |  Phase 3: 3.0–5.0x   |  Marketed: 4.0–8.0x

   Adjustments to base multiple:
     Top buyer urgency ≥ 1.3 → +0.3x  |  ≥ 1.5 → +0.5x
     Bidding tension ≥ 0.6 → +0.3x    |  ≥ 0.8 → +0.5x
     best_in_class or new_class_creation → +0.3x
     Platform / multi-indication → +0.3x
     me_too or worse_in_class → −0.5x

   if_success    = Σ(peak_sales_with_displacement_bn) × deal_multiple
   risk_adjusted = if_success × weighted_average_ptrs_adjusted

   The if_success strategic value is what a motivated buyer pays. Real deal prices track this number.
   The risk_adjusted number shows the expected value of the acquisition.

STEP 4 — CVR STRUCTURE DETECTION
If the asset has significant early-stage platform components (preclinical or Phase 1 assets alongside
the lead program) OR material approval-path milestones not yet achieved, split the strategic scenario:
- predicted_upfront_bn: base value the buyer pays at signing
- predicted_cvr_bn: contingent value rights tied to milestones (typically 20-40% of total deal value)
- The CVR captures PTRS-discounted value of the uncertain milestones.
If no CVR is warranted, set predicted_cvr_bn to 0 and predicted_upfront_bn equals the strategic value.

STEP 5 — COMPOSITE SCORE AND RECOMMENDATION
composite_score = 0.60 × mean(science_scores) + 0.40 × mean(market_scores)
Adjust ±1 for portfolio breadth (more indications = higher ceiling).
- GO: composite_score ≥ 6.5
- WATCH: 4.5–6.4
- NO-GO: < 4.5

Return ONLY valid JSON (no markdown fences):

{{
  "composite_score": 7.8,
  "science_score": 8.2,
  "market_score": 7.5,
  "recommendation": "GO",
  "summary": "3-4 sentences for a GP partner. Lead with asset + thesis. Key data. Market + deal range. Risk.",
  "buyers": [
    {{
      "name": "Merck",
      "urgency_multiplier": 1.5,
      "rationale": "Keytruda LOE 2028 + deal velocity (4 deals >$1B in 12 months) + oncology franchise fit",
      "confidence": "high"
    }},
    {{
      "name": "Novartis",
      "urgency_multiplier": 1.2,
      "rationale": "Defending Scemblix franchise; moderate urgency from Entresto LOE",
      "confidence": "high"
    }},
    {{
      "name": "Pfizer",
      "urgency_multiplier": 1.2,
      "rationale": "Multiple LOEs by 2027; hematology franchise interest",
      "confidence": "medium"
    }}
  ],
  "bidding_tension": {{
    "score": 0.75,
    "premium": 0.25,
    "signals": [
      {{"signal": "analyst_coverage", "present": true, "contribution": 0.25}},
      {{"signal": "stock_movement", "present": true, "contribution": 0.25}},
      {{"signal": "capable_buyers", "present": true, "contribution": 0.25}},
      {{"signal": "ta_deal_velocity", "present": false, "contribution": 0.0}}
    ],
    "confidence": "high"
  }},
  "scenario_standalone": {{
    "if_success_bn": 2.0,
    "risk_adjusted_bn": 0.6,
    "derivation_string": "Standalone: $0.8B peak × 4.0 rev × 0.62 NPV = $2.0B if success; × 30% PTRS = $0.6B risk-adj"
  }},
  "scenario_displacement": {{
    "if_success_bn": 8.7,
    "risk_adjusted_bn": 2.6,
    "derivation_string": "Displacement: $3.5B peak × 4.0 rev × 0.62 NPV = $8.7B if success; × 30% PTRS = $2.6B risk-adj"
  }},
  "scenario_strategic": {{
    "if_success_bn": 7.0,
    "risk_adjusted_bn": 2.1,
    "deal_multiple": 2.0,
    "predicted_upfront_bn": 5.5,
    "predicted_cvr_bn": 1.5,
    "derivation_string": "Strategic: $3.5B peak × 2.0x deal multiple = $7.0B (base 1.5x Ph1/2 + 0.3x urgency + 0.2x bidding); risk-adj $2.1B"
  }}
}}

recommendation must be exactly one of: GO, WATCH, NO-GO.
summary must be plain English, no jargon, no bullet points, no markdown."""


def run_synthesizer(asset_name: str, indications: list[dict]) -> dict:
    """
    Produce buyer mapping, bidding tension, three-scenario valuation, and composite score.
    Indications must have all science + market fields populated.
    """
    _empty_scenario = {"if_success_bn": 0, "risk_adjusted_bn": 0, "derivation_string": "No data"}
    if not indications:
        return {
            "composite_score": 0.0, "science_score": 0.0, "market_score": 0.0,
            "recommendation": "NO-GO",
            "summary": "No indications found — unable to complete analysis.",
            "buyers": [], "bidding_tension": {"score": 0, "premium": 0, "signals": [], "confidence": "low"},
            "scenario_standalone": _empty_scenario,
            "scenario_displacement": _empty_scenario,
            "scenario_strategic": {**_empty_scenario, "deal_multiple": 0, "predicted_upfront_bn": 0, "predicted_cvr_bn": 0},
        }

    # Pre-compute NPV discount factors and per-indication dual values
    npv_lines = []
    for ind in indications:
        ly = ind.get("launch_year")
        npv = _npv_discount(ly)
        ptrs = ind.get("ptrs_adjusted", 0.25)
        peak_displace = ind.get("peak_sales_with_displacement_bn", 0)
        peak_standalone = ind.get("peak_sales_standalone_bn", 0)
        # Per-indication dual values (annual peak × NPV, with/without PTRS)
        ind["peak_sales_if_succeed_bn"] = round(peak_displace * npv, 2)
        ind["peak_sales_risk_adjusted_bn"] = round(peak_displace * ptrs * npv, 2)
        npv_lines.append(
            f"  {ind['name']}: launch_year={ly or 'unknown'} | npv_discount={npv} | "
            f"peak_displace=${peak_displace}B | if_succeed=${ind['peak_sales_if_succeed_bn']}B | "
            f"risk_adj=${ind['peak_sales_risk_adjusted_bn']}B"
        )
    npv_table = "\n".join(npv_lines)

    # Build detailed indication summary for prompt
    detail_parts = []
    ta_set = set()
    for i, ind in enumerate(indications):
        ta_set.add(ind.get("therapeutic_area", "oncology"))
        profile = ind.get("positioning_profile", {})
        comp = ind.get("comparator", {})
        verdict = ind.get("differentiation_verdict", "me_too")
        lines = [
            f"Indication {i+1}: \"{ind['name']}\"",
            f"  Phase: {ind['phase']} | TA: {ind['therapeutic_area']} | Launch: {ind.get('launch_year', 'unknown')}",
            f"  Science score: {ind.get('science_score', 'N/A')} | Market score: {ind.get('market_score', 'N/A')}",
            f"  PTRS: base={ind.get('ptrs_base', 'N/A')}, adjusted={ind.get('ptrs_adjusted', 'N/A')}",
            f"  De-risking signals: {', '.join(ind.get('de_risking_signals', []))}",
            f"  Target: {profile.get('target', 'unknown')} | MOA: {profile.get('moa', 'unknown')}",
            f"  Comparator: {comp.get('name', 'unknown')} (peak ${comp.get('peak_sales_bn', '?')}B) — {comp.get('source', '')}",
            f"  Differentiation verdict: {verdict} | Comparator confidence: {ind.get('comparator_confidence', 'low')}",
            f"  Peak sales standalone: ${ind.get('peak_sales_standalone_bn', 0)}B | With displacement: ${ind.get('peak_sales_with_displacement_bn', 0)}B",
        ]
        # Add metric comparison if available
        metrics = ind.get("metric_comparison", [])
        if metrics:
            lines.append("  Metric comparison:")
            for m in metrics:
                lines.append(f"    {m.get('metric', '?')}: asset={m.get('asset_value', '?')} vs comp={m.get('comparator_value', '?')} → {m.get('direction', '?')}")
        detail_parts.append("\n".join(lines))
    indications_detail = "\n\n".join(detail_parts)

    # Tavily searches for buyer mapping and bidding tension
    ta_str = " ".join(ta_set)
    franchise_data = _tavily_search(
        f"pharma companies commercial franchise {ta_str} pipeline deals acquisitions 2025 2026"
    )

    # Search deal velocity for top patent cliff buyers in relevant TAs
    known_buyers = list(BUYER_PATENT_CLIFFS.keys()) + list(FLUSH_BUYERS.keys())
    buyer_names = " ".join(list(set(known_buyers))[:6])
    deal_velocity_data = _tavily_search(
        f"{buyer_names} pharma M&A acquisition deal 2024 2025 2026 billion"
    )

    # Analyst / sentiment for bidding tension
    sentiment_data = _tavily_search(
        f"{asset_name} analyst rating coverage price target pharma acquisition"
    )

    # TA deal velocity
    ta_velocity_data = _tavily_search(
        f"{ta_str} pharma M&A acquisition deal 2025 2026 billion oncology hematology"
    )

    buyer_context = format_buyer_context_for_prompt()

    prompt = SYNTHESIZER_PROMPT.format(
        asset_name=asset_name,
        indications_detail=indications_detail,
        buyer_context=buyer_context,
        franchise_data=franchise_data,
        deal_velocity_data=deal_velocity_data,
        sentiment_data=sentiment_data,
        ta_velocity_data=ta_velocity_data,
        npv_table=npv_table,
    )

    logger.info(f"Synthesizer: calling Sonnet for {asset_name}")
    response = sonnet.invoke([HumanMessage(content=prompt)])
    raw = response.content
    if isinstance(raw, list):
        raw = " ".join(str(r) for r in raw)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        parsed = json.loads(raw)
        return {
            "indications": indications,  # enriched with per-indication dual values
            "composite_score": parsed.get("composite_score"),
            "science_score": parsed.get("science_score"),
            "market_score": parsed.get("market_score"),
            "recommendation": parsed.get("recommendation", "WATCH"),
            "summary": parsed.get("summary", ""),
            "buyers": parsed.get("buyers", []),
            "bidding_tension": parsed.get("bidding_tension", {}),
            "scenario_standalone": parsed.get("scenario_standalone", {}),
            "scenario_displacement": parsed.get("scenario_displacement", {}),
            "scenario_strategic": parsed.get("scenario_strategic", {}),
        }
    except json.JSONDecodeError as e:
        logger.error(f"Synthesizer JSON parse error: {e}\nRaw: {raw[:300]}")
        sci_avg = sum(ind.get("science_score", 5) for ind in indications) / len(indications)
        mkt_avg = sum(ind.get("market_score", 5) for ind in indications) / len(indications)
        composite = round(sci_avg * 0.6 + mkt_avg * 0.4, 1)
        return {
            "composite_score": composite,
            "science_score": round(sci_avg, 1),
            "market_score": round(mkt_avg, 1),
            "recommendation": "GO" if composite >= 6.5 else ("WATCH" if composite >= 4.5 else "NO-GO"),
            "summary": f"Analysis of {asset_name} across {len(indications)} indication(s). Score {composite}/10.",
            "buyers": [],
            "bidding_tension": {"score": 0, "premium": 0, "signals": [], "confidence": "low"},
            "scenario_standalone": {"if_success_bn": 0, "risk_adjusted_bn": 0, "derivation_string": "Parse error — fallback"},
            "scenario_displacement": {"if_success_bn": 0, "risk_adjusted_bn": 0, "derivation_string": "Parse error — fallback"},
            "scenario_strategic": {"if_success_bn": 0, "risk_adjusted_bn": 0, "deal_multiple": 0, "predicted_upfront_bn": 0, "predicted_cvr_bn": 0, "derivation_string": "Parse error — fallback"},
        }
