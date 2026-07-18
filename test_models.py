import os
import sys

# Add root directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.cortex_gateway import CortexGateway

models_to_test = [
    "claude-4-sonnet",
    "claude-4-opus",
    "claude-3-5-sonnet",
    "claude-3-5-haiku",
    "llama3.3-70b",
    "llama3.1-405b",
    "llama3.1-70b",
    "llama3.1-8b",
    "mistral-large2",
    "mistral-small2",
    "snowflake-arctic",
    "deepseek-r1"
]

print("Connecting to Snowflake...")
try:
    gateway = CortexGateway()
except Exception as e:
    print(f"Failed to connect: {e}")
    sys.exit(1)

print("\nQuerying CORTEX_SUPPORTED_MODELS view...")
try:
    sql = "SELECT MODEL_NAME FROM TABLE(INFORMATION_SCHEMA.CORTEX_SUPPORTED_MODELS())"
    results = gateway.session.sql(sql).collect()
    print("Supported models according to INFORMATION_SCHEMA:")
    for row in results:
        print(f" - {row['MODEL_NAME']}")
except Exception as e:
    print(f"Failed to query INFORMATION_SCHEMA: {e}")


print("\nTesting individual model invocation...")
available = []
unavailable = []

for model in models_to_test:
    print(f"Testing {model}...", end=" ", flush=True)
    try:
        # A very simple prompt to minimize cost and time
        res = gateway.complete("Say 'hi' in one word.", model)
        if res and len(res) > 0:
            print("OK")
            available.append(model)
        else:
            print("FAILED (Empty response)")
            unavailable.append(model)
    except Exception as e:
        print(f"FAILED: {e}")
        unavailable.append(model)

print("\n--- RESULTS ---")
print("AVAILABLE MODELS:")
for m in available:
    print(f"  {m}")

print("\nUNAVAILABLE MODELS:")
for m in unavailable:
    print(f"  {m}")
