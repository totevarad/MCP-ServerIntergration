# Problem Statement: MCP Integration

## Brief
The goal of this project is to integrate the **Model Context Protocol (MCP)** by replacing custom, direct-access tools with standardized MCP servers. This will involve implementing proper tool interfaces and deploying production-ready systems.

## Learning Objectives
- **Understand Model Context Protocol (MCP)**
- **Replace custom tools with MCP servers**
- **Implement standardized tool interfaces**
- **Deploy production-ready systems**

---

## Assignment Requirements

### Part A: MCP Server Implementation (50%)
Create `filesystem_mcp_server.py` to handle all file system operations via MCP.

**Key Tasks:**
- Convert existing File System Tools to MCP.
- Implement the MCP protocol specification.
- Expose all Milestone 1 tools as MCP resources.
- Add new MCP-specific capabilities:
  - `watch_directory()`: Monitor a directory for new resumes.
  - `batch_process()`: Handle multiple files efficiently.

**Required MCP Server Features:**
- JSON-RPC 2.0 compliant interface
- Proper error handling and status codes
- Resource discovery endpoints
- Configuration management

### Part B: Agent Refactoring (30%)
Update `matching_agent.py` to interact with the new MCP server.

**Key Tasks:**
- **Replace Custom Tools**: Remove direct file system tools from the agent.
- **MCP Client Integration**: Connect the agent to the MCP server via an MCP client.
- **Maintain Functionality**: Ensure the agent retains the same functionality but with a cleaner, decoupled architecture.

### Multi-MCP Integration (Bonus)
- Connect to additional MCP servers (e.g., web search, database).
- Demonstrate the agent intelligently using multiple MCP resources simultaneously.

---

## Submission Guidelines

### Deliverables
1. **MCP Server Implementation** (`filesystem_mcp_server.py`):
   - Must be a JSON-RPC 2.0 compliant MCP server with resource discovery.
   - Must include the new `watch_directory()` and `batch_process()` capabilities.
2. **Refactored Agent** (`matching_agent.py`): 
   - A LangGraph agent with proper MCP client integration.
3. **Workflow Diagram**: 
   - A state machine / workflow diagram visualizing the interaction between the Agent and the MCP server.
4. **Test Scenarios**: 
   - Scenarios demonstrating MCP resource usage and the end-to-end agent workflow.
5. **Demo Video (5–6 minutes)**: 
   - A walk-through showing the MCP server running, the agent integration, and successful end-to-end execution.
