import asyncio
import sys
import json
import os
import dotenv

# Ensure UTF-8 output encoding on Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from typing import Any, List, Dict, Optional
from pydantic import create_model, Field
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

from logger_config import setup_logger

logger = setup_logger("agent", "agent.log")

# Load environment variables (e.g., ANTHROPIC_API_KEY)
dotenv.load_dotenv()

def build_langchain_tools(mcp_tools, session):
    """Dynamically build LangChain StructuredTools from MCP tool definitions."""
    langchain_tools = []
    for t in mcp_tools:
        # Closure to capture tool name securely
        def create_coroutine(tool_name):
            async def afunc(**kwargs):
                clean_kwargs = {k: v for k, v in kwargs.items() if v not in ("", None)}
                logger.info(f"[Tool Execution] Calling '{tool_name}' with args: {clean_kwargs}")
                print(f"\n  [Agent Tool Execution] Calling '{tool_name}' with args {clean_kwargs}")
                try:
                    res = await session.call_tool(tool_name, clean_kwargs)
                    text_content = res.content[0].text if res.content else ""
                    if text_content.startswith("Error:"):
                        logger.warning(f"[Tool Execution] '{tool_name}' returned error response: {text_content}")
                    else:
                        logger.debug(f"[Tool Execution] '{tool_name}' response length: {len(text_content)} chars")
                    return text_content
                except Exception as e:
                    logger.exception(f"[Tool Execution] Exception in '{tool_name}': {e}")
                    return f"Error executing {tool_name}: {str(e)}"
            return afunc
            
        # Dynamically build Pydantic schema for the tool arguments
        fields = {}
        if "properties" in t.inputSchema:
            required_props = set(t.inputSchema.get("required", []))
            type_map = {
                "string": str,
                "array": List[Any],
                "object": Dict[str, Any],
                "integer": int,
                "number": float,
                "boolean": bool,
            }
            for prop_name, prop_info in t.inputSchema["properties"].items():
                p_type = type_map.get(prop_info.get("type", "string"), Any)
                desc = prop_info.get("description", "")
                if prop_name in required_props:
                    fields[prop_name] = (p_type, Field(..., description=desc))
                else:
                    fields[prop_name] = (Optional[p_type], Field(default=None, description=desc))
        
        DynamicSchema = create_model(f"{t.name}Schema", **fields)
        
        ltool = StructuredTool(
            name=t.name,
            description=t.description,
            args_schema=DynamicSchema,
            coroutine=create_coroutine(t.name)
        )
        langchain_tools.append(ltool)
        logger.debug(f"Registered LangChain tool: '{t.name}'")
    return langchain_tools

async def main():
    groq_api_key = os.environ.get("GROQ_API_KEY")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    if not groq_api_key and not openai_api_key:
        print("Error: Neither GROQ_API_KEY nor OPENAI_API_KEY found. Please set GROQ_API_KEY in .env.")
        sys.exit(1)

    fs_params = StdioServerParameters(command=sys.executable, args=["filesystem_mcp_server.py"])
    web_params = StdioServerParameters(command=sys.executable, args=["mock_web_mcp_server.py"])
    
    logger.info("Connecting to MCP Servers: filesystem_mcp_server and mock_web_mcp_server...")
    print("Connecting to multiple MCP Servers...")
    try:
        async with stdio_client(fs_params) as (fs_read, fs_write), \
                   stdio_client(web_params) as (web_read, web_write):
            
            async with ClientSession(fs_read, fs_write) as fs_session, \
                       ClientSession(web_read, web_write) as web_session:
                
                # Initialize both sessions concurrently
                await asyncio.gather(fs_session.initialize(), web_session.initialize())
                logger.info("Successfully initialized MCP sessions.")
                print("Successfully initialized MCP sessions!")
                
                # Fetch tools from both servers
                fs_tools_res = await fs_session.list_tools()
                web_tools_res = await web_session.list_tools()
                
                logger.info(f"Discovered {len(fs_tools_res.tools)} File System tools: {[t.name for t in fs_tools_res.tools]}")
                logger.info(f"Discovered {len(web_tools_res.tools)} Web Search tools: {[t.name for t in web_tools_res.tools]}")
                print(f"Discovered {len(fs_tools_res.tools)} File System tools and {len(web_tools_res.tools)} Web Search tools.")
                
                # Build and combine LangChain tools
                langchain_tools = build_langchain_tools(fs_tools_res.tools, fs_session)
                langchain_tools.extend(build_langchain_tools(web_tools_res.tools, web_session))
                
                # Initialize LLM (supports Groq or OpenAI)
                if groq_api_key:
                    groq_model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
                    logger.info(f"Using Groq model: {groq_model}")
                    print(f"Using Groq model: {groq_model}")
                    llm = ChatGroq(model=groq_model, temperature=0, groq_api_key=groq_api_key)
                else:
                    logger.info("Using OpenAI model: gpt-4o")
                    print("Using OpenAI model: gpt-4o")
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
                logger.info("LangGraph agent created and ready for interaction.")
                
                print("\n=== Agent Ready ===")
                print("Type your query (or 'quit' to exit):")
                
                while True:
                    try:
                        user_input = input("\nUser > ").strip()
                    except (EOFError, KeyboardInterrupt):
                        logger.info("User requested exit via EOF or KeyboardInterrupt.")
                        break
                        
                    if user_input.lower() in ('quit', 'exit'):
                        logger.info("User requested exit.")
                        break
                    if not user_input:
                        continue
                        
                    logger.info(f"Received User Query: '{user_input}'")
                    print("Agent is thinking...")
                    
                    # Run LangGraph agent
                    state = {"messages": [("user", user_input)]}
                    try:
                        async for chunk in agent.astream(state):
                            if "agent" in chunk:
                                msg = chunk["agent"]["messages"][0]
                                if msg.content:
                                    logger.info(f"Agent Assistant reply: {msg.content[:200]}...")
                                    print(f"\nAssistant: {msg.content}")
                            elif "tools" in chunk:
                                msg = chunk["tools"]["messages"][0]
                                logger.debug(f"Agent tool chunk result received: {len(msg.content)} chars")
                                print(f"\n  [Tool Result] length: {len(msg.content)} chars")
                    except Exception as e:
                        logger.exception(f"Error executing agent stream for query '{user_input}': {e}")
                        print(f"\n[Agent Error]: An error occurred while processing: {e}")

    except Exception as e:
        logger.exception(f"Fatal error during MCP client lifecycle: {e}")
        print(f"\nFatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
