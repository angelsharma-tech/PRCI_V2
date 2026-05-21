import streamlit as st
from phase_4_models.detection_engine_impl import DetectionEngineImpl
from phase_5_risk_engine.procrastination_risk_engine import ProcrastinationRiskEngine

# Page configuration
st.set_page_config(
    page_title="CORE:AI - Intelligent Mental Health Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING ---
st.markdown("""
<style>
    /* Main content area */
    .main {
        background-color: #F0F2F6;
        padding: 2rem;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: #FFFFFF;
        border-right: 1px solid #E0E0E0;
    }
    
    /* Title */
    .css-10trblm {
        color: #1E1E1E;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
    }

    /* Subheader */
    h2 {
        color: #4A4A4A;
        font-family: 'Helvetica Neue', sans-serif;
    }

    /* Text area */
    .stTextArea textarea {
        border: 1px solid #E0E0E0;
        border-radius: 0.5rem;
        background-color: #FFFFFF;
        font-size: 1rem;
    }

    /* Button */
    .stButton>button {
        background-image: linear-gradient(to right, #4B79A1, #283E51);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 0.5rem;
        font-size: 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        opacity: 0.9;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }

    /* Metrics */
    .stMetric {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 0.5rem;
        padding: 1rem;
    }
    
</style>
""", unsafe_allow_html=True)


# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configuration")
    
    st.info("**Note:** These settings are for advanced users and developers.")

    bert_path = st.text_input(
        "Two-head BERT checkpoint path",
        value="F:/sem8/PRCI_v2/legacy_model_pipeline/best.pt",
        help="Path to the best.pt or last.pt file for the BERT model."
    )
    
    demo_mode = st.toggle("Demo Mode", value=True)

    if st.button("Reset Configuration"):
        st.rerun()

    st.selectbox(
        "Root cause model",
        options=["ovr_logreg", "other_model_1", "other_model_2"],
        index=0
    )
    
    st.divider()
    st.caption("© 2024 CORE:AI Project")


# --- MAIN CONTENT ---
st.markdown("<h1 style='text-align: center; color: #1E1E1E;'>🧠 CORE:AI</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #4A4A4A;'>Intelligent Mental Health Analysis System</h3>", unsafe_allow_html=True)

st.markdown(
    "<p style='text-align: center; font-style: italic; color: #6C757D;'>"
    "This system provides insights based on your text input. It is not a substitute for professional medical advice."
    "</p>", unsafe_allow_html=True
)

st.divider()

# --- ANALYSIS SECTION ---
col1, col2 = st.columns([2, 1])

with col1:
    user_input = st.text_area(
        "Enter your current academic/mental state text:",
        placeholder="e.g., I keep delaying work even after planning everything...",
        height=150
    )
    
    analyze_button = st.button("Analyze Now 🚀")

with col2:
    st.image("https://i.imgur.com/OKVQu4g.png", width=200) # Placeholder for a nice graphic

# --- RESULTS ---
if analyze_button:
    if not user_input.strip():
        st.warning("Please enter some text to analyze.")
    else:
        try:
            # Initialize engines
            @st.cache_resource
            def load_engines():
                detection_engine = DetectionEngineImpl(emotion_model=None, root_model=None, extractor=None)
                risk_engine = ProcrastinationRiskEngine()
                return detection_engine, risk_engine

            detection_engine, risk_engine = load_engines()

            # Analysis
            with st.spinner("🤖 Analyzing your text..."):
                detection_result = detection_engine.predict(user_input)
                risk_result = risk_engine.assess([detection_result])

            st.subheader("🔍 Analysis Results")
            
            # --- Detection Analysis ---
            with st.container():
                st.markdown("**Detection Analysis**")
                c1, c2 = st.columns(2)
                c1.metric("Anxiety Signal", f"{detection_result.anxiety_prob:.2f}")
                c2.metric("Depression Signal", f"{detection_result.depression_prob:.2f}")
                
                st.write("**Identified Root Causes:**")
                if detection_result.root_causes:
                    for cause in detection_result.root_causes:
                        st.markdown(f"- *{cause}*")
                else:
                    st.markdown("- *None detected*")
                
                st.progress(detection_result.confidence, text=f"Confidence: {detection_result.confidence:.2f}")

            st.divider()

            # --- Risk Assessment ---
            with st.container():
                st.markdown("**Risk Assessment**")
                
                risk_color = {"LOW": "#28a745", "MEDIUM": "#ffc107", "HIGH": "#dc3545"}.get(risk_result.level, "#6c757d")
                
                st.markdown(f"### Risk Level: <span style='color:{risk_color}; font-weight:bold;'>{risk_result.level}</span>", unsafe_allow_html=True)
                
                st.write(f"**Risk Score:** {risk_result.score:.3f}")
                st.write(f"**Trend:** {risk_result.trend}")
                
                if risk_result.contributing_factors:
                    st.write("**Main Contributing Factors:**")
                    for factor in risk_result.contributing_factors:
                        st.markdown(f"- {factor}")

            st.divider()

            # --- Recommendations ---
            if risk_result.recommendations:
                st.subheader("💡 Suggested Academic Support")
                for rec in risk_result.recommendations:
                    st.success(f"**{rec}**")
            
            # --- Feedback ---
            st.subheader("Was this analysis helpful?")
            if st.button("👍 Yes, it was helpful"):
                st.balloons()
                st.success("Thank you for your feedback!")
            if st.button("👎 No, not really"):
                st.info("We appreciate your feedback. We are constantly improving.")

        except Exception as e:
            st.error(f"An error occurred during analysis: {e}")
            st.info("Please try rephrasing your input or contact support.")

