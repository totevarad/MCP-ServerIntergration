# Implementation Plan: MCP Integration

This document outlines a structured, phase-by-phase implementation plan for integrating the Model Context Protocol (MCP) into the existing agent workflow, satisfying the requirements from the Problem Statement and Architecture Reference.

## Phase 1: Environment & Server Initialization
**Goal:** Set up the fundamental MCP server structure.
1. **Initialize Project & Dependencies:**
   - Install necessary MCP Python SDKs (e.g., `mcp` library).
   - Set up the environment for `filesystem_mcp_server.py`.
2. **Server Boilerplate:**
   - Create the base `Server` instance.
   - Implement the `stdio` server transport for local process communication.
   - Run a basic `ping` test to ensure the JSON-RPC interface is active.

## Phase 2: Core MCP Server Capabilities (Part A)
**Goal:** Migrate existing file system tools and expose them as MCP resources and tools.
1. **Migrate Tools:**
   - Convert Milestone 1 functions (e.g., `read_file`, `write_file`, `list_directory`) into MCP tools using the `@server.tool()` decorator.
2. **Resource Discovery:**
   - Implement resource templates and the `resources/list` endpoint to expose specific directories or files as discoverable resources.
3. **Configuration & Security:**
   - Implement configuration management to restrict the server to a specific base directory, preventing access to unauthorized files.

## Phase 3: Advanced MCP Server Capabilities (Part A)
**Goal:** Implement the new capabilities required by the assignment.
1. **Implement `watch_directory()`:**
   - Develop a tool or continuous process that monitors a specified directory for new resume files.
2. **Implement `batch_process()`:**
   - Develop a tool that accepts an array of file operations and processes them sequentially or concurrently, returning a combined result.
3. **Error Handling & Compliance:**
   - Ensure all exceptions are caught and returned as valid JSON-RPC 2.0 error objects with proper status codes.

## Phase 4: Agent Refactoring & MCP Client Integration (Part B)
**Goal:** Decouple the LangGraph agent from direct file system access.
1. **Remove Old Code:**
   - Strip out all direct Python file system tools from `matching_agent.py`.
2. **Initialize MCP Client:**
   - Instantiate an MCP client within the agent using a `stdio` subprocess connecting to `filesystem_mcp_server.py`.
3. **Tool Binding:**
   - Fetch the available tools from the MCP server using `tools/list`.
   - Dynamically bind these tools to the LangGraph LLM node so the agent can reason about them.

## Phase 5: Agent Workflow & Integration Testing
**Goal:** Ensure the LangGraph agent functions correctly end-to-end.
1. **End-to-End Workflow:**
   - Update the agent's prompts and graph state to properly handle MCP tool responses instead of direct function returns.
2. **State Machine Verification:**
   - Validate the interaction loop: Agent -> LLM Tool Call -> MCP Client -> MCP Server -> MCP Client -> Agent State.
3. **Resilience Testing:**
   - Test how the agent handles JSON-RPC errors (e.g., file not found).

## Phase 6: Multi-MCP Integration (Bonus)
**Goal:** Expand the agent's capabilities using additional servers.
1. **Mock Additional Servers:**
   - Create or use existing lightweight MCP servers (e.g., Web Search, SQLite).
2. **Multi-Client Connection:**
   - Update the agent to connect to multiple MCP servers simultaneously.
3. **Combined Toolset:**
   - Aggregate tools from all servers and bind them to the LLM.
4. **Demonstrate Execution:**
   - Create a prompt that forces the agent to use both the File System MCP and the additional MCP to solve a problem.
