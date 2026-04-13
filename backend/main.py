"""FastAPI entry point for BD intelligence API."""
import json
import logging
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.graph import bd_graph
from backend.state import BDState
from backend.agents.research_planner import run_research_planner
from backend.agents.discovery_agent import run_discovery_agent
from backend.agents.market_agent import run_market_agent
from backend.agents.synthesizer import run_synthesizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="BD Intelligence API",
    description="Multi-agent system for pharma BD decision intelligence",
    version="0.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request / Response models ---

class AnalyzeRequest(BaseModel):
    message: str
    filters: Dict[str, Any] = {}


class RecalculateRequest(BaseModel):
    """Accept current state + user overrides; re-run from market agent onward."""
    asset_name: str
    indications: List[Dict[str, Any]]  # IndicationAnalysis dicts with science fields
    overrides: Dict[str, Any] = {}     # e.g. {"indication_name": "CML", "field": "ptrs_adjusted", "value": 0.35}


class IndicationOut(BaseModel):
    name: str
    phase: str
    # Science
    positioningProfile: Optional[Dict[str, Any]] = None
    deRiskingSignals: Optional[List[str]] = None
    ptrsBase: Optional[float] = None
    ptrsAdjusted: Optional[float] = None
    ptrsBreakdown: Optional[List[Dict[str, Any]]] = None
    scienceScore: Optional[float] = None
    scienceRationale: Optional[str] = None
    # Market
    comparator: Optional[Dict[str, Any]] = None
    metricComparison: Optional[List[Dict[str, Any]]] = None
    differentiationVerdict: Optional[str] = None
    peakSalesStandaloneBn: Optional[float] = None
    peakSalesWithDisplacementBn: Optional[float] = None
    marketScore: Optional[float] = None
    marketRationale: Optional[str] = None
    comparatorConfidence: Optional[str] = None
    # Per-indication dual values (computed by synthesizer)
    peakSalesRiskAdjustedBn: Optional[float] = None
    peakSalesIfSucceedBn: Optional[float] = None


class ScenarioOut(BaseModel):
    ifSuccessBn: Optional[float] = None
    riskAdjustedBn: Optional[float] = None
    dealMultiple: Optional[float] = None
    predictedUpfrontBn: Optional[float] = None
    predictedCvrBn: Optional[float] = None
    derivationString: Optional[str] = None


class BuyerOut(BaseModel):
    name: str
    urgencyMultiplier: Optional[float] = None
    rationale: Optional[str] = None
    confidence: Optional[str] = None


class BiddingTensionOut(BaseModel):
    score: Optional[float] = None
    premium: Optional[float] = None
    signals: Optional[List[Dict[str, Any]]] = None
    confidence: Optional[str] = None


class AnalyzeResult(BaseModel):
    assetName: str
    compositeScore: Optional[float] = None
    scienceScore: Optional[float] = None
    marketScore: Optional[float] = None
    recommendation: Optional[str] = None
    indications: List[IndicationOut] = []
    # Three scenarios
    scenarioStandalone: Optional[ScenarioOut] = None
    scenarioDisplacement: Optional[ScenarioOut] = None
    scenarioStrategic: Optional[ScenarioOut] = None
    # Buyers
    buyers: List[BuyerOut] = []
    biddingTension: Optional[BiddingTensionOut] = None
    summary: Optional[str] = None


class AnalyzeResponse(BaseModel):
    message: str
    result: Optional[AnalyzeResult] = None


# --- Helpers ---

def _indication_to_out(ind: dict) -> dict:
    return {
        "name": ind.get("name", ""),
        "phase": ind.get("phase", ""),
        "positioningProfile": ind.get("positioning_profile"),
        "deRiskingSignals": ind.get("de_risking_signals"),
        "ptrsBase": ind.get("ptrs_base"),
        "ptrsAdjusted": ind.get("ptrs_adjusted"),
        "ptrsBreakdown": ind.get("ptrs_breakdown"),
        "scienceScore": ind.get("science_score"),
        "scienceRationale": ind.get("science_rationale"),
        "comparator": ind.get("comparator"),
        "metricComparison": ind.get("metric_comparison"),
        "differentiationVerdict": ind.get("differentiation_verdict"),
        "peakSalesStandaloneBn": ind.get("peak_sales_standalone_bn"),
        "peakSalesWithDisplacementBn": ind.get("peak_sales_with_displacement_bn"),
        "marketScore": ind.get("market_score"),
        "marketRationale": ind.get("market_rationale"),
        "comparatorConfidence": ind.get("comparator_confidence"),
        "peakSalesRiskAdjustedBn": ind.get("peak_sales_risk_adjusted_bn"),
        "peakSalesIfSucceedBn": ind.get("peak_sales_if_succeed_bn"),
    }


def _scenario_to_out(s: dict | None) -> dict | None:
    if not s:
        return None
    return {
        "ifSuccessBn": s.get("if_success_bn"),
        "riskAdjustedBn": s.get("risk_adjusted_bn"),
        "dealMultiple": s.get("deal_multiple"),
        "predictedUpfrontBn": s.get("predicted_upfront_bn"),
        "predictedCvrBn": s.get("predicted_cvr_bn"),
        "derivationString": s.get("derivation_string"),
    }


def _build_result(state: dict) -> dict:
    """Build the AnalyzeResult dict from final graph state."""
    asset_name = state.get("drug_asset_name", "Unknown Asset")
    indications = state.get("indications", [])
    indications_out = [_indication_to_out(ind) for ind in indications]

    composite = state.get("composite_score")
    rec = state.get("recommendation")
    strategic = state.get("scenario_strategic", {})
    success_val = strategic.get("if_success_bn") if strategic else None
    risk_val = strategic.get("risk_adjusted_bn") if strategic else None
    upfront_val = strategic.get("predicted_upfront_bn") if strategic else None
    cvr_val = strategic.get("predicted_cvr_bn") if strategic else None

    # Build chat message
    if composite is not None:
        rec_str = rec or ("GO" if composite >= 6.5 else ("WATCH" if composite >= 4.5 else "NO-GO"))
        chat_msg = f"Analysis complete for **{asset_name}**: {rec_str} (score {composite:.1f}/10)."
        if success_val:
            if cvr_val and cvr_val > 0:
                chat_msg += f" Strategic scenario: ${upfront_val:.1f}B upfront + ${cvr_val:.1f}B CVR = ${success_val:.1f}B if succeeds (${risk_val:.1f}B risk-adjusted)."
            else:
                chat_msg += f" Strategic scenario: ${success_val:.1f}B if succeeds (${risk_val:.1f}B risk-adjusted)."
    else:
        chat_msg = f"Parsed **{asset_name}** with {len(indications)} indication(s)."

    buyers = state.get("buyers", [])
    tension = state.get("bidding_tension", {})

    return {
        "message": chat_msg,
        "result": {
            "assetName": asset_name,
            "compositeScore": composite,
            "scienceScore": state.get("science_score"),
            "marketScore": state.get("market_score"),
            "recommendation": rec,
            "indications": indications_out,
            "scenarioStandalone": _scenario_to_out(state.get("scenario_standalone")),
            "scenarioDisplacement": _scenario_to_out(state.get("scenario_displacement")),
            "scenarioStrategic": _scenario_to_out(state.get("scenario_strategic")),
            "buyers": [
                {"name": b.get("name", ""), "urgencyMultiplier": b.get("urgency_multiplier"),
                 "rationale": b.get("rationale"), "confidence": b.get("confidence")}
                for b in buyers
            ],
            "biddingTension": {
                "score": tension.get("score"),
                "premium": tension.get("premium"),
                "signals": tension.get("signals"),
                "confidence": tension.get("confidence"),
            } if tension else None,
            "summary": state.get("summary"),
        }
    }


# --- Routes ---

@app.get("/")
async def root():
    return {"status": "healthy", "service": "BD Intelligence API", "version": "0.3.0"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    try:
        initial_state: BDState = {
            "message": request.message,
            "filters": request.filters,
            "indications": [],
            "messages": [],
            "errors": [],
        }

        logging.info(f"Analyzing: {request.message[:80]}")
        result = bd_graph.invoke(initial_state)

        clarification = result.get("clarification_needed")
        if clarification:
            return AnalyzeResponse(message=clarification, result=None)

        payload = _build_result(result)
        return AnalyzeResponse(**payload)

    except Exception as e:
        logging.error(f"Error in /analyze: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


STREAM_LABELS = {
    "research_planner": "Parsing asset and indications...",
    "discovery_agent": "Scanning pipeline for matching candidates...",
    "science_agent": "Building positioning profile and de-risking analysis...",
    "market_agent": "Discovering comparators and sizing market opportunity...",
    "synthesizer": "Mapping buyers, bidding tension, and valuation scenarios...",
}


@app.post("/analyze/stream")
async def analyze_stream(request: AnalyzeRequest):
    """Stream agent progress as SSE events, then send the final result."""

    async def generate():
        try:
            # Step 1: classify the query
            yield f"data: {json.dumps({'type': 'progress', 'node': 'research_planner', 'message': 'Classifying query...'})}\n\n"
            parsed = run_research_planner(request.message, request.filters)

            # Step 2a: discovery / scan query
            if parsed.get("query_type") == "discovery":
                scan_criteria = parsed.get("scan_criteria") or {}
                ta = scan_criteria.get("therapeutic_area", "oncology")
                phase = scan_criteria.get("phase", "")
                label = f"Scanning {phase} {ta} pipeline...".strip()
                yield f"data: {json.dumps({'type': 'progress', 'node': 'discovery_agent', 'message': label})}\n\n"

                candidates = run_discovery_agent(scan_criteria)
                n = len(candidates)
                chat_msg = f"Found **{n} candidate{'s' if n != 1 else ''}** matching your criteria. Click 'Run full diligence' on any to start a deep-dive."
                payload = json.dumps({
                    "type": "done",
                    "message": chat_msg,
                    "result": {"discoveryMode": True, "candidates": candidates},
                })
                yield f"data: {payload}\n\n"
                return

            # Step 2b: specific asset — run the full graph
        except Exception as e:
            logging.error(f"Pre-graph error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

        initial_state: BDState = {
            "message": request.message,
            "filters": request.filters,
            "indications": [],
            "messages": [],
            "errors": [],
        }

        final_state = dict(initial_state)

        try:
            async for chunk in bd_graph.astream(initial_state, stream_mode="updates"):
                node_name = list(chunk.keys())[0]
                node_updates = chunk[node_name]
                if isinstance(node_updates, dict):
                    final_state.update(node_updates)

                label = STREAM_LABELS.get(node_name, f"Running {node_name}...")
                event = json.dumps({"type": "progress", "node": node_name, "message": label})
                yield f"data: {event}\n\n"

            clarification = final_state.get("clarification_needed")
            if clarification:
                payload = json.dumps({"type": "done", "message": clarification, "result": None})
                yield f"data: {payload}\n\n"
                return

            result_payload = _build_result(final_state)
            yield f"data: {json.dumps({'type': 'done', **result_payload})}\n\n"

        except Exception as e:
            logging.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/recalculate")
async def recalculate(request: RecalculateRequest):
    """
    Re-run from market agent onward with user overrides applied.
    Use this when the user edits an assumption (PTRS, verdict, comparator, etc.)
    in the AssumptionsPanel — avoids a full re-run from the research planner.
    """
    try:
        indications = request.indications

        # Apply overrides
        for ind in indications:
            if request.overrides.get("indication_name") == ind.get("name"):
                field = request.overrides.get("field")
                value = request.overrides.get("value")
                if field and value is not None:
                    ind[field] = value

        # Re-run market agent (reads science fields including ptrs_adjusted)
        market_enriched = run_market_agent(request.asset_name, indications)

        # Re-run synthesizer
        synth_result = run_synthesizer(request.asset_name, market_enriched)

        # Build response in the same format as /analyze
        state = {
            "drug_asset_name": request.asset_name,
            "indications": market_enriched,
            **synth_result,
        }
        return _build_result(state)

    except Exception as e:
        logging.error(f"Error in /recalculate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
