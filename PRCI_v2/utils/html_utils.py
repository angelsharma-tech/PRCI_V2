"""
HTML Utilities for PRCI v2
Phase 4.1 - Backend Stabilization & Architecture Refactor
"""

import logging
from typing import Dict, List, Optional, Any
from config import UI_COLORS, UI_SPACING, UI_BORDERS

logger = logging.getLogger(__name__)


def generate_css_styles() -> str:
    """
    Generate comprehensive CSS styles for the application
    """
    return """
    <style>
        /* --- TRAE STRICT REBUILD (PHASE 3B.4) --- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Manrope:wght@600;800&family=Poppins:wght@400;600;700&display=swap');

        :root {
            --bg-main: radial-gradient(circle at top left, #071426 0%, #030712 45%, #000814 100%);
            --glass-bg: rgba(255, 255, 255, 0.03);
            --glass-border: rgba(255, 255, 255, 0.08);
            --text-primary: #ffffff;
            --text-muted: #94a3b8;
            --accent: #00e5ff;
            --accent-secondary: #8b5cf6;
            --card-bg: rgba(255, 255, 255, 0.02);
        }

        html, body, [class*="css"] {
            background: var(--bg-main);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background: var(--bg-main);
        }

        /* --- GLASS CARD COMPONENT --- */
        .glass-card {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 22px;
            padding: 20px;
            transition: all 0.3s ease;
        }

        .glass-card:hover {
            border-color: rgba(0, 229, 255, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 8px 32px rgba(0, 229, 255, 0.1);
        }

        /* --- SIDEBAR STYLING --- */
        .css-1d391kg {
            background: linear-gradient(135deg, rgba(8, 15, 35, 0.95), rgba(5, 20, 40, 0.9));
            border-right: 1px solid rgba(0, 229, 255, 0.1);
        }

        .sidebar-logo-area {
            padding: 1.5rem 1rem;
            margin-bottom: 2rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }

        .nav-item {
            padding: 0.75rem 1rem;
            margin: 0.25rem 0;
            border-radius: 12px;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .nav-item:hover {
            background: rgba(0, 229, 255, 0.1);
            color: var(--text-primary);
        }

        .nav-item.active {
            background: rgba(0, 229, 255, 0.15);
            color: var(--accent);
            border-left: 3px solid var(--accent);
        }

        /* --- CARD TITLES --- */
        .card-title-strict {
            color: var(--text-primary);
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 18px;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* --- METRIC CARDS --- */
        .metric-card {
            background: var(--card-bg);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s ease;
        }

        .metric-card:hover {
            border-color: rgba(0, 229, 255, 0.2);
            transform: translateY(-1px);
        }

        .metric-value {
            font-size: 2.5rem;
            font-weight: 800;
            font-family: 'Manrope', sans-serif;
            margin: 0;
            line-height: 1;
        }

        .metric-label {
            font-size: 0.875rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 0.5rem;
        }

        /* --- HEADER STYLING --- */
        .header-icon-btn {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .header-icon-btn:hover {
            background: rgba(0, 229, 255, 0.1);
            border-color: rgba(0, 229, 255, 0.3);
        }

        /* --- CHART CONTAINERS --- */
        .chart-container {
            background: var(--card-bg);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }

        /* --- BUTTON STYLING --- */
        .stButton > button {
            background: linear-gradient(135deg, var(--accent), var(--accent-secondary));
            border: none;
            border-radius: 12px;
            color: white;
            font-weight: 600;
            padding: 0.75rem 1.5rem;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 229, 255, 0.3);
        }

        /* --- INPUT STYLING --- */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            color: var(--text-primary);
        }

        /* --- EXPANDER STYLING --- */
        .streamlit-expanderHeader {
            background: var(--glass-bg);
            border-radius: 8px;
        }

        /* --- LABEL STYLING --- */
        .label-muted {
            color: var(--text-muted);
            font-size: 0.875rem;
            margin: 0;
        }

        /* --- ANIMATIONS --- */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .fade-in {
            animation: fadeIn 0.5s ease-out;
        }

        /* --- RESPONSIVE DESIGN --- */
        @media (max-width: 768px) {
            .glass-card {
                padding: 1rem;
                margin-bottom: 1rem;
            }
            
            .metric-value {
                font-size: 2rem;
            }
            
            .card-title-strict {
                font-size: 16px;
            }
        }
    </style>
    """


def create_sidebar_html() -> str:
    """
    Create the sidebar HTML structure
    """
    return f"""
    <div class="sidebar-logo-area">
        <div style="display:flex; align-items:center; gap:14px; padding-left:10px;">
            <span>{get_icon('core_ai_logo')}</span>
            <div>
                <div style="font-size: 18px; font-weight: 800; color: white; font-family: 'Poppins', sans-serif; margin: 0;">CORE:AI</div>
                <div style="font-size: 11px; color: #94A3B8; margin: 0;">MENTAL WELLNESS</div>
            </div>
        </div>
    </div>
    """


def create_header_html() -> str:
    """
    Create the main header HTML structure
    """
    return f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2.5rem;">
        <div>
            <h1 style="margin: 0;">Wellness Dashboard</h1>
            <p class="label-muted" style="margin-top: 4px;">Monitor your mental health metrics in real-time.</p>
        </div>
        <div style="display: flex; align-items: center; gap: 16px;">
            <div class="header-icon-btn">
                <span>{get_icon('shield')}</span>
            </div>
            <div class="header-icon-btn">
                <span>{get_icon('run')}</span>
            </div>
        </div>
    </div>
    """


def create_insight_summary_html(
    depression_level: str,
    anxiety_level: str,
    top_root: str,
    risk_level: str
) -> str:
    """
    Create the insight summary HTML
    """
    return f"""
    <div class="glass-card fade-in" style="margin-bottom: 2rem;">
        <div style="display: flex; align-items: flex-start; gap: 16px;">
            <div style="width: 48px; height: 48px; min-width: 48px; border-radius: 12px; background: rgba(0,229,255,0.08); display: flex; align-items: center; justify-content: center;">
                <span>{get_icon('insight')}</span>
            </div>
            <div style="flex: 1;">
                <div style="font-size: 16px; font-weight: 700; color: white; margin-bottom: 8px;">
                    Key Insights
                </div>
                <div style="color: #94A3B8; line-height: 1.6;">
                    Your analysis shows {anxiety_level} anxiety and {depression_level} depression patterns. 
                    Primary concern: <strong>{top_root.replace('_', ' ').title()}</strong>. 
                    Overall risk level: {create_risk_badge(risk_level)}
                </div>
            </div>
        </div>
    </div>
    """


def create_root_cause_analysis_html(
    root_cause_data: Dict[str, float],
    top_root: str
) -> str:
    """
    Create the root cause analysis HTML
    """
    items_html = ""
    for cause, score in root_cause_data.items():
        percentage = score * 100
        bar_color = "#00E5FF" if cause == top_root else "#475569"
        
        items_html += f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 13px; color: white; font-weight: 500;">
                    {cause.replace('_', ' ').title()}
                </span>
                <span style="font-size: 12px; color: #94A3B8;">
                    {percentage:.0f}%
                </span>
            </div>
            <div style="height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">
                <div style="height: 100%; width: {percentage}%; background: {bar_color}; border-radius: 3px; transition: width 0.5s ease;"></div>
            </div>
        </div>
        """
    
    return f"""
    <div class="glass-card">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
            <span>{get_icon('brain')}</span>
            <div style="font-size: 16px; font-weight: 700; color: white;">
                Root Cause Analysis
            </div>
        </div>
        {items_html}
    </div>
    """


def get_icon(name: str) -> str:
    """
    Get an SVG icon by name (imported from config to avoid circular imports)
    """
    from config import SVG_ICONS
    return SVG_ICONS.get(name, "")


def create_risk_badge(level: str) -> str:
    """
    Create a risk badge HTML (imported from config to avoid circular imports)
    """
    from config import RISK_COLORS
    lvl = str(level or "").upper()
    color = RISK_COLORS.get(lvl, RISK_COLORS["LOW"])
    return f"<span style='color:{color}; font-weight:700'>{lvl}</span>"


def escape_html(text: str) -> str:
    """
    Escape HTML special characters
    """
    import html
    return html.escape(text)


def validate_html_attributes(attributes: Dict[str, str]) -> Dict[str, str]:
    """
    Validate and clean HTML attributes
    """
    valid_attributes = {}
    for key, value in attributes.items():
        if isinstance(key, str) and isinstance(value, str):
            # Remove potentially dangerous attributes
            if key.lower() not in ['onclick', 'onload', 'onerror', 'javascript:']:
                valid_attributes[key] = escape_html(value)
    return valid_attributes


def create_style_string(styles: Dict[str, str]) -> str:
    """
    Convert a dictionary of CSS styles to a style string
    """
    validated_styles = validate_html_attributes(styles)
    return "; ".join([f"{k}: {v}" for k, v in validated_styles.items()])


def sanitize_html(html_content: str) -> str:
    """
    Basic HTML sanitization
    """
    import re
    
    # Remove script tags
    html_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove on* attributes
    html_content = re.sub(r'on\w+="[^"]*"', '', html_content, flags=re.IGNORECASE)
    
    return html_content
