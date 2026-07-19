import pytest
import sys
import os

def test_streamlit_app_syntax():
    """
    Smoke test to ensure streamlit_app.py can be compiled 
    without SyntaxError or IndentationError.
    """
    app_path = os.path.join(os.path.dirname(__file__), "..", "streamlit_app.py")
    
    with open(app_path, "r", encoding="utf-8") as f:
        source = f.read()
        
    try:
        compile(source, app_path, "exec")
    except SyntaxError as e:
        pytest.fail(f"Syntax/Indentation Error in streamlit_app.py: {e}")
