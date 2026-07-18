# StructZero Enterprise - Project DNA

## 1. Project Overview
**StructZero Enterprise** is an Enterprise AI Software Architecture Copilot built specifically for the **Snowflake CoCo CLI Hackathon**. 
It sits between a developer and an AI coding IDE (like Cursor or Claude Desktop) and serves as an "Enterprise Planning Engine". 
Instead of prompting an IDE to blindly generate code, developers ask StructZero, which retrieves enterprise knowledge from Snowflake, reasons using multiple AI agents in a deterministic workflow, validates against enterprise standards, and generates a production-ready architectural blueprint that the IDE can then safely implement.

## 2. Technology Stack
*   **Language:** Python 3.12+ (managed via `uv`)
*   **Frontend:** Streamlit (Custom Enterprise Dashboard)
*   **Backend Services:** Python Native Services (FastAPI later if needed)
*   **Agent Framework:** LangGraph & LangChain
*   **Database / Enterprise Brain:** Snowflake (Primary source of truth for Memory, Architecture History, and Incident Reports)
*   **Vector Search & AI:** Snowflake Cortex Search / Native Vector Search, Snowpark
*   **CLI Integration:** Snowflake CoCo CLI (`cortex`)
*   **AI Models:** 
    *   Claude 4 Sonnet (via Snowflake Cortex)
    *   Llama 3.3 (via Snowflake Cortex)
    *   Mistral Large 2 (via Snowflake Cortex)
*   **Diagrams:** Mermaid.js
*   **IDE Integration:** Model Context Protocol (MCP) Server (Python implementation)

## 3. Necessary Credentials & Environment (.env)
The project relies on a `.env` file at the root directory containing the following critical keys:
```env
# Snowflake Authentication
SNOWFLAKE_ACCOUNT="KRPMABK-RU28442"
SNOWFLAKE_USER="VISHALVR28"
SNOWFLAKE_PASSWORD="" # Kept secure
SNOWFLAKE_ROLE="ACCOUNTADMIN"
SNOWFLAKE_WAREHOUSE=""
SNOWFLAKE_DATABASE=""
SNOWFLAKE_SCHEMA=""

# Vertex AI (Gemini)
VERTEX_AI_PROJECT=""
VERTEX_AI_LOCATION=""

# AWS Bedrock (Claude, DeepSeek)
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
AWS_REGION=""
```

## 4. Implementation Phases (A to Z)
- **Phase 0:** Enterprise Intelligence Layer (Snowflake Brain Foundation, Auto-seeding Standards) - **[COMPLETE]**
- **Phase 1:** Project Skeleton (DDD Structure, `uv` init, `.env`, local memory wrappers) - **[COMPLETE]**
- **Phase 2:** Snowflake Integration (Cortex, Snowpark, CoCo CLI connections) - **[COMPLETE]**
- **Phase 3:** Enterprise Planning Pipeline (Core Agents & Flow) - **[COMPLETE]**
- **Phase 4:** Streamlit UI & Enterprise Digital Brain (Dashboard, Timeline Visualization, Architecture Explainability) - **[COMPLETE]**
- **Phase 5:** Multi-Agent Debate Engine (Claude Critic, DeepSeek Synthesizer, ADK Gatekeeper) - **[COMPLETE]**
- **Phase 6:** MCP Server (Exposing Blueprints to Cursor/Claude Desktop/Antigravity via `mcp.server.fastmcp`) - **[COMPLETE]**
- **Phase 7:** Engineering Knowledge Platform (Documents, Chunks, Plugin Loaders, Knowledge Registry) - **[COMPLETE]**
- **Phase 8:** Observability (Granular metric tracking: Latency, Tokens, Cost, Knowledge Retrieved, Scores) - **[COMPLETE]**
- **Phase 9:** Polish & End-to-End Testing (Demo Workflow execution) - **[COMPLETE]**

## 5. Daily Work & Troubleshooting Log

### [Day 1] - 2026-07-18
- **Goal:** Set up the initial project skeleton, finalize the architectural plan, and locate the CoCo CLI.
- **Problem:** CoCo CLI was requested, but `coco` was not recognized in the system path.
- **Troubleshooting:**
  - Attempted to locate `coco` via PowerShell `Get-Command` and manual search.
  - Investigated Snowflake documentation and discovered the actual executable name for Cortex Copilot is `cortex`, not `coco`.
  - Refreshed system PATH from the Windows registry.
- **Solution/Result:** 
  - `cortex` (Cortex Code v1.1.41) successfully located. 
  - Project initialized with `uv`, `.env` populated with Snowflake details, and `.ai` folder created for IDE context tracking. Phase 1 completed successfully.

- **Problem:** When installing `snowflake-ml-python` for Cortex API access, the dependency `llvmlite` failed to build on Python 3.14.
- **Troubleshooting:** Snowflake ML strictly requires older Python versions (<3.10 for some deep dependencies).
- **Solution/Result:** Pinned the project to Python 3.9 in `pyproject.toml` and cleared/rebuilt the `uv` virtual environment.

- **Next Steps:** Finish testing the Cortex API connections and proceed fully into Phase 2 (Snowflake Integration).

### [Day 2] - 2026-07-19
- **Goal:** Evolve into an Enterprise Knowledge Graph via normalized database schema, multi-agent debate, and MCP server.
- **Solution/Result:** 
  - Overhauled data model to use explicitly versioned `Project`, `DebateSession`, and `ExecutionMetrics` records.
  - Re-wrote `save_blueprint` to persist properly normalized JSON records into `STRUCTZERO_DB.ENTERPRISE`.
  - Implemented Phase 5 (Multi-Agent Debate) by refactoring the reviewer pipeline.
  - Implemented Phase 6 (MCP Server) using `mcp.server.fastmcp`, exposing `list_projects`, `get_blueprint`, and `search_blueprints` as native IDE tools.
### [Day 2 - Part 2] - 2026-07-19
- **Goal:** Build a Progressive Knowledge Architecture (Phase 7) and complete granular Observability (Phase 8).
- **Solution/Result:** 
  - Abandoned rigid `ENTERPRISE_STANDARDS` table for a generalized `KNOWLEDGE_DOCUMENTS`, `KNOWLEDGE_CHUNKS`, and `KNOWLEDGE_REGISTRY` schema.
  - Implemented a plugin-based `KnowledgeLoader` (`BaseLoader`, `MarkdownLoader`) to ingest a rich `knowledge/` directory structure.
  - Seeded realistic mock data for AWS KMS, PCI-DSS, Redis Incidents, and CQRS patterns.
  - Updated Architect prompt to mandate an **Evidence Summary** documenting knowledge applied and ignored.
  - Rendered all new telemetry directly in the Streamlit UI dashboard.
  - Successfully executed a full end-to-end pipeline run (`test_pipeline.py`) simulating an enterprise AI query against Snowflake Cortex, confirming latency (~88s), scoring, and ingestion pipelines function perfectly. Project is 100% ready for demo.

## 6. Project Rules
*   **Living Document:** This `techstack.md` (Project DNA) is a living document. Any architectural suggestion, workflow change, or feedback provided by the user MUST be immediately updated in this file so that it remains the absolute source of truth.
