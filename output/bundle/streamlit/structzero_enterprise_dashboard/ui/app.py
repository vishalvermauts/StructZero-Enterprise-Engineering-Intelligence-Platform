import streamlit as st
import sys
import os

# Add root directory to python path so we can import 'core'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.models import PlanningRequest
from core.pipeline import PlanningPipeline
from core.storage import StorageClient
from core.cortex_gateway import CortexGateway

# Page config
st.set_page_config(page_title="StructZero - Enterprise Engineering Intelligence Platform", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for enterprise aesthetic
st.markdown("""
    <style>
    .main { background-color: #0E1117; color: #FFFFFF; }
    .stTextArea textarea { background-color: #1E2127 !important; color: white !important; }
    h1, h2, h3 { color: #58A6FF !important; }
    .pass { color: #2EA043; font-weight: bold; }
    .warn { color: #D29922; font-weight: bold; }
    .fail { color: #F85149; font-weight: bold; }
    .metric-box { padding: 10px; background-color: #161B22; border-radius: 5px; margin-bottom: 10px; border: 1px solid #30363D; }
    </style>
""", unsafe_allow_html=True)

# Initialize Gateway (cached to avoid reconnecting constantly)
@st.cache_resource
def get_cortex_gateway():
    return CortexGateway()

@st.cache_resource
def get_planning_pipeline():
    return PlanningPipeline()

gateway = get_cortex_gateway()
storage = StorageClient(gateway.session)
pipeline = get_planning_pipeline()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/ff/Snowflake_Logo.svg", width=150)
    st.title("Planning Controls")
    
    project = st.text_input("Project Name", value="New Enterprise Project")
    
    cloud_target = st.selectbox("Cloud Target", ["AWS", "Azure", "GCP", "On-Prem"])
    compliance = st.selectbox("Compliance Requirement", ["None", "PCI-DSS", "SOC2", "HIPAA", "GDPR"])
    
    st.divider()
    
    st.subheader("Planning Mode")
    st.radio("Active Engine", ["○ Architect (Legacy)", "● Collaborative Architecture Review Board", "○ Enterprise (Coming Soon)"], disabled=True, index=1)
    
    st.divider()
    
    st.subheader("Blueprint History")
    history = storage.get_blueprint_history()
    if not history:
        st.write("No history found.")
    else:
        for item in history:
            req_data = item['data'].get('request', {})
            model_used = req_data.get('model', 'Unknown')
            st.button(f"{item['id'][:8]}... ({model_used})", key=item['id'])

# --- MAIN DASHBOARD ---
st.title("StructZero - Enterprise Engineering Intelligence Platform")
st.markdown("### Advanced AI Software Architecture Copilot")

prompt = st.text_area("Planning Request", placeholder="e.g., Design a scalable payment microservice...", height=150)

if st.button("Generate Blueprint", type="primary", use_container_width=True):
    if not prompt:
        st.warning("Please enter a planning request.")
    else:
        request = PlanningRequest(
            project_name=project,
            prompt=prompt,
            cloud_target=cloud_target,
            compliance=compliance,
            model="Multi-Model"
        )
        
        st.markdown("### Debate Timeline & Artifacts")
        
        # We will dynamically render the cards here as they come in from the generator
        blueprint = None
        reviews = None
        metrics = None
        val = None
        
        container = st.container()
        agent_placeholders = {}

        def render_agent_card(agent_name, icon, model_name, status, details=None):
            if agent_name not in agent_placeholders:
                agent_placeholders[agent_name] = container.empty()
                
            placeholder = agent_placeholders[agent_name]
            
            with placeholder.container():
                if status == "running":
                    with st.expander(f"{icon} {agent_name} ({model_name}) - Status: ⏳ Running...", expanded=True):
                        st.write("Executing...")
                elif status == "complete":
                    with st.expander(f"{icon} {agent_name} ({model_name}) - Status: Completed", expanded=False):
                        if details:
                            st.markdown(details, unsafe_allow_html=True)
                elif status == "error":
                    with st.expander(f"{icon} {agent_name} ({model_name}) - Status: ❌ ERROR", expanded=True):
                        st.error(details)

        icons = {
            "Enterprise Context Builder": "⚪",
            "Architect": "🟢",
            "Critical Reviewer": "🟠",
            "Security Reviewer": "🔴",
            "Performance Reviewer": "🟣",
            "Synthesizer": "🔵",
            "Critical Voter": "🗳️",
            "Security Voter": "🛡️",
            "Performance Voter": "⚡",
            "Production Validator": "✅",
            "Snowflake Storage": "❄️"
        }

        for state in pipeline.run(request):
            if state.get("status") == "finished":
                blueprint = state["blueprint"]
                reviews = state["reviews"]
                metrics = state["metrics"]
                break
                
            agent = state.get("agent")
            status = state.get("status")
            model = state.get("model", "Python Deterministic")
            icon = icons.get(agent, "✓")
            
            output_content = None
            if status == "complete":
                if "output" in state:
                    output_content = state["output"]
                elif "validation" in state:
                    val = state["validation"]
                    status_color = "green" if "APPROVED" in val.status else "red"
                    val_str = f"### Overall: <span style='color:{status_color}'>{val.status}</span>\n\n"
                    
                    overall_score = getattr(val, "overall_score", 100)
                    category_scores = getattr(val, "category_scores", {})
                    
                    val_str += f"**Architecture Quality:** {overall_score}/100\n\n"
                    val_str += "---\n"
                    for cat, score in category_scores.items():
                        val_str += f"**{cat}:** {score}\n\n"
                    if val.errors: val_str += "---\n**Errors:**\n- " + "\n- ".join(val.errors) + "\n"
                    if val.warnings: val_str += "---\n**Warnings:**\n- " + "\n- ".join(val.warnings) + "\n"
                    output_content = val_str

            render_agent_card(agent, icon, model, status, output_content)

        st.divider()
        
        if blueprint and metrics:
            st.markdown("### Final Approval Board")
            
            votes = reviews.get("votes", {})
            v_crit = votes.get("critical", "Unknown")
            v_sec = votes.get("security", "Unknown")
            v_perf = votes.get("performance", "Unknown")
            
            # Helper to parse the vote and reason
            def parse_vote(v_str):
                lines = v_str.strip().split("\n")
                vote = lines[0].strip()
                reason = "\n".join(lines[1:]).replace("Reason:", "").strip()
                if "APPROVE WITH WARNINGS" in vote:
                    return "⚠ WARN", reason
                elif "APPROVE" in vote:
                    return "✅ APPROVE", reason
                else:
                    return "❌ BLOCK", reason
            
            crit_vote, crit_reason = parse_vote(v_crit)
            sec_vote, sec_reason = parse_vote(v_sec)
            perf_vote, perf_reason = parse_vote(v_perf)
            val_status = val.status if val else "UNKNOWN"
            val_icon = "✅ PASS" if "APPROVED" in val_status else ("⚠ WARN" if "WARNINGS" in val_status else "❌ FAIL")
            
            st.markdown(f"""
| Reviewer     | Vote      | Reason |
| ------------ | --------- | ------ |
| Architecture (Validator) | {val_icon} | Deterministic rules engine |
| Critical     | {crit_vote} | {crit_reason} |
| Security     | {sec_vote} | {sec_reason} |
| Performance  | {perf_vote} | {perf_reason} |
""")

            st.markdown("### Engineering Telemetry (Pipeline Observability)")
            
            # Latency Metrics
            st.markdown("#### Agent Latency")
            cols_l = st.columns(5)
            cols_l[0].metric("Architect", f"{metrics.get('architect_latency_ms', 0)}ms")
            cols_l[1].metric("Reviewers", f"{metrics.get('review_latency_ms', 0)}ms")
            cols_l[2].metric("Synthesizer", f"{metrics.get('synthesizer_latency_ms', 0)}ms")
            cols_l[3].metric("Validator", f"{metrics.get('validation_latency_ms', 0)}ms")
            cols_l[4].metric("Total", f"{metrics.get('total_latency_ms', 0)}ms")
            
            # Knowledge Metrics
            st.markdown("#### Enterprise Knowledge Metrics")
            cols_k = st.columns(4)
            cols_k[0].metric("Documents Searched", f"{metrics.get('knowledge_documents_searched', 0)}")
            cols_k[1].metric("Chunks Searched", f"{metrics.get('knowledge_chunks_searched', 0)}")
            cols_k[2].metric("Documents Retrieved", f"{metrics.get('knowledge_documents_retrieved', 0)}")
            cols_k[3].metric("Chunks Retrieved", f"{metrics.get('knowledge_chunks_retrieved', 0)}")
            
            # Cortex Gateway Metrics
            st.markdown("#### Snowflake Cortex Telemetry")
            cols_c = st.columns(4)
            cols_c[0].metric("Cortex Calls", f"{metrics.get('cortex_calls', 0)}")
            cols_c[1].metric("Est. Input Tokens", f"{metrics.get('estimated_input_tokens', 0)}")
            cols_c[2].metric("Est. Output Tokens", f"{metrics.get('estimated_output_tokens', 0)}")
            cols_c[3].metric("Est. Cost (USD)", f"${metrics.get('estimated_cost_usd', 0.0):.4f}")
            
            # Quality Scores
            st.markdown("#### Architecture Quality Scores")
            cols_q = st.columns(4)
            cols_q[0].metric("Overall Score", f"{metrics.get('blueprint_score', 0)}")
            cols_q[1].metric("Security", f"{metrics.get('security_score', 0)}")
            cols_q[2].metric("Performance", f"{metrics.get('performance_score', 0)}")
            cols_q[3].metric("Validation", f"{metrics.get('validation_score', 0)}")
                
            st.success("Blueprint generation successful and persisted to Snowflake. Ready for MCP consumption.")
