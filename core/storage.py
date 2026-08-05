# Snowpark persistence layer for StructZero JSON variant documents.
# Co-authored with CoCo
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

MIN_CONTEXT_CHUNKS = 4

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
            "PROJECTS", "BLUEPRINTS", "BLUEPRINT_HISTORY", "DEBATE_SESSIONS",
            "VALIDATIONS", "VALIDATION_RESULTS", "PIPELINE_RUNS", "OBSERVABILITY",
            "KNOWLEDGE_REGISTRY", "KNOWLEDGE_DOCUMENTS", "KNOWLEDGE_CHUNKS",
            "SEARCH_TELEMETRY"
        ]
        for table in tables:
            self.session.sql(
                f"""CREATE TABLE IF NOT EXISTS {table} (
                    ID VARCHAR(100) DEFAULT UUID_STRING(),
                    DATA VARIANT,
                    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                )"""
            ).collect()

    def _save_object(self, table: str, obj_id: str, data: dict):
        data_json = json.dumps(data)

        # Upsert logic (delete then insert) to handle versioning updates cleanly for MVP.
        # Values are bound, never interpolated: blueprint markdown routinely contains
        # quotes and '$$' sequences that would otherwise corrupt the statement.
        self.session.sql(f"DELETE FROM {table} WHERE ID = ?", params=[obj_id]).collect()
        self.session.sql(
            f"INSERT INTO {table} (ID, DATA) SELECT ?, PARSE_JSON(?)",
            params=[obj_id, data_json],
        ).collect()

    def _append_object(self, table: str, obj_id: str, data: dict):
        """Insert-only write for append-only audit tables (no delete-then-insert)."""
        self.session.sql(
            f"INSERT INTO {table} (ID, DATA) SELECT ?, PARSE_JSON(?)",
            params=[obj_id, json.dumps(data)],
        ).collect()


    def save_project(self, project: Project):
        self._save_object("PROJECTS", project.id, dataclasses.asdict(project))

    def save_blueprint(self, blueprint: Blueprint):
        self._save_object("BLUEPRINTS", blueprint.id, blueprint.to_dict())

    def save_debate_session(self, debate: DebateSession):
        self._save_object("DEBATE_SESSIONS", debate.id, dataclasses.asdict(debate))
        
    def save_observability(self, run_id: str, blueprint_id: str, metrics: dict):
        self._save_object("OBSERVABILITY", run_id, metrics)

    def save_validation(self, blueprint_id: str, validation: dict):
        """Persist the validation verdict as a first-class record, keyed by blueprint."""
        self._save_object("VALIDATIONS", blueprint_id, {
            "blueprint_id": blueprint_id,
            **validation,
        })

    def save_validation_results(self, blueprint_id: str, validation: dict):
        """Explode the verdict into one row per individual rule finding."""
        import uuid
        for category, score in (validation.get("category_scores") or {}).items():
            self._append_object("VALIDATION_RESULTS", str(uuid.uuid4()), {
                "blueprint_id": blueprint_id,
                "finding_type": "CATEGORY_SCORE",
                "category": category,
                "score": score,
                "message": None,
            })
        for msg in validation.get("errors") or []:
            self._append_object("VALIDATION_RESULTS", str(uuid.uuid4()), {
                "blueprint_id": blueprint_id,
                "finding_type": "ERROR",
                "category": None,
                "score": None,
                "message": msg,
            })
        for msg in validation.get("warnings") or []:
            self._append_object("VALIDATION_RESULTS", str(uuid.uuid4()), {
                "blueprint_id": blueprint_id,
                "finding_type": "WARNING",
                "category": None,
                "score": None,
                "message": msg,
            })

    def save_pipeline_run(self, run: dict):
        """Append one row per pipeline execution, including failed runs."""
        self._append_object("PIPELINE_RUNS", run["id"], run)

    def save_blueprint_history(self, blueprint: Blueprint):
        """Append-only snapshot of every blueprint version ever produced."""
        self._append_object("BLUEPRINT_HISTORY", blueprint.id, blueprint.to_dict())

    def count_knowledge_corpus(self) -> dict:
        """Actual size of the indexed corpus, for search telemetry."""
        try:
            row = self.session.sql(
                """SELECT (SELECT COUNT(*) FROM KNOWLEDGE_DOCUMENTS) AS DOCS,
                          (SELECT COUNT(*) FROM KNOWLEDGE_CHUNKS) AS CHUNKS"""
            ).collect()[0]
            return {"documents": int(row["DOCS"]), "chunks": int(row["CHUNKS"])}
        except Exception as e:
            print(f"Warning: could not count knowledge corpus: {e}")
            return {"documents": 0, "chunks": 0}

    # --- Knowledge Storage Methods ---
    def upsert_knowledge_registry(self, entry: dict):
        # The registry is keyed by source_path, not by the entry's freshly minted uuid.
        # Deleting on uuid alone would leave one stale row per re-ingest, and the stale row
        # could win the lookup in get_knowledge_registry_by_path.
        self.session.sql(
            "DELETE FROM KNOWLEDGE_REGISTRY WHERE DATA:source_path::STRING = ?",
            params=[entry["source_path"]],
        ).collect()
        self._append_object("KNOWLEDGE_REGISTRY", entry["id"], entry)
        
    def get_knowledge_registry_by_path(self, path: str):
        # upsert_knowledge_registry keeps at most one row per path; ordering on
        # ingestion_time (a DATA field, since this table has no CREATED_AT column)
        # makes the lookup deterministic even if a legacy duplicate survives.
        sql = """SELECT DATA FROM KNOWLEDGE_REGISTRY
                 WHERE DATA:source_path::STRING = ?
                 ORDER BY DATA:ingestion_time::STRING DESC LIMIT 1"""
        results = self.session.sql(sql, params=[path]).collect()
        return json.loads(results[0]["DATA"]) if results else None
        
    def upsert_knowledge_document(self, doc: dict):
        self._save_object("KNOWLEDGE_DOCUMENTS", doc["id"], doc)
        
    def clear_document_chunks(self, document_id: str):
        self.session.sql(
            "DELETE FROM KNOWLEDGE_CHUNKS WHERE DATA:document_id::STRING = ?",
            params=[document_id],
        ).collect()

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
                
            # Progressive widening. Requiring every filter to match excluded documents that
            # carry no cloud/compliance tag at all (the CQRS pattern, the Redis incident),
            # even though those apply universally - so any non-AWS target retrieved nothing.
            attempts = []
            if len(filter_conditions) > 1:
                attempts.append(("all filters", {"@and": filter_conditions}))
                attempts.append(("any filter", {"@or": filter_conditions}))
            elif len(filter_conditions) == 1:
                attempts.append(("all filters", filter_conditions[0]))
            attempts.append(("unfiltered", None))

            svc = root.databases["STRUCTZERO_DB"].schemas["ENTERPRISE"].cortex_search_services["STRUCTZERO_KNOWLEDGE_SEARCH"]

            target = min(MIN_CONTEXT_CHUNKS, limit)
            merged, seen_text, modes_used = [], set(), []
            
            for label, attempt_filter in attempts:
                resp = svc.search(
                    query=prompt,
                    columns=["chunk_text", "source", "category", "cloud", "compliance", "technology"],
                    filter=attempt_filter,
                    limit=limit
                )
                added = 0
                for result in (resp.results or []):
                    key = (result.get("chunk_text") or "").strip()
                    if not key or key in seen_text:
                        continue
                    seen_text.add(key)
                    merged.append({
                        "chunk_text": result.get("chunk_text", ""),
                        "metadata": {
                            "source": result.get("source", "Unknown"),
                            "cloud": result.get("cloud", ""),
                            "compliance": result.get("compliance", ""),
                            "category": result.get("category", "")
                        },
                        "score": 0.95, # Default high confidence for semantic search
                    })
                    added += 1
                modes_used.append(f"{label} (+{added})")
                if len(merged) >= target:
                    break
                    
            applied_filters["match_mode"] = " -> ".join(modes_used)
            applied_filters["min_chunks"] = target
            returned_chunks = merged[:limit]
            
            cortex_used = True
            
        except Exception as e:
            print(f"Warning: Cortex Search failed ({e}). Falling back to legacy SQL retrieval.")
            
        if not cortex_used:
            # Legacy Fallback
            sql = "SELECT DATA FROM KNOWLEDGE_CHUNKS"
            results = self.session.sql(sql).collect()
            
            relevant_chunks = []
            for row in results:
                chunk = json.loads(row["DATA"])
                meta = chunk.get("metadata", {})
                # Baseline of 1 so an untagged but universally applicable document stays
                # eligible; tag matches then rank it higher. Previously untagged chunks
                # scored 0 and were discarded entirely.
                score = 1
                if "General" in meta.get("category", "") or not meta:
                    score += 1
                doc_cloud = meta.get("cloud") or []
                doc_comp = meta.get("compliance") or []
                if cloud and cloud != "None":
                    if cloud in doc_cloud or cloud in meta.get("tags", []):
                        score += 5
                    elif not doc_cloud:
                        score += 2   # cloud-agnostic guidance
                if compliance and compliance != "None":
                    if compliance in doc_comp or compliance in meta.get("tags", []):
                        score += 5
                    elif not doc_comp:
                        score += 2   # regime-agnostic guidance

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
        sql = "SELECT DATA FROM BLUEPRINTS WHERE DATA:project_id::STRING = ? ORDER BY DATA:version::INT DESC"
        results = self.session.sql(sql, params=[project_id]).collect()
        return [json.loads(row["DATA"]) for row in results]

    def get_blueprint(self, blueprint_id: str):
        sql = "SELECT DATA FROM BLUEPRINTS WHERE ID = ?"
        results = self.session.sql(sql, params=[blueprint_id]).collect()
        return json.loads(results[0]["DATA"]) if results else None
        
    def get_debate_session(self, blueprint_id: str):
        sql = "SELECT DATA FROM DEBATE_SESSIONS WHERE DATA:blueprint_id::STRING = ?"
        results = self.session.sql(sql, params=[blueprint_id]).collect()
        return json.loads(results[0]["DATA"]) if results else None
        
    def get_validation_report(self, blueprint_id: str):
        # We stored validation inside blueprint for now, but we can extract it
        bp = self.get_blueprint(blueprint_id)
        if bp and "validation" in bp:
            return bp["validation"]
        return None

    def search_blueprints(self, query: str):
        # Basic ILIKE search on raw markdown; the term is bound, not interpolated
        sql = "SELECT DATA FROM BLUEPRINTS WHERE DATA:raw_markdown::STRING ILIKE ?"
        results = self.session.sql(sql, params=[f"%{query}%"]).collect()
        return [json.loads(row["DATA"]) for row in results]

    def get_blueprint_history(self):
        sql = "SELECT ID, DATA FROM BLUEPRINTS ORDER BY CREATED_AT DESC LIMIT 20"
        results = self.session.sql(sql).collect()
        return [{"id": row["ID"], "data": json.loads(row["DATA"])} for row in results]
