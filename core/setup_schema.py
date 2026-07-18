import os
from dotenv import load_dotenv
from snowflake.snowpark import Session

def setup_database():
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
        "BLUEPRINTS",
        "BLUEPRINT_HISTORY", 
        "PROJECT_MEMORY",
        "ENTERPRISE_MEMORY",
        "SKILLS",
        "PIPELINE_RUNS",
        "VALIDATION_RESULTS",
        "OBSERVABILITY"
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
            
    print("\nDatabase Schema Initialization Complete.")

if __name__ == "__main__":
    setup_database()
