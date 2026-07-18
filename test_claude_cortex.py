import os
from dotenv import load_dotenv
from snowflake.snowpark import Session
import time

def test_claude():
    load_dotenv()
    connection_parameters = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
    }
    
    session = Session.builder.configs(connection_parameters).create()
    
    print("Granting CORTEX_USER role to ACCOUNTADMIN...")
    try:
        session.sql("GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE ACCOUNTADMIN;").collect()
        print("[SUCCESS] Granted role.")
    except Exception as e:
        print(f"[WARNING] Could not grant role: {e}")
        
    print("\nQuerying INFORMATION_SCHEMA.CORTEX_SUPPORTED_MODELS()...")
    try:
        query = "SELECT * FROM TABLE(INFORMATION_SCHEMA.CORTEX_SUPPORTED_MODELS()) WHERE MODEL_NAME ILIKE '%claude%';"
        result = session.sql(query).collect()
        print(f"Found {len(result)} Claude models supported in this region:")
        for row in result:
            print(f" - {row['MODEL_NAME']}")
    except Exception as e:
        print(f"[FAILED] Could not query CORTEX_SUPPORTED_MODELS: {e}")

    print("\nTesting Claude Models...")
    models_to_test = ["claude-4-opus", "claude-4-sonnet", "claude-3-5-sonnet", "claude-3-5-haiku"]
    
    for model in models_to_test:
        try:
            query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', 'say hi') as response"
            result = session.sql(query).collect()
            print(f"[OK] {model} is AVAILABLE! Response: {result[0]['RESPONSE']}")
        except Exception as e:
            err = str(e).split('\n')[0]
            print(f"[FAILED] {model} -> {err}")
        time.sleep(0.1)

if __name__ == "__main__":
    test_claude()
