# -*- coding: utf-8 -*-
"""
Datara — AI-Powered Data Workspace (Streamlit).
Single-file app: only app.py + theme.py needed for GitHub.
"""

import json
import pandas as pd
import plotly.express as px
import streamlit as st
from openai import OpenAI

from theme import FONT_LINKS, get_theme_css

# -----------------------------------------------------------------------------
# Page config & theme
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Datara - AI-Powered Data Workspace",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(FONT_LINKS, unsafe_allow_html=True)
st.markdown(get_theme_css(), unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------
def init_session_state():
    for key, default in [
        ("analysis_result", None),
        ("chat_history", []),
        ("last_uploaded_name", None),
        ("theme", "dark"),
        ("pending_question", None),
        ("suggested_questions", None),
        ("chart_explanations", {}),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

def reset_app_state():
    st.session_state.analysis_result = None
    st.session_state.chat_history = []
    st.session_state.last_uploaded_name = None
    st.session_state.suggested_questions = None
    st.session_state.chart_explanations = {}

init_session_state()

# -----------------------------------------------------------------------------
# Data & profile
# -----------------------------------------------------------------------------
def load_data(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)

def file_size_mb(uploaded_file):
    return round(uploaded_file.size / (1024 * 1024), 1)

def infer_data_types(df):
    kinds = set()
    for col in df.columns:
        dtype = str(df[col].dtype)
        if "int" in dtype or "float" in dtype:
            kinds.add("Numeric")
        elif "object" in dtype or "category" in dtype:
            kinds.add("Categorical")
        elif "datetime" in dtype:
            kinds.add("Time-series")
    return ", ".join(sorted(kinds)) if kinds else "Mixed"

def profile_dataframe(df):
    n = len(df)
    profile = {
        "missing_pct": {}, "missing_total": 0, "duplicate_rows": int(df.duplicated().sum()),
        "total_rows": n, "total_columns": len(df.columns), "column_types": {},
        "unique_counts": {}, "high_null_columns": [], "quality_recommendations": [],
        "recommended_measure_columns": [], "recommended_grouping_columns": [],
        "id_like_columns": [], "text_heavy_columns": [],
    }
    for col in df.columns:
        s = df[col]
        null_count = s.isna().sum()
        pct = round(100 * null_count / n, 1) if n else 0
        profile["missing_pct"][col] = pct
        profile["missing_total"] += null_count
        profile["unique_counts"][col] = int(s.nunique())
        dtype = str(s.dtype)
        profile["column_types"][col] = "numeric" if ("int" in dtype or "float" in dtype) else "datetime" if "datetime" in dtype else "categorical"
        if pct > 20:
            profile["high_null_columns"].append((col, pct))
        if col.lower().endswith("id") or col.lower() == "id" or (profile["unique_counts"][col] == n and n > 10):
            profile["id_like_columns"].append(col)
        if dtype == "object" and s.notna().any():
            try:
                if s.dropna().astype(str).str.len().max() > 80:
                    profile["text_heavy_columns"].append(col)
            except Exception:
                pass
    profile["high_null_columns"].sort(key=lambda x: -x[1])
    num_cols = [c for c, t in profile["column_types"].items() if t == "numeric"]
    cat_cols = [c for c, t in profile["column_types"].items() if t == "categorical"]
    profile["recommended_measure_columns"] = num_cols[:15]
    profile["recommended_grouping_columns"] = [c for c in cat_cols if profile["unique_counts"].get(c, 0) <= 50 and c not in profile["id_like_columns"]][:15]
    if not profile["recommended_grouping_columns"] and cat_cols:
        profile["recommended_grouping_columns"] = cat_cols[:10]
    avg_null = sum(profile["missing_pct"].values()) / len(profile["missing_pct"]) if profile["missing_pct"] else 0
    score = max(0, min(100, round(100 - avg_null - min(15, profile["duplicate_rows"] // 50) - min(20, len(profile["high_null_columns"]) * 5))))
    profile["readiness_pct"] = score
    factors = []
    if avg_null > 5:
        factors.append(f"Missing values ({avg_null:.0f}% of cells on average)")
    if profile["duplicate_rows"] > 0:
        factors.append(f"Duplicate rows ({profile['duplicate_rows']})")
    if profile["high_null_columns"]:
        factors.append(f"Columns with >20% nulls: {len(profile['high_null_columns'])}")
    profile["readiness_factors"] = factors
    profile["readiness_summary"] = "Data is suitable for analysis." if score >= 70 else "Data has quality issues; review before heavy analysis."
    for col, pct in profile["high_null_columns"][:5]:
        profile["quality_recommendations"].append(f"Column '{col}' has {pct}% missing values.")
    if profile["duplicate_rows"] > 0:
        profile["quality_recommendations"].append(f"Remove or review {profile['duplicate_rows']} duplicate rows.")
    if not profile["quality_recommendations"]:
        profile["quality_recommendations"].append("No major quality issues detected.")
    return profile

# -----------------------------------------------------------------------------
# AI (OpenAI)
# -----------------------------------------------------------------------------
def _get_client():
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def parse_analysis_json(text):
    text = (text or "").strip()
    if not text or text.find("{") == -1:
        return None
    start = text.find("{")
    depth, end = 0, -1
    for i in range(start, len(text)):
        if text[i] == "{": depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        return None
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass
    return {"summary": {"overview": "Analysis could not be parsed.", "key_insights": [], "recommendations": [], "final_summary": ""}, "charts": []}

def _default_analysis_result():
    return {"summary": {"overview": "Analysis unavailable.", "top_finding": "", "biggest_risk": "", "biggest_opportunity": "", "notable_trend": "", "data_quality_concern": "", "recommended_next_step": "", "key_insights": [], "recommendations": [], "final_summary": ""}, "charts": []}

def _validate_chart(df, profile, ch):
    valid = set(df.columns)
    x, y = ch.get("x_column"), ch.get("y_column")
    agg = ch.get("aggregation") or "sum"
    if not x or x not in valid:
        return False
    if agg == "count":
        return True
    if not y or y not in valid:
        return False
    ctypes = profile.get("column_types", {})
    xt, yt = ctypes.get(x), ctypes.get(y)
    chart_type = (ch.get("chart_type") or "bar").lower()
    if chart_type in ("bar", "line", "pie"):
        return yt == "numeric" and (xt == "categorical" or xt == "datetime" or profile["unique_counts"].get(x, 0) <= 100)
    if chart_type == "scatter":
        return xt == "numeric" and yt == "numeric"
    return True

def ask_agent_for_analysis(df, profile):
    client = _get_client()
    columns = list(df.columns)
    measure_cols = profile.get("recommended_measure_columns", []) or [c for c, t in profile.get("column_types", {}).items() if t == "numeric"][:10]
    group_cols = profile.get("recommended_grouping_columns", []) or [c for c, t in profile.get("column_types", {}).items() if t == "categorical"][:10]
    sample_rows = df.head(12).to_dict(orient="records")
    for row in sample_rows:
        for k, v in row.items():
            if hasattr(v, "isoformat"):
                row[k] = v.isoformat()
    prompt = f"""You are a professional data analysis AI agent. Analyze this dataset and return ONLY valid JSON.

COLUMNS: {columns}
TYPES: {profile.get('column_types', {})}
MEASURE COLUMNS (use for y-axis): {measure_cols}
GROUPING COLUMNS (use for x-axis): {group_cols}
SAMPLE ROWS: {json.dumps(sample_rows, default=str)}
DATA QUALITY: {profile.get('missing_total')} missing cells, {profile.get('duplicate_rows')} duplicate rows.

Return this exact JSON structure (no markdown, no extra text):
{{ "summary": {{ "overview": "...", "top_finding": "...", "biggest_risk": "...", "biggest_opportunity": "...", "notable_trend": "...", "data_quality_concern": "...", "recommended_next_step": "...", "key_insights": [], "recommendations": [], "final_summary": "" }}, "charts": [ {{ "title": "...", "chart_type": "bar", "x_column": "...", "y_column": "...", "aggregation": "sum", "explanation": "..." }} ] }}
RULES: Use ONLY column names from COLUMNS. Return exactly 2 charts. Include "explanation" for each chart."""
    try:
        response = client.responses.create(model="gpt-4.1-mini", input=prompt)
        raw = (response.output_text or "").strip()
        result = parse_analysis_json(raw)
        if not result:
            result = _default_analysis_result()
        summary = result.get("summary") or {}
        for key in ("top_finding", "biggest_risk", "biggest_opportunity", "notable_trend", "data_quality_concern", "recommended_next_step"):
            if key not in summary:
                summary[key] = ""
        result["summary"] = summary
        valid_charts = []
        for ch in result.get("charts", []):
            if _validate_chart(df, profile, ch):
                if "explanation" not in ch:
                    ch["explanation"] = "Chart of selected metrics."
                valid_charts.append(ch)
        result["charts"] = valid_charts[:2] if valid_charts else []
        return result
    except Exception as e:
        return {"summary": {**_default_analysis_result()["summary"], "overview": f"Analysis failed: {str(e)[:120]}."}, "charts": []}

def ask_agent_suggested_questions(df, profile):
    client = _get_client()
    columns = list(df.columns)[:40]
    col_types = profile.get("column_types", {})
    measure = profile.get("recommended_measure_columns", [])[:8]
    group = profile.get("recommended_grouping_columns", [])[:8]
    readiness = profile.get("readiness_pct", 100)
    high_null = [c for c, _ in profile.get("high_null_columns", [])[:5]]
    dup_count = profile.get("duplicate_rows", 0)
    n_rows = profile.get("total_rows", len(df))
    quality_note = ""
    if readiness < 70 or high_null or dup_count > 0:
        quality_note = " Data quality is a concern. Include at least one question about data quality or reliability."
    prompt = f"""Generate 5-6 short suggested questions for this dataset. Columns: {columns}. Types: {col_types}. Measure columns: {measure}. Group columns: {group}. Rows: {n_rows}. Readiness: {readiness}. High null columns: {high_null or 'none'}. Duplicates: {dup_count}.{quality_note} Return ONLY a JSON array of strings, e.g. ["Q1?", "Q2?"]."""
    try:
        response = client.responses.create(model="gpt-4.1-mini", input=prompt)
        raw = (response.output_text or "").strip()
        start, end = raw.find("["), raw.rfind("]") + 1
        if start >= 0 and end > start:
            out = json.loads(raw[start:end])
            if isinstance(out, list) and len(out) >= 3:
                return [str(q).strip()[:100] for q in out[:6]]
    except Exception:
        pass
    fallback = [f"Which {group[0]} has the highest {measure[0]}?"] if measure and group else []
    fallback += ["What are the main drivers?", "Are there outliers?", "What should I investigate next?"]
    if readiness < 70 or high_null:
        fallback.append("How reliable is this data?")
    while len(fallback) < 5:
        fallback.append("What are the key patterns?")
    return fallback[:6]

def ask_agent_chart_explanation(chart_spec, df):
    client = _get_client()
    try:
        title = chart_spec.get("title", "Chart")
        x, y = chart_spec.get("x_column"), chart_spec.get("y_column")
        agg = chart_spec.get("aggregation", "sum")
        response = client.responses.create(model="gpt-4.1-mini", input=f"Chart: {title}. X: {x}, Y: {y}, aggregation: {agg}. In 1-2 sentences, what does this chart show. No preamble.")
        return (response.output_text or "").strip()[:300]
    except Exception:
        return "This chart visualizes the selected dimensions and measures."

def ask_agent_question(df, analysis_result, user_question, profile=None):
    client = _get_client()
    columns = list(df.columns)
    sample = df.head(15).to_dict(orient="records")
    for row in sample:
        for k, v in row.items():
            if hasattr(v, "isoformat"):
                row[k] = v.isoformat()
    profile_summary = f"Data profile: {profile.get('total_rows')} rows, {profile.get('total_columns')} columns; readiness {profile.get('readiness_pct')}%." if profile else ""
    prompt = f"""You are an analytical data assistant. {profile_summary} Columns: {columns}. Sample: {json.dumps(sample, default=str)}. Summary: {json.dumps(analysis_result.get('summary', {}) if isinstance(analysis_result, dict) else {}, ensure_ascii=False)}. User: {user_question}. Answer in 2-4 short paragraphs from the data."""
    try:
        response = client.responses.create(model="gpt-4.1-mini", input=prompt)
        return (response.output_text or "").strip()
    except Exception as e:
        return f"Sorry: {str(e)[:100]}."

def prepare_chart_data(df, x_column, y_column, aggregation):
    data = df.copy()
    if aggregation == "count" or not y_column:
        data = data.groupby(x_column, as_index=False).size()
        data.columns = [x_column, "count"]
        return data, "count"
    if aggregation == "sum":
        data = data.groupby(x_column, as_index=False)[y_column].sum()
    elif aggregation == "mean":
        data = data.groupby(x_column, as_index=False)[y_column].mean()
    else:
        data = data.groupby(x_column, as_index=False)[y_column].sum()
    return data, y_column

def render_chart_fig(df, chart, is_dark):
    chart_type = (chart.get("chart_type") or "bar").lower()
    x_column = chart.get("x_column")
    y_column = chart.get("y_column")
    aggregation = chart.get("aggregation") or "sum"
    if not x_column or x_column not in df.columns:
        return None
    if aggregation != "count" and (not y_column or y_column not in df.columns):
        return None
    data, final_y = prepare_chart_data(df, x_column, y_column or x_column, aggregation)
    if chart_type == "bar":
        fig = px.bar(data, x=x_column, y=final_y, title=None, template="plotly_white")
    elif chart_type == "line":
        fig = px.line(data, x=x_column, y=final_y, title=None, template="plotly_white")
    elif chart_type == "pie":
        fig = px.pie(data, names=x_column, values=final_y, title=None)
    elif chart_type == "scatter":
        fig = px.scatter(data, x=x_column, y=final_y, title=None, template="plotly_white")
    else:
        return None
    if is_dark:
        fig.update_layout(paper_bgcolor="rgba(18,18,22,0.35)", plot_bgcolor="rgba(18,18,22,0.15)", font=dict(color="#F3F4F6", size=12), margin=dict(l=24, r=24, t=12, b=24), xaxis=dict(gridcolor="rgba(255,255,255,0.06)"), yaxis=dict(gridcolor="rgba(255,255,255,0.06)"))
    else:
        fig.update_layout(paper_bgcolor="rgba(255,255,255,0.6)", plot_bgcolor="rgba(248,250,252,0.8)", font=dict(color="#0f172a", size=12), margin=dict(l=24, r=24, t=12, b=24), xaxis=dict(gridcolor="rgba(15,23,42,0.08)"), yaxis=dict(gridcolor="rgba(15,23,42,0.08)"))
    return fig

# -----------------------------------------------------------------------------
# UI: Navbar, Hero, Upload, File pill, KPI, Action row
# -----------------------------------------------------------------------------
def render_navbar():
    st.markdown("""<header style="display:flex;justify-content:space-between;align-items:center;padding:16px 0;border-bottom:1px solid rgba(245,240,255,0.05);margin-bottom:-16px;">
        <div style="display:flex;align-items:center;gap:16px;">
            <a href="#" style="display:flex;align-items:center;gap:8px;text-decoration:none;">
                <div style="width:24px;height:24px;background:#a78bfa;border-radius:6px;box-shadow:0 0 15px #8b5cf6;"></div>
                <span style="font-family:'Inter',sans-serif;font-weight:600;font-size:16px;color:#F5F0FF;">Datara</span>
            </a>
            <span style="font-size:13px;color:#807a9e;border-left:1px solid rgba(245,240,255,0.05);padding-left:16px;">AI-Powered Data Workspace</span>
        </div>
    </header>""", unsafe_allow_html=True)

def render_hero():
    st.markdown('<p style="margin-top:24px;"></p>', unsafe_allow_html=True)
    st.title("Is your data usable? What matters? What's next?")
    st.caption("Upload your dataset to generate an instant executive summary and deep-dive analysis.")

def render_file_pill(file_name, size_mb, data_type):
    st.markdown(f'<div style="display:inline-flex;align-items:center;gap:8px;background:#1c162b;border:1px solid rgba(245,240,255,0.1);padding:6px 14px;border-radius:999px;font-size:13px;color:#F5F0FF;margin-top:8px;">{file_name} <span style="color:#807a9e;font-size:12px;">{size_mb:.2f} MB</span> <span style="color:#807a9e;margin-left:4px;">· {data_type}</span></div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
render_navbar()
render_hero()
uploaded_file = st.file_uploader("Upload CSV or XLSX — drag & drop or browse", type=["csv", "xlsx"], key="main_uploader")

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

k1, k2, k3, k4, k5 = st.columns(5)
with k1: st.metric("Total Rows", f"{n_rows:,}")
with k2: st.metric("Total Columns", n_cols)
with k3: st.metric("Missing Values", profile["missing_total"])
with k4: st.metric("Duplicates", profile["duplicate_rows"])
with k5: st.metric("Readiness %", f"{profile['readiness_pct']}%")

if st.button("Generate Executive Summary", key="cta_gen"):
    with st.spinner("Analyzing..."):
        st.session_state.analysis_result = ask_agent_for_analysis(df, profile)
    st.rerun()
if profile.get("readiness_factors"):
    with st.expander("What affects the readiness score?"):
        for f in profile["readiness_factors"]:
            st.write("-", str(f) if f is not None else "—")

tab_overview, tab_health, tab_findings, tab_charts, tab_ai = st.tabs(["Overview", "Data Health", "Top Findings", "Charts", "Ask AI"])

with tab_overview:
    if result and result.get("summary", {}).get("overview"):
        st.write(result["summary"]["overview"])
    else:
        st.write(f"Dataset has **{n_rows:,}** rows and **{n_cols}** columns. Generate summary for an AI overview.")
    ctypes = profile.get("column_types") or {}
    if ctypes:
        num = [c for c, t in ctypes.items() if t == "numeric"]
        cat = [c for c, t in ctypes.items() if t == "categorical"]
        dt = [c for c, t in ctypes.items() if t == "datetime"]
        if num: st.caption("**Numeric:** " + ", ".join(num[:15]) + (" …" if len(num) > 15 else ""))
        if cat: st.caption("**Categorical:** " + ", ".join(cat[:15]) + (" …" if len(cat) > 15 else ""))
        if dt: st.caption("**Datetime:** " + ", ".join(dt))
    meas, grp = profile.get("recommended_measure_columns") or [], profile.get("recommended_grouping_columns") or []
    if meas or grp: st.caption("**Measures:** " + (", ".join(meas[:10]) if meas else "—") + " · **Groups:** " + (", ".join(grp[:10]) if grp else "—"))
    st.caption("Data preview")
    st.dataframe(df.head(200), height=280, use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Export CSV", df.to_csv(index=False).encode("utf-8"), file_name=uploaded_file.name or "data.csv", mime="text/csv", key="dl_csv")
    with c2:
        rep = (result.get("summary", {}) if result else {}) or {}
        lines = ["# Executive Summary", "", "## Overview", rep.get("overview") or "—", "", "## Data Readiness", f"Score: {profile.get('readiness_pct', 0)}/100.", "", "## Top Finding", rep.get("top_finding") or "—", "", "## Biggest Risk", rep.get("biggest_risk") or "—", "", "## Biggest Opportunity", rep.get("biggest_opportunity") or "—", "", "## Recommended Next Step", rep.get("recommended_next_step") or "—", "", "## Key Insights"] + [f"- {x}" for x in (rep.get("key_insights") or [])] + ["", "## Recommendations"] + [f"- {x}" for x in (rep.get("recommendations") or [])]
        if result and result.get("charts"):
            lines += ["", "## Chart Explanations"] + [f"- **{ch.get('title', 'Chart')}:** " + (ch.get("explanation") or "") for ch in result["charts"]]
        st.download_button("Executive report", "\n".join(lines).encode("utf-8"), file_name="executive_report.md", mime="text/markdown", key="dl_report")

with tab_health:
    total_cells = (profile.get("total_rows") or 0) * max(len(profile.get("column_types") or {}), 1)
    missing_pct = (100 * profile["missing_total"] / total_cells) if total_cells else 0
    st.write("**Missing values:**", profile["missing_total"], f"cells ({missing_pct:.1f}%)")
    st.write("**Duplicate rows:**", profile["duplicate_rows"])
    if profile.get("high_null_columns"):
        st.write("**Columns with highest null %:**")
        for col, pct in profile["high_null_columns"][:10]:
            st.write(f"- {col}: {pct}% null")
    if profile.get("text_heavy_columns"):
        st.write("**Text-heavy:**", ", ".join(profile["text_heavy_columns"][:8]))
    recs = profile.get("quality_recommendations") or []
    if recs:
        st.write("**Cleanup recommendations:**")
        for rec in recs:
            st.write("-", rec)
    if not recs and profile["missing_total"] == 0 and profile["duplicate_rows"] == 0:
        st.caption("No major data health issues detected.")

with tab_findings:
    if result is None:
        st.caption("Generate summary above to see findings.")
    else:
        summary = result.get("summary") or {}
        for label, key in [("Top Finding", "top_finding"), ("Biggest Risk", "biggest_risk"), ("Biggest Opportunity", "biggest_opportunity"), ("Recommended Next Step", "recommended_next_step")]:
            value = (summary.get(key) or "").strip() or "—"
            st.markdown(f"**{label}**")
            st.markdown(value)

with tab_charts:
    if result is None:
        st.caption("Generate summary above to see charts.")
    else:
        charts = (result.get("charts") or [])[:2]
        if not charts:
            st.caption("No charts generated.")
        else:
            is_dark = st.session_state.get("theme", "dark") == "dark"
            for i, ch in enumerate(charts):
                st.write("**" + (ch.get("title") or "Chart") + "**")
                fig = render_chart_fig(df, ch, is_dark)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, key=f"chart_{i}")
                expl = ch.get("explanation") or st.session_state.get("chart_explanations", {}).get(i)
                if expl:
                    st.caption(expl)
                elif st.button("Explain this chart", key=f"explain_{i}"):
                    with st.spinner("..."):
                        st.session_state.chart_explanations[i] = ask_agent_chart_explanation(ch, df)
                    st.rerun()

with tab_ai:
    suggested_qs = st.session_state.suggested_questions or []
    st.caption("Suggested questions (from this dataset):")
    if suggested_qs:
        cols = st.columns(3)
        for i, q in enumerate(suggested_qs):
            with cols[i % 3]:
                if st.button(q[:60] + ("…" if len(q) > 60 else ""), key=f"sug_{i}"):
                    st.session_state.pending_question = q
                    st.rerun()
    if st.session_state.get("pending_question"):
        q = st.session_state.pending_question
        st.session_state.pending_question = None
        st.session_state.chat_history.append({"role": "user", "content": q})
        with st.spinner("..."):
            answer = ask_agent_question(df, result or {}, q, profile)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()
    for msg in st.session_state.get("chat_history", []):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    user_question = st.chat_input("Ask anything about your data...")
    if user_question:
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        with st.chat_message("assistant"):
            answer = ask_agent_question(df, result or {}, user_question, profile)
            st.write(answer)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()
