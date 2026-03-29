"""
Global CSS and layout helpers for the Siteworks Streamlit UI.
"""

from typing import List

import streamlit as st


def apply_global_styles() -> None:
    """Inject once per run: typography, tabs, sidebar density, scrollbars."""
    st.markdown(
        """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=IBM+Plex+Mono:wght@400;500&display=swap');

    html, body, [class*="css"]  {
        font-family: 'DM Sans', 'Segoe UI', system-ui, -apple-system, sans-serif;
    }

    h1, h2, h3 {
        font-weight: 600 !important;
        letter-spacing: -0.02em;
        color: #0f172a !important;
    }

    /* Main content width & breathing room */
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 4rem;
        max-width: 1280px;
    }

    /* Hero strip */
    div.sw-hero {
        background: linear-gradient(135deg, #f0fdfa 0%, #f8fafc 45%, #ecfeff 100%);
        border: 1px solid #ccfbf1;
        border-radius: 16px;
        padding: 1.05rem 1.35rem 0.9rem 1.35rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 24px -8px rgba(15, 118, 110, 0.15);
    }
    div.sw-hero h1 {
        font-size: 2.15rem !important;
        margin-bottom: 0.15rem !important;
        background: linear-gradient(90deg, #0f766e, #0e7490);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    div.sw-hero .sw-tagline {
        color: #334155;
        font-size: 1rem;
        margin: 0;
        font-weight: 500;
    }
    div.sw-hero .sw-badge-row {
        margin-top: 0.58rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        align-items: center;
    }
    span.sw-badge {
        display: inline-block;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 0.28rem 0.65rem;
        border-radius: 999px;
        border: 1px solid transparent;
    }
    span.sw-badge-live {
        background: #ecfdf5;
        color: #047857;
        border-color: #a7f3d0;
    }
    span.sw-badge-pilot {
        background: #fffbeb;
        color: #b45309;
        border-color: #fde68a;
    }
    span.sw-badge-course {
        background: #f1f5f9;
        color: #475569;
        border-color: #e2e8f0;
    }

    /* Scenario callout */
    div.sw-scenario {
        border-radius: 12px;
        border-left: 4px solid #f59e0b;
        background: #fffbeb;
        padding: 0.85rem 1.1rem;
        margin: 0 0 1.25rem 0;
        color: #78350f;
        font-size: 0.95rem;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: transparent;
        padding: 4px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 0.55rem 1rem;
        font-weight: 600;
        font-size: 0.92rem;
    }
    .stTabs [aria-selected="true"] {
        background: #ccfbf1 !important;
        color: #0f766e !important;
    }

    /* Sidebar section titles */
    section[data-testid="stSidebar"] h2 {
        font-size: 1rem !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.25rem;
    }
    section[data-testid="stSidebar"] hr {
        margin: 1.25rem 0;
        border-color: #e2e8f0;
    }

    /* Dataframes — subtle chrome */
    [data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        overflow: hidden;
    }

    /* Slider thumbs — teal */
    .stSlider [data-testid="stThumbValue"] {
        font-weight: 600;
    }

    /* Reduce noisy caption size in main */
    .stMain .stCaption {
        color: #475569 !important;
    }
    .stMain h4 {
        margin-top: 0.3rem;
        font-size: 1.24rem !important;
    }
    .stMain h5 {
        font-size: 1.07rem !important;
        color: #0f172a !important;
    }

    /* Section spacing rhythm */
    .sw-spacer {
        height: 0.9rem;
    }

    /* Snapshot cards */
    .sw-snapshot-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0.5rem 0 0.9rem 0;
    }
    .sw-snapshot-card {
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        background: #ffffff;
        padding: 0.9rem 1rem;
    }
    .sw-snapshot-card.is-leader {
        border-color: #99f6e4;
        box-shadow: 0 12px 30px -17px rgba(13, 148, 136, 0.5);
        background: linear-gradient(135deg, #ecfeff 0%, #ffffff 80%);
    }
    .sw-snapshot-card.is-secondary {
        background: #f8fafc;
        opacity: 0.95;
    }
    .sw-snapshot-role {
        margin: 0;
        font-size: 0.78rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #64748b;
        font-weight: 700;
    }
    .sw-snapshot-city {
        margin: 0.1rem 0 0 0;
        font-size: 1.01rem;
        color: #0f172a;
        font-weight: 600;
    }
    .sw-snapshot-score {
        margin: 0.2rem 0 0.05rem 0;
        font-size: 1.84rem;
        line-height: 1.08;
        color: #0f172a;
        font-weight: 700;
    }
    .sw-snapshot-sub {
        margin: 0;
        font-size: 0.84rem;
        color: #64748b;
    }
</style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(*, from_workbook: bool) -> None:
    """Hero header with data-source badges."""
    badge_live = (
        '<span class="sw-badge sw-badge-live">Excel workbook</span>'
        if from_workbook
        else '<span class="sw-badge sw-badge-pilot">Built-in pilot data</span>'
    )
    badge_course = '<span class="sw-badge sw-badge-course">CIVE-580</span>'

    st.markdown(
        f"""
<div class="sw-hero">
  <h1>Siteworks</h1>
  <p class="sw-tagline">Data center site selection — weighted sustainability scoring</p>
  <div class="sw-badge-row">{badge_live}{badge_course}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_scenario_banner(labels: List[str]) -> None:
    """Styled callout when drought / climate modifiers are on."""
    if not labels:
        return
    text = " · ".join(labels)
    st.markdown(
        f'<div class="sw-scenario"><strong>What-if mode:</strong> {text} — '
        f"scores are adjusted for exploration; not a forecast.</div>",
        unsafe_allow_html=True,
    )
