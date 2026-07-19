import streamlit as st
import sys
import os



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
            from core.parser import parse_blueprint
            parsed = parse_blueprint(blueprint.raw_markdown)
            
            # --- 1. APPROVAL BANNER ---
            val_status = val.status if val else "UNKNOWN"
            banner_color = "🟢" if "APPROVED" in val_status else "🔴"
            st.markdown(f"## {banner_color} {val_status}")
            
            # --- 2. EXECUTIVE DASHBOARD METRICS ---
            st.markdown("### Architecture Quality")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Overall Score", f"{metrics.get('blueprint_score', 0)}")
            c2.metric("Security", f"{metrics.get('security_score', 0)}")
            c3.metric("Performance", f"{metrics.get('performance_score', 0)}")
            c4.metric("Est. Cost", f"${metrics.get('estimated_cost_usd', 0.0):.4f}")
            c5.metric("Pipeline Time", f"{metrics.get('total_latency_ms', 0)/1000:.1f}s")
            
            st.divider()
            
            # --- 3. EXECUTIVE SUMMARY ---
            st.markdown("### Executive Summary")
            st.write(parsed.executive_summary)
            
            st.divider()
            
            # --- 4. ARCHITECTURE DIAGRAM ---
            if parsed.graphviz:
                st.markdown("### Architecture Diagram")
                st.graphviz_chart(parsed.graphviz)
                st.divider()
                
            # --- 5. TABS ---
            st.markdown("### Architecture Overview")
            t1, t2, t3, t4, t5 = st.tabs(["Components", "Security", "Performance", "Risks", "Roadmap"])
            with t1: st.write(parsed.components)
            with t2: st.write(parsed.security)
            with t3: st.write(parsed.performance)
            with t4: st.write(parsed.risks)
            with t5: st.write(parsed.roadmap)
            
            st.divider()
            
            # --- 6. AI REVIEW BOARD ---
            st.markdown("### AI Review Board Findings")
            
            votes = reviews.get("votes", {})
            v_crit = votes.get("critical", "Unknown")
            v_sec = votes.get("security", "Unknown")
            v_perf = votes.get("performance", "Unknown")
            
            with st.expander(f"🔴 Security Review", expanded=False):
                st.write(v_sec)
            with st.expander(f"🟣 Performance Review", expanded=False):
                st.write(v_perf)
            with st.expander(f"🟠 Critical Review", expanded=False):
                st.write(v_crit)
                
            st.divider()
            
            # --- 7. DECISION LOG & ACTIONS ---
            c_log, c_act = st.columns(2)
            with c_log:
                st.markdown("### Decision Log")
                st.write(parsed.decision_log)
            with c_act:
                st.markdown("### Recommended Actions")
                st.write(parsed.recommended_actions)
                
            st.divider()
            
            # --- 8. ENGINEERING TELEMETRY ---
            st.markdown("### Engineering Telemetry")
            
            col_score, col_tele = st.columns(2)
            with col_score:
                st.markdown("**Compliance & Quality**")
                # Ensure values are between 0.0 and 1.0 for st.progress
                overall_p = max(0.0, min(1.0, metrics.get("blueprint_score", 0)/100))
                sec_p = max(0.0, min(1.0, metrics.get("security_score", 0)/100))
                perf_p = max(0.0, min(1.0, metrics.get("performance_score", 0)/100))
                
                st.progress(overall_p, text=f"Overall {metrics.get('blueprint_score', 0)}")
                st.progress(sec_p, text=f"Security {metrics.get('security_score', 0)}")
                st.progress(perf_p, text=f"Performance {metrics.get('performance_score', 0)}")
            
            with col_tele:
                st.markdown("**Enterprise Metrics**")
                t_c1, t_c2 = st.columns(2)
                t_c1.metric("Docs Searched", f"{metrics.get('knowledge_documents_searched', 0)}")
                t_c2.metric("Chunks Extracted", f"{metrics.get('knowledge_chunks_searched', 0)}")
                t_c1.metric("Cortex Calls", f"{metrics.get('cortex_calls', 0)}")
                t_c2.metric("Tokens", f"{metrics.get('estimated_input_tokens', 0) + metrics.get('estimated_output_tokens', 0)}")
            
            st.divider()
            
            # --- 9. RAW BLUEPRINT ---
            with st.expander("▼ Full Technical Blueprint (Raw Output)", expanded=False):
                st.markdown(blueprint.raw_markdown)
                
            st.success("Blueprint generation successful and persisted to Snowflake. Ready for MCP consumption.")
