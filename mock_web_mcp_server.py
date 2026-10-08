import asyncio
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
import json

# Initialize the MCP server
server = Server("web-search-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available web tools."""
    return [
        types.Tool(
            name="search_web",
            description="Search the web for information about a company, person, or technical topic.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """Handle tool execution requests."""
    if arguments is None:
        arguments = {}
        
    try:
        if name == "search_web":
            query = arguments.get("query", "")
            # Return a mock search result
            response = {
                "success": True, 
                "query": query,
                "results": f"Mock web search result for '{query}': High relevance. This technology or person is highly regarded in the industry."
            }
            return [types.TextContent(type="text", text=json.dumps(response))]
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: Server exception: {str(e)}")]

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="web-search-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
