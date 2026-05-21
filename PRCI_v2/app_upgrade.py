import os
import pandas as pd
import streamlit as st
import sys
import traceback

# Import new architecture components
from config import (
    ROOT_CAUSE_DATASET, DEFAULT_MODEL_PATH, MODEL_CONFIG,
    SVG_ICONS, UI_COLORS, RISK_COLORS, SCORE_THRESHOLDS,
    INTERVENTION_TEMPLATES, INSIGHT_TEMPLATES
)
from utils.ui_helpers import (
    safe_html, create_risk_badge, create_action_card,
    create_motivational_card, create_sidebar_card,
    display_error_message, display_success_message,
    get_icon
)
from utils.html_utils import generate_css_styles
from utils.chart_utils import (
    create_risk_gauge_chart, create_trend_chart,
    create_comparison_bar_chart, create_fallback_chart,
    is_plotly_available
)
from utils.logging_utils import get_logger, PerformanceTimer
from utils.error_handling import (
    handle_dataset_errors, handle_model_errors, handle_chart_errors,
    handle_report_errors, handle_email_errors,
    validate_file_exists, validate_model_file, validate_dataset_file,
    DatasetError, ModelError, ChartError, ReportError, EmailError
)
from huggingface_hub import hf_hub_download
from services.inference_service import get_inference_service
from services.scoring_service import get_scoring_service
from services.intervention_service import get_intervention_service
from services.report_service import get_report_service

# Legacy imports (maintained for backward compatibility)
from upgrade_pipeline.explainability import explain_root_causes_top_words
from upgrade_pipeline.tracker import SlidingWindowTracker, TrackerEntry
from upgrade_pipeline.report_generator import generate_pdf_report
from upgrade_pipeline.email_sender import send_email
from upgrade_pipeline.core.inference_engine import InferenceEngine
from upgrade_pipeline.conversation import ConversationEngine

# Initialize logger
logger = get_logger(__name__)

# HuggingFace model hosting config
HF_REPO_ID = os.getenv(
    "HF_REPO_ID",
    "angelsharma-tech/prci-v2-models"
)
HF_MODEL_FILENAME = os.getenv("HF_MODEL_FILENAME", "best_fp16.pt")


def _ensure_model_downloaded(local_path: str) -> str:
    """Download model from HuggingFace Hub if not present locally.
    This is now called lazily during the first inference request.
    """
    if os.path.isfile(local_path):
        return local_path

    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        # Check if the path is the default one or a custom one
        filename = os.path.basename(local_path)
        if filename != HF_MODEL_FILENAME:
            # If it's a custom path and doesn't exist, we can't download it from HF
            # unless we assume it's meant to be the HF model.
            logger.warning(f"Custom model path {local_path} not found. Attempting HF download of {HF_MODEL_FILENAME} as fallback.")
            filename = HF_MODEL_FILENAME

        downloaded = hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=filename,
            local_dir=os.path.dirname(local_path),
            local_dir_use_symlinks=False,
        )
        logger.info(f"Model downloaded from HuggingFace: {downloaded}")
        return downloaded
    except Exception as e:
        logger.warning(f"HF download failed ({e}). Falling back to local path.")
        return local_path


# =========================================================
# BACKWARD COMPATIBILITY LAYER
# =========================================================
# Legacy icon variables for backward compatibility
BRAIN_ICON = SVG_ICONS["brain"]
CORE_AI_LOGO = SVG_ICONS["core_ai_logo"]
DEPRESSION_ICON = SVG_ICONS["depression"]
ANXIETY_ICON = SVG_ICONS["anxiety"]
INSIGHT_ICON = SVG_ICONS["insight"]
RUN_ICON = SVG_ICONS["run"]
SHIELD_ICON = SVG_ICONS["shield"]
LEAF_ICON = SVG_ICONS["leaf"]
HEART_ICON = SVG_ICONS["heart"]


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
    root = (top_root or "none").replace("_", " ").lower()
    rl = (risk_level or "LOW").upper()
    
    # Softer phrasing
    if rl == "LOW" and top_root == "none":
        return "You seem to be handling things well overall. Keep maintaining your current positive habits."
    
    return (
        f"You seem a bit overwhelmed with {anx_word} anxiety and {dep_word} depressive signals. "
        f"It looks like <strong>{root}</strong> patterns might be contributing to your current state. "
        f"Focusing on these areas could help you find more balance."
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


@handle_dataset_errors(default_return=None)
@st.cache_resource
def load_inference_engine(
    ckpt_path: str,
    dataset_path: str = ROOT_CAUSE_DATASET,
    model_type: str = "ovr_logreg",
) -> InferenceEngine:
    """Cached factory for centralized inference engine.
    Initializes lazily only when requested.
    """
    try:
        # 1. Lazy Download/Verification
        actual_ckpt_path = _ensure_model_downloaded(ckpt_path)

        # 2. Validation
        validate_file_exists(actual_ckpt_path, f"Model checkpoint not found: {actual_ckpt_path}")
        validate_dataset_file(dataset_path)
        
        # 3. Core Engine Initialization
        logger.info(f"Initializing InferenceEngine with model: {model_type}...")
        return InferenceEngine(
            bert_ckpt_path=actual_ckpt_path,
            root_cause_dataset_path=dataset_path,
            root_cause_model_type=model_type,
            root_cause_model_dir=os.path.join(
                os.path.dirname(os.path.abspath(dataset_path)),
                "serialized_root_model",
            ),
        )
    except Exception as e:
        logger.error(f"Failed to load inference engine: {e}")
        raise ModelError(f"Failed to load inference engine: {str(e)}")


@handle_model_errors(default_return=None)
def _ensure_conversation_engine(ckpt_path: str, model_type: str) -> ConversationEngine:
    """Lazy-initialize or return existing ConversationEngine from session state.
    This is the production-grade entry point for AI functionality.
    """
    try:
        state = st.session_state

        # Detect config changes that require rebuilding engine
        rebuild = (
            "conversation_engine" not in state
            or getattr(state, "_ce_ckpt", None) != ckpt_path
            or getattr(state, "_ce_model_type", None) != model_type
        )

        if rebuild:
            # Use the cached resource loader
            inf = load_inference_engine(ckpt_path, ROOT_CAUSE_DATASET, model_type)

            if inf is None:
                st.error("Model checkpoint missing or corrupted.")
                return None

            # Wrap in the high-level conversation logic
            state.conversation_engine = ConversationEngine(
                inf,
                max_history=MODEL_CONFIG["conversation_max_history"]
            )
            state._ce_ckpt = ckpt_path
            state._ce_model_type = model_type
            logger.info(f"Refreshed conversation engine context: {model_type}")

        return state.conversation_engine
    except Exception as e:
        logger.error(f"Failed to ensure conversation engine: {e}")
        raise ModelError(f"Failed to initialize conversation engine: {str(e)}")


@handle_chart_errors(default_return=None)
def safe_html(content: str):
    """Safe HTML rendering with error handling"""
    try:
        st.markdown(content.strip(), unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"HTML rendering failed: {e}")
        st.error("Content rendering failed. Please try refreshing.")


def main():
    # --- PAGE CONFIGURATION ---
    st.set_page_config(
        page_title="CORE:AI Dashboard",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # --- CSS STYLING ---
    st.markdown("""
    <style>
        /* --- TRAE STRICT REBUILD (PHASE 3B.4) --- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Manrope:wght@600;800&family=Poppins:wght@400;600;700&display=swap');

        :root {
            --bg-main: radial-gradient(circle at top left, #071426 0%, #030712 45%, #000814 100%);
            --glass-bg: rgba(255, 255, 255, 0.03);
            --glass-border: rgba(255, 255, 255, 0.08);
            --cyan-accent: #00E5FF;
            --purple-accent: #8B5CF6;
            --text-primary: #F8FAFC;
            --text-muted: #94A3B8;
            --card-radius: 24px;
            --nav-active-bg: rgba(0, 229, 255, 0.08);
        }

        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', sans-serif;
            background: var(--bg-main) !important;
            color: var(--text-primary);
        }

        /* Subtle Glow Overlays */
        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: radial-gradient(circle at 80% 20%, rgba(0, 229, 255, 0.05) 0%, transparent 50%),
                        radial-gradient(circle at 20% 80%, rgba(139, 92, 246, 0.05) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }

        .main .block-container {
            max-width: 1400px;
            padding: 1rem 3rem !important;
            z-index: 1;
        }

        /* --- STRICT GLASS CARDS --- */
        .glass-card {
            background: var(--glass-bg);
            backdrop-filter: blur(14px);
            border: 1px solid var(--glass-border);
            border-radius: var(--card-radius);
            padding: 24px;
            transition: all 0.25s ease;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            position: relative;
            overflow: hidden;
        }
        .glass-card::after {
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, transparent 100%);
            pointer-events: none;
        }
        .glass-card:hover {
            transform: translateY(-2px);
            border-color: rgba(0, 229, 255, 0.3);
            box-shadow: 0 12px 48px rgba(0, 229, 255, 0.15);
        }

        /* --- TYPOGRAPHY HIERARCHY --- */
        h1 { font-family: 'Manrope', sans-serif; font-size: 48px !important; font-weight: 800 !important; letter-spacing: -1.5px !important; margin-bottom: 0.5rem !important; }
        .card-title-strict { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; color: var(--text-muted); margin-bottom: 12px; }
        .score-value-strict { font-family: 'Manrope', sans-serif; font-size: 48px; font-weight: 800; line-height: 1; margin: 8px 0; color: #fff; }
        .label-muted { font-size: 14px; color: var(--text-muted); }

        /* --- SIDEBAR REBUILD --- */
        [data-testid="stSidebar"] {
            background: rgba(3, 7, 18, 0.98) !important;
            backdrop-filter: blur(25px);
            border-right: 1px solid var(--glass-border) !important;
            width: 320px !important;
        }
        
        .sidebar-logo-area { padding: 1.5rem 0; margin-bottom: 1.5rem; border-bottom: 1px solid var(--glass-border); }
        
        /* Sidebar Navigation Item */
        .nav-item {
            display: flex; align-items: center; gap: 12px;
            padding: 12px 16px; border-radius: 12px;
            color: var(--text-muted); cursor: pointer;
            transition: all 0.2s; margin-bottom: 4px;
        }
        .nav-item:hover, .nav-item.active {
            background: rgba(255,255,255,0.05); color: #fff;
            box-shadow: inset 0 0 10px rgba(255,255,255,0.02);
        }
        .nav-item.active { border-left: 3px solid var(--cyan-accent); }

        .stButton > button {
            background: var(--glass-bg) !important;
            border: 1px solid var(--glass-border) !important;
            color: var(--text-primary) !important;
            border-radius: 12px !important;
            padding: 10px 20px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
            text-align: left !important;
            width: 100% !important;
            font-size: 14px !important;
        }
        .stButton > button:hover {
            border-color: var(--cyan-accent) !important;
            box-shadow: 0 0 20px rgba(0, 229, 255, 0.15) !important;
            background: rgba(0, 229, 255, 0.08) !important;
            transform: translateX(2px);
        }

        /* --- SCORE CARDS --- */
        .icon-box-strict {
            width: 44px; height: 44px; border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            background: rgba(255,255,255,0.02);
            border: 1px solid var(--glass-border);
            margin-bottom: 12px;
        }
        .sparkline-container { height: 45px; margin-top: 15px; width: 100%; opacity: 0.8; }
        
        @keyframes glow-pulse {
            0% { filter: drop-shadow(0 0 2px var(--glow-color)); }
            50% { filter: drop-shadow(0 0 8px var(--glow-color)); }
            100% { filter: drop-shadow(0 0 2px var(--glow-color)); }
        }
        .glow-line { animation: glow-pulse 3s infinite ease-in-out; }

        /* --- CHAT BUBBLES --- */
        [data-testid="stChatMessage"] { 
            background: transparent !important; 
            padding: 0 !important;
            margin-bottom: 2rem !important; 
        }
        .chat-bubble-assistant {
            background: rgba(13, 22, 40, 0.6) !important;
            backdrop-filter: blur(10px);
            padding: 1.5rem; border-radius: 4px 24px 24px 24px;
            border: 1px solid var(--glass-border);
            box-shadow: 0 4px 24px rgba(0,0,0,0.2);
        }
        .chat-bubble-user {
            background: rgba(139, 92, 246, 0.05) !important;
            backdrop-filter: blur(10px);
            padding: 1.2rem; border-radius: 24px 4px 24px 24px;
            border: 1px solid rgba(139, 92, 246, 0.2);
            box-shadow: 0 4px 24px rgba(139, 92, 246, 0.05);
        }

        /* --- FLOATING INPUT --- */
        .stChatInputContainer {
            padding: 0 !important;
            background: transparent !important;
        }
        [data-testid="stChatInput"] {
            position: fixed; bottom: 40px; left: 55%; transform: translateX(-50%);
            width: 60%; max-width: 800px; z-index: 1000;
        }
        [data-testid="stChatInput"] > div {
            background: rgba(10, 18, 32, 0.8) !important;
            backdrop-filter: blur(20px); border-radius: 100px !important;
            padding: 8px 16px !important; border: 1px solid var(--glass-border) !important;
            box-shadow: 0 20px 60px rgba(0,0,0,0.6);
        }
        [data-testid="stChatInput"] textarea {
            color: #fff !important;
            font-size: 15px !important;
        }
        [data-testid="stChatInput"] button {
            background: var(--cyan-accent) !important; color: #030712 !important;
            border-radius: 50% !important; width: 40px !important; height: 40px !important;
            transition: all 0.2s;
        }
        [data-testid="stChatInput"] button:hover {
            transform: scale(1.1);
            box-shadow: 0 0 15px var(--cyan-accent);
        }

        /* --- ACTION CARDS --- */
        .action-card-strict {
            background: var(--glass-bg); border: 1px solid var(--glass-border);
            border-radius: 20px; padding: 20px; display: flex; align-items: center;
            gap: 18px; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer;
        }
        .action-card-strict:hover {
            background: rgba(0, 229, 255, 0.04); border-color: rgba(0, 229, 255, 0.4);
            transform: translateY(-3px) translateX(4px);
            box-shadow: 0 10px 30px rgba(0, 229, 255, 0.1);
        }

        /* Header Icons */
        .header-icon-btn {
            width:42px; height:42px; border-radius:12px; 
            background:rgba(255,255,255,0.03); 
            display:flex; align-items:center; justify-content:center; 
            border:1px solid var(--glass-border); 
            cursor:pointer; transition: all 0.2s;
            color: var(--text-muted);
        }
        .header-icon-btn:hover {
            background: rgba(255,255,255,0.06);
            border-color: var(--cyan-accent);
            color: var(--cyan-accent);
            box-shadow: 0 0 15px rgba(0, 229, 255, 0.1);
        }

        /* --- HIDE STREAMLIT --- */
        #MainMenu, footer, header { visibility: hidden; }
        .stDeployButton { display:none; }
    </style>
    """, unsafe_allow_html=True)

    # --- SIDEBAR ---
    # Logo Area
    sidebar_logo_html = (
        f'<div class="sidebar-logo-area">'
        f'<div style="display:flex; align-items:center; gap:14px; padding-left:10px;">'
        f'<span>{CORE_AI_LOGO}</span>'
        f'<div style="font-family:\'Manrope\',sans-serif; font-size:28px; font-weight:800;'
        f' letter-spacing:2px; color:white;">CORE:AI</div>'
        f'</div></div>'
    )
    st.sidebar.markdown(sidebar_logo_html, unsafe_allow_html=True)

    # Navigation
    st.sidebar.markdown('<div class="card-title-strict" style="margin-left:10px;">CORE</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f'<div class="nav-item active"><span>{BRAIN_ICON}</span> <span>Analysis Dashboard</span></div>', unsafe_allow_html=True)
    
    st.sidebar.markdown('<div class="card-title-strict" style="margin-top:2rem; margin-left:10px;">Settings</div>', unsafe_allow_html=True)
    with st.sidebar.expander("Model Configuration", expanded=False):
        _project_root = os.path.dirname(os.path.abspath(__file__))
        default_ckpt = os.path.join(_project_root, "legacy_model_pipeline", "outputs", "twohead", "best.pt")
        ckpt_path = st.text_input("BERT Checkpoint", value=default_ckpt, label_visibility="collapsed")
        # Optimization: Moved _ensure_model_downloaded to lazy loader to speed up startup
        model_type = st.selectbox("Analysis Model", ["ovr_logreg", "xgboost"], index=0, label_visibility="collapsed")

    st.sidebar.markdown('<div style="padding: 0 10px; margin-top: 1rem;">', unsafe_allow_html=True)
    demo_mode = st.sidebar.toggle("Demo Mode", value=False)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    st.sidebar.markdown('<div class="card-title-strict" style="margin-top:2rem; margin-left:10px;">Conversations</div>', unsafe_allow_html=True)
    if st.sidebar.button("New Conversation", key="btn_new_conv"):
        st.session_state.messages = []
        st.session_state.latest_result = None
        st.rerun()
        
    if st.sidebar.button("Reset Conversation", key="btn_reset_conv"):
        if "conversation_engine" in st.session_state:
            st.session_state.conversation_engine.clear_history()
        st.session_state.messages = []
        st.session_state.latest_result = None
        st.rerun()

    # Bottom Motivational Card
    sidebar_card = (
        '<div class="glass-card" style="margin-top:3rem; padding:1.2rem; border-radius:20px; background:rgba(255,255,255,0.02);">'
        '<div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">'
        '<div style="width:32px; height:32px; border-radius:50%; background:rgba(0,229,255,0.1);'
        ' display:flex; align-items:center; justify-content:center;">'
        '&#10084;'
        '</div>'
        '<span style="font-weight:700; font-size:14px; color:#fff;">You matter.</span>'
        '</div>'
        '<div style="font-size:11px; color:#94A3B8; line-height:1.4; padding-left:44px;">'
        'Your journey to balance starts with a single step.'
        '</div>'
        '</div>'
    )

    st.sidebar.markdown(sidebar_card, unsafe_allow_html=True)

    # --- HEADER ---
    _svg_bar   = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
    _svg_bell  = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>'
    _svg_moon  = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>'
    header_html = (
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2.5rem;">'
        '<div>'
        '<h1 style="margin:0;">Wellness Dashboard</h1>'
        '<p class="label-muted" style="margin-top:4px;">Monitor your mental health metrics in real-time.</p>'
        '</div>'
        '<div style="display:flex;align-items:center;gap:16px;">'
        f'<div class="header-icon-btn">{_svg_bar}</div>'
        f'<div class="header-icon-btn">{_svg_bell}</div>'
        f'<div class="header-icon-btn">{_svg_moon}</div>'
        '<div style="width:1px;height:24px;background:var(--glass-border);margin:0 8px;"></div>'
        '<div style="background:rgba(0,229,255,0.1);border:1px solid var(--cyan-accent);'
        'padding:10px 24px;border-radius:12px;color:var(--cyan-accent);font-weight:700;'
        'font-size:13px;cursor:pointer;letter-spacing:0.5px;'
        'box-shadow:0 0 20px rgba(0,229,255,0.1);">Deploy App</div>'
        '</div>'
        '</div>'
    )
    safe_html(header_html)

    # --- SESSION STATE INITIALIZATION ---
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "tracker" not in st.session_state:
        st.session_state.tracker = SlidingWindowTracker(window_size=7)
    if "latest_result" not in st.session_state:
        st.session_state.latest_result = None
    if "pending_message" not in st.session_state:
        st.session_state.pending_message = None

    # --- CHAT INTERFACE (PRIMARY) ---
    st.markdown('<div style="margin-top: 1rem; margin-bottom: 6rem;">', unsafe_allow_html=True)

    # Render existing conversation
    for msg in st.session_state.messages:
        role_class = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-assistant"
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                icon_html = (
                    f'<div style="width:32px;height:32px;border-radius:8px;background:rgba(139,92,246,0.2);'
                    f'display:flex;align-items:center;justify-content:center;margin-bottom:10px;">'
                    f'<span>{BRAIN_ICON}</span></div>'
                )
            else:
                icon_html = (
                    f'<div style="width:36px;height:36px;border-radius:10px;background:rgba(0,229,255,0.1);'
                    f'display:flex;align-items:center;justify-content:center;margin-bottom:12px;">'
                    f'<span>{CORE_AI_LOGO}</span></div>'
                )
            bubble_html = (
                f'<div class="{role_class}">'
                f'{icon_html}'
                f'<div style="line-height:1.7;font-size:15px;color:#E2E8F0;">'
                f'{msg["content"]}'
                f'</div></div>'
            )
            safe_html(bubble_html)

    # Process new message (from chat_input OR demo button pending_message)
    message_to_process = st.session_state.pending_message
    st.session_state.pending_message = None

    if message_to_process is None:
        message_to_process = st.chat_input("Type your message here...")

    if message_to_process and message_to_process.strip():
        # Production-grade Lazy Loading: Model initializes only on first message
        with st.spinner("Initializing AI engine..."):
            chat_engine = _ensure_conversation_engine(
                ckpt_path,
                model_type
            )

        if chat_engine is None:
            st.error("Failed to initialize AI model.")
            st.stop()

        with st.spinner("Processing..."):
            result = chat_engine.generate_response(message_to_process.strip())

        # Build assistant message
        assistant_body = result["response"]
        follow_up = result["follow_up"]

        # Store for display
        st.session_state.messages.append({"role": "user", "content": message_to_process.strip()})
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"{assistant_body}\n\n**{follow_up}**",
        })

        # Store latest structured result for report generation
        st.session_state.latest_result = result

        # Update tracker
        st.session_state.tracker.add(TrackerEntry(
            text=message_to_process.strip(),
            depression_score=result["emotion_context"]["depression_score"],
            anxiety_score=result["emotion_context"]["anxiety_score"],
            risk_score=result["risk"]["score"],
            top_root_cause=result.get("root_causes", {}).get("top_root_cause", "none"),
        ))

        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # --- ANALYSIS DASHBOARD (latest result) ---
    if st.session_state.latest_result:
        result = st.session_state.latest_result
        mental_ctx = result["emotion_context"]
        risk = result["risk"]
        root_causes = result.get("root_causes", {})
        root_probs = root_causes.get("probabilities", {})
        top_root = root_causes.get("top_root_cause", "none")
        planner = result.get("planner", {})

        risk_level = (risk.get("level", "LOW")).upper()
        # Gauge Color Logic
        risk_score = risk.get("score", 0.0)
        if risk_score < 0.3:
            risk_color = "#10b981" # Green
        elif risk_score < 0.7:
            risk_color = "#f59e0b" # Orange
        else:
            risk_color = "#ef4444" # Red

        # Detailed Analytics (Expandable Panel)
        with st.expander("View detailed analysis & support tools", expanded=True):
            # Row 1: Score Cards & Gauge
            col_s1, col_s2, col_g, col_i = st.columns([1, 1, 1.1, 1.2])
            
            with col_s1:
                dep_val = mental_ctx['depression_score']
                status_color = "#10B981" if dep_val < 0.33 else "#F59E0B" if dep_val < 0.66 else "#EF4444"
                status_text = "Stable" if dep_val < 0.33 else "Moderate" if dep_val < 0.66 else "High"
                dep_card_html = (
                    f'<div class="glass-card" style="height:100%;">'
                    f'<div class="card-title-strict">Depression Score</div>'
                    f'<div class="icon-box-strict" style="border-color:rgba(139,92,246,0.3);box-shadow:0 0 15px rgba(139,92,246,0.1);">'
                    f'<span>{DEPRESSION_ICON}</span></div>'
                    f'<div class="score-value-strict">{dep_val:.3f}</div>'
                    f'<div style="font-size:13px;font-weight:700;color:{status_color};text-transform:uppercase;">{status_text}</div>'
                    f'<div class="sparkline-container">'
                    f'<svg width="100%" height="100%" viewBox="0 0 100 40" preserveAspectRatio="none">'
                    f'<path class="glow-line" d="M0 35 Q 15 15, 30 25 T 50 10 T 75 30 T 100 15"'
                    f' stroke="#8B5CF6" stroke-width="2.5" fill="none" style="--glow-color:#8B5CF6;"/>'
                    f'</svg></div></div>'
                )
                safe_html(dep_card_html)

            with col_s2:
                anx_val = mental_ctx['anxiety_score']
                status_color = "#10B981" if anx_val < 0.33 else "#F59E0B" if anx_val < 0.66 else "#EF4444"
                status_text = "Stable" if anx_val < 0.33 else "Moderate" if anx_val < 0.66 else "High"
                anx_card_html = (
                    f'<div class="glass-card" style="height:100%;">'
                    f'<div class="card-title-strict">Anxiety Score</div>'
                    f'<div class="icon-box-strict" style="border-color:rgba(0,229,255,0.3);box-shadow:0 0 15px rgba(0,229,255,0.1);">'
                    f'<span>{ANXIETY_ICON}</span></div>'
                    f'<div class="score-value-strict">{anx_val:.3f}</div>'
                    f'<div style="font-size:13px;font-weight:700;color:{status_color};text-transform:uppercase;">{status_text}</div>'
                    f'<div class="sparkline-container">'
                    f'<svg width="100%" height="100%" viewBox="0 0 100 40" preserveAspectRatio="none">'
                    f'<path class="glow-line" d="M0 20 Q 20 35, 40 15 T 70 25 T 100 10"'
                    f' stroke="#00E5FF" stroke-width="2.5" fill="none" style="--glow-color:#00E5FF;"/>'
                    f'</svg></div></div>'
                )
                safe_html(anx_card_html)

            with col_g:
                try:
                    if is_plotly_available():
                        fig_gauge = create_risk_gauge_chart(risk_score, "Risk Level")
                        if fig_gauge:
                            st.plotly_chart(fig_gauge, width="stretch", config={'displayModeBar': False})
                            st.markdown(f"<div style='text-align:center; margin-top:-55px; font-size:11px; font-weight:800; color:{risk_color}; letter-spacing:2px; text-transform:uppercase;'>{risk_level} RISK LEVEL</div>", unsafe_allow_html=True)
                        else:
                            st.metric("Risk Level", risk_level)
                            st.warning("Chart engine returned empty view.")
                    else:
                        st.metric("Risk Level", risk_level)
                        st.info("ℹ️ Interactive charts are unavailable: 'plotly' module not found in this environment.")
                except Exception as e:
                    import traceback
                    logger.error(f"Dashboard gauge render failed: {e}\n{traceback.format_exc()}")
                    st.metric("Risk Level", risk_level)
                    st.error(f"Render Error: {e}")

            with col_i:
                insight_text = _final_insight(
                    mental_ctx['depression_score'], mental_ctx['anxiety_score'], top_root, risk_level
                )
                insight_card_html = (
                    f'<div class="glass-card" style="height:100%;background:rgba(139,92,246,0.02);border-color:rgba(139,92,246,0.15);">'
                    f'<div class="card-title-strict">Insight Summary</div>'
                    f'<div style="margin-bottom:12px;display:flex;align-items:center;gap:10px;">'
                    f'<span>{INSIGHT_ICON}</span>'
                    f'<span style="font-weight:700;color:#fff;font-size:14px;">Key Discovery</span>'
                    f'</div>'
                    f'<div style="font-size:14px;line-height:1.6;color:#cbd5e1;min-height:100px;">'
                    f'{insight_text}'
                    f'</div>'
                    f'<div style="margin-top:15px;background:rgba(255,255,255,0.05);border:1px solid var(--glass-border);'
                    f'padding:8px 16px;border-radius:10px;font-size:11px;display:inline-flex;align-items:center;'
                    f'gap:8px;font-weight:700;color:#fff;text-transform:uppercase;letter-spacing:0.5px;">'
                    f'<span style="width:8px;height:8px;border-radius:50%;background:{risk_color};"></span>'
                    f'{risk_level} Risk Active'
                    f'</div></div>'
                )
                safe_html(insight_card_html)

            # Row 2: Root Cause & Action Plan
            col_rc, col_ap = st.columns([1.2, 1])
            
            with col_rc:
                st.markdown('<div class="card-title-strict" style="margin: 24px 0 16px 0;">Root Cause Analysis</div>', unsafe_allow_html=True)
                if root_probs:
                    try:
                        if is_plotly_available():
                            # Define the 5 core categories we want to track
                            CORE_CATEGORIES = [
                                "perfectionism", 
                                "fear_of_failure", 
                                "lack_of_interest", 
                                "environment_distraction", 
                                "dopamine_addiction"
                            ]
                            
                            # Merge model output with core categories to ensure all 5 show up
                            merged_probs = {}
                            for cat in CORE_CATEGORIES:
                                # Get value from model or default to 0.0
                                val = root_probs.get(cat, 0.0)
                                if hasattr(val, "item"): val = val.item()
                                merged_probs[cat] = float(val)
                            
                            # Sort by probability
                            sorted_probs = dict(sorted(merged_probs.items(), key=lambda x: x[1], reverse=True))
                            
                            labels = [k.replace('_', ' ').title() for k in sorted_probs.keys()]
                            values = list(sorted_probs.values())
                            
                            # LOGGING CHART PAYLOAD
                            logger.info(f"Root Cause Chart Payload: labels={labels}, values={values}")
                            
                            fig_bar = create_comparison_bar_chart(
                                labels,
                                values,
                                "Root Cause Distribution"
                            )
                            if fig_bar:
                                st.plotly_chart(fig_bar, width="stretch", config={'displayModeBar': False})
                            else:
                                st.warning("Root cause chart engine returned empty view.")
                        else:
                            st.info("ℹ️ Interactive analysis charts unavailable (Plotly missing).")
                            # Text fallback
                            for cause, prob in root_probs.items():
                                p = float(prob.item() if hasattr(prob, "item") else prob)
                                st.write(f"**{cause.replace('_', ' ').title()}:** {p:.2%}")
                    except Exception as e:
                        import traceback
                        logger.error(f"Root cause chart failed: {e}\n{traceback.format_exc()}")
                        st.error(f"Visualization Error: {e}")
                        # Fallback to simple text display
                        for cause, prob in root_probs.items():
                            try:
                                p = float(prob.item() if hasattr(prob, "item") else prob)
                            except Exception:
                                p = 0.0
                            st.write(f"**{cause.replace('_', ' ').title()}:** {p:.2%}")

            with col_ap:
                st.markdown('<div class="card-title-strict" style="margin: 24px 0 16px 0;">Actionable Plan</div>', unsafe_allow_html=True)
                interventions = _planner_suggestions(top_root)
                if interventions:
                    for i, rec in enumerate(interventions[:2]):

                        card_html = (
                            f'<div style="display:flex;align-items:center;gap:18px;padding:20px;margin-bottom:16px;'
                            f'border-radius:22px;background:linear-gradient(135deg,rgba(8,15,35,0.96),rgba(5,20,40,0.92));'
                            f'border:1px solid rgba(0,229,255,0.14);box-shadow:0 0 25px rgba(0,229,255,0.05);">'
                            f'<div style="width:52px;height:52px;min-width:52px;border-radius:16px;'
                            f'background:rgba(0,229,255,0.08);border:1px solid rgba(0,229,255,0.18);'
                            f'display:flex;align-items:center;justify-content:center;color:#00E5FF;font-size:22px;">'
                            f'&#10022;'
                            f'</div>'
                            f'<div style="flex:1;">'
                            f'<div style="color:white;font-size:15px;font-weight:700;margin-bottom:6px;">{rec}</div>'
                            f'<div style="color:#94A3B8;font-size:12px;line-height:1.5;">'
                            f'Take meaningful small steps toward mental balance today.'
                            f'</div></div>'
                            f'<div style="color:#00E5FF;font-size:20px;font-weight:300;">&#8594;</div>'
                            f'</div>'
                        )
                        safe_html(card_html)

            # Row 3: Motivational Mini Cards
            st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
            mi_c1, mi_c2, mi_c3 = st.columns(3)
            with mi_c1:
                safe_html(
                    f'<div class="glass-card" style="padding:20px;display:flex;align-items:center;gap:16px;border-color:rgba(132,204,22,0.15);">'
                    f'<span>{LEAF_ICON}</span>'
                    f'<span style="font-size:14px;font-weight:700;color:#fff;">Small steps matter.</span></div>'
                )
            with mi_c2:
                safe_html(
                    f'<div class="glass-card" style="padding:20px;display:flex;align-items:center;gap:16px;border-color:rgba(0,229,255,0.15);">'
                    f'<span>{ANXIETY_ICON}</span>'
                    f'<span style="font-size:14px;font-weight:700;color:#fff;">Consistency &gt; Intensity.</span></div>'
                )
            with mi_c3:
                safe_html(
                    f'<div class="glass-card" style="padding:20px;display:flex;align-items:center;gap:16px;border-color:rgba(236,72,153,0.15);">'
                    f'<span>{HEART_ICON}</span>'
                    f'<span style="font-size:14px;font-weight:700;color:#fff;">You\'re doing great.</span></div>'
                )

            # Row 4: Export Section
            st.markdown('<div class="card-title-strict" style="margin-top: 32px; margin-bottom: 20px;">Export Analysis Report</div>', unsafe_allow_html=True)
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown('<div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px;">Full Name</div>', unsafe_allow_html=True)
                user_name = st.text_input("Name", value=st.session_state.get("user_name", ""), placeholder="e.g. Alex Smith", label_visibility="collapsed")
                st.session_state.user_name = user_name
            with col_r2:
                st.markdown('<div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px;">Email Address</div>', unsafe_allow_html=True)
                user_email = st.text_input("Email", value=st.session_state.get("user_email", ""), placeholder="e.g. alex@example.com", label_visibility="collapsed")
                st.session_state.user_email = user_email

            st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
            
            # PDF Export Logic with Graceful Fallback
            # Use session state to manage report generation status and prevent button flickering
            if "report_ready" not in st.session_state:
                st.session_state.report_ready = False
            if "report_pdf_bytes" not in st.session_state:
                st.session_state.report_pdf_bytes = None

            # Prepare report data using exact reference variable names
            # Reference mapping:
            # - ai_summary
            # - conversational_insight
            # - final_status
            # - recommendations
            # - behavioral_findings
            # - status_metrics
            
            report_payload_data = {
                "ai_summary": insight_text,
                "conversational_insight": "User showed positive receptivity to AI-driven insights.",
                "final_status": f"{risk_level} RISK · ACTIVE",
                "recommendations": interventions,
                "behavioral_findings": [
                    "High cognitive pressure linked to ambiguous task outcomes.",
                    "Dopamine-driven distraction cycles during deep-work intervals.",
                    "Responsive pattern detected for empathetic mirroring techniques."
                ],
                "status_metrics": [
                    {"label": "Risk Score", "value": f"{risk_score}%", "color": "AMBER"},
                    {"label": "Anxiety Idx", "value": f"{int(mental_ctx['anxiety_score']*100)}%", "color": "CYAN"},
                    {"label": "Sessions", "value": "1", "color": "PURPLE"},
                    {"label": "Trend", "value": "NEW", "color": "EMERALD"}
                ]
            }

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("Generate Premium Report", key="btn_pdf", width="stretch"):
                    if not user_name or not user_email:
                        display_error_message("Please provide name and email.")
                    else:
                        with st.spinner("Analyzing behavioral patterns & generating PDF..."):
                            try:
                                report_service = get_report_service()
                                user_data = {"name": user_name, "email": user_email}
                                
                                # Use the correct variable structure from reference architecture
                                analysis_results = {
                                    "depression_score": mental_ctx['depression_score'],
                                    "anxiety_score": mental_ctx['anxiety_score'],
                                    "risk_score": risk_score,
                                    "risk_level": risk_level,
                                    "top_root_cause": top_root,
                                    "root_causes": root_probs,
                                    "ai_summary": report_payload_data["ai_summary"],
                                    "conversational_insight": report_payload_data["conversational_insight"],
                                    "final_status": report_payload_data["final_status"],
                                    "recommendations": report_payload_data["recommendations"],
                                    "behavioral_findings": report_payload_data["behavioral_findings"],
                                    "status_metrics": report_payload_data["status_metrics"],
                                    "engagement": 85 # Placeholder
                                }
                                
                                result = report_service.generate_comprehensive_report(
                                    user_data=user_data,
                                    analysis_results=analysis_results,
                                    interventions=interventions,
                                    format_type="pdf"
                                )
                                
                                if result["status"] == "success":
                                    with open(result["file_path"], "rb") as f:
                                        st.session_state.report_pdf_bytes = f.read()
                                    st.session_state.report_ready = True
                                    st.session_state.report_id = result["report_id"]
                                    display_success_message("Premium Report Generated! Click below to download.")
                                else:
                                    display_error_message(f"Generation failed: {result.get('error', 'Unknown error')}")
                            except Exception as e:
                                logger.error(f"PDF generation failed: {e}")
                                display_error_message("Generation failed. Please check logs.")

                if st.session_state.report_ready:
                    st.download_button(
                        label="Download PDF Report", 
                        data=st.session_state.report_pdf_bytes, 
                        file_name=f"COREAI_Premium_Report_{user_name.replace(' ', '_')}.pdf", 
                        mime="application/pdf", 
                        width="stretch"
                    )

            with col_btn2:
                if st.button("Send via Secure Email", key="btn_email", width="stretch"):
                    if not user_name or not user_email:
                        display_error_message("Please provide name and email.")
                    elif not st.session_state.report_ready:
                        display_error_message("Please generate the report first.")
                    else:
                        with st.spinner("Encrypting & sending secure email..."):
                            try:
                                report_service = get_report_service()
                                email_result = report_service.send_report_email(
                                    report_id=st.session_state.report_id,
                                    recipient_email=user_email,
                                    user_name=user_name,
                                    message="Your CORE:AI Premium Behavioral Intelligence Report is attached."
                                )
                                
                                if email_result["status"] == "success":
                                    display_success_message("Report dispatched to your inbox!")
                                else:
                                    display_error_message(f"Email failed: {email_result.get('message', 'Unknown error')}")
                                    
                            except Exception as e:
                                logger.error(f"Email sending failed: {e}")
                                display_error_message("Email service unavailable.")


if __name__ == "__main__":
    main()
