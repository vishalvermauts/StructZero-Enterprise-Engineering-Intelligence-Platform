import os
from dotenv import load_dotenv
from snowflake.snowpark import Session
from snowflake.snowpark.context import get_active_session

class CortexGateway:
    def __init__(self):
        try:
            # Native Streamlit in Snowflake (SiS) uses the active session automatically
            self.session = get_active_session()
        except Exception:
            # Local development fallback (MCP, Local Streamlit)
            load_dotenv()
            connection_parameters = {
                "account": os.getenv("SNOWFLAKE_ACCOUNT"),
                "user": os.getenv("SNOWFLAKE_USER"),
                "password": os.getenv("SNOWFLAKE_PASSWORD"),
                "role": os.getenv("SNOWFLAKE_ROLE"),
            }
            self.session = Session.builder.configs(connection_parameters).create()
        self.reset_metrics()

    def reset_metrics(self):
        self.total_calls = 0
        self.estimated_input_tokens = 0
        self.estimated_output_tokens = 0
        self.estimated_cost_usd = 0.0

    def complete(self, prompt: str, model: str = "claude-4-sonnet") -> str:
        """
        Sends a completion request to Snowflake Cortex natively via Snowpark.
        """
        # Escape single quotes in the prompt to prevent SQL injection/syntax errors
        safe_prompt = prompt.replace("'", "''")
        query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', '{safe_prompt}') as response"
        
        try:
            self.total_calls += 1
            input_tokens = int(len(prompt.split()) * 1.3)
            self.estimated_input_tokens += input_tokens
            
            result = self.session.sql(query).collect()
            response_text = result[0]['RESPONSE']
            
            output_tokens = int(len(response_text.split()) * 1.3)
            self.estimated_output_tokens += output_tokens
            # Rough MVP pricing: $3/M input, $15/M output
            self.estimated_cost_usd += (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)
            
            return response_text
        except Exception as e:
            print(f"Cortex API Error: {str(e)}")
            return None

# Simple testing block
if __name__ == "__main__":
    gateway = CortexGateway()
    print("Testing Architect Model (Claude 4 Sonnet)...")
    res1 = gateway.complete("Explain the purpose of a multi-agent system in one sentence.", "claude-4-sonnet")
    print(f"Response: {res1}\n")
    
    print("Testing Critic Model (Llama 3.3)...")
    res2 = gateway.complete("Explain the purpose of a multi-agent system in one sentence.", "llama3.3-70b")
    print(f"Response: {res2}")
