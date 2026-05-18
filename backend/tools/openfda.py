"""OpenFDA API client for drug designations and approval status."""
import httpx
import logging

logger = logging.getLogger(__name__)

OPENFDA_DRUG_URL = "https://api.fda.gov/drug/drugsfda.json"
OPENFDA_ORPHAN_URL = "https://api.fda.gov/other/orphan.json"


def search_fda_designations(drug_name: str) -> dict:
    """
    Search OpenFDA for drug designations (orphan, fast track, breakthrough, accelerated).
    Returns a dict with boolean flags for each designation type.
    """
    result = {
        "orphan_drug": False,
        "fast_track": False,
        "breakthrough_designation": False,
        "accelerated_approval": False,
        "fda_approved": False,
        "applications": [],
    }

    headers = {"User-Agent": "bd-intelligence/1.0 (research tool)"}

    try:
        with httpx.Client(timeout=15, headers=headers) as client:
            # Search drugsfda for approval and designation info
            _search_drugsfda(client, drug_name, result)
            # Search orphan drug database
            _search_orphan(client, drug_name, result)
    except Exception as e:
        logger.error(f"OpenFDA search failed for '{drug_name}': {e}")

    return result


def _search_drugsfda(client: httpx.Client, drug_name: str, result: dict):
    """Search the drugsfda endpoint for approval submissions and designations."""
    try:
        resp = client.get(OPENFDA_DRUG_URL, params={
            "search": f'openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}" OR openfda.substance_name:"{drug_name}"',
            "limit": 5,
        })
        if resp.status_code != 200:
            return

        data = resp.json()
        results = data.get("results", [])

        for drug in results:
            submissions = drug.get("submissions", [])
            for sub in submissions:
                sub_type = sub.get("submission_type", "")
                sub_status = sub.get("submission_status", "")

                if sub_status == "AP":
                    result["fda_approved"] = True

                app_docs = sub.get("application_docs", [])
                for doc in app_docs:
                    doc_type = doc.get("type", "").lower()
                    if "orphan" in doc_type:
                        result["orphan_drug"] = True
                    if "fast track" in doc_type:
                        result["fast_track"] = True
                    if "breakthrough" in doc_type:
                        result["breakthrough_designation"] = True
                    if "accelerated" in doc_type:
                        result["accelerated_approval"] = True

            # Collect application info
            app_number = drug.get("application_number", "")
            sponsor = drug.get("sponsor_name", "")
            if app_number:
                result["applications"].append({
                    "application_number": app_number,
                    "sponsor": sponsor,
                })
    except Exception as e:
        logger.error(f"OpenFDA drugsfda search error: {e}")


def _search_orphan(client: httpx.Client, drug_name: str, result: dict):
    """Search the orphan drug designation database."""
    try:
        resp = client.get(OPENFDA_ORPHAN_URL, params={
            "search": f'generic_name:"{drug_name}" OR trade_name:"{drug_name}"',
            "limit": 5,
        })
        if resp.status_code != 200:
            return

        data = resp.json()
        orphan_results = data.get("results", [])
        if orphan_results:
            result["orphan_drug"] = True
            for orph in orphan_results:
                designation = orph.get("designation_status", "")
                indication = orph.get("orphan_designation_description", "") or orph.get("indication", "")
                if designation or indication:
                    result.setdefault("orphan_indications", []).append({
                        "status": designation,
                        "indication": indication,
                    })
    except Exception as e:
        logger.error(f"OpenFDA orphan search error: {e}")


def format_fda_for_prompt(fda_data: dict) -> str:
    """Format FDA designation data as readable text for LLM prompt."""
    if not fda_data:
        return "No FDA designation data found."

    lines = ["FDA Designation Status:"]

    designations = []
    if fda_data.get("orphan_drug"):
        designations.append("Orphan Drug Designation")
    if fda_data.get("fast_track"):
        designations.append("Fast Track")
    if fda_data.get("breakthrough_designation"):
        designations.append("Breakthrough Therapy")
    if fda_data.get("accelerated_approval"):
        designations.append("Accelerated Approval")
    if fda_data.get("fda_approved"):
        designations.append("FDA Approved")

    if designations:
        lines.append(f"  Designations: {', '.join(designations)}")
    else:
        lines.append("  No FDA designations found (may be too early-stage or not yet filed)")

    orphan_inds = fda_data.get("orphan_indications", [])
    if orphan_inds:
        lines.append("  Orphan designations:")
        for oi in orphan_inds:
            lines.append(f"    - {oi.get('indication', 'unknown')} ({oi.get('status', '')})")

    apps = fda_data.get("applications", [])
    if apps:
        lines.append("  Applications:")
        for app in apps:
            lines.append(f"    - {app['application_number']} (sponsor: {app.get('sponsor', 'unknown')})")

    return "\n".join(lines)
