"""
UI Helper Utilities for PRCI v2
Phase 4.1 - Backend Stabilization & Architecture Refactor
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any
import logging

# Optional plotly imports for chart utilities
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None
    px = None

from config import UI_COLORS, UI_SPACING, UI_BORDERS, RISK_COLORS, SVG_ICONS

logger = logging.getLogger(__name__)


def safe_html(content: str) -> None:
    """
    Safely render HTML content in Streamlit
    """
    try:
        st.markdown(content, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error rendering HTML content: {e}")
        st.error("Error rendering content")


def create_risk_badge(level: str) -> str:
    """
    Create a colored risk badge HTML
    """
    lvl = str(level or "").upper()
    color = RISK_COLORS.get(lvl, RISK_COLORS["LOW"])
    return f"<span style='color:{color}; font-weight:700'>{lvl}</span>"


def create_glass_card(
    content: str,
    padding: Optional[str] = None,
    border_color: Optional[str] = None,
    additional_styles: Optional[str] = None
) -> str:
    """
    Create a glass card with content
    """
    padding = padding or UI_SPACING["card_padding"]
    border_color = border_color or UI_COLORS["glass_border"]
    
    styles = [
        f"padding: {padding}",
        f"border: 1px solid {border_color}",
        f"border-radius: {UI_BORDERS['card_radius']}",
        f"background: {UI_COLORS['glass_bg']}",
        "backdrop-filter: blur(10px)"
    ]
    
    if additional_styles:
        styles.append(additional_styles)
    
    style_attr = "; ".join(styles)
    
    return f"""
    <div class="glass-card" style="{style_attr}">
        {content}
    </div>
    """


def create_action_card(
    title: str,
    description: str = "Take meaningful small steps toward mental balance today.",
    icon: str = "✦"
) -> str:
    """
    Create an action card with title and description
    """
    return f"""
    <div style="
        display:flex;
        align-items:center;
        gap:18px;
        padding:20px;
        margin-bottom:16px;
        border-radius:22px;
        background:linear-gradient(
            135deg,
            rgba(8,15,35,0.96),
            rgba(5,20,40,0.92)
        );
        border:1px solid rgba(0,229,255,0.14);
        box-shadow:0 0 25px rgba(0,229,255,0.05);
    ">
        <div style="
            width:52px;
            height:52px;
            min-width:52px;
            border-radius:16px;
            background:rgba(0,229,255,0.08);
            border:1px solid rgba(0,229,255,0.18);
            display:flex;
            align-items:center;
            justify-content:center;
            color:#00E5FF;
            font-size:22px;
        ">
            {icon}
        </div>

        <div style="flex:1;">
            <div style="
                color:white;
                font-size:15px;
                font-weight:700;
                margin-bottom:6px;
            ">
                {title}
            </div>

            <div style="
                color:#94A3B8;
                font-size:12px;
                line-height:1.5;
            ">
                {description}
            </div>
        </div>

        <div style="
            color:#00E5FF;
            font-size:20px;
            font-weight:300;
        ">
            →
        </div>
    </div>
    """


def create_motivational_card(
    icon: str,
    text: str,
    border_color: Optional[str] = None
) -> str:
    """
    Create a small motivational card
    """
    border_color = border_color or UI_COLORS["glass_border"]
    
    return f"""
    <div class="glass-card" style="
        padding: 20px; 
        display: flex; 
        align-items: center; 
        gap: 16px; 
        border-color: {border_color};
    ">
        <span>{icon}</span> 
        <span style="font-size: 14px; font-weight: 700; color: #fff;">{text}</span>
    </div>
    """


def create_metric_card(
    title: str,
    value: str,
    delta: Optional[str] = None,
    icon: Optional[str] = None
) -> str:
    """
    Create a metric display card
    """
    icon_html = f"<span>{icon}</span>" if icon else ""
    delta_html = f"<div style='color: {UI_COLORS['success']}; font-size: 12px;'>{delta}</div>" if delta else ""
    
    return f"""
    <div style="
        padding: 16px;
        border-radius: 12px;
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.08);
        text-align: center;
    ">
        <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 8px;">
            {icon_html}
            <div style="font-size: 12px; color: {UI_COLORS['text_muted']}; text-transform: uppercase;">
                {title}
            </div>
        </div>
        <div style="font-size: 24px; font-weight: 700; color: {UI_COLORS['text_primary']};">
            {value}
        </div>
        {delta_html}
    </div>
    """


def create_sidebar_card(
    title: str,
    content: str,
    icon: str = "❤"
) -> str:
    """
    Create a sidebar card
    """
    return f"""
    <div class="glass-card" style="
        margin-top:3rem;
        padding:1.2rem;
        border-radius:20px;
        background:rgba(255,255,255,0.02);
    ">
        <div style="
            display:flex;
            align-items:center;
            gap:12px;
            margin-bottom:8px;
        ">
            <div style="
                width:32px;
                height:32px;
                border-radius:50%;
                background:rgba(0,229,255,0.1);
                display:flex;
                align-items:center;
                justify-content:center;
            ">
                {icon}
            </div>

            <span style="
                font-weight:700;
                font-size:14px;
                color:#fff;
            ">
                {title}
            </span>
        </div>

        <div style="
            font-size:11px;
            color:#94A3B8;
            line-height:1.4;
            padding-left:44px;
        ">
            {content}
        </div>
    </div>
    """


def create_chart_container(title: str, chart_html: str) -> str:
    """
    Wrap a chart in a styled container
    """
    return f"""
    <div style="
        background: rgba(255,255,255,0.02);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(255,255,255,0.08);
    ">
        <h3 style="
            color: white;
            margin: 0 0 16px 0;
            font-size: 16px;
            font-weight: 600;
        ">
            {title}
        </h3>
        {chart_html}
    </div>
    """


def display_error_message(message: str, show_details: bool = False) -> None:
    """
    Display a standardized error message
    """
    st.error(message)
    if show_details:
        with st.expander("Error Details"):
            st.code(message)


def display_success_message(message: str) -> None:
    """
    Display a standardized success message
    """
    st.success(message)


def display_warning_message(message: str) -> None:
    """
    Display a standardized warning message
    """
    st.warning(message)


def create_loading_spinner(text: str = "Loading...") -> None:
    """
    Create a loading spinner with custom text
    """
    with st.spinner(text):
        yield


def get_icon(name: str) -> str:
    """
    Get an SVG icon by name
    """
    return SVG_ICONS.get(name, "")


def format_score(score: float, threshold_type: str = "depression") -> str:
    """
    Format a score into a readable level
    """
    from config import SCORE_THRESHOLDS
    
    thresholds = SCORE_THRESHOLDS.get(threshold_type, SCORE_THRESHOLDS["depression"])
    
    if score < thresholds["low"]:
        return "low"
    elif score < thresholds["moderate"]:
        return "moderate"
    else:
        return "high"


def create_progress_bar(
    current: float,
    total: float = 1.0,
    color: str = None,
    height: str = "8px"
) -> str:
    """
    Create a custom progress bar
    """
    color = color or UI_COLORS["primary"]
    percentage = min((current / total) * 100, 100)
    
    return f"""
    <div style="
        width: 100%;
        height: {height};
        background: rgba(255,255,255,0.1);
        border-radius: 4px;
        overflow: hidden;
    ">
        <div style="
            width: {percentage}%;
            height: 100%;
            background: {color};
            border-radius: 4px;
            transition: width 0.3s ease;
        "></div>
    </div>
    """
