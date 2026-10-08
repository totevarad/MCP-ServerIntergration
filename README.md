# MCP Server Integration: Resume Matching Agent

This project demonstrates a fully decoupled, agentic architecture leveraging the **Model Context Protocol (MCP)**. It transforms legacy, direct-access Python file system tools into a robust, JSON-RPC 2.0 compliant MCP Server. An intelligent LangGraph agent then acts as the client, dynamically discovering tools from multiple MCP servers simultaneously to perform advanced resume matching and file analysis.

## 🌟 Main Features

*   **MCP File System Server:** A standalone server (`filesystem_mcp_server.py`) that sandboxes file operations (read, write, list, search) to a specific `workspace/` directory, preventing path traversal vulnerabilities.
*   **Advanced File Capabilities:** Includes MCP-specific tools like `watch_directory` (to detect new files) and `batch_process` (to execute multiple operations in one JSON-RPC call efficiently).
*   **Resource Discovery:** The MCP server dynamically exposes files as discoverable resources via standard `resources/list` and `read_resource` endpoints.
*   **Multi-MCP Integration:** The LangGraph agent seamlessly connects to *multiple* MCP servers simultaneously (e.g., the File System Server and a Mock Web Search Server).
*   **LangGraph Orchestration:** `matching_agent.py` dynamically converts MCP tool JSON schemas into LangChain `StructuredTool` instances, allowing the GPT-4o LLM to reason and act upon them transparently.

## 🛠 Tech Stack

*   **Protocol:** [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) via the official `mcp` Python SDK
*   **Agent Framework:** LangGraph & LangChain (`langchain-core`, `langchain-openai`)
*   **LLM Provider:** OpenAI (GPT-4o)
*   **Document Parsers:** `pypdf`, `python-docx`
*   **Language:** Python 3.10+

## ⚙️ How It Works

1.  **Startup:** When you run `matching_agent.py`, the agent spins up the MCP servers (`filesystem_mcp_server.py` and `mock_web_mcp_server.py`) as background subprocesses using `stdio` transport.
2.  **Discovery:** The agent establishes a JSON-RPC session with both servers and calls `tools/list` to discover their capabilities.
3.  **Binding:** The agent dynamically parses the MCP JSON Schemas and binds them as native LangChain tools using a custom conversion factory.
4.  **Execution:** When you ask a question (e.g., "Match resumes to the JD"), the LLM determines which tools to call. The agent forwards these calls over `stdio` to the appropriate MCP server, which executes the logic in a sandboxed environment and returns the result safely.

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.10 or higher.
*   An OpenAI API Key (required to run the LangGraph agent).

### 1. Installation

Clone the repository and install the required dependencies:

```bash
# Optional: Create a virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the root of the project and add your OpenAI API Key:

```env
OPENAI_API_KEY=your-api-key-here
```

### 3. Usage

**Running the Agent:**
Start the interactive LangGraph agent. It will automatically spin up the MCP servers and connect to them.

```bash
python matching_agent.py
```
*Example Prompt:* `"Read the job description and the resumes in the workspace. Match them and write a report to match_report.txt. If you don't know a technology in a resume, use the web search tool to look it up."*

**Running the Test Client (Debugging):**
If you want to debug the MCP server endpoints (like testing `watch_directory` and `batch_process`) without invoking the LLM, you can run the test client:

```bash
python test_client.py
```

### 4. Workspace Sandboxing
All file system operations performed by the agent are strictly sandboxed to the `workspace/` directory located in the project root. This is a security measure built into the MCP server. Place any test resumes (`.pdf`, `.docx`, `.txt`) or job descriptions inside this folder so the agent can interact with them.
