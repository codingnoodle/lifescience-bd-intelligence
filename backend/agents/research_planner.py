"""Research planner agent — parses free text, extracts asset + indications, looks up PTRS."""
import json
import logging
from langchain_core.messages import HumanMessage
from backend.config import haiku

logger = logging.getLogger(__name__)

PARSE_PROMPT = """You are a research planner for a pharma BD intelligence system with deep knowledge of drug pipelines.

Parse the user's message and return ONLY valid JSON (no markdown, no explanation).

User message: "{message}"

Sidebar filters the user has set (use as hints when not explicit in message):
- Phases: {phases}
- Launch years: {launch_years}
- Therapeutic areas: {therapeutic_areas}

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

Rules:
- NEVER set clarification_needed. Always make your best inference.
- For discovery queries: populate scan_criteria from message + sidebar filters. launch_year and keywords are optional (null if not mentioned).
- For specific asset queries: populate asset_name + indications as normal.
- IMPORTANT: If the user explicitly states a phase in their message (e.g. "Phase 1", "what if Phase 2"), use EXACTLY that phase — supports what-if scenario analysis.
- If phase is not stated, use the sidebar phase filter if set, otherwise infer from knowledge of the drug.
- If TA is not stated, infer from training knowledge (e.g. BNT-217 = ADC → oncology, GLP-1 → cardio_metabolic).
- launch_year is an integer or null if unknown.
- TA mapping: cancer/tumor/leukemia/ADC/NSCLC → oncology | CNS/brain/psychiatric → neurology | rare/orphan → rare_disease | MASH/NASH/heart/metabolic/GLP-1 → cardio_metabolic | autoimmune/inflammatory/IBD → immunology"""


def run_research_planner(message: str, filters: dict) -> dict:
    """
    Call Haiku to parse user message into structured asset + indications.
    Returns parsed dict with keys: asset_name, indications, clarification_needed.
    """
    phases = ", ".join(filters.get("phases", [])) or "not specified"
    launch_years = ", ".join(str(y) for y in filters.get("launchYears", [])) or "not specified"
    therapeutic_areas = ", ".join(filters.get("therapeuticAreas", [])) or "not specified"

    prompt = PARSE_PROMPT.format(
        message=message,
        phases=phases,
        launch_years=launch_years,
        therapeutic_areas=therapeutic_areas,
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
