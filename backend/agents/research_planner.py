"""Research planner agent — parses free text, extracts asset + indications, looks up PTRS."""
import json
import logging
import re
from langchain_core.messages import HumanMessage
from backend.config import haiku
from backend.tools.clinicaltrials import search_trials, format_trials_for_prompt

logger = logging.getLogger(__name__)

PARSE_PROMPT = """You are a research planner for a pharma BD intelligence system with deep knowledge of drug pipelines.

Parse the user's message and return ONLY valid JSON (no markdown, no explanation).

User message: "{message}"

Sidebar filters the user has set (use as hints when not explicit in message):
- Phases: {phases}
- Launch years: {launch_years}
- Therapeutic areas: {therapeutic_areas}

--- ClinicalTrials.gov data (authoritative — use this to determine indication, phase, and TA) ---
{ct_data}

First, decide the query type:
- "discovery" — user is asking for a LIST of assets (e.g. "top Phase 2 oncology assets", "scan oncology", "what are the best ADCs", "show me assets launching 2028"). No specific drug name is mentioned.
- "specific_asset" — user mentions a specific drug, asset code, or compound name (e.g. "ARV-471", "tovorafenib", "BNT-217").

Return this JSON schema:

{{
  "query_type": "discovery",
  "scan_criteria": {{
    "phase": "phase2",
    "therapeutic_area": "oncology",
    "launch_year": 2028,
    "keywords": "ADC oncology"
  }},
  "asset_name": null,
  "indications": [],
  "clarification_needed": null
}}

OR for a specific asset:

{{
  "query_type": "specific_asset",
  "scan_criteria": null,
  "asset_name": "drug or asset name",
  "indications": [
    {{
      "name": "indication/disease name",
      "phase": "one of: preclinical | ind_enabling | phase1 | phase1_2 | phase2 | phase2b | phase3 | nda_submitted",
      "therapeutic_area": "one of: oncology | immunology | neurology | rare_disease | cardio_metabolic | infectious_disease",
      "launch_year": 2028
    }}
  ],
  "clarification_needed": null
}}

Also detect deal_mode from the user's language:
- "licensing", "partnership", "out-license", "ex-US rights", "ex-China", "royalty", "co-develop" → "licensing"
- "acquisition", "M&A", "buyout", "acquire", "takeover" → "ma"
- Otherwise → "auto" (let the synthesizer decide based on asset characteristics)

Add to your JSON output: "deal_mode": "auto" (or "ma" or "licensing")

Rules:
- NEVER set clarification_needed. Always make your best inference.
- For discovery queries: populate scan_criteria from message + sidebar filters. launch_year and keywords are optional (null if not mentioned).
- For specific asset queries: populate asset_name + indications as normal.
- IMPORTANT: ClinicalTrials.gov data above is AUTHORITATIVE. If it shows conditions, phase, and status, use those for indication name, phase, and TA — do NOT guess from training knowledge when trial data is available.
- IMPORTANT: If the user explicitly states a phase in their message (e.g. "Phase 1", "what if Phase 2"), use EXACTLY that phase — supports what-if scenario analysis.
- If phase is not stated, use ClinicalTrials.gov phase first, then sidebar filter, then infer.
- If TA is not stated, derive from ClinicalTrials.gov conditions first, then infer from training knowledge.
- launch_year is an integer or null if unknown.
- TA mapping: cancer/tumor/leukemia/ADC/NSCLC → oncology | CNS/brain/psychiatric → neurology | rare/orphan → rare_disease | MASH/NASH/heart/metabolic/GLP-1/obesity → cardio_metabolic | autoimmune/inflammatory/IBD → immunology"""


def _extract_asset_name(message: str) -> str | None:
    """Try to extract a drug/asset name from the user message for ClinicalTrials.gov lookup."""
    # Look for common asset code patterns: letters+digits, hyphenated codes
    patterns = [
        r'\b[A-Z]{2,5}-?\d{2,5}\b',       # e.g., TERN-701, BNT327, SYH2082
        r'\b[A-Z]{2,5}\d{2,5}[a-z]?\b',    # e.g., ARV471
    ]
    for pat in patterns:
        match = re.search(pat, message, re.IGNORECASE)
        if match:
            return match.group(0)
    # Fallback: use first 1-2 words as potential drug name
    words = message.strip().split()
    if words:
        return words[0]
    return None


def run_research_planner(message: str, filters: dict) -> dict:
    """
    Call Haiku to parse user message into structured asset + indications.
    Searches ClinicalTrials.gov first to ground the planner with real trial data.
    Returns parsed dict with keys: asset_name, indications, clarification_needed.
    """
    # Pre-fetch ClinicalTrials.gov data to ground the planner
    candidate_name = _extract_asset_name(message)
    if candidate_name:
        trials = search_trials(candidate_name)
        ct_data = format_trials_for_prompt(trials)
        logger.info(f"Research planner: found {len(trials)} trials for '{candidate_name}'")
    else:
        ct_data = "No asset name detected for trial lookup."

    phases = ", ".join(filters.get("phases", [])) or "not specified"
    launch_years = ", ".join(str(y) for y in filters.get("launchYears", [])) or "not specified"
    therapeutic_areas = ", ".join(filters.get("therapeuticAreas", [])) or "not specified"

    prompt = PARSE_PROMPT.format(
        message=message,
        phases=phases,
        launch_years=launch_years,
        therapeutic_areas=therapeutic_areas,
        ct_data=ct_data,
    )

    response = haiku.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse research planner JSON: {e}\nRaw: {raw}")
        # Fallback: treat entire message as asset name, no indications parsed
        return {
            "asset_name": message[:100],
            "indications": [],
            "clarification_needed": "Could you provide the asset name, indication, phase, and expected launch year?"
        }
