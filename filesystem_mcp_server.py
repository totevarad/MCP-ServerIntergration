import asyncio
import sys
import os
import json
from pathlib import Path
from typing import Dict, Set
from pydantic import AnyUrl

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Add File_System_Tools to python path to import fs_tools
sys.path.append(os.path.join(os.path.dirname(__file__), "File_System_Tools"))
import fs_tools

# Configure the base directory for sandboxing (Phase 2 requirement)
workspace_dir = Path(__file__).parent / "workspace"
workspace_dir.mkdir(exist_ok=True)
fs_tools.set_base_dir(workspace_dir)

# Initialize the MCP server
server = Server("filesystem-server")

# State for watch_directory
_DIRECTORY_STATE: Dict[str, Set[str]] = {}

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available file system tools."""
    return [
        types.Tool(
            name="read_file",
            description="Read a document (.txt, .pdf, .docx) and return its extracted text content and metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Relative or absolute path to the target file."}
                },
                "required": ["filepath"],
            },
        ),
        types.Tool(
            name="list_files",
            description="List files in the specified directory, optionally filtered by extension.",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Path to the target directory."},
                    "extension": {"type": "string", "description": "Optional file extension to filter by (e.g. '.pdf')."}
                },
                "required": ["directory"],
            },
        ),
        types.Tool(
            name="write_file",
            description="Write text content to a file, creating any missing parent directories.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path where the file should be written."},
                    "content": {"type": "string", "description": "Text content to write into the file."}
                },
                "required": ["filepath", "content"],
            },
        ),
        types.Tool(
            name="search_in_file",
            description="Search for occurrences of a keyword within a file and return context snippets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the target file."},
                    "keyword": {"type": "string", "description": "The keyword or phrase to search for."}
                },
                "required": ["filepath", "keyword"],
            },
        ),
        types.Tool(
            name="watch_directory",
            description="Monitor a directory for new files since the last time this tool was called.",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Path to the directory to watch."}
                },
                "required": ["directory"],
            },
        ),
        types.Tool(
            name="batch_process",
            description="Execute multiple file operations in a single request efficiently.",
            inputSchema={
                "type": "object",
                "properties": {
                    "operations": {
                        "type": "array",
                        "description": "List of operations. Each operation must have 'tool' (name of tool) and 'arguments' (dict).",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tool": {"type": "string"},
                                "arguments": {"type": "object"}
                            },
                            "required": ["tool", "arguments"]
                        }
                    }
                },
                "required": ["operations"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    if arguments is None:
        arguments = {}
        
    try:
        if name == "read_file":
            filepath = arguments.get("filepath", "")
            result = fs_tools.read_file(filepath)
            if not result.get("success"):
                # Return proper error info within the text content
                return [types.TextContent(type="text", text=f"Error: {result.get('error')}")]
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        elif name == "list_files":
            directory = arguments.get("directory", ".")
            extension = arguments.get("extension")
            result = fs_tools.list_files(directory, extension)
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        elif name == "write_file":
            filepath = arguments.get("filepath", "")
            content = arguments.get("content", "")
            result = fs_tools.write_file(filepath, content)
            if not result.get("success"):
                return [types.TextContent(type="text", text=f"Error: {result.get('error')}")]
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        elif name == "search_in_file":
            filepath = arguments.get("filepath", "")
            keyword = arguments.get("keyword", "")
            result = fs_tools.search_in_file(filepath, keyword)
            if not result.get("success"):
                return [types.TextContent(type="text", text=f"Error: {result.get('error')}")]
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        elif name == "watch_directory":
            directory = arguments.get("directory", ".")
            result = fs_tools.list_files(directory)
            current_files = {f["name"] for f in result}
            
            previous_files = _DIRECTORY_STATE.get(directory, set())
            new_files = current_files - previous_files
            
            # Update state
            _DIRECTORY_STATE[directory] = current_files
            return [types.TextContent(type="text", text=json.dumps({"new_files": list(new_files), "total_files": len(current_files)}))]
            
        elif name == "batch_process":
            operations = arguments.get("operations", [])
            results = []
            for op in operations:
                op_tool = op.get("tool")
                op_args = op.get("arguments", {})
                try:
                    if op_tool == "read_file":
                        results.append(fs_tools.read_file(op_args.get("filepath", "")))
                    elif op_tool == "write_file":
                        results.append(fs_tools.write_file(op_args.get("filepath", ""), op_args.get("content", "")))
                    elif op_tool == "list_files":
                        results.append(fs_tools.list_files(op_args.get("directory", "."), op_args.get("extension")))
                    elif op_tool == "search_in_file":
                        results.append(fs_tools.search_in_file(op_args.get("filepath", ""), op_args.get("keyword", "")))
                    else:
                        results.append({"success": False, "error": f"Unsupported batch tool: {op_tool}"})
                except Exception as e:
                    results.append({"success": False, "error": str(e)})
            return [types.TextContent(type="text", text=json.dumps({"batch_results": results}))]
            
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        # Catch unexpected errors to maintain JSON-RPC compliance without crashing the server
        return [types.TextContent(type="text", text=f"Error: Server exception: {str(e)}")]

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available resources in the base directory."""
    resources = []
    files = fs_tools.list_files(".")
    for f in files:
        uri = f"file:///{f['name']}"
        resources.append(
            types.Resource(
                uri=AnyUrl(uri),
                name=f["name"],
                mimeType="text/plain" if f["extension"] == ".txt" else "application/octet-stream"
            )
        )
    return resources

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str | bytes:
    """Read a specific resource by URI."""
    uri_str = str(uri)
    if uri_str.startswith("file:///"):
        filename = uri_str[len("file:///"):]
        result = fs_tools.read_file(filename)
        if result.get("success"):
            content = result.get("content")
            return content if content is not None else ""
        raise ValueError(result.get("error"))
    raise ValueError(f"Unsupported URI scheme: {uri_str}")

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="filesystem-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
