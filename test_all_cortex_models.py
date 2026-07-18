import os
from dotenv import load_dotenv
from snowflake.snowpark import Session
import time

def check_models():
    load_dotenv()
    connection_parameters = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
    }
    
    session = Session.builder.configs(connection_parameters).create()
    
    models_to_test = [
        "claude-4-opus",
        "claude-4-sonnet",
        "claude-opus-4.6",
        "claude-3-5-sonnet",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "claude-3.5-sonnet",
        "llama3-8b",
        "llama3-70b",
        "llama3.1-8b",
        "llama3.1-70b",
        "llama3.1-405b",
        "llama3.2-1b",
        "llama3.2-3b",
        "llama3.3-70b",
        "snowflake-llama-3.3-70b",
        "mistral-large",
        "mistral-large2",
        "mistral-small2",
        "mistral-7b",
        "mixtral-8x7b",
        "snowflake-arctic",
        "jamba-instruct",
        "gemma-7b",
        "reka-core",
        "deepseek-r1"
    ]
    
    print("Testing models via API (SNOWFLAKE.CORTEX.COMPLETE)...")
    available_models = []
    
    for model in models_to_test:
        try:
            query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', 'hi') as response"
            result = session.sql(query).collect()
            print(f"[OK] {model} is available!")
            available_models.append(model)
        except Exception as e:
            err = str(e).split('\n')[0]
            print(f"[FAILED] {model} -> {err}")
        time.sleep(0.1)
        
    print("\n--- FINAL LIST OF AVAILABLE MODELS ---")
    for m in available_models:
        print(f" - {m}")

if __name__ == "__main__":
    check_models()
