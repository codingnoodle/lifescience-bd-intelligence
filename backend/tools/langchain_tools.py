"""LangChain tool wrappers for research tools."""
import os
import logging
from typing import Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from tavily import TavilyClient

logger = logging.getLogger(__name__)


class WebSearchInput(BaseModel):
    """Input schema for web search tool."""
    query: str = Field(..., description="The search query to execute")


class WebSearchTool(BaseTool):
    """Tool for searching the web via Tavily API."""

    name: str = "web_search"
    description: str = (
        "Search the web for information about drug assets, clinical trials, "
        "market data, competitive intelligence, or indication expansion opportunities. "
        "Useful for finding recent news, trial results, market reports, and pipeline data. "
        "Returns comprehensive search results with snippets and sources."
    )
    args_schema: Type[BaseModel] = WebSearchInput

    def __init__(self):
        super().__init__()
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            logger.warning("TAVILY_API_KEY not set - web search will fail")
        self.client = TavilyClient(api_key=api_key) if api_key else None

    def _run(self, query: str) -> str:
        """Execute web search using Tavily."""
        if not self.client:
            return "Error: TAVILY_API_KEY not configured"

        try:
            # Tavily search with focus on pharma/biotech content
            response = self.client.search(
                query=query,
                search_depth="advanced",  # More comprehensive search
                max_results=10,
                include_domains=["clinicaltrials.gov", "fda.gov", "ema.europa.eu", "pubmed.ncbi.nlm.nih.gov"],
                # exclude_domains=[]  # Can exclude unreliable sources
            )

            # Format results
            results = []
            for i, result in enumerate(response.get('results', []), 1):
                results.append(
                    f"{i}. {result.get('title', 'No title')}\n"
                    f"   Source: {result.get('url', 'No URL')}\n"
                    f"   {result.get('content', 'No content')}\n"
                )

            if not results:
                return f"No results found for query: {query}"

            return "\n".join(results)

        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return f"Search error: {str(e)}"


# Tool registry - add tools here as they're implemented
def get_tools() -> list[BaseTool]:
    """
    Get all available tools for agents.

    Returns:
        List of LangChain tools (currently: web search via Tavily)
    """
    tools = []

    # Add web search if Tavily API key is configured
    if os.getenv("TAVILY_API_KEY"):
        tools.append(WebSearchTool())
        logger.info("WebSearchTool enabled (Tavily)")
    else:
        logger.warning("WebSearchTool disabled - TAVILY_API_KEY not set")

    return tools
