import os
from dotenv import load_dotenv
from snowflake.snowpark import Session

def enable_and_test():
    load_dotenv()
    connection_parameters = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
    }
    
    session = Session.builder.configs(connection_parameters).create()
    
    print("Enabling Cross-Region Cortex Models...")
    try:
        session.sql("ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';").collect()
        print("[SUCCESS] Enabled cross-region models.")
    except Exception as e:
        print(f"[WARNING] Could not enable cross-region: {e}")
        
    print("Clearing Model Allowlist...")
    try:
        # We can also try just removing the parameter if it throws an error
        session.sql("ALTER ACCOUNT UNSET CORTEX_MODELS_ALLOWLIST;").collect()
        print("[SUCCESS] Cleared model allowlist.")
    except Exception as e:
        print(f"[WARNING] Could not unset allowlist (might not be set): {e}")

    print("\nTesting Claude Models again...")
    models_to_test = ["claude-3-5-sonnet", "claude-3-7-sonnet", "claude-3-opus"]
    
    for model in models_to_test:
        try:
            query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', 'say hi') as response"
            result = session.sql(query).collect()
            print(f"[OK] {model} is NOW AVAILABLE! Response: {result[0]['RESPONSE']}")
        except Exception as e:
            err = str(e).split('\n')[0]
            print(f"[FAILED] {model} -> {err}")

if __name__ == "__main__":
    enable_and_test()
