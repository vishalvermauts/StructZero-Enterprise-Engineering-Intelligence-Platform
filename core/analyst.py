# Cortex Analyst client that works both inside Streamlit in Snowflake and in local dev.
# Co-authored with CoCo
import json
from snowflake.snowpark import Session

_ANALYST_PATH = "/api/v2/cortex/analyst/message"
_TIMEOUT_MS = 60000


class AnalystClient:
    """Client for interacting with Snowflake Cortex Analyst NLQ API."""

    def __init__(self, session: Session, semantic_model_file: str = None):
        self.session = session

        # Inside Snowflake (SiS, stored procs) the `_snowflake` module is available and
        # proxies REST calls using the app's own identity. There is no client session
        # token to reuse there: session._conn._conn is a StoredProcRestful object with
        # no `.rest.token`, which is why reading it raised AttributeError.
        try:
            import _snowflake
            self._api = _snowflake
            self.host = None
            self.token = None
        except ImportError:
            # Local development against a client connector connection.
            self._api = None
            conn = self.session._conn._conn
            self.host = conn.host
            self.token = conn.rest.token

        db = self.session.sql("SELECT CURRENT_DATABASE()").collect()[0][0] or "STRUCTZERO_DB"
        schema = self.session.sql("SELECT CURRENT_SCHEMA()").collect()[0][0] or "ENTERPRISE"
        self.semantic_model_file = (
            semantic_model_file
            or f"@{db}.{schema}.ANALYST_MODELS/structzero_semantic_model.yaml"
        )

    @property
    def in_snowflake(self) -> bool:
        return self._api is not None

    def send_message(self, messages: list) -> dict:
        """
        Send a conversation history to Cortex Analyst and get a response.
        `messages` is a list of dicts: [{"role": "user", "content": [{"type": "text", "text": "show me..."}]}]
        """
        payload = {
            "messages": messages,
            "semantic_model_file": self.semantic_model_file,
        }

        if self.in_snowflake:
            response = self._api.send_snow_api_request(
                "POST", _ANALYST_PATH, {}, {}, payload, None, _TIMEOUT_MS
            )
            status = response.get("status")
            content = response.get("content")
            if status != 200:
                raise Exception(f"Cortex Analyst API Error: {status} - {content}")
            return json.loads(content) if isinstance(content, str) else content

        # Local dev path: direct REST call with the client session token.
        import requests

        url = f"https://{self.host}{_ANALYST_PATH}"
        headers = {
            "Authorization": f'Snowflake Token="{self.token}"',
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(
                f"Cortex Analyst API Error: {response.status_code} - {response.text}"
            )
        return response.json()
