"""
Chart Utilities for PRCI v2
Phase 4.1 - Backend Stabilization & Architecture Refactor
"""

import math
import streamlit as st
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Any, Union

# Dynamic Plotly detection helper
def is_plotly_available():
    """Runtime check for Plotly availability to avoid stale import-time flags."""
    try:
        import plotly
        import plotly.graph_objects as go
        import plotly.express as px
        return True
    except Exception as e:
        # Avoid logging this every time to keep logs clean
        return False


def _sanitize_chart_values(values: List[Any], clamp_zero: bool = True) -> List[float]:
    """Convert raw values (FP16 tensors, numpy scalars, etc.) to safe Python floats.

    FP16 inference produces torch.float16 / np.float16 values that Plotly's
    text formatting (f'{v:.2f}') and JSON serialization cannot handle.
    Explicit float() conversion + NaN/inf guarding keeps charts stable.
    """
    safe = []
    for v in values:
        try:
            # Unwrap torch tensors (including FP16) and numpy scalars
            if hasattr(v, "item"):
                v = v.item()
            f = float(v)
            if math.isnan(f) or math.isinf(f):
                f = 0.0
            if clamp_zero:
                f = max(0.0, f)
            safe.append(f)
        except Exception:
            safe.append(0.0)
    return safe

from config import UI_COLORS, RISK_COLORS

logger = logging.getLogger(__name__)


def create_risk_gauge_chart(
    risk_score: float,
    title: str = "Risk Level"
) -> Union['go.Figure', None]:
    """
    Create a gauge chart for risk visualization
    """
    if not is_plotly_available():
        logger.warning("Plotly not available, returning None for gauge chart")
        return None
        
    try:
        # Detailed traceback for debugging
        import traceback
        import plotly.graph_objects as go

        # Defensive: FP16 tensors / np.float16 break gauge value and JSON serialization
        risk_score = float(risk_score.item() if hasattr(risk_score, "item") else risk_score)
        if math.isnan(risk_score) or math.isinf(risk_score):
            risk_score = 0.0

        # Determine color based on risk level
        if risk_score < 0.33:
            color = RISK_COLORS["LOW"]
        elif risk_score < 0.66:
            color = RISK_COLORS["MODERATE"]
        else:
            color = RISK_COLORS["HIGH"]

        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = risk_score * 100,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': title, 'font': {'color': 'white', 'size': 14}},
            delta = {'reference': 50},
            gauge = {
                'axis': {'range': [None, 100], 'tickcolor': "white", 'tickfont': {'color': 'white'}},
                'bar': {'color': color},
                'bgcolor': "rgba(255,255,255,0.1)",
                'borderwidth': 2,
                'bordercolor': color,
                'steps': [
                    {'range': [0, 33], 'color': 'rgba(46, 125, 50, 0.3)'},
                    {'range': [33, 66], 'color': 'rgba(239, 108, 0, 0.3)'},
                    {'range': [66, 100], 'color': 'rgba(198, 40, 40, 0.3)'}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': risk_score * 100
                }
            }
        ))

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "white"},
            height=300,
            margin=dict(l=0, r=0, t=40, b=0)
        )

        return fig

    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error creating risk gauge chart: {e}\n{error_details}")
        st.error(f"Visualization Logic Error: {e}")
        return create_fallback_chart(title)


def create_trend_chart(
    data: List[float],
    title: str = "Trend Analysis",
    dates: Optional[List[str]] = None,
    color: str = None
) -> Union['go.Figure', None]:
    """
    Create a trend line chart
    """
    if not is_plotly_available():
        logger.warning("Plotly not available, returning None for trend chart")
        return None
        
    try:
        import plotly.graph_objects as go
        # Defensive: FP16 tensors / np.float16 break Plotly formatting and JSON serialization
        data = _sanitize_chart_values(data)

        if not dates:
            dates = [f"Day {i+1}" for i in range(len(data))]

        color = color or UI_COLORS["primary"]

        fig = go.Figure()

        # Add main trend line
        fig.add_trace(go.Scatter(
            x=dates,
            y=data,
            mode='lines+markers',
            line=dict(color=color, width=3),
            marker=dict(color=color, size=8),
            name='Trend',
            hovertemplate='<b>%{x}</b><br>Value: %{y:.2f}<extra></extra>'
        ))

        # Add average line
        avg_value = np.mean(data)
        fig.add_trace(go.Scatter(
            x=dates,
            y=[avg_value] * len(dates),
            mode='lines',
            line=dict(color='rgba(255,255,255,0.3)', width=2, dash='dash'),
            name='Average',
            hovertemplate='Average: %{y:.2f}<extra></extra>'
        ))

        fig.update_layout(
            title={'text': title, 'font': {'color': 'white', 'size': 16}},
            xaxis=dict(
                title=dict(font=dict(color='white')),
                tickfont=dict(color='white'),
                gridcolor='rgba(255,255,255,0.1)'
            ),
            yaxis=dict(
                title=dict(font=dict(color='white')),
                tickfont=dict(color='white'),
                gridcolor='rgba(255,255,255,0.1)'
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=300,
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=True,
            legend=dict(
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='rgba(255,255,255,0.2)',
                font=dict(color='white')
            )
        )

        return fig

    except Exception as e:
        st.error(f"Chart error: {e}")
        logger.error(f"Error creating trend chart: {e}")
        return create_fallback_chart(title)


def create_comparison_bar_chart(
    categories: List[str],
    values: List[float],
    title: str = "Comparison Chart",
    color: str = None
) -> Union['go.Figure', None]:
    """
    Create a horizontal bar chart for comparisons
    """
    if not is_plotly_available():
        logger.warning("Plotly not available, returning None for comparison chart")
        return None
        
    try:
        import plotly.graph_objects as go
        
        # 1. Strict Sanitization
        safe_values = _sanitize_chart_values(values, clamp_zero=True)
        
        # 2. Scale check: If values are 0.0-1.0, scale to 0-100 for better visibility
        # Only scale if we have some non-zero values and they all fit in 0-1 range
        if safe_values and all(0.0 <= v <= 1.0 for v in safe_values) and any(v > 0 for v in safe_values):
            safe_values = [v * 100 for v in safe_values]

        # 3. Handle empty categories case
        if not categories:
            logger.warning(f"No categories provided for chart: {title}")
            return None

        # Sort categories by value for better visual hierarchy
        # Using stable sort to preserve order for tied values (like multiple zeros)
        sorted_indices = sorted(range(len(safe_values)), key=lambda k: safe_values[k])
        categories = [categories[i] for i in sorted_indices]
        safe_values = [safe_values[i] for i in sorted_indices]

        fig = go.Figure(go.Bar(
            x=safe_values,
            y=categories,
            orientation='h',
            marker=dict(
                color=color if color else 'rgba(0, 209, 255, 0.6)',
                line=dict(color=color if color else 'rgba(0, 209, 255, 1.0)', width=1)
            ),
            text=[f"{v:.1f}%" for v in safe_values],
            textposition='auto',
            textfont=dict(color='white')
        ))

        fig.update_layout(
            title={'text': title, 'font': {'color': 'white', 'size': 14}},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "white"},
            xaxis=dict(
                showgrid=True, 
                gridcolor='rgba(255,255,255,0.1)',
                range=[0, 100], # Force 0-100 range for consistency
                tickfont=dict(color='white'),
                dtick=20 # Show ticks at 20% intervals
            ),
            yaxis=dict(
                showgrid=False,
                tickfont=dict(color='white')
            ),
            height=300,
            margin=dict(l=0, r=20, t=40, b=20)
        )

        return fig

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error creating comparison bar chart: {e}\n{error_details}")
        st.error(f"Visualization Logic Error (Bar): {e}")
        return create_fallback_chart(title)


def create_pie_chart(
    labels: List[str],
    values: List[float],
    title: str = "Distribution Chart"
) -> Union['go.Figure', None]:
    """
    Create a pie chart for distribution visualization
    """
    if not is_plotly_available():
        logger.warning("Plotly not available, returning None for pie chart")
        return None
        
    try:
        import plotly.graph_objects as go
        # Generate colors based on UI_COLORS
        colors = [
            UI_COLORS["primary"],
            UI_COLORS["secondary"],
            UI_COLORS["accent"],
            UI_COLORS["success"],
            "#F59E0B",
            "#EF4444"
        ][:len(labels)]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker=dict(colors=colors, line=dict(color='rgba(255,255,255,0.3)', width=2)),
            textinfo='label+percent',
            textfont=dict(color='white'),
            hovertemplate='<b>%{label}</b><br>Value: %{value}<br>Percentage: %{percent}<extra></extra>'
        )])

        fig.update_layout(
            title={'text': title, 'font': {'color': 'white', 'size': 16}},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=300,
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=True,
            legend=dict(
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='rgba(255,255,255,0.2)',
                font=dict(color='white')
            )
        )

        return fig

    except Exception as e:
        st.error(f"Chart error: {e}")
        logger.error(f"Error creating pie chart: {e}")
        return create_fallback_chart(title)


def create_heatmap(
    data: pd.DataFrame,
    title: str = "Heatmap Analysis"
) -> Union['go.Figure', None]:
    """
    Create a heatmap for correlation or pattern visualization
    """
    if not is_plotly_available():
        logger.warning("Plotly not available, returning None for heatmap")
        return None
        
    try:
        import plotly.graph_objects as go
        fig = go.Figure(data=go.Heatmap(
            z=data.values,
            x=data.columns,
            y=data.index,
            colorscale='Viridis',
            showscale=True,
            hovertemplate='<b>%{y}</b><br><b>%{x}</b><br>Value: %{z:.2f}<extra></extra>'
        ))

        fig.update_layout(
            title={'text': title, 'font': {'color': 'white', 'size': 16}},
            xaxis=dict(
                title=dict(font=dict(color='white')),
                tickfont=dict(color='white'),
                gridcolor='rgba(255,255,255,0.1)'
            ),
            yaxis=dict(
                title=dict(font=dict(color='white')),
                tickfont=dict(color='white'),
                gridcolor='rgba(255,255,255,0.1)'
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=300,
            margin=dict(l=0, r=0, t=40, b=0)
        )

        return fig

    except Exception as e:
        st.error(f"Chart error: {e}")
        logger.error(f"Error creating heatmap: {e}")
        return create_fallback_chart(title)


def create_scatter_plot(
    x_data: List[float],
    y_data: List[float],
    title: str = "Scatter Analysis",
    x_label: str = "X Axis",
    y_label: str = "Y Axis",
    color: str = None
) -> Union['go.Figure', None]:
    """
    Create a scatter plot for correlation analysis
    """
    if not is_plotly_available():
        logger.warning("Plotly not available, returning None for scatter plot")
        return None
        
    try:
        import plotly.graph_objects as go
        color = color or UI_COLORS["primary"]

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode='markers',
            marker=dict(
                color=color,
                size=10,
                line=dict(color='rgba(255,255,255,0.5)', width=1)
            ),
            text=[f'({x:.2f}, {y:.2f})' for x, y in zip(x_data, y_data)],
            hovertemplate='<b>%{text}</b><extra></extra>'
        ))

        # Add trend line
        if len(x_data) > 1:
            z = np.polyfit(x_data, y_data, 1)
            p = np.poly1d(z)
            fig.add_trace(go.Scatter(
                x=x_data,
                y=p(x_data),
                mode='lines',
                line=dict(color='rgba(255,255,255,0.5)', width=2, dash='dash'),
                name='Trend',
                hovertemplate='Trend: %{y:.2f}<extra></extra>'
            ))

        fig.update_layout(
            title={'text': title, 'font': {'color': 'white', 'size': 16}},
            xaxis=dict(
                title=dict(text=x_label, font=dict(color='white')),
                tickfont=dict(color='white'),
                gridcolor='rgba(255,255,255,0.1)'
            ),
            yaxis=dict(
                title=dict(text=y_label, font=dict(color='white')),
                tickfont=dict(color='white'),
                gridcolor='rgba(255,255,255,0.1)'
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=300,
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=True,
            legend=dict(
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='rgba(255,255,255,0.2)',
                font=dict(color='white')
            )
        )

        return fig

    except Exception as e:
        st.error(f"Chart error: {e}")
        logger.error(f"Error creating scatter plot: {e}")
        return create_fallback_chart(title)


def create_fallback_chart(title: str = "Chart Unavailable") -> Union['go.Figure', None]:
    """
    Create a fallback chart when chart creation fails
    """
    if not is_plotly_available():
        logger.warning("Plotly not available, returning None for fallback chart")
        return None
        
    import plotly.graph_objects as go
    fig = go.Figure()

    fig.add_annotation(
        text=f"Chart temporarily unavailable<br>{title}",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(color="white", size=16)
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    return fig


def validate_chart_data(data: Any) -> bool:
    """
    Validate chart data before processing
    """
    if data is None:
        return False
    
    if isinstance(data, (list, tuple)):
        return len(data) > 0
    
    if isinstance(data, pd.DataFrame):
        return not data.empty
    
    if isinstance(data, dict):
        return len(data) > 0
    
    return True


def format_chart_number(value: float, decimals: int = 2) -> str:
    """
    Format numbers for chart display
    """
    if pd.isna(value):
        return "N/A"
    
    if abs(value) >= 1000000:
        return f"{value/1000000:.{decimals}f}M"
    elif abs(value) >= 1000:
        return f"{value/1000:.{decimals}f}K"
    else:
        return f"{value:.{decimals}f}"


def get_chart_theme() -> Dict[str, Any]:
    """
    Get standardized chart theme settings
    """
    return {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': 'white'},
        'colorway': [
            UI_COLORS["primary"],
            UI_COLORS["secondary"],
            UI_COLORS["accent"],
            UI_COLORS["success"],
            "#F59E0B",
            "#EF4444"
        ]
    }
