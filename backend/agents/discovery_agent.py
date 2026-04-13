"""Discovery agent — scans for candidate assets matching a set of criteria."""
import json
import logging
from langchain_core.messages import HumanMessage
from backend.config import sonnet

logger = logging.getLogger(__name__)

DISCOVERY_PROMPT = """You are a pharma BD intelligence analyst with deep knowledge of clinical-stage drug pipelines.

The user wants to discover assets matching these scan criteria:
- Phase: {phase}
- Therapeutic area: {therapeutic_area}
- Target launch year: {launch_year}
- Keywords / focus: {keywords}

Return ONLY valid JSON (no markdown, no explanation) — a list of 3–5 real, publicly known drug candidates ranked by match confidence and commercial interest. Use your training knowledge of clinical pipelines, ClinicalTrials.gov data, and recent pharma news.

Each candidate must follow this schema:
{{
  "name": "asset name (INN or code)",
  "sponsor": "company name",
  "status": "active" | "discontinued" | "partnered",
  "phase": "e.g. Phase 2",
  "details": "1–2 sentence description of mechanism, target, and key trial data",
  "target": "molecular target or MOA",
  "trialId": "NCT number if known, else null",
  "sites": "geographic trial sites or null",
  "lastUpdate": "approx date of most recent public update or null",
  "historicalDeal": "deal value if partnered or acquired, else null"
}}

Return a JSON array: [{{}}, {{}}, ...]

Rules:
- Only include REAL assets you have reliable knowledge of. Do not hallucinate trial IDs.
- Rank by: (1) how well they match the criteria, (2) commercial potential, (3) recency.
- If a drug was recently partnered (e.g. big-pharma deal), set status to "partnered" and populate historicalDeal.
- If a program was discontinued, set status to "discontinued" and note why in details.
- trialId: only populate if you are highly confident it is correct. Otherwise null.
"""


def run_discovery_agent(scan_criteria: dict) -> list[dict]:
    """Return a ranked list of candidate assets for the given scan criteria."""
    phase = scan_criteria.get("phase") or "any phase"
    ta = scan_criteria.get("therapeutic_area") or "any"
    launch_year = scan_criteria.get("launch_year") or "any"
    keywords = scan_criteria.get("keywords") or f"{phase} {ta} assets"

    prompt = DISCOVERY_PROMPT.format(
        phase=phase,
        therapeutic_area=ta,
        launch_year=launch_year,
        keywords=keywords,
    )

    try:
        response = sonnet.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        candidates = json.loads(raw)
        if not isinstance(candidates, list):
            candidates = candidates.get("candidates", [])

        logger.info(f"discovery_agent: found {len(candidates)} candidates")
        return candidates

    except Exception as e:
        logger.error(f"Discovery agent error: {e}", exc_info=True)
        return []
