# Phase-wise Evaluations

This document defines the evaluation criteria for each phase of the implementation plan to ensure correctness, stability, and adherence to the Problem Statement.

---

## Phase 1: Environment & Server Initialization
**Evaluation Criteria:**
- [ ] Dependencies are correctly installed in `requirements.txt` or `pyproject.toml`.
- [ ] `filesystem_mcp_server.py` can be executed without syntax or import errors.
- [ ] The server successfully starts a `stdio` transport and waits for stdin/stdout communication.
- [ ] An external client (like the MCP Inspector) can connect and receive an `Initialize` response.

---

## Phase 2: Core MCP Server Capabilities
**Evaluation Criteria:**
- [ ] Executing a `tools/list` request returns the migrated Milestone 1 tools (`read_file`, `write_file`, etc.).
- [ ] Executing a `resources/list` request returns the designated file system resources.
- [ ] Calling the `read_file` tool via JSON-RPC returns the correct file contents.
- [ ] Attempting to read or write a file outside the configured base directory results in an explicit permission/access error.

---

## Phase 3: Advanced MCP Server Capabilities
**Evaluation Criteria:**
- [ ] **watch_directory:** When invoked, the tool correctly identifies newly added files in the target directory compared to a previous state.
- [ ] **batch_process:** Passing a list of multiple file operations (e.g., read file A, write file B) successfully executes them in one JSON-RPC call and returns a structured array of results.
- [ ] **Error Handling:** Intentionally causing a failure (e.g., reading a non-existent file) returns a well-formed JSON-RPC error object, not a raw Python exception crash.

---

## Phase 4: Agent Refactoring & MCP Client Integration
**Evaluation Criteria:**
- [ ] `matching_agent.py` contains no direct imports or usage of local file system manipulation functions (e.g., `open()`, `os.read()`).
- [ ] The agent successfully spawns the `filesystem_mcp_server.py` subprocess upon startup.
- [ ] The agent correctly retrieves the tool list from the MCP server.
- [ ] The LangGraph LLM node is successfully injected with the dynamically loaded MCP tools.

---

## Phase 5: Agent Workflow & Integration Testing
**Evaluation Criteria:**
- [ ] The LangGraph agent can successfully complete a full resume matching workflow (read resume, read job description, analyze, write result) purely through the MCP Server.
- [ ] The workflow matches the state machine diagram proposed in `architecture.md`.
- [ ] The agent gracefully handles tool errors (e.g., the LLM receives the error text and attempts a correction instead of the agent crashing).

---

## Phase 6: Multi-MCP Integration (Bonus)
**Evaluation Criteria:**
- [ ] The agent successfully connects to the File System MCP Server AND at least one other MCP Server (e.g., Web Search, DB).
- [ ] `tools/list` from the agent's perspective contains a union of tools from all connected servers.
- [ ] A test scenario successfully demonstrates the agent reading a local file via the FS MCP, and searching for related information via the Web Search MCP.
