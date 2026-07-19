"""
Streamlit UI Dashboard Module
=============================
The primary user interface for StructZero, built on Streamlit.
This dashboard can be hosted locally or natively deployed into Snowflake via Streamlit in Snowflake (SiS).
"""
import streamlit as st
import sys
import os



from core.models import PlanningRequest
from core.pipeline import PlanningPipeline
from core.storage import StorageClient
from core.cortex_gateway import CortexGateway

# Page config
st.set_page_config(
    page_title="StructZero Enterprise Engineering Intelligence Platform", 
    page_icon="❄️", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

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
            
    st.divider()
    st.markdown("""
    ### About StructZero
    **StructZero Enterprise Engineering Intelligence Platform**
    
    Version: 1.0.0
    
    Developed by **Vishal Verma**
    
    🌐 [https://www.vishalverma.me/](https://www.vishalverma.me/)
    
    © 2026 Vishal Verma. All Rights Reserved.
    """)

# --- MAIN DASHBOARD ---
st.title("StructZero - Enterprise Engineering Intelligence Platform")
st.markdown("### Advanced AI Software Architecture Copilot")

tab_gen, tab_analytics, tab_batch = st.tabs(["🏗️ Architecture Generator", "📊 Decision Analytics (Cortex Analyst)", "🧪 Batch Tester"])

with tab_gen:
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
            enterprise_citations = []
            
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
                if status == "error" and "error" in state:
                    output_content = state["error"]
                elif status == "complete":
                    if "output" in state:
                        output_content = state["output"]
                    elif "citations" in state:
                        enterprise_citations = state["citations"]
                        output_content = f"✅ Retrieved **{len(enterprise_citations)}** documents from Cortex Search."
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
                
                # --- 1.5. ENTERPRISE KNOWLEDGE USED ---
                if enterprise_citations:
                    with st.expander("📚 Enterprise Knowledge Cited (Cortex Search)", expanded=True):
                        for cite in enterprise_citations:
                            score = cite.get('score', 0.0)
                            st.markdown(f"- ✓ **{cite['source']}** ({cite['cloud']} | {cite['compliance']}) - *Relevance: {score:.2f}*")
                
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
    
# --- GLOBAL FOOTER ---
st.divider()
with tab_analytics:
    st.markdown("### 📜 Searchable History")
    st.markdown("Browse and filter historical architecture blueprints generated across the enterprise.")
    
    try:
        # Fetch history data
        history_df = gateway.session.sql("SELECT * FROM ENTERPRISE_ANALYTICS_V ORDER BY BLUEPRINT_ID DESC").to_pandas()
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            search_proj = st.text_input("🔍 Search Project Name")
        with col2:
            cloud_options = ["All"] + list(history_df['CLOUD_TARGET'].dropna().unique()) if not history_df.empty and 'CLOUD_TARGET' in history_df else ["All"]
            cloud_filter = st.selectbox("☁️ Cloud Target", cloud_options)
        with col3:
            status_options = ["All"] + list(history_df['VALIDATION_STATUS'].dropna().unique()) if not history_df.empty and 'VALIDATION_STATUS' in history_df else ["All"]
            status_filter = st.selectbox("✅ Validation Status", status_options)
            
        # Apply Filters
        filtered_df = history_df.copy()
        if search_proj and not filtered_df.empty and 'PROJECT_NAME' in filtered_df:
            filtered_df = filtered_df[filtered_df['PROJECT_NAME'].str.contains(search_proj, case=False, na=False)]
        if cloud_filter != "All" and not filtered_df.empty and 'CLOUD_TARGET' in filtered_df:
            filtered_df = filtered_df[filtered_df['CLOUD_TARGET'] == cloud_filter]
        if status_filter != "All" and not filtered_df.empty and 'VALIDATION_STATUS' in filtered_df:
            filtered_df = filtered_df[filtered_df['VALIDATION_STATUS'] == status_filter]
            
        # Show Grid
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        # Detail View
        selected_id = st.text_input("Enter a BLUEPRINT_ID from above to view the full markdown:")
        if selected_id:
            try:
                bp_row = gateway.session.sql(f"SELECT DATA:raw_markdown::VARCHAR FROM BLUEPRINTS WHERE DATA:id::VARCHAR = '{selected_id}'").collect()
                if bp_row and bp_row[0][0]:
                    with st.expander(f"Full Blueprint: {selected_id}", expanded=True):
                        st.markdown(bp_row[0][0])
                else:
                    st.warning("Blueprint ID not found.")
            except Exception as e:
                st.error(f"Error fetching blueprint: {e}")
                
    except Exception as e:
        st.error(f"Could not load history: {e}")
        
    st.divider()

    st.markdown("### 🤖 Ask StructZero about Historical Data")
    st.markdown("Interact with historical architecture blueprints, quality metrics, and cost telemetry using natural language.")
    
    from core.analyst import AnalystClient
    if "analyst_client" not in st.session_state:
        st.session_state.analyst_client = AnalystClient(gateway.session)
        
    if "analyst_messages" not in st.session_state:
        st.session_state.analyst_messages = []
        
    for msg in st.session_state.analyst_messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.write(msg["content"][0]["text"])
            else:
                for content in msg["content"]:
                    if content["type"] == "text":
                        st.write(content["text"])
                    elif content["type"] == "sql":
                        st.code(content["statement"], language="sql")
                        # Show data
                        try:
                            df = gateway.session.sql(content["statement"]).to_pandas()
                            st.dataframe(df)
                        except Exception as e:
                            st.error(f"Execution error: {e}")
                        
    if chat_prompt := st.chat_input("E.g., Which cloud provider produced the highest architecture quality score?"):
        st.session_state.analyst_messages.append({"role": "user", "content": [{"type": "text", "text": chat_prompt}]})
        with st.chat_message("user"):
            st.write(chat_prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    response = st.session_state.analyst_client.send_message(st.session_state.analyst_messages)
                    if "message" in response:
                        msg_obj = response["message"]
                        st.session_state.analyst_messages.append(msg_obj)
                        
                        for content in msg_obj["content"]:
                            if content["type"] == "text":
                                st.write(content["text"])
                            elif content["type"] == "sql":
                                sql_query = content["statement"]
                                st.code(sql_query, language="sql")
                                # Automatically execute SQL to show the results
                                try:
                                    df = gateway.session.sql(sql_query).to_pandas()
                                    st.dataframe(df)
                                except Exception as e:
                                    st.error(f"Execution error: {e}")
                except Exception as e:
                    st.error(f"Error querying Analyst: {e}")

with tab_batch:
    st.markdown("### 🧪 Batch Architecture Tester")
    st.markdown("Run multiple architectural prompts sequentially. Each architecture will be generated, saved to Snowflake dynamically, and evaluated by an AI model.")
    
    batch_topic = st.text_input("Theme/Domain (Optional)", placeholder="e.g., Healthcare, FinTech, E-Commerce...")
    num_iterations = st.number_input("Number of Iterations", min_value=1, max_value=50, value=10)
    
    if st.button("Run Batch Test", type="primary"):
        st.info(f"Starting batch test for {num_iterations} iterations...")
        
        master_markdown = f"# StructZero Batch Test Report\n\nTotal Iterations: {num_iterations}\n\n"
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(num_iterations):
            status_text.text(f"Processing ({i+1}/{num_iterations}): Generating prompt...")
            
            # 0. Generate the prompt
            theme_instruction = f" in the {batch_topic} domain" if batch_topic.strip() else ""
            generate_prompt_query = f"Generate a unique, realistic enterprise software architecture design prompt{theme_instruction} for a new system. It should be 1-3 sentences. Output ONLY the prompt."
            p = gateway.complete(generate_prompt_query, model="claude-4-sonnet") or "Design a standard microservices application."
            
            status_text.text(f"Processing ({i+1}/{num_iterations}): {p[:50]}...")
                
            # 1. Generate short project name based on prompt
            name_prompt = f"Generate a very short 2-4 word project name based on this prompt: '{p}'. ONLY output the 2-4 words. Do not include quotes or any other text."
            project_name = gateway.complete(name_prompt, model="claude-4-sonnet") or f"Batch Project {i+1}"
            project_name = project_name.strip().replace('"', '').replace("'", "")
            
            # 2. Run pipeline
            req = PlanningRequest(
                project_name=project_name,
                prompt=p,
                cloud_target=cloud_target,
                compliance=compliance,
                model="Multi-Model"
            )
            
            blueprint = None
            reviews = None
            
            # Run silently without UI rendering to save space
            for state in pipeline.run(req):
                if state.get("status") == "finished":
                    blueprint = state["blueprint"]
                    reviews = state["reviews"]
                    break
                    
            if blueprint and reviews:
                # 3. Summarize and grade with another AI model
                eval_prompt = f"""
                You are evaluating an AI-generated architecture blueprint. 
                
                Initial User Prompt: {p}
                
                AI Reviewer Feedback (Flaws identified): 
                {reviews.get('critical', '')}
                {reviews.get('security', '')}
                {reviews.get('performance', '')}
                
                Final Improved Architecture Blueprint:
                {blueprint.raw_markdown}
                
                Please provide a Markdown response with:
                1. A short summary of the Initial Prompt.
                2. A short summary of what the AI reviewers suggested (flaws vs improvements).
                3. A rating out of 100 on how accurate the final architecture is based on the initial prompt.
                
                Format it nicely with headings.
                """
                
                st.write(f"Evaluating architecture for '{project_name}'...")
                evaluation = gateway.complete(eval_prompt, model="claude-4-sonnet")
                
                master_markdown += f"---\n\n## Project: {project_name}\n\n"
                master_markdown += evaluation + "\n\n"
                
            progress_bar.progress((i + 1) / num_iterations)
                
        status_text.success("Batch test completed!")
            
        st.download_button(
            label="Download Markdown Report",
            data=master_markdown,
            file_name="batch_results.md",
            mime="text/markdown"
        )

st.markdown("""
<div style='text-align: center; color: #8B949E; margin-top: 50px; padding: 20px; border-top: 1px solid #30363D;'>
    Developed by <a href='https://www.vishalverma.me/' target='_blank' style='color: #58A6FF; text-decoration: none;'><b>Vishal Verma</b></a>
</div>
""", unsafe_allow_html=True)
