"""
Science agent — builds positioning profile, identifies de-risking signals,
computes adjusted PTRS, and scores each indication for scientific quality.
Owns: intrinsic asset properties only (MOA, clinical data, regulatory signals).
Does NOT do comparator analysis (market agent) or buyer reasoning (synthesizer).
"""
import json
import logging
import os
from langchain_core.messages import HumanMessage
from backend.config import sonnet
from backend.utils.ptrs_lookup import get_adjusted_ptrs, VALID_DERISKING_SIGNALS

logger = logging.getLogger(__name__)

_SIGNAL_VOCAB = ", ".join(sorted(VALID_DERISKING_SIGNALS))

SCIENCE_PROMPT = """You are a senior biotech scientist conducting pharma BD due diligence.
Your job: extract a structured scientific profile and score each indication.
Do NOT analyze market competition or buyers — that is handled by separate agents.

Asset: {asset_name}

Indications to assess:
{indications_list}

--- ClinicalTrials.gov data ---
{ct_data}

--- PubMed / conference literature (Tavily) ---
{tavily_data}

---

For each indication, output a structured positioning_profile and de-risking signals.

DE-RISKING SIGNAL VOCABULARY — use ONLY these exact strings, no others:
{signal_vocab}

Signal definitions:
- orphan_drug: has orphan drug designation from FDA or EMA
- fast_track: has FDA fast track designation
- breakthrough_designation: has FDA breakthrough therapy designation
- patients_dosed_50plus: 50+ patients dosed in clinical program to date
- patients_dosed_100plus: 100+ patients dosed (use this OR 50plus, not both)
- best_in_class_efficacy: efficacy metrics meaningfully exceed current SOC benchmarks
- fda_registrational_alignment: FDA has agreed on a registration-enabling trial design
- biomarker_defined_population: trial uses biomarker-selected patient population
- platform_multi_indication: MOA/platform potentially applicable across multiple indications

Return ONLY valid JSON (no markdown fences):

{{
  "indications": [
    {{
      "name": "exact indication name from list above",
      "positioning_profile": {{
        "target": "molecular target or pathway",
        "moa": "mechanism of action (1-2 sentences)",
        "indication": "disease",
        "line_of_therapy": "1L / 2L / 3L+ / unspecified",
        "efficacy_metrics": [
          {{"metric_name": "ORR", "value": "74%", "source": "ASH 2025 poster"}},
          {{"metric_name": "duration of response", "value": "12+ months", "source": "ASH 2025"}}
        ],
        "safety_metrics": [
          {{"metric_name": "Grade 3+ AE rate", "value": "18%", "source": "ASH 2025"}}
        ],
        "differentiation_claims": [
          "Overcomes T315I resistance mutation",
          "Allosteric binding site avoids kinase domain mutations"
        ]
      }},
      "de_risking_signals": ["orphan_drug", "patients_dosed_50plus"],
      "science_score": 8.0,
      "science_rationale": "2-3 sentences: MOA quality, strength of clinical evidence, key differentiators and risks."
    }}
  ]
}}

Science score guide (0-10):
- 9-10: Registrational-ready or pivotal-positive; unambiguous efficacy/safety; landmark differentiation
- 7-8: Phase 2/3 with strong signals; differentiated MOA; manageable safety; clear path to registration
- 5-6: Phase 1/2 with promising early data; MOA credible; uncertainties remain
- 3-4: Phase 1 first-in-human; limited efficacy data; MOA validated in preclinical only
- 1-2: Preclinical only; no human data; unvalidated target; class safety concerns
- 0: No credible scientific basis

Base scores on evidence found. If data is sparse for a specific asset, score the archetype (MOA class)
and note this in science_rationale."""


def _tavily_search(query: str, domains: list[str] | None = None) -> str:
    try:
        from tavily import TavilyClient
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "Tavily not configured."
        client = TavilyClient(api_key=api_key)
        default_domains = [
            "pubmed.ncbi.nlm.nih.gov", "fda.gov", "clinicaltrials.gov",
            "nejm.org", "thelancet.com", "nature.com",
            "asco.org", "esmo.org", "ash.confex.com", "biorxiv.org",
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
        logger.error(f"Tavily search error: {e}")
        return f"Search unavailable: {e}"


def run_science_agent(asset_name: str, indications: list[dict]) -> list[dict]:
    """
    For each indication dict (with name, phase, therapeutic_area, launch_year):
    1. Search for clinical/scientific data
    2. Extract positioning_profile and de_risking_signals via LLM
    3. Compute ptrs_base, ptrs_adjusted, ptrs_breakdown via get_adjusted_ptrs()
    4. Return enriched indication dicts

    Returns the input list with science fields added (modifies a copy, returns updated list).
    """
    logger.info(f"Science agent: analyzing {len(indications)} indication(s) for {asset_name}")

    ct_data = _tavily_search(
        f"{asset_name} clinical trial ClinicalTrials.gov results patients dosed",
        domains=["clinicaltrials.gov", "pubmed.ncbi.nlm.nih.gov", "fda.gov",
                 "asco.org", "esmo.org", "ash.confex.com", "biorxiv.org"]
    )
    tavily_data = _tavily_search(
        f"{asset_name} mechanism of action efficacy safety trial results ASH ASCO ESMO conference"
    )

    ind_lines = "\n".join(
        f"{i+1}. name: \"{ind['name']}\" | phase: {ind['phase']} | area: {ind['therapeutic_area']}"
        for i, ind in enumerate(indications)
    )

    prompt = SCIENCE_PROMPT.format(
        asset_name=asset_name,
        indications_list=ind_lines,
        ct_data=ct_data,
        tavily_data=tavily_data,
        signal_vocab=_SIGNAL_VOCAB,
    )

    logger.info(f"Science agent: calling Sonnet for {asset_name}")
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
        logger.error(f"Science agent JSON parse error: {e}\nRaw: {raw[:300]}")
        llm_results = []

    # Build lookup by name
    results_by_name: dict[str, dict] = {}
    for r in llm_results:
        results_by_name[r.get("name", "").lower()] = r

    enriched = []
    for ind in indications:
        ind_copy = dict(ind)
        name_lower = ind["name"].lower()

        # Find matching result (exact then substring)
        result = results_by_name.get(name_lower)
        if not result:
            for k, v in results_by_name.items():
                if name_lower in k or k in name_lower:
                    result = v
                    break

        if not result:
            logger.warning(f"Science agent: no result for '{ind['name']}', using fallback")
            result = {
                "positioning_profile": {"target": "unknown", "moa": "unknown", "indication": ind["name"],
                                        "line_of_therapy": "unspecified", "efficacy_metrics": [],
                                        "safety_metrics": [], "differentiation_claims": []},
                "de_risking_signals": [],
                "science_score": 5.0,
                "science_rationale": "Insufficient data found for this asset.",
            }

        # Compute adjusted PTRS in Python (not by LLM)
        signals = [s for s in result.get("de_risking_signals", []) if s in VALID_DERISKING_SIGNALS]
        ptrs_result = get_adjusted_ptrs(ind["phase"], ind["therapeutic_area"], signals)

        ind_copy.update({
            "positioning_profile": result.get("positioning_profile", {}),
            "de_risking_signals": signals,
            "ptrs_base": ptrs_result["base"],
            "ptrs_adjusted": ptrs_result["adjusted"],
            "ptrs_breakdown": ptrs_result["breakdown"],
            "science_score": result.get("science_score", 5.0),
            "science_rationale": result.get("science_rationale", ""),
        })
        enriched.append(ind_copy)

    return enriched
