import os
import sys

# Add root directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.cortex_gateway import CortexGateway

print("Connecting to Snowflake as ACCOUNTADMIN...")
try:
    gateway = CortexGateway()
    print("Executing ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';")
    gateway.session.sql("ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';").collect()
    print("Successfully enabled cross-region inference for the account!")
except Exception as e:
    print(f"Failed: {e}")
