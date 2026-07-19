"""
Blueprint Parser Module
=======================
A deterministic normalizer that converts raw markdown from the AI Synthesizer 
into a structured BlueprintPresentation object for the Streamlit Executive Dashboard.
"""
import re
from dataclasses import dataclass

@dataclass
class BlueprintPresentation:
    """A structured presentation object representing the key sections of an architecture blueprint."""
    executive_summary: str = ""
    graphviz: str = ""
    components: str = ""
    security: str = ""
    performance: str = ""
    risks: str = ""
    decision_log: str = ""
    roadmap: str = ""
    recommended_actions: str = ""
    raw_markdown: str = ""

def extract_section(markdown: str, section_name: str) -> str:
    """
    Extracts the content of a specific markdown section by its heading name.
    
    Args:
        markdown (str): The raw markdown string.
        section_name (str): The heading text to search for (e.g., 'Executive Summary').
        
    Returns:
        str: The extracted markdown content under the heading, or empty string if not found.
    """
    # Looks for a heading that contains the section name, and captures everything until the next heading or EOF
    pattern = rf"(?i)#+.*{section_name}.*?\n(.*?)(?=\n#+ |\Z)"
    match = re.search(pattern, markdown, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def extract_graphviz(markdown: str) -> str:
    """
    Extracts the Graphviz DOT syntax block from the raw markdown.
    """
    matches = re.findall(r"```graphviz\s*(.*?)\s*```", markdown, re.DOTALL | re.IGNORECASE)
    if matches:
        return matches[0].strip()
    return ""

def parse_blueprint(raw_markdown: str) -> BlueprintPresentation:
    """
    Parses a raw markdown string into a structured BlueprintPresentation dataclass.
    """
    return BlueprintPresentation(
        executive_summary=extract_section(raw_markdown, "Executive Summary") or "No Summary Found.",
        graphviz=extract_graphviz(raw_markdown),
        components=extract_section(raw_markdown, "Components"),
        security=extract_section(raw_markdown, "Security"),
        performance=extract_section(raw_markdown, "Performance"),
        risks=extract_section(raw_markdown, "Risks"),
        decision_log=extract_section(raw_markdown, "Decision Log"),
        roadmap=extract_section(raw_markdown, "Roadmap"),
        recommended_actions=extract_section(raw_markdown, "Recommended Actions"),
        raw_markdown=raw_markdown
    )
