import os
from dotenv import load_dotenv
from snowflake.snowpark import Session

def list_models():
    load_dotenv()
    connection_parameters = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
    }
    
    session = Session.builder.configs(connection_parameters).create()
    
    print("Fetching available Cortex models...")
    query = "SHOW CORTEX BASE MODELS;"
    result = session.sql(query).collect()
    
    print("\n--- Available Cortex Models ---")
    for row in result:
        print(f"- {row['name']} (Provider: {row['provider']})")

if __name__ == "__main__":
    list_models()
