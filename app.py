# -*- coding: utf-8 -*-
"""
Datara — AI-Powered Data Workspace.
Refactored: theme, services, components, single entry point.
"""

import streamlit as st

from theme import FONT_LINKS, get_theme_css
from state import init_session_state, reset_app_state
from services import (
    load_data,
    file_size_mb,
    infer_data_types,
    profile_dataframe,
    ask_agent_for_analysis,
    ask_agent_suggested_questions,
    render_chart_fig,
)
from services.ai import ask_agent_chart_explanation
from components import (
    render_navbar,
    render_hero,
    render_upload_zone,
    render_file_pill,
    render_kpi_grid,
    render_action_row,
)
from components.tabs import (
    render_overview_tab,
    render_data_health_tab,
    render_findings_tab,
    render_charts_tab,
    render_ask_ai_tab,
)

st.set_page_config(
    page_title="Datara - AI-Powered Data Workspace",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_session_state()

# Apply design theme (fonts + CSS)
st.markdown(FONT_LINKS, unsafe_allow_html=True)
st.markdown(get_theme_css(), unsafe_allow_html=True)

# Layout: Navbar, Hero, Upload
render_navbar()
render_hero()
uploaded_file = render_upload_zone()

if uploaded_file is None:
    if st.session_state.last_uploaded_name is not None:
        reset_app_state()
    st.info("Upload your dataset to generate an instant executive summary and deep-dive analysis.")
    st.stop()

if st.session_state.last_uploaded_name != uploaded_file.name:
    st.session_state.analysis_result = None
    st.session_state.chat_history = []
    st.session_state.last_uploaded_name = uploaded_file.name
    st.session_state.suggested_questions = None
    st.session_state.chart_explanations = {}

try:
    df = load_data(uploaded_file)
except Exception as e:
    st.error(str(e))
    st.stop()

profile = profile_dataframe(df)
size_mb = file_size_mb(uploaded_file)
n_rows, n_cols = df.shape
result = st.session_state.analysis_result

render_file_pill(uploaded_file.name, size_mb, infer_data_types(df))
if profile.get("readiness_summary"):
    st.caption(profile["readiness_summary"])

if st.session_state.suggested_questions is None:
    with st.spinner("Preparing suggested questions..."):
        st.session_state.suggested_questions = ask_agent_suggested_questions(df, profile)
    st.rerun()

render_kpi_grid(n_rows, n_cols, profile["missing_total"], profile["duplicate_rows"], profile["readiness_pct"])


def do_generate():
    st.session_state.analysis_result = ask_agent_for_analysis(df, profile)


render_action_row(profile, do_generate)

tab_overview, tab_health, tab_findings, tab_charts, tab_ai = st.tabs([
    "Overview",
    "Data Health",
    "Top Findings",
    "Charts",
    "Ask AI",
])

with tab_overview:
    render_overview_tab(df, profile, result, uploaded_file)

with tab_health:
    render_data_health_tab(profile)

with tab_findings:
    render_findings_tab(result)

with tab_charts:
    render_charts_tab(df, result)

with tab_ai:
    render_ask_ai_tab(df, result, profile, st.session_state.suggested_questions or [])
