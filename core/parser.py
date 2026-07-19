import re
from pydantic import BaseModel, Field

class BlueprintPresentation(BaseModel):
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
    # Looks for a heading that contains the section name, and captures everything until the next heading or EOF
    pattern = rf"(?i)#+.*{section_name}.*?\n(.*?)(?=\n#+ |\Z)"
    match = re.search(pattern, markdown, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def extract_graphviz(markdown: str) -> str:
    matches = re.findall(r"```graphviz\s*(.*?)\s*```", markdown, re.DOTALL | re.IGNORECASE)
    if matches:
        return matches[0].strip()
    return ""

def parse_blueprint(raw_markdown: str) -> BlueprintPresentation:
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
