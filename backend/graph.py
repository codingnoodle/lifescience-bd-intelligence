"""LangGraph state graph for BD intelligence multi-agent system.

Sequential topology:
    research_planner → science_agent → market_agent → synthesizer

Science writes ptrs_adjusted, market reads it — so they must run in sequence, not parallel.
"""
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from backend.state import BDState, IndicationAnalysis
from backend.agents.research_planner import run_research_planner
from backend.agents.science_agent import run_science_agent
from backend.agents.market_agent import run_market_agent
from backend.agents.synthesizer import run_synthesizer
from backend.utils.ptrs_lookup import normalize_phase, normalize_ta

logger = logging.getLogger(__name__)


def research_planner_node(state: BDState) -> Dict[str, Any]:
    """Parse user message, extract asset + indications as IndicationAnalysis dicts."""
    logger.info("research_planner_node: Parsing user message")

    message = state.get("message", "")
    filters = state.get("filters", {})
    parsed = run_research_planner(message, filters)

    asset_name = parsed.get("asset_name", "Unknown Asset")
    clarification = parsed.get("clarification_needed")

    indications: list[IndicationAnalysis] = []
    for ind in parsed.get("indications", []):
        phase = normalize_phase(ind.get("phase", "phase2"))
        ta = normalize_ta(ind.get("therapeutic_area", "oncology"))
        indications.append({
            "name": ind.get("name", "Unknown indication"),
            "phase": phase,
            "therapeutic_area": ta,
            "launch_year": ind.get("launch_year"),
        })

    logger.info(f"Parsed: {asset_name}, {len(indications)} indication(s)")
    return {
        "drug_asset_name": asset_name,
        "indications": indications,
        "clarification_needed": clarification,
        "research_plan": f"Analyzing {asset_name} across {len(indications)} indication(s).",
    }


def science_agent_node(state: BDState) -> Dict[str, Any]:
    """Enrich indications with positioning profile, de-risking signals, PTRS, science score."""
    logger.info("science_agent_node: Building positioning profiles")

    asset_name = state.get("drug_asset_name", "")
    indications = state.get("indications", [])
    if not indications:
        return {"indications": []}

    enriched = run_science_agent(asset_name, indications)
    logger.info(f"science_agent_node: enriched {len(enriched)} indications")
    return {"indications": enriched}


def market_agent_node(state: BDState) -> Dict[str, Any]:
    """Enrich indications with comparator, differentiation, peak sales, market score."""
    logger.info("market_agent_node: Comparator discovery and market sizing")

    asset_name = state.get("drug_asset_name", "")
    indications = state.get("indications", [])
    if not indications:
        return {"indications": []}

    enriched = run_market_agent(asset_name, indications)
    logger.info(f"market_agent_node: enriched {len(enriched)} indications")
    return {"indications": enriched}


def synthesizer_node(state: BDState) -> Dict[str, Any]:
    """Buyer mapping, bidding tension, three-scenario valuation, composite score."""
    logger.info("synthesizer_node: Buyer analysis and deal valuation")

    asset_name = state.get("drug_asset_name", "")
    indications = state.get("indications", [])

    result = run_synthesizer(asset_name, indications)
    return result


def create_bd_graph() -> StateGraph:
    """
    BD intelligence workflow — sequential pipeline:

        research_planner → science_agent → market_agent → synthesizer

    Sequential because market_agent reads ptrs_adjusted written by science_agent.
    """
    workflow = StateGraph(BDState)

    workflow.add_node("research_planner", research_planner_node)
    workflow.add_node("science_agent", science_agent_node)
    workflow.add_node("market_agent", market_agent_node)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.set_entry_point("research_planner")
    workflow.add_edge("research_planner", "science_agent")
    workflow.add_edge("science_agent", "market_agent")
    workflow.add_edge("market_agent", "synthesizer")
    workflow.add_edge("synthesizer", END)

    return workflow.compile()


bd_graph = create_bd_graph()
