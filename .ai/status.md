# Project Memory / Architecture State

## Current State
The project has successfully implemented the **Multi-Agent Debate Engine** (Phase 5) and the **Enterprise Knowledge Graph / MCP Server** (Phase 6). Phase 0 (Enterprise Intelligence Layer) has also been fully implemented to proactively inject corporate policies into the agent debate.

## Snowflake Brain Foundation
- The system automatically creates and seeds `ENTERPRISE_STANDARDS` inside Snowflake.
- Policies are stored with categories (GLOBAL, AWS, SOC2, etc.).
- The Context Builder queries these policies and they are securely injected into the Architecture and Reviewer prompts.

## MCP Server
- Available at `mcp/run.py` using `mcp.server.fastmcp`.
- Exposes tools like `list_projects`, `search_blueprints`, and `get_debate_transcript`.
- Natively integrated to allow Cursor, Claude Desktop, or Antigravity IDE to query the Snowflake knowledge graph.

## Next Objectives
- The next major focus is Phase 8 (Observability) which involves tracking metrics like CoCo CLI time, agent latency, and model token usage.
