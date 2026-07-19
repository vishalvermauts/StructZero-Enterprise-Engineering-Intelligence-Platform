import json
import dataclasses
from snowflake.snowpark import Session
from core.models import Blueprint, Project, DebateSession, ExecutionMetrics

class StorageClient:
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
    def get_enterprise_context(self, request) -> list[str]:
        # Intelligent retrieval querying JSON arrays using array_contains or basic matching
        # For MVP, we will grab all chunks, but simulate smart retrieval based on request features
        sql = f"SELECT DATA FROM KNOWLEDGE_CHUNKS"
        results = self.session.sql(sql).collect()
        
        relevant_chunks = []
        for row in results:
            chunk = json.loads(row["DATA"])
            meta = chunk.get("metadata", {})
            
            # Simple scoring mechanism based on tags/cloud/compliance
            score = 0
            if "General" in meta.get("category", "") or not meta:
                score += 1
            if request.cloud_target in meta.get("cloud", []) or request.cloud_target in meta.get("tags", []):
                score += 5
            if request.compliance in meta.get("compliance", []) or request.compliance in meta.get("tags", []):
                score += 5
                
            # Grab high scoring chunks
            if score > 0:
                relevant_chunks.append({
                    "chunk_text": chunk["chunk_text"],
                    "score": score,
                    "metadata": meta
                })
                
        # Sort by score descending and take top N (e.g. 15 chunks)
        relevant_chunks.sort(key=lambda x: x["score"], reverse=True)
        top_chunks = relevant_chunks[:15]
        
        # Return formatted strings
        return [f"[{c['metadata'].get('title', 'Knowledge')}] (Confidence {min(0.99, 0.70 + (c['score']/100))}): {c['chunk_text']}" for c in top_chunks]

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
