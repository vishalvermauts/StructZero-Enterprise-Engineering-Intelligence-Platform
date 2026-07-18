import sys
import os
import json

# Add root to python path to resolve 'core' imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.server.fastmcp import FastMCP, Context
from core.cortex_gateway import CortexGateway
from core.storage import StorageClient

# Initialize Server
mcp = FastMCP("StructZero Enterprise")

# Global dependencies
gateway = None
storage = None

def get_storage():
    global gateway, storage
    if not gateway:
        gateway = CortexGateway()
        storage = StorageClient(gateway.session)
    return storage

@mcp.tool()
def list_projects() -> str:
    """List all enterprise architecture projects in the StructZero knowledge graph."""
    storage = get_storage()
    projects = storage.list_projects()
    if not projects:
        return "No projects found."
    return json.dumps([{"id": p.get("id"), "name": p.get("name")} for p in projects], indent=2)

@mcp.tool()
def list_project_versions(project_id: str) -> str:
    """List all blueprint versions for a specific project."""
    storage = get_storage()
    versions = storage.list_project_versions(project_id)
    if not versions:
        return f"No versions found for project {project_id}."
    return json.dumps([{"id": v.get("id"), "version": v.get("version"), "created_at": v.get("created_at")} for v in versions], indent=2)

@mcp.tool()
def get_blueprint(blueprint_id: str) -> str:
    """Get the full raw Markdown and Mermaid diagram for a specific blueprint."""
    storage = get_storage()
    bp = storage.get_blueprint(blueprint_id)
    if not bp:
        return f"Blueprint {blueprint_id} not found."
    return f"## Raw Markdown\n\n{bp.get('raw_markdown', '')}\n\n## Mermaid Diagram\n\n```mermaid\n{bp.get('mermaid_diagram', '')}\n```"

@mcp.tool()
def get_decision_log(blueprint_id: str) -> str:
    """Extract just the Decision Log section from a blueprint."""
    storage = get_storage()
    bp = storage.get_blueprint(blueprint_id)
    if not bp:
        return f"Blueprint {blueprint_id} not found."
    raw = bp.get("raw_markdown", "")
    if "# Architecture Review Board Decision Log" in raw:
        # Super simple extraction logic
        parts = raw.split("# Architecture Review Board Decision Log")
        if len(parts) > 1:
            log_section = parts[1].split("# Executive Summary")[0]
            return f"# Architecture Review Board Decision Log\n{log_section.strip()}"
    return "No Decision Log found in this blueprint."

@mcp.tool()
def get_debate_transcript(blueprint_id: str) -> str:
    """Retrieve the full Debate Session (Architect, Reviews, Votes) for a blueprint."""
    storage = get_storage()
    debate = storage.get_debate_session(blueprint_id)
    if not debate:
        return f"No Debate Session found for Blueprint {blueprint_id}."
    return json.dumps(debate, indent=2)

@mcp.tool()
def get_execution_metrics(blueprint_id: str) -> str:
    """Get the execution time and performance metrics for how this blueprint was generated."""
    storage = get_storage()
    results = storage.session.sql(f"SELECT DATA FROM OBSERVABILITY WHERE ID = '{blueprint_id}'").collect()
    if results:
        return json.dumps(json.loads(results[0]["DATA"]), indent=2)
    return "No metrics found."

@mcp.tool()
def search_blueprints(query: str) -> str:
    """Search across all enterprise blueprints using ILIKE match (MVP)."""
    storage = get_storage()
    results = storage.search_blueprints(query)
    if not results:
        return f"No blueprints matched query: {query}"
    return json.dumps([{"id": b.get("id"), "project_id": b.get("project_id"), "version": b.get("version")} for b in results], indent=2)

# --- Resources ---
# FastMCP natively supports exposing endpoints as resources

@mcp.resource("structzero://project/{project_id}")
def resource_project(project_id: str) -> str:
    storage = get_storage()
    projects = storage.list_projects()
    proj = next((p for p in projects if p.get("id") == project_id), None)
    return json.dumps(proj, indent=2) if proj else "Project not found"

@mcp.resource("structzero://blueprint/{blueprint_id}")
def resource_blueprint(blueprint_id: str) -> str:
    return get_blueprint(blueprint_id)

@mcp.resource("structzero://debate/{blueprint_id}")
def resource_debate(blueprint_id: str) -> str:
    return get_debate_transcript(blueprint_id)

@mcp.resource("structzero://decision/{blueprint_id}")
def resource_decision(blueprint_id: str) -> str:
    return get_decision_log(blueprint_id)

if __name__ == "__main__":
    # Start the FastMCP stdio server
    mcp.run()
