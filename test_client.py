import asyncio
import sys
import json
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["filesystem_mcp_server.py"]
    )
    
    print("Connecting to MCP Server...")
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                print("Successfully initialized!")
                
                print("\n--- TEST WATCH DIRECTORY ---")
                # Initial check
                res1 = await session.call_tool("watch_directory", {"directory": "."})
                print(f"Initial watch: {res1.content[0].text}")
                
                # Write a new file
                await session.call_tool("write_file", {"filepath": "resume1.txt", "content": "Jane Doe Resume"})
                
                # Second check
                res2 = await session.call_tool("watch_directory", {"directory": "."})
                print(f"Second watch (should see resume1.txt): {res2.content[0].text}")
                
                print("\n--- TEST BATCH PROCESS ---")
                batch_ops = [
                    {"tool": "write_file", "arguments": {"filepath": "resume2.txt", "content": "John Doe Resume"}},
                    {"tool": "read_file", "arguments": {"filepath": "resume2.txt"}}
                ]
                batch_res = await session.call_tool("batch_process", {"operations": batch_ops})
                print(f"Batch result: {batch_res.content[0].text}")

                print("\n--- TEST ERROR HANDLING ---")
                # Intentionally cause failure
                err_res = await session.call_tool("read_file", {"filepath": "does_not_exist.txt"})
                print(f"Error handling result: {err_res.content[0].text}")

    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
