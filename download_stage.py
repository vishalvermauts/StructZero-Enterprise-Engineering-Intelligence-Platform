import os
from snowflake.snowpark import Session

def main():
    connection_parameters = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
        "user": os.getenv("SNOWFLAKE_USER", ""),
        "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
        "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "STRUCTZERO_DB"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "ENTERPRISE")
    }
    
    if not connection_parameters["account"]:
        from dotenv import load_dotenv
        load_dotenv()
        for k in connection_parameters.keys():
            connection_parameters[k] = os.getenv(f"SNOWFLAKE_{k.upper()}")

    session = Session.builder.configs(connection_parameters).create()
    print("Connected to Snowflake!")
    
    print("\n--- SHOW STAGES ---")
    stages = session.sql("SHOW STAGES IN SCHEMA STRUCTZERO_DB.ENTERPRISE").collect()
    for s in stages:
        print(s)
        
    print("\n--- SHOW STREAMLITS ---")
    streamlits = session.sql("SHOW STREAMLITS IN SCHEMA STRUCTZERO_DB.ENTERPRISE").collect()
    for s in streamlits:
        print(s)
        
if __name__ == "__main__":
    main()
