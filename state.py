# -*- coding: utf-8 -*-
"""Session state initialization and reset."""

import streamlit as st


def init_session_state():
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_uploaded_name" not in st.session_state:
        st.session_state.last_uploaded_name = None
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None
    if "suggested_questions" not in st.session_state:
        st.session_state.suggested_questions = None
    if "chart_explanations" not in st.session_state:
        st.session_state.chart_explanations = {}


def reset_app_state():
    st.session_state.analysis_result = None
    st.session_state.chat_history = []
    st.session_state.last_uploaded_name = None
    st.session_state.suggested_questions = None
    st.session_state.chart_explanations = {}
