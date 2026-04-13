"""
Market agent — comparator discovery, differentiation verdict, displacement math, peak sales.
Owns: competitive and commercial environment analysis.
Reads ptrs_adjusted from state (set by science agent). Does NOT re-compute PTRS.
Does NOT reason about buyers (synthesis agent).
"""
import json
import logging
import os
from datetime import date
from langchain_core.messages import HumanMessage
from backend.config import sonnet

logger = logging.getLogger(__name__)
CURRENT_YEAR = date.today().year


def _tavily_search(query: str, domains: list[str] | None = None) -> str:
    try:
        from tavily import TavilyClient
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "Tavily not configured."
        client = TavilyClient(api_key=api_key)
        default_domains = [
            "evaluate.com", "fiercepharma.com", "biopharmadive.com",
            "pharmacytimes.com", "globenewswire.com", "businesswire.com",
            "sec.gov", "pubmed.ncbi.nlm.nih.gov", "nature.com",
            "asco.org", "esmo.org",
        ]
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=8,
            include_domains=domains or default_domains,
        )
        results = response.get("results", [])
        lines = [f"- {r.get('title', '')}: {r.get('content', '')[:400]}" for r in results]
        return "\n".join(lines) if lines else "No results."
    except Exception as e:
        logger.error(f"Tavily market search error: {e}")
        return f"Search unavailable: {e}"


MARKET_PROMPT = """You are a senior pharma commercial analyst doing BD due diligence.
Your job: discover comparators, assess differentiation, and size the market opportunity.
You have the asset's positioning profile from the science agent — use it for metric comparison.
Do NOT reason about potential buyers — that is the synthesizer's job.

Asset: {asset_name}

Indications (with science agent output):
{indications_list}

--- SOC / comparator search results ---
{soc_data}

--- Market sizing and revenue forecasts ---
{market_data}

--- Competitive pipeline search ---
{pipeline_data}

---

For each indication, perform the following steps in order:

STEP 1 — COMPARATOR DISCOVERY
Find the current standard of care (SOC) for this indication and line of therapy.
Pull peak sales forecasts for 1-3 key incumbent drugs.

STEP 2 — METRIC COMPARISON
Compare each metric in the positioning_profile.efficacy_metrics and safety_metrics against
the incumbent's published label data or pivotal trial results.
Build a metric_comparison table.

STEP 3 — DIFFERENTIATION VERDICT
Apply this strict rubric:
- best_in_class: 2+ efficacy metrics meaningfully better, no key metrics worse
  → displacement scenario: capture 40-60% of SOC peak annual sales
- better_in_class: 1 metric meaningfully better, none worse
  → displacement: 20-40% capture of SOC peak annual sales
- me_too: minor improvements or parity → size on own patient population only
- worse_in_class: clearly inferior on key metric → salvage/niche, 5-10% of SOC
- new_class_creation: SOC addresses SYMPTOMS rather than underlying pathology,
  OR analyst/KOL language includes "first-in-class", "disease-modifying", "new standard of care",
  OR the asset targets a pathway where no approved drug exists.
  → category expansion: TA category sales × expansion_multiplier (conservative 1.5x, base 2.0x) × 35% capture
  Surface as "Category creation scenario" (not displacement math).

STEP 4 — PEAK SALES SIZING
Compute two UNDISCOUNTED peak sales estimates (do NOT apply PTRS or time discounting here):
a. peak_sales_standalone_bn: asset's own patient population × treatment rate × annual price × achievable share
b. peak_sales_with_displacement_bn:
   - For best_in_class / better_in_class: include SOC displacement capture + standalone
   - For new_class_creation: use category expansion formula (see above)
   - For me_too / worse_in_class: same as standalone

For comparator_confidence:
- high: single dominant SOC drug, clear clinical benchmark data available
- medium: 2-3 competing SOC options or data is from conference abstracts
- low: fragmented SOC or metric data is sparse/indirect

Return ONLY valid JSON (no markdown fences):

{{
  "indications": [
    {{
      "name": "exact indication name",
      "comparator": {{
        "name": "drug name (e.g. Scemblix/asciminib)",
        "sponsor": "company",
        "peak_sales_bn": 3.5,
        "source": "EvaluatePharma 2025 forecast"
      }},
      "metric_comparison": [
        {{
          "metric": "MMR rate at 12 months",
          "asset_value": "74%",
          "comparator_value": "25%",
          "direction": "better"
        }},
        {{
          "metric": "Grade 3+ AE rate",
          "asset_value": "18%",
          "comparator_value": "22%",
          "direction": "better"
        }}
      ],
      "differentiation_verdict": "best_in_class",
      "peak_sales_standalone_bn": 1.2,
      "peak_sales_with_displacement_bn": 3.8,
      "market_score": 8.0,
      "market_rationale": "2-3 sentences: (1) patient population + pricing rationale, (2) competitive landscape and differentiation basis, (3) which comparator/data source anchored the peak sales estimate.",
      "comparator_confidence": "high"
    }}
  ]
}}

market_score guide (0-10):
- 9-10: Blockbuster potential, large unmet need, limited competition, strong pricing power
- 7-8: Strong market ($1-3B+ peak), moderate competition, differentiated positioning
- 5-6: Moderate market ($0.5-1B peak), competitive space, viable niche
- 3-4: Small market (<$500M peak) or highly competitive with pricing pressure
- 1-2: Niche/orphan or market already well-served"""


def run_market_agent(asset_name: str, indications: list[dict]) -> list[dict]:
    """
    For each indication dict (with science agent output including ptrs_adjusted and positioning_profile):
    1. Search for SOC, market size, competitive pipeline
    2. Build comparator, metric_comparison, differentiation_verdict, dual peak sales via LLM
    3. Return enriched indication dicts

    Reads ptrs_adjusted from each indication dict — does not recompute PTRS.
    """
    logger.info(f"Market agent: analyzing {len(indications)} indication(s) for {asset_name}")

    ta_list = list({ind["therapeutic_area"] for ind in indications})
    phase_list = list({ind["phase"] for ind in indications})
    indication_names = [ind["name"] for ind in indications]

    soc_data = _tavily_search(
        f"standard of care {' '.join(indication_names)} {' '.join(ta_list)} approved drugs treatment guidelines"
    )
    market_data = _tavily_search(
        f"{asset_name} {' '.join(indication_names)} market size peak sales revenue commercial forecast"
    )
    pipeline_data = _tavily_search(
        f"{' '.join(indication_names)} {' '.join(phase_list)} pipeline competitors drugs clinical trials"
    )

    # Build indication list including positioning_profile for metric comparison
    ind_lines_parts = []
    for i, ind in enumerate(indications):
        profile = ind.get("positioning_profile", {})
        efficacy = profile.get("efficacy_metrics", [])
        safety = profile.get("safety_metrics", [])
        claims = profile.get("differentiation_claims", [])
        ptrs_adj = ind.get("ptrs_adjusted", ind.get("ptrs_base", 0.25))

        lines = [
            f"{i+1}. name: \"{ind['name']}\" | phase: {ind['phase']} | area: {ind['therapeutic_area']} | launch_year: {ind.get('launch_year', 'unknown')}",
            f"   ptrs_adjusted: {ptrs_adj:.1%} (use this for any risk-adjusted sizing references)",
            f"   target: {profile.get('target', 'unknown')} | moa: {profile.get('moa', 'unknown')}",
            f"   line_of_therapy: {profile.get('line_of_therapy', 'unspecified')}",
        ]
        if efficacy:
            metrics_str = "; ".join(f"{m['metric_name']}={m['value']} ({m.get('source','')})" for m in efficacy)
            lines.append(f"   efficacy_metrics: {metrics_str}")
        if safety:
            safety_str = "; ".join(f"{m['metric_name']}={m['value']}" for m in safety)
            lines.append(f"   safety_metrics: {safety_str}")
        if claims:
            lines.append(f"   differentiation_claims: {'; '.join(claims)}")
        ind_lines_parts.append("\n".join(lines))

    ind_lines = "\n\n".join(ind_lines_parts)

    prompt = MARKET_PROMPT.format(
        asset_name=asset_name,
        indications_list=ind_lines,
        soc_data=soc_data,
        market_data=market_data,
        pipeline_data=pipeline_data,
    )

    logger.info(f"Market agent: calling Sonnet for {asset_name}")
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
        llm_results = parsed.get("indications", [])
    except json.JSONDecodeError as e:
        logger.error(f"Market agent JSON parse error: {e}\nRaw: {raw[:300]}")
        llm_results = []

    results_by_name: dict[str, dict] = {r.get("name", "").lower(): r for r in llm_results}

    enriched = []
    for ind in indications:
        ind_copy = dict(ind)
        name_lower = ind["name"].lower()

        result = results_by_name.get(name_lower)
        if not result:
            for k, v in results_by_name.items():
                if name_lower in k or k in name_lower:
                    result = v
                    break

        if not result:
            logger.warning(f"Market agent: no result for '{ind['name']}', using fallback")
            result = {
                "comparator": {"name": "unknown", "sponsor": "unknown", "peak_sales_bn": 1.0, "source": "estimate"},
                "metric_comparison": [],
                "differentiation_verdict": "me_too",
                "peak_sales_standalone_bn": 1.0,
                "peak_sales_with_displacement_bn": 1.0,
                "market_score": 5.0,
                "market_rationale": "Insufficient market data — fallback estimate.",
                "comparator_confidence": "low",
            }

        ind_copy.update({
            "comparator": result.get("comparator", {}),
            "metric_comparison": result.get("metric_comparison", []),
            "differentiation_verdict": result.get("differentiation_verdict", "me_too"),
            "peak_sales_standalone_bn": result.get("peak_sales_standalone_bn", 1.0),
            "peak_sales_with_displacement_bn": result.get("peak_sales_with_displacement_bn", 1.0),
            "market_score": result.get("market_score", 5.0),
            "market_rationale": result.get("market_rationale", ""),
            "comparator_confidence": result.get("comparator_confidence", "low"),
        })
        enriched.append(ind_copy)

    return enriched
