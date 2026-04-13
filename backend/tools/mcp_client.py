"""MCP client manager for connecting to external MCP servers."""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClientManager:
    """Manages connections to multiple MCP servers."""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.server_configs = {
            # Example MCP server configurations
            # Uncomment and configure as needed:
            
            # "brave_search": StdioServerParameters(
            #     command="npx",
            #     args=["-y", "@modelcontextprotocol/server-brave-search"],
            #     env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", "")}
            # ),
            # "filesystem": StdioServerParameters(
            #     command="npx",
            #     args=["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"]
            # ),
        }
    
    @asynccontextmanager
    async def connect(self, server_name: str):
        """Connect to an MCP server and yield the session."""
        if server_name not in self.server_configs:
            raise ValueError(f"Unknown MCP server: {server_name}")
        
        params = self.server_configs[server_name]
        
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                logger.info(f"Connected to MCP server: {server_name}")
                
                # List available tools
                tools = await session.list_tools()
                logger.info(f"Available tools from {server_name}: {[t.name for t in tools.tools]}")
                
                yield session
    
    async def call_tool(
        self, 
        server_name: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Any:
        """Call a tool on a specific MCP server."""
        async with self.connect(server_name) as session:
            result = await session.call_tool(tool_name, arguments)
            return result


# Global MCP client manager instance
mcp_manager = MCPClientManager()


async def search_web(query: str) -> str:
    """
    Search the web using Brave Search MCP server.
    
    Args:
        query: Search query string
        
    Returns:
        Search results as formatted string
    """
    try:
        result = await mcp_manager.call_tool(
            server_name="brave_search",
            tool_name="brave_web_search",
            arguments={"query": query}
        )
        return result.content[0].text if result.content else "No results"
    except Exception as e:
        logger.error(f"Error searching web: {e}")
        return f"Search error: {str(e)}"


async def read_file(path: str) -> str:
    """
    Read a file using Filesystem MCP server.
    
    Args:
        path: File path to read
        
    Returns:
        File contents
    """
    try:
        result = await mcp_manager.call_tool(
            server_name="filesystem",
            tool_name="read_file",
            arguments={"path": path}
        )
        return result.content[0].text if result.content else "No content"
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return f"Read error: {str(e)}"
