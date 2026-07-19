"""
Schema Setup Module
===================
Initializes the Snowflake database, schema, and necessary native VARIANT tables 
to persist projects, blueprints, and engineering telemetry.
"""
import os
from dotenv import load_dotenv
from snowflake.snowpark import Session

def setup_database():
    """
    Connects to Snowflake and idempotently creates the STRUCTZERO_DB database, 
    ENTERPRISE schema, and core JSON variant tables.
    """
    load_dotenv()
    connection_parameters = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
    }
    
    print("Connecting to Snowflake...")
    session = Session.builder.configs(connection_parameters).create()
    
    tables = [
        "PROJECTS", "BLUEPRINTS", "DEBATE_SESSIONS", "VALIDATIONS", "OBSERVABILITY",
        "KNOWLEDGE_REGISTRY", "KNOWLEDGE_DOCUMENTS", "KNOWLEDGE_CHUNKS",
        "SEARCH_TELEMETRY"
    ]
    
    print("Creating database and tables...")
    try:
        session.sql("CREATE DATABASE IF NOT EXISTS STRUCTZERO_DB;").collect()
        session.sql("USE DATABASE STRUCTZERO_DB;").collect()
        session.sql("CREATE SCHEMA IF NOT EXISTS ENTERPRISE;").collect()
        session.sql("USE SCHEMA ENTERPRISE;").collect()
    except Exception as e:
        print(f"Failed to setup database/schema: {e}")
        
    for table in tables:
        # Using VARIANT for highly flexible JSON storage natively in Snowflake
        sql = f"""
        CREATE TABLE IF NOT EXISTS {table} (
            ID VARCHAR(100) DEFAULT UUID_STRING(),
            DATA VARIANT,
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
        """
        try:
            session.sql(sql).collect()
            print(f"[OK] Table {table} is ready.")
        except Exception as e:
            print(f"[ERROR] Failed to create {table}: {str(e)}")
            
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    if not warehouse:
        warehouse = "COMPUTE_WH"
    
    print("\nCreating KNOWLEDGE_SEARCH_VIEW...")
    try:
        view_sql = """
        CREATE OR REPLACE VIEW KNOWLEDGE_SEARCH_VIEW AS
        SELECT 
            DATA:chunk_text::VARCHAR as chunk_text,
            DATA:metadata:source::VARCHAR as source,
            DATA:metadata:category::VARCHAR as category,
            DATA:metadata:cloud::ARRAY as cloud,
            DATA:metadata:compliance::ARRAY as compliance,
            DATA:metadata:technology::ARRAY as technology,
            DATA:metadata:provider::VARCHAR as provider,
            DATA:metadata:language::VARCHAR as language,
            DATA:metadata:framework::VARCHAR as framework,
            DATA:metadata:architecture_pattern::VARCHAR as architecture_pattern,
            DATA:metadata:document_type::VARCHAR as document_type,
            DATA:metadata:version::VARCHAR as version,
            DATA:metadata:last_updated::VARCHAR as last_updated
        FROM KNOWLEDGE_CHUNKS
        WHERE DATA:chunk_text::VARCHAR IS NOT NULL;
        """
        session.sql(view_sql).collect()
        print("[OK] KNOWLEDGE_SEARCH_VIEW created.")
    except Exception as e:
        print(f"[ERROR] Failed to create KNOWLEDGE_SEARCH_VIEW: {e}")

    print("\nCreating CORTEX SEARCH SERVICE...")
    try:
        cortex_sql = f"""
        CREATE OR REPLACE CORTEX SEARCH SERVICE structzero_knowledge_search
        ON chunk_text
        ATTRIBUTES source, category, cloud, compliance, technology, provider, language, framework, architecture_pattern, document_type, version, last_updated
        WAREHOUSE = {warehouse}
        TARGET_LAG = '1 minute'
        AS (SELECT * FROM KNOWLEDGE_SEARCH_VIEW);
        """
        print(f"Executing: {cortex_sql}")
        session.sql(cortex_sql).collect()
        print("[OK] CORTEX SEARCH SERVICE created.")
    except Exception as e:
        print(f"[ERROR] Failed to create CORTEX SEARCH SERVICE: {str(e)}")


    print("\nDatabase Schema Initialization Complete.")
    
    print("\nCreating Analytics View and Stage...")
    try:
        analytics_sql = """
        CREATE OR REPLACE VIEW ENTERPRISE_ANALYTICS_V AS
        SELECT
            b.DATA:id::VARCHAR AS blueprint_id,
            b.DATA:request:project_name::VARCHAR AS project_name,
            b.DATA:request:cloud_target::VARCHAR AS cloud_target,
            b.DATA:request:compliance::VARCHAR AS compliance_target,
            b.DATA:validation:status::VARCHAR AS validation_status,
            b.DATA:validation:overall_score::NUMBER AS overall_score,
            b.DATA:validation:category_scores:Security::NUMBER AS security_score,
            b.DATA:validation:category_scores:Performance::NUMBER AS performance_score,
            o.DATA:total_latency_ms::NUMBER AS total_latency_ms,
            o.DATA:estimated_cost_usd::FLOAT AS estimated_cost_usd
        FROM BLUEPRINTS b
        LEFT JOIN OBSERVABILITY o ON b.DATA:id::VARCHAR = o.DATA:blueprint_id::VARCHAR;
        """
        session.sql(analytics_sql).collect()
        print("[OK] ENTERPRISE_ANALYTICS_V created.")
        
        session.sql("CREATE STAGE IF NOT EXISTS ANALYST_MODELS;").collect()
        print("[OK] ANALYST_MODELS stage created.")
        
        # Upload the yaml if it exists
        yaml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models', 'structzero_semantic_model.yaml')
        if os.path.exists(yaml_path):
            session.file.put(yaml_path, "@ANALYST_MODELS", auto_compress=False, overwrite=True)
            print("[OK] Uploaded semantic model to stage.")
            
    except Exception as e:
        print(f"[ERROR] Failed to set up Analytics: {e}")

if __name__ == "__main__":
    setup_database()
