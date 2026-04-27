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

    :root {
        --sw-bg: #f4f7fb;
        --sw-surface: #ffffff;
        --sw-surface-soft: #f7faff;
        --sw-border: #e7edf5;
        --sw-border-strong: #d5dfeb;
        --sw-text: #0f172a;
        --sw-muted: #334155;
        --sw-accent: #0f766e;
        --sw-radius: 14px;
        --sw-pad: 0.95rem;
        --sw-shadow: 0 14px 34px -24px rgba(15, 23, 42, 0.35);
    }

    .stApp {
        background: linear-gradient(180deg, #f4f7fb 0%, #f7f9fc 38%, #f4f7fb 100%);
    }

    h1, h2, h3 {
        font-weight: 600 !important;
        letter-spacing: -0.02em;
        color: var(--sw-text) !important;
    }

    /* Main content width & breathing room */
    .block-container {
        padding-top: 0.9rem;
        padding-bottom: 2.4rem;
        max-width: 1240px;
    }

    /* Hero strip */
    div.sw-hero {
        background: linear-gradient(135deg, #f0fdfa 0%, #f8fafc 45%, #ecfeff 100%);
        border: 1px solid #bde8e1;
        border-radius: 16px;
        padding: 0.95rem 1.2rem 0.82rem 1.2rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 12px 30px -22px rgba(15, 118, 110, 0.48);
    }
    div.sw-hero h1 {
        font-size: 2.16rem !important;
        margin-bottom: 0.2rem !important;
        background: linear-gradient(90deg, #0f766e, #0e7490);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    div.sw-hero .sw-tagline {
        color: var(--sw-muted);
        font-size: 1.03rem;
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

    /* Top summary KPI row */
    .sw-kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.65rem;
        margin: 0.45rem 0 0.8rem 0;
    }
    .sw-kpi-card {
        background: var(--sw-surface);
        border: 1px solid #e8eef6;
        border-radius: var(--sw-radius);
        padding: 0.85rem 0.9rem;
        box-shadow: var(--sw-shadow);
    }
    .sw-kpi-label {
        margin: 0;
        font-size: 0.78rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
    }
    .sw-kpi-value {
        margin: 0.28rem 0 0.12rem 0;
        font-size: 1.48rem;
        font-weight: 700;
        color: var(--sw-text);
        line-height: 1.1;
    }
    .sw-kpi-sub {
        margin: 0;
        font-size: 0.84rem;
        color: #64748b;
    }

    .stMain [data-testid="stMetric"] {
        background: #f8fbff;
        border: 1px solid var(--sw-border);
        border-radius: 10px;
        padding: 0.4rem 0.55rem;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #f8fbff;
        padding: 3px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 0.43rem 0.84rem;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background: #e8f4ff !important;
        color: #1d4e89 !important;
        border: 1px solid #c7d9ef !important;
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
        border: 1px solid var(--sw-border);
        border-radius: 12px;
        overflow: hidden;
        box-shadow: var(--sw-shadow);
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #ecf1f7 !important;
        border-radius: var(--sw-radius) !important;
        background: var(--sw-surface);
        box-shadow: var(--sw-shadow);
    }

    /* Inputs and controls */
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div {
        border-color: var(--sw-border-strong) !important;
        border-radius: 10px !important;
        background: #ffffff !important;
    }
    [data-baseweb="select"] > div:hover,
    [data-baseweb="input"] > div:hover {
        border-color: #9fb5cf !important;
    }
    [data-baseweb="select"] > div:focus-within,
    [data-baseweb="input"] > div:focus-within {
        box-shadow: 0 0 0 2px rgba(29, 78, 137, 0.16) !important;
        border-color: #7d9fc4 !important;
    }
    [data-baseweb="tag"] {
        border-radius: 999px !important;
        border: 1px solid #a9bdd8 !important;
        background: #deebfb !important;
        box-shadow: inset 0 0 0 1px #c9d9ed;
        padding: 0.1rem 0.12rem;
    }
    [data-baseweb="tag"] span {
        color: #1e3a5f !important;
        font-weight: 600 !important;
    }
    [data-baseweb="tag"] svg {
        color: #335a86 !important;
    }
    .stButton > button {
        border-radius: 10px;
        border: 1px solid var(--sw-border-strong);
        background: #f8fbff;
        font-weight: 600;
    }
    .stButton > button:hover {
        border-color: #9fb5cf;
        background: #edf4fc;
    }

    /* Slider thumbs — teal */
    .stSlider [data-testid="stThumbValue"] {
        font-weight: 600;
    }

    /* Reduce noisy caption size in main */
    .stMain .stCaption {
        color: #334155 !important;
    }
    .stMain h4 {
        margin-top: 0.38rem;
        font-size: 1.36rem !important;
        font-weight: 700 !important;
    }
    .stMain h5 {
        font-size: 1.14rem !important;
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* Section spacing rhythm */
    .sw-spacer {
        height: 0.72rem;
    }

    /* Snapshot cards */
    .sw-snapshot-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.65rem;
        margin: 0.4rem 0 0.7rem 0;
    }
    .sw-snapshot-card {
        border-radius: var(--sw-radius);
        border: 1px solid #e8eef6;
        background: var(--sw-surface);
        padding: var(--sw-pad);
        box-shadow: var(--sw-shadow);
    }
    .sw-snapshot-card.is-leader {
        border-color: #bfe7dc;
        box-shadow: 0 10px 22px -16px rgba(70, 120, 112, 0.32);
        background: linear-gradient(135deg, #f3fbf8 0%, #ffffff 80%);
    }
    .sw-snapshot-card.is-secondary {
        background: var(--sw-surface-soft);
        opacity: 0.95;
    }
    .sw-snapshot-role {
        margin: 0;
        font-size: 0.82rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #64748b;
        font-weight: 700;
    }
    .sw-snapshot-city {
        margin: 0.1rem 0 0 0;
        font-size: 1.08rem;
        color: #0f172a;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.45rem;
    }
    .sw-city-dot {
        width: 0.62rem;
        height: 0.62rem;
        border-radius: 999px;
        display: inline-block;
        flex: 0 0 auto;
    }
    .sw-snapshot-score {
        margin: 0.2rem 0 0.05rem 0;
        font-size: 2.0rem;
        line-height: 1.08;
        color: #0f172a;
        font-weight: 700;
    }
    .sw-snapshot-sub {
        margin: 0;
        font-size: 0.88rem;
        color: #64748b;
    }

    /* Interpretation cards */
    .sw-insight-card {
        background: var(--sw-surface-soft);
        border: 1px solid #e8eef6;
        border-radius: var(--sw-radius);
        padding: var(--sw-pad);
        min-height: 128px;
    }
    .sw-insight-title {
        margin: 0 0 0.35rem 0;
        color: #1e293b;
        font-size: 0.86rem;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        font-weight: 700;
    }
    .sw-insight-body {
        margin: 0;
        color: #334155;
        font-size: 0.96rem;
        line-height: 1.45;
    }
    .sw-insight-key {
        margin: 0 0 0.58rem 0;
        font-size: 1.02rem;
        color: #0f172a;
        font-weight: 700;
    }

    @media (max-width: 1100px) {
        .sw-kpi-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    @media (max-width: 760px) {
        .sw-kpi-grid,
        .sw-snapshot-grid {
            grid-template-columns: 1fr;
        }
        .block-container {
            padding-top: 0.65rem;
        }
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
        else '<span class="sw-badge sw-badge-pilot">Workbook not loaded</span>'
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


def render_kpi_strip(cards: List[dict]) -> None:
    """Render compact SaaS-style KPI tiles under the hero."""
    parts = []
    for c in cards:
        label = c.get("label", "")
        value = c.get("value", "")
        sub = c.get("sub", "")
        parts.append(
            (
                '<div class="sw-kpi-card">'
                f'<p class="sw-kpi-label">{label}</p>'
                f'<p class="sw-kpi-value">{value}</p>'
                f'<p class="sw-kpi-sub">{sub}</p>'
                "</div>"
            )
        )
    st.markdown(f'<div class="sw-kpi-grid">{"".join(parts)}</div>', unsafe_allow_html=True)
