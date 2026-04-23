import os

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from upgrade_pipeline.explainability import explain_root_causes_top_words
from upgrade_pipeline.preprocess import TwoHeadBertInference
from upgrade_pipeline.planner import generate_planner
from upgrade_pipeline.risk_engine import calculate_risk_score
from upgrade_pipeline.root_cause_model import RootCauseClassifier
from upgrade_pipeline.tracker import SlidingWindowTracker, TrackerEntry
from upgrade_pipeline.web_agent import get_suggestions
from upgrade_pipeline.report_generator import generate_pdf_report
from upgrade_pipeline.email_sender import send_email


ROOT_CAUSE_DATASET = "phase_3_data/raw/root_cause/procrastination_dataset.csv"


def _risk_badge(level: str) -> str:
    lvl = str(level or "").upper()
    if lvl == "LOW":
        color = "#2E7D32"
    elif lvl == "MODERATE":
        color = "#EF6C00"
    else:
        color = "#C62828"
    return f"<span style='color:{color}; font-weight:700'>{lvl}</span>"


def _final_insight(depression: float, anxiety: float, top_root: str, risk_level: str) -> str:
    dep_word = "low" if depression < 0.33 else "moderate" if depression < 0.66 else "high"
    anx_word = "low" if anxiety < 0.33 else "moderate" if anxiety < 0.66 else "high"
    root = (top_root or "none").replace("_", " ")
    rl = (risk_level or "LOW").upper()
    return (
        f"You are showing {anx_word} anxiety and {dep_word} depressive signals. "
        f"Your main delay driver looks like **{root}**. "
        f"Overall this leads to a **{rl}** risk level."
    )


def _planner_suggestions(top_cause: str):
    mapping = {
        "perfectionism": [
            "Define a 'good enough' target before starting.",
            "Timebox: 25 minutes draft, then refine later.",
        ],
        "fear_of_failure": [
            "Start with a low-stakes first step (outline / rough draft).",
            "Write the smallest deliverable version first.",
        ],
        "lack_of_interest": [
            "Attach a small reward after completing a 20-minute focus sprint.",
            "Connect the task to a personal goal (why it matters).",
        ],
        "environment_distraction": [
            "Remove one distraction (phone away / site blocker) for 30 minutes.",
            "Prepare a clean workspace and set a single-task timer.",
        ],
        "dopamine_addiction": [
            "Replace quick scrolling with a planned short break after a sprint.",
            "Use app limits during study blocks.",
        ],
        "none": [
            "Break the task into 2-3 micro-steps and start with the easiest.",
        ],
    }
    return mapping.get(top_cause, mapping["none"])


@st.cache_resource
def load_root_cause_model(model_type: str = "ovr_logreg") -> RootCauseClassifier:
    df = pd.read_csv(ROOT_CAUSE_DATASET)
    clf = RootCauseClassifier(model_type=model_type)
    clf.fit(df, text_col="statement")
    return clf


def main():
    # --- PAGE CONFIGURATION ---
    st.set_page_config(
    page_title="CORE:AI - Intelligent Mental Health Analysis",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING ---
st.markdown("""
<style>
    /* --- GLOBAL STYLES --- */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f5f7fb 0%, #e8ecff 100%);
    }
    
    .main .block-container {
        max-width: 1200px;
        padding-top: 3rem;
        padding-bottom: 5rem;
    }

    /* --- GLASSMORPHISM CARD --- */
    .glass-card {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(12px) saturate(180%);
        -webkit-backdrop-filter: blur(12px) saturate(180%);
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 10px 40px 0 rgba(31, 38, 135, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.3);
        margin-bottom: 2.5rem;
        transition: transform 0.3s ease;
    }
    .glass-card:hover {
        transform: translateY(-5px);
    }

    /* --- HERO SECTION --- */
    .hero-section {
        text-align: center;
        padding: 4rem 0 3rem 0;
    }
    .hero-section .icon {
        font-size: 72px;
        margin-bottom: 1rem;
        display: block;
    }
    .hero-section h1 {
        font-size: 64px !important;
        font-weight: 800 !important;
        background: linear-gradient(90deg, #7F00FF 0%, #E100FF 50%, #00DBDE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -2px;
        margin-bottom: 0.5rem !important;
    }
    .hero-section p {
        font-size: 1.4rem;
        color: #5a647d;
        font-weight: 400;
        letter-spacing: 0.5px;
    }

    /* --- TEXT AREA --- */
    .stTextArea label {
        font-weight: 600 !important;
        color: #1e293b !important;
        margin-bottom: 0.8rem !important;
        font-size: 1.1rem !important;
    }
    .stTextArea textarea {
        height: 180px !important;
        border-radius: 15px !important;
        border: 1px solid rgba(0,0,0,0.05) !important;
        background-color: rgba(255,255,255,0.7) !important;
        padding: 1.2rem !important;
        font-size: 1.05rem !important;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
    }
    .stTextArea textarea:focus {
        border-color: #7F00FF !important;
        box-shadow: 0 0 0 4px rgba(127, 0, 255, 0.1) !important;
    }

    /* --- BUTTON --- */
    div.stButton > button {
        border-radius: 50px !important;
        padding: 1rem 3rem !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        color: white !important;
        background: linear-gradient(90deg, #7F00FF 0%, #00DBDE 100%) !important;
        border: none !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 10px 25px rgba(127, 0, 255, 0.3) !important;
        width: auto !important;
        margin-top: 1rem !important;
    }
    div.stButton > button:hover {
        transform: scale(1.08) translateY(-2px) !important;
        box-shadow: 0 15px 35px rgba(127, 0, 255, 0.4) !important;
    }

    /* --- SIDEBAR --- */
    section[data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(0,0,0,0.05);
    }
    section[data-testid="stSidebar"] h1 {
        font-size: 24px !important;
        color: #1e293b !important;
    }

    /* --- METRICS --- */
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 14px !important;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* --- TITLES & SUBHEADERS --- */
    h2, h3 {
        color: #1e293b !important;
        font-weight: 700 !important;
    }

    /* --- ANIMATIONS --- */
    .result-card {
        animation: slideUp 0.6s cubic-bezier(0.23, 1, 0.32, 1);
    }
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1>⚙️ Configuration</h1>", unsafe_allow_html=True)
    st.divider()

    with st.expander("**🤖 Model Paths**", expanded=True):
        default_ckpt = "F:/sem8/PRCI_v2/legacy_model_pipeline/outputs/twohead/best.pt"
        ckpt_path = st.text_input(
            "Two-head BERT Path",
            value=default_ckpt,
            label_visibility="visible"
        )
    
    with st.expander("**🛠️ Parameters**"):
        demo_mode = st.toggle("Enable Demo Mode", value=False)
        model_type = st.selectbox("Root cause model", ["ovr_logreg", "xgboost"], index=0)

    if demo_mode:
        st.sidebar.markdown("### 🧪 Demo Cases")
        col1, col2 = st.sidebar.columns(2)
        if col1.button("Anxiety", use_container_width=True):
            st.session_state.input_text = "I feel nervous about tomorrow and deadlines make me anxious. My mind keeps racing."
            st.session_state.run_analysis = True
        if col2.button("Depression", use_container_width=True):
            st.session_state.input_text = "Nothing excites me anymore. I feel empty and tired all the time, and life feels meaningless lately."
            st.session_state.run_analysis = True
        if col1.button("Procrastination", use_container_width=True):
            st.session_state.input_text = "I keep delaying my assignment even after planning. I end up scrolling on my phone instead of starting."
            st.session_state.run_analysis = True

    st.divider()
    if st.sidebar.button("🔄 Reset App", use_container_width=True):
        st.session_state.input_text = ""
        st.session_state.tracker = SlidingWindowTracker(window_size=7)
        st.session_state.run_analysis = False
        st.rerun()
    
    st.caption("CORE:AI v2.0 • Premium Edition")

# --- MAIN CONTENT ---

# --- HEADER ---
st.markdown("""
<div class="hero-section">
    <span class="icon">🧠</span>
    <h1>CORE:AI</h1>
    <p>Intelligent Mental Health Analysis & Support Dashboard</p>
</div>
""", unsafe_allow_html=True)

# --- INPUT SECTION ---
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    if "input_text" not in st.session_state:
        st.session_state.input_text = ""
    if "run_analysis" not in st.session_state:
        st.session_state.run_analysis = False
    if "tracker" not in st.session_state:
        st.session_state.tracker = SlidingWindowTracker(window_size=7)

    text = st.text_area(
        "Describe your current academic or mental situation:",
        placeholder="e.g., I feel overwhelmed with my assignments and can't seem to start...",
        key="input_text"
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        analyze_clicked = st.button("Analyze Now 🚀")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- ANALYSIS & RESULTS ---
should_run = bool(analyze_clicked or st.session_state.run_analysis)
if analyze_clicked:
    st.session_state.run_analysis = True

if should_run:
    if not text.strip():
        st.warning("Please enter some text to analyze.")
        st.session_state.run_analysis = False
    else:
        # All backend logic remains here
        with st.spinner("🧠 AI is analyzing your thoughts..."):
            bert = TwoHeadBertInference(ckpt_path).load()
            mental = bert.predict(text)

            root_model = load_root_cause_model(model_type=model_type)
            root_pred = root_model.predict_proba(text)
            root_probs = root_pred.probabilities

            risk = calculate_risk_score(
                depression_score=mental.depression_score,
                anxiety_score=mental.anxiety_score,
                root_cause_probs=root_probs,
            )

            top_root = max(root_probs.items(), key=lambda kv: kv[1])[0] if root_probs else "none"
            tracker: SlidingWindowTracker = st.session_state.tracker
            tracker.add(
                TrackerEntry(
                    text=text,
                    depression_score=mental.depression_score,
                    anxiety_score=mental.anxiety_score,
                    risk_score=risk.score,
                    top_root_cause=top_root,
                )
            )

            planner_type, plan = generate_planner(
                mental.depression_score,
                mental.anxiety_score,
                root_probs,
            )

            suggestions = get_suggestions(top_root)
        
        # --- DISPLAY RESULTS IN CARDS ---
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        
        # Row 1: Scores & Risk
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("🧠 Mental Health Scores")
            c1, c2 = st.columns(2)
            c1.metric("Depression", f"{mental.depression_score:.3f}")
            c2.metric("Anxiety", f"{mental.anxiety_score:.3f}")
            st.markdown(f"<p style='color:#64748b; font-size:14px;'>Analysis based on input text length: {len(text)} chars</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("⚠️ Risk Assessment")
            risk_color = {"LOW": "#10b981", "MODERATE": "#f59e0b", "HIGH": "#ef4444"}.get(risk.level, "#64748b")
            st.markdown(f"""
                <div style="background: {risk_color}15; border-radius: 12px; padding: 1.5rem; border: 1px solid {risk_color}30;">
                    <h2 style="color: {risk_color} !important; margin: 0; font-size: 32px;">{risk.level} RISK</h2>
                    <p style="color: #475569; margin: 10px 0 0 0; font-size: 18px;">Score: <b>{risk.score:.3f}</b></p>
                </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Row 2: Charts & Plans
        col3, col4 = st.columns(2)
        with col3:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("📊 Root Cause Analysis")
            if root_probs:
                import plotly.express as px
                labels = list(root_probs.keys())
                values = [root_probs[k] for k in labels]
                # Better looking horizontal bar chart with Plotly
                df_chart = pd.DataFrame({"Cause": labels, "Probability": values})
                fig = px.bar(df_chart, x="Probability", y="Cause", orientation='h',
                             color="Probability", color_continuous_scale="Purples",
                             range_x=[0, 1])
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    height=300,
                    margin=dict(l=0, r=0, t=0, b=0),
                    yaxis={'categoryorder':'total ascending'}
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.markdown("- *None detected*")
            st.markdown('</div>', unsafe_allow_html=True)

        with col4:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("📅 Actionable Plan")
            interventions = _planner_suggestions(top_root)
            if interventions:
                for i, rec in enumerate(interventions):
                    st.markdown(f"""
                        <div style="background: #10b98110; border-left: 4px solid #10b981; padding: 12px 20px; border-radius: 8px; margin-bottom: 12px;">
                            <span style="color: #065f46; font-weight: 500;">{rec}</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No specific recommendations at this time.")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # --- GENERATE REPORT SECTION ---
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📄 Generate Detailed Report")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        user_name = st.text_input("Enter your name", placeholder="John Doe")
    with col_r2:
        user_email = st.text_input("Enter your email", placeholder="john@example.com")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("Download Report 📥", use_container_width=True):
            if not user_name or not user_email:
                st.error("Please enter name and email to generate the report.")
            else:
                with st.spinner("Generating your PDF report..."):
                    try:
                        from upgrade_pipeline.report_generator import generate_pdf_report
                        
                        pdf_bytes = generate_pdf_report(
                            name=user_name,
                            email=user_email,
                            depression=mental.depression_score,
                            anxiety=mental.anxiety_score,
                            risk_level=risk.level,
                            root_causes=root_probs,
                            interventions=interventions
                        )

                        st.download_button(
                            label="Click here to Download PDF",
                            data=pdf_bytes,
                            file_name=f"mental_health_report_{user_name.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        st.success("Report generated successfully!")
                    except Exception as e:
                        st.error(f"Error generating report: {str(e)}")
                        st.info("Ensure 'reportlab' is installed: pip install reportlab")

    with col_btn2:
        if st.button("Send to Email 📧", use_container_width=True):
            if not user_name or not user_email:
                st.error("Please enter name and email to send the report.")
            else:
                with st.spinner("Generating and sending email..."):
                    try:
                        from upgrade_pipeline.report_generator import generate_pdf_report
                        from upgrade_pipeline.email_sender import send_email_with_pdf
                        
                        pdf_bytes = generate_pdf_report(
                            name=user_name,
                            email=user_email,
                            depression=mental.depression_score,
                            anxiety=mental.anxiety_score,
                            risk_level=risk.level,
                            root_causes=root_probs,
                            interventions=interventions
                        )
                        
                        send_email_with_pdf(user_email, pdf_bytes, user_name)
                        st.success(f"Email sent successfully to {user_email} ✅")
                    except Exception as e:
                        st.error(f"Email failed: {str(e)}")
                        st.info("Ensure SENDER_EMAIL and APP_PASSWORD environment variables are set.")

    st.markdown('</div>', unsafe_allow_html=True)
    
    st.session_state.run_analysis = False


if __name__ == "__main__":
    main()
