"""ClinicalTrials.gov REST API v2 client."""
import httpx
import logging

logger = logging.getLogger(__name__)

CT_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"


def search_trials(asset_name: str, max_results: int = 8) -> list[dict]:
    """
    Search ClinicalTrials.gov for studies matching an asset name.
    Returns a list of simplified study dicts.
    """
    params = {
        "query.term": asset_name,
        "pageSize": max_results,
        "format": "json",
    }
    headers = {"User-Agent": "Mozilla/5.0 (compatible; bd-intelligence research tool)"}
    try:
        with httpx.Client(timeout=15, headers=headers) as client:
            resp = client.get(CT_BASE_URL, params=params)
            resp.raise_for_status()
            studies = resp.json().get("studies", [])
            return [_parse_study(s) for s in studies]
    except Exception as e:
        logger.error(f"ClinicalTrials.gov search failed for '{asset_name}': {e}")
        return []


def _parse_study(study: dict) -> dict:
    proto = study.get("protocolSection", {})
    id_mod = proto.get("identificationModule", {})
    status_mod = proto.get("statusModule", {})
    desc_mod = proto.get("descriptionModule", {})
    cond_mod = proto.get("conditionsModule", {})
    design_mod = proto.get("designModule", {})
    arms_mod = proto.get("armsInterventionsModule", {})
    outcome_mod = proto.get("outcomesModule", {})

    phases = design_mod.get("phases", [])
    conditions = cond_mod.get("conditions", [])
    interventions = [
        i.get("name", "") for i in arms_mod.get("interventions", [])
    ]
    primary_outcomes = [
        o.get("measure", "") for o in outcome_mod.get("primaryOutcomes", [])
    ]

    return {
        "nct_id": id_mod.get("nctId", ""),
        "title": id_mod.get("briefTitle", ""),
        "status": status_mod.get("overallStatus", ""),
        "phases": phases,
        "conditions": conditions,
        "interventions": interventions,
        "primary_outcomes": primary_outcomes[:3],
        "summary": (desc_mod.get("briefSummary", "") or "")[:600],
    }


def format_trials_for_prompt(trials: list[dict]) -> str:
    """Format trial list as readable text for inclusion in LLM prompt."""
    if not trials:
        return "No ClinicalTrials.gov results found."
    lines = []
    for t in trials:
        phases_str = ", ".join(t["phases"]) if t["phases"] else "N/A"
        conditions_str = ", ".join(t["conditions"][:3]) if t["conditions"] else "N/A"
        outcomes_str = "; ".join(t["primary_outcomes"]) if t["primary_outcomes"] else "N/A"
        lines.append(
            f"- [{t['nct_id']}] {t['title']}\n"
            f"  Status: {t['status']} | Phase: {phases_str}\n"
            f"  Conditions: {conditions_str}\n"
            f"  Primary endpoints: {outcomes_str}\n"
            f"  Summary: {t['summary'][:300]}"
        )
    return "\n\n".join(lines)
