# StructZero - Enterprise Engineering Intelligence Platform

**StructZero - Enterprise Engineering Intelligence Platform** is built natively on Snowflake Cortex. It goes far beyond a simple LLM wrapper—it acts as an autonomous AI architecture review board. By combining a Progressive Knowledge Platform, Multi-Agent Debate Engine, comprehensive Telemetry, and an MCP Server, it helps engineering teams design, review, validate, and evolve production software systems securely using their own internal enterprise wisdom.

---

## 🏗️ Architecture Overview

The system is decomposed into a clean separation of concerns, operating as independent, interacting engines:

```mermaid
flowchart TD
    KP[Engineering Knowledge Platform] -->|Standards & Incidents| PE[Policy Engine]
    PE -->|Organizational Constraints| ARB[Enterprise Architecture Review Board]
    
    subgraph ARB [Multi-Agent Review Board]
        A[Architect] --> CR[Critical Reviewer]
        A --> SR[Security Reviewer]
        A --> PR[Performance Reviewer]
        CR --> PA[Principal Architect]
        SR --> PA
        PR --> PA
        PA --> V[Voters]
    end
    
    ARB --> VE[Validation Engine + Observability]
    VE -->|Validated JSON Blueprints| MCP[MCP Knowledge Server]
    VE -.->|Storage via Snowpark| SF[(Snowflake DB)]
    MCP --> IDE[Cursor / IDE]
```

For a deep dive into the subsystems (Knowledge Loader, Decision Logs, Evidence Summaries, and Telemetry), see our detailed architecture document: **[docs/architecture.md](docs/architecture.md)**.

---

## 🚀 How to Install and Run

### 1. Prerequisites
- **Python 3.11+**
- **uv**: We use `uv` for lightning-fast dependency management (`pip install uv`).
- **Snowflake Account**: You need access to a Snowflake instance with Cortex AI enabled.

### 2. Clone and Install
```bash
git clone https://github.com/vishalvermauts/StructZero-Enterprise-Engineering-Intelligence-Platform.git
cd StructZero-Enterprise-Engineering-Intelligence-Platform

# Sync dependencies using uv
uv sync
```

### 3. Environment Variables
Create a `.env` file in the root directory and add your Snowflake credentials:

```env
SNOWFLAKE_ACCOUNT=your_account_locator
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ROLE=your_role
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=STRUCTZERO_DB
SNOWFLAKE_SCHEMA=ENTERPRISE
```

### 4. Setup Snowflake Schema
Before running the application, you need to create the `STRUCTZERO_DB` database and the dynamic JSON tables. Run the setup script:
```bash
uv run python -m core.setup_schema
```
*(This will safely drop and recreate the necessary JSON variant tables: PROJECTS, BLUEPRINTS, DEBATE_SESSIONS, OBSERVABILITY, KNOWLEDGE_REGISTRY, etc.)*

### 5. Run the Platform

**To run the UI Dashboard (Streamlit):**
```bash
uv run streamlit run ui/app.py
```
This will launch the interactive Enterprise Dashboard where you can query the system, watch the agents debate in real-time, and view the observability telemetry.

**To run the end-to-end backend test pipeline:**
```bash
uv run python test_pipeline.py
```

**To run the MCP Server (for Cursor/IDE integration):**
```bash
uv run python -m mcp.run
```

---

## 📂 Code Structure & Components

The repository is modularly designed into distinct enterprise components:

### `core/` (The Engine)
- **`pipeline.py`**: The orchestration heart of the system. Manages the lifecycle of a request from Knowledge Ingestion -> Architect -> Reviewers -> Synthesizer -> Validation -> Snowflake Storage.
- **`agents.py`**: Contains the system prompts and wrappers for the Cortex LLMs. Defines the personas for the Architect, Security Reviewer, Performance Reviewer, and the Principal Architect (Synthesizer).
- **`cortex_gateway.py`**: An abstraction over `snowflake.cortex.Complete()`. It dynamically routes models, estimates token usage, and calculates approximate USD costs for observability.
- **`storage.py`**: The Snowflake storage layer using Snowpark. Saves massive JSON blobs into Snowflake `VARIANT` columns using double-dollar `$${...}$$` string escaping.
- **`knowledge_loader.py` & `loaders/`**: The plugin-based knowledge orchestrator. Scans the `/knowledge` directory, parses Markdown frontmatter, calculates MD5 checksums, and chunks data for the Enterprise Brain.
- **`validators.py`**: A deterministic Python rules engine that scores the final AI blueprints out of 100 based on security and performance rules.

### `ui/` (The Interface)
- **`app.py`**: A rich Streamlit dashboard. It renders real-time Mermaid.js diagrams, displays the AI's "Evidence Summary", and provides a granular telemetry sidebar (tracking latency, Cortex API calls, and estimated costs).

### `knowledge/` (The Enterprise Brain)
- A mock directory structure (`aws/`, `security/`, `incidents/`, `patterns/`) containing Markdown files. The system ingests these at runtime, allowing the Architect to explicitly cite internal company policies (e.g., PCI-DSS constraints) in its blueprints.

### `mcp/` (The IDE Server)
- **`server.py` & `run.py`**: Exposes the Snowflake intelligence directly to local developer tools using the Model Context Protocol (`mcp.server.fastmcp`). This allows developers to query architecture blueprints directly from Cursor or Claude Desktop.
