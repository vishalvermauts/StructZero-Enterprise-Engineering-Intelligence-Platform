import os
from pathlib import Path
from dotenv import load_dotenv
import toml

def setup_cli_config():
    # Load .env
    env_path = Path(".env")
    if not env_path.exists():
        print("Error: .env file not found.")
        return

    load_dotenv(env_path)

    # Map .env variables to Snowflake CLI config format
    connection_config = {
        "default": {
            "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
            "user": os.getenv("SNOWFLAKE_USER", ""),
            "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
            "role": os.getenv("SNOWFLAKE_ROLE", ""),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", ""),
            "database": os.getenv("SNOWFLAKE_DATABASE", ""),
            "schema": os.getenv("SNOWFLAKE_SCHEMA", "")
        }
    }

    # Ensure ~/.snowflake exists
    snow_dir = Path.home() / ".snowflake"
    snow_dir.mkdir(parents=True, exist_ok=True)

    # Write to connections.toml
    config_path = snow_dir / "connections.toml"
    
    # Read existing config if it exists
    if config_path.exists():
        try:
            existing_config = toml.load(config_path)
        except Exception:
            existing_config = {}
    else:
        existing_config = {}

    # Update with new default connection
    existing_config.update(connection_config)

    with open(config_path, "w") as f:
        toml.dump(existing_config, f)
        
    print(f"Successfully configured Snowflake CLI at {config_path}!")

if __name__ == "__main__":
    setup_cli_config()
