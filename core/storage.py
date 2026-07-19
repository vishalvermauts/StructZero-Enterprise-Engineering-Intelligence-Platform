"""
Storage Client Module
=====================
Handles all native Snowflake persistence operations using Snowpark. Manages the storage 
and retrieval of JSON variant data for projects, blueprints, and observability telemetry.
"""
import json
import dataclasses
from snowflake.snowpark import Session
from core.models import Blueprint, Project, DebateSession, ExecutionMetrics

class StorageClient:
    """Snowpark-based client for managing Native JSON document persistence in Snowflake."""
    def __init__(self, session: Session):
        self.session = session
        # Ensure database and schema are selected
        try:
            self.session.sql("USE DATABASE STRUCTZERO_DB;").collect()
            self.session.sql("USE SCHEMA ENTERPRISE;").collect()
            self.setup_tables()
        except Exception as e:
            print(f"Warning: Database or schema not set. Error: {e}")

    def setup_tables(self):
        tables = [
            "PROJECTS", "BLUEPRINTS", "DEBATE_SESSIONS", "VALIDATIONS", "OBSERVABILITY",
            "KNOWLEDGE_REGISTRY", "KNOWLEDGE_DOCUMENTS", "KNOWLEDGE_CHUNKS"
        ]
        for table in tables:
            self.session.sql(f"CREATE TABLE IF NOT EXISTS {table} (ID VARCHAR, DATA VARIANT)").collect()

    def _save_object(self, table: str, obj_id: str, data: dict):
        data_json = json.dumps(data)
        
        # Upsert logic (delete then insert) to handle versioning updates cleanly for MVP
        self.session.sql(f"DELETE FROM {table} WHERE ID = '{obj_id}'").collect()
        # Use Snowflake double-dollar string literal to avoid escaping nightmares
        safe_json = data_json.replace("$$", "\\$\\$")
        sql = f"""
        INSERT INTO {table} (ID, DATA)
        SELECT '{obj_id}', PARSE_JSON($${safe_json}$$)
        """
        self.session.sql(sql).collect()

    def save_project(self, project: Project):
        self._save_object("PROJECTS", project.id, dataclasses.asdict(project))

    def save_blueprint(self, blueprint: Blueprint):
        self._save_object("BLUEPRINTS", blueprint.id, blueprint.to_dict())

    def save_debate_session(self, debate: DebateSession):
        self._save_object("DEBATE_SESSIONS", debate.id, dataclasses.asdict(debate))
        
    def save_observability(self, run_id: str, blueprint_id: str, metrics: dict):
        self._save_object("OBSERVABILITY", run_id, metrics)

    # --- Knowledge Storage Methods ---
    def upsert_knowledge_registry(self, entry: dict):
        self._save_object("KNOWLEDGE_REGISTRY", entry["id"], entry)
        
    def get_knowledge_registry_by_path(self, path: str):
        sql = f"SELECT DATA FROM KNOWLEDGE_REGISTRY WHERE DATA:source_path::STRING = '{path}'"
        results = self.session.sql(sql).collect()
        return json.loads(results[0]["DATA"]) if results else None
        
    def upsert_knowledge_document(self, doc: dict):
        self._save_object("KNOWLEDGE_DOCUMENTS", doc["id"], doc)
        
    def clear_document_chunks(self, document_id: str):
        self.session.sql(f"DELETE FROM KNOWLEDGE_CHUNKS WHERE DATA:document_id::STRING = '{document_id}'").collect()
        
    def upsert_knowledge_chunk(self, chunk: dict):
        self._save_object("KNOWLEDGE_CHUNKS", chunk["id"], chunk)

    # --- Read Methods ---
    def get_enterprise_context(self, prompt: str, cloud: str = None, compliance: str = None, category: str = None, technologies: list = None, limit: int = 8) -> list[dict]:
        import time
        import uuid
        start_time = time.time()
        cortex_used = False
        returned_chunks = []
        applied_filters = {}
        
        try:
            from snowflake.core import Root
            root = Root(self.session)
            
            # Prepare metadata filters
            filter_conditions = []
            
            if cloud and cloud != "None":
                filter_conditions.append({"@contains": {"cloud": cloud}})
                applied_filters["cloud"] = cloud
            if compliance and compliance != "None":
                filter_conditions.append({"@contains": {"compliance": compliance}})
                applied_filters["compliance"] = compliance
            if category:
                filter_conditions.append({"@eq": {"category": category}})
                applied_filters["category"] = category
                
            cortex_filter = None
            if len(filter_conditions) == 1:
                cortex_filter = filter_conditions[0]
            elif len(filter_conditions) > 1:
                cortex_filter = {"@and": filter_conditions}
                
            svc = root.databases["STRUCTZERO_DB"].schemas["ENTERPRISE"].cortex_search_services["STRUCTZERO_KNOWLEDGE_SEARCH"]
            
            resp = svc.search(
                query=prompt,
                columns=["chunk_text", "source", "category", "cloud", "compliance", "technology"],
                filter=cortex_filter,
                limit=limit
            )
            
            for result in resp.results:
                returned_chunks.append({
                    "chunk_text": result.get("chunk_text", ""),
                    "metadata": {
                        "source": result.get("source", "Unknown"),
                        "cloud": result.get("cloud", ""),
                        "compliance": result.get("compliance", ""),
                        "category": result.get("category", "")
                    },
                    "score": 0.95, # Default high confidence for semantic search
                })
            cortex_used = True
            
        except Exception as e:
            print(f"Warning: Cortex Search failed ({e}). Falling back to legacy SQL retrieval.")
            
        if not cortex_used:
            # Legacy Fallback
            sql = f"SELECT DATA FROM KNOWLEDGE_CHUNKS"
            results = self.session.sql(sql).collect()
            
            relevant_chunks = []
            for row in results:
                chunk = json.loads(row["DATA"])
                meta = chunk.get("metadata", {})
                score = 0
                if "General" in meta.get("category", "") or not meta:
                    score += 1
                if cloud and cloud != "None" and (cloud in meta.get("cloud", []) or cloud in meta.get("tags", [])):
                    score += 5
                if compliance and compliance != "None" and (compliance in meta.get("compliance", []) or compliance in meta.get("tags", [])):
                    score += 5
                    
                if score > 0:
                    relevant_chunks.append({
                        "chunk_text": chunk["chunk_text"],
                        "score": score,
                        "metadata": meta
                    })
                    
            relevant_chunks.sort(key=lambda x: x["score"], reverse=True)
            returned_chunks = relevant_chunks[:limit]
            
        latency = time.time() - start_time
        
        # Log telemetry
        telemetry_event = {
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "query": prompt,
            "engine": "Cortex Search" if cortex_used else "Legacy SQL",
            "latency_sec": latency,
            "returned_count": len(returned_chunks),
            "applied_filters": applied_filters
        }
        self._save_object("SEARCH_TELEMETRY", telemetry_event["id"], telemetry_event)
        
        return returned_chunks

    def list_projects(self):
        results = self.session.sql("SELECT ID, DATA FROM PROJECTS").collect()
        return [json.loads(row["DATA"]) for row in results]

    def list_project_versions(self, project_id: str):
        sql = f"SELECT DATA FROM BLUEPRINTS WHERE DATA:project_id::STRING = '{project_id}' ORDER BY DATA:version::INT DESC"
        results = self.session.sql(sql).collect()
        return [json.loads(row["DATA"]) for row in results]

    def get_blueprint(self, blueprint_id: str):
        sql = f"SELECT DATA FROM BLUEPRINTS WHERE ID = '{blueprint_id}'"
        results = self.session.sql(sql).collect()
        return json.loads(results[0]["DATA"]) if results else None
        
    def get_debate_session(self, blueprint_id: str):
        sql = f"SELECT DATA FROM DEBATE_SESSIONS WHERE DATA:blueprint_id::STRING = '{blueprint_id}'"
        results = self.session.sql(sql).collect()
        return json.loads(results[0]["DATA"]) if results else None
        
    def get_validation_report(self, blueprint_id: str):
        # We stored validation inside blueprint for now, but we can extract it
        bp = self.get_blueprint(blueprint_id)
        if bp and "validation" in bp:
            return bp["validation"]
        return None

    def search_blueprints(self, query: str):
        safe_query = query.replace("'", "''")
        # MVP: Basic ILIKE search on raw markdown
        sql = f"SELECT DATA FROM BLUEPRINTS WHERE DATA:raw_markdown::STRING ILIKE '%{safe_query}%'"
        results = self.session.sql(sql).collect()
        return [json.loads(row["DATA"]) for row in results]

    def get_blueprint_history(self):
        sql = "SELECT ID, DATA FROM BLUEPRINTS ORDER BY DATA:created_at::STRING DESC LIMIT 20"
        results = self.session.sql(sql).collect()
        return [{"id": row["ID"], "data": json.loads(row["DATA"])} for row in results]
