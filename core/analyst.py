import requests
import json
from snowflake.snowpark import Session

class AnalystClient:
    """Client for interacting with Snowflake Cortex Analyst NLQ API."""
    
    def __init__(self, session: Session):
        self.session = session
        # Extract the underlying snowflake connector python connection
        self.conn = self.session._conn._conn
        self.host = self.conn.host
        self.token = self.conn.rest.token
        
        # We assume database and schema are already set, but let's query them to be safe
        db_row = self.session.sql("SELECT CURRENT_DATABASE()").collect()[0][0]
        schema_row = self.session.sql("SELECT CURRENT_SCHEMA()").collect()[0][0]
        
        db = db_row if db_row else "STRUCTZERO_DB"
        schema = schema_row if schema_row else "ENTERPRISE"
        
        self.semantic_model_file = f"@{db}.{schema}.ANALYST_MODELS/structzero_semantic_model.yaml"
        
    def send_message(self, messages: list) -> dict:
        """
        Send a conversation history to Cortex Analyst and get a response.
        `messages` is a list of dicts: [{"role": "user", "content": [{"type": "text", "text": "show me..."}]}]
        """
        url = f"https://{self.host}/api/v2/cortex/analyst/message"
        headers = {
            "Authorization": f'Snowflake Token="{self.token}"',
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "messages": messages,
            "semantic_model_file": self.semantic_model_file
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Cortex Analyst API Error: {response.status_code} - {response.text}")
            
        return response.json()
