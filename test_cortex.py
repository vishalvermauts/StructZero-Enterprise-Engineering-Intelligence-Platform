import os
from dotenv import load_dotenv
from snowflake.snowpark import Session

def test_cortex_methods():
    print("Loading environment variables...")
    load_dotenv()
    
    password = os.getenv("SNOWFLAKE_PASSWORD")
    if not password:
        print("ERROR: SNOWFLAKE_PASSWORD is empty in .env. Please fill it in.")
        return

    connection_parameters = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": password,
        "role": os.getenv("SNOWFLAKE_ROLE"),
    }
    
    print(f"Connecting to Snowflake account: {connection_parameters['account']}...")
    try:
        session = Session.builder.configs(connection_parameters).create()
        print("Successfully connected to Snowflake!")
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return

# Method 1: Using SQL / Snowpark (The most robust method)
    print("\n--- Testing Snowpark SQL ---")
    try:
        # We try to use a small model like llama3-8b or mistral-large
        query = "SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3-8b', 'Say hello in exactly one word.') as response"
        result = session.sql(query).collect()
        print(f"Cortex Response: {result[0]['RESPONSE']}")
    except Exception as e:
        print(f"Cortex Call Failed: {str(e)}")

if __name__ == "__main__":
    test_cortex_methods()
