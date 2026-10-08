import asyncio
import sys
import json
import os
import dotenv
from pydantic import create_model, Field
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

# Load environment variables (e.g., ANTHROPIC_API_KEY)
dotenv.load_dotenv()

def build_langchain_tools(mcp_tools, session):
    """Dynamically build LangChain StructuredTools from MCP tool definitions."""
    langchain_tools = []
    for t in mcp_tools:
        # Closure to capture tool name securely
        def create_coroutine(tool_name):
            async def afunc(**kwargs):
                print(f"\n  [Agent Tool Execution] Calling '{tool_name}' with args {kwargs}")
                res = await session.call_tool(tool_name, kwargs)
                text_content = res.content[0].text if res.content else ""
                return text_content
            return afunc
            
        # Dynamically build Pydantic schema for the tool arguments
        fields = {}
        if "properties" in t.inputSchema:
            for prop_name, prop_info in t.inputSchema["properties"].items():
                fields[prop_name] = (str, Field(default="", description=prop_info.get("description", "")))
        
        DynamicSchema = create_model(f"{t.name}Schema", **fields)
        
        ltool = StructuredTool(
            name=t.name,
            description=t.description,
            args_schema=DynamicSchema,
            coroutine=create_coroutine(t.name)
        )
        langchain_tools.append(ltool)
    return langchain_tools

async def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is missing. Please set it in .env or your environment.")
        sys.exit(1)

    fs_params = StdioServerParameters(command=sys.executable, args=["filesystem_mcp_server.py"])
    web_params = StdioServerParameters(command=sys.executable, args=["mock_web_mcp_server.py"])
    
    print("Connecting to multiple MCP Servers...")
    async with stdio_client(fs_params) as (fs_read, fs_write), \
               stdio_client(web_params) as (web_read, web_write):
        
        async with ClientSession(fs_read, fs_write) as fs_session, \
                   ClientSession(web_read, web_write) as web_session:
            
            # Initialize both sessions concurrently
            await asyncio.gather(fs_session.initialize(), web_session.initialize())
            print("Successfully initialized MCP sessions!")
            
            # Fetch tools from both servers
            fs_tools_res = await fs_session.list_tools()
            web_tools_res = await web_session.list_tools()
            
            print(f"Discovered {len(fs_tools_res.tools)} File System tools and {len(web_tools_res.tools)} Web Search tools.")
            
            # Build and combine LangChain tools
            langchain_tools = build_langchain_tools(fs_tools_res.tools, fs_session)
            langchain_tools.extend(build_langchain_tools(web_tools_res.tools, web_session))
            
            # Initialize LLM
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            
            system_prompt = (
                "You are an intelligent File System Assistant and Resume Matcher. "
                "You have access to File System tools and Web Search tools provided by MCP servers.\n"
                "When matching resumes:\n"
                "1. Use list_files and read_file to analyze resumes and job descriptions.\n"
                "2. If you need to evaluate a candidate's unfamiliar skill or past company, use search_web.\n"
                "3. Analyze all findings and use write_file to save a report.\n"
                "Gracefully explain any tool errors to the user."
            )
            
            # Create LangGraph Agent
            agent = create_react_agent(llm, langchain_tools, prompt=system_prompt)
            
            print("\n=== Agent Ready ===")
            print("Type your query (or 'quit' to exit):")
            
            while True:
                try:
                    user_input = input("\nUser > ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                    
                if user_input.lower() in ('quit', 'exit'):
                    break
                if not user_input:
                    continue
                    
                print("Agent is thinking...")
                
                # Run LangGraph agent
                state = {"messages": [("user", user_input)]}
                async for chunk in agent.astream(state):
                    if "agent" in chunk:
                        msg = chunk["agent"]["messages"][0]
                        if msg.content:
                            print(f"\nAssistant: {msg.content}")
                    elif "tools" in chunk:
                        msg = chunk["tools"]["messages"][0]
                        print(f"\n  [Tool Result] length: {len(msg.content)} chars")

if __name__ == "__main__":
    asyncio.run(main())
