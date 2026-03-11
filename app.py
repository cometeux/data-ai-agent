import json
import pandas as pd
import streamlit as st
import plotly.express as px
from openai import OpenAI

st.set_page_config(
    page_title="Data Analysis AI Agent",
    page_icon="📊",
    layout="wide"
)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# Session state
# -----------------------------
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_uploaded_name" not in st.session_state:
    st.session_state.last_uploaded_name = None


# -----------------------------
# Helpers
# -----------------------------
def reset_app_state():
    st.session_state.analysis_result = None
    st.session_state.chat_history = []
    st.session_state.last_uploaded_name = None


def load_data(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


def file_size_mb(uploaded_file):
    return round(uploaded_file.size / (1024 * 1024), 1)


def ask_agent_for_analysis(df):
    columns = list(df.columns)
    dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
    sample_rows = df.head(10).to_dict(orient="records")

    prompt = f"""
You are a professional data analysis AI agent.

Analyze the uploaded dataset and return ONLY valid JSON.

Dataset columns:
{columns}

Dataset types:
{dtypes}

Sample rows:
{sample_rows}

Return JSON in exactly this structure:
{{
  "summary": {{
    "overview": "brief overview of the dataset",
    "key_insights": [
      "insight 1",
      "insight 2",
      "insight 3"
    ],
    "recommendations": [
      "recommendation 1",
      "recommendation 2"
    ],
    "final_summary": "clear professional final summary"
  }},
  "charts": [
    {{
      "title": "chart title",
      "chart_type": "bar",
      "x_column": "exact column name",
      "y_column": "exact column name",
      "aggregation": "sum"
    }},
    {{
      "title": "chart title",
      "chart_type": "line",
      "x_column": "exact column name",
      "y_column": "exact column name",
      "aggregation": "mean"
    }}
  ]
}}

Rules:
- Return at least 2 charts
- chart_type must be one of: bar, line, pie, scatter
- aggregation must be one of: sum, mean, count, none
- use exact dataset column names
- choose useful charts for understanding the data
- keep the summary concise and practical
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return json.loads(response.output_text)


def ask_agent_question(df, analysis_result, user_question):
    columns = list(df.columns)
    sample_rows = df.head(10).to_dict(orient="records")

    prompt = f"""
You are a helpful data analysis AI agent.

Dataset columns:
{columns}

Sample rows:
{sample_rows}

Existing analysis summary:
{json.dumps(analysis_result, ensure_ascii=False)}

User follow-up question:
{user_question}

Answer the user's question clearly and directly based only on the uploaded data and existing analysis.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text


def prepare_chart_data(df, x_column, y_column, aggregation):
    data = df.copy()

    if aggregation == "sum":
        data = data.groupby(x_column, as_index=False)[y_column].sum()
    elif aggregation == "mean":
        data = data.groupby(x_column, as_index=False)[y_column].mean()
    elif aggregation == "count":
        data = data.groupby(x_column, as_index=False).size()
        data.columns = [x_column, "count"]
        y_column = "count"

    return data, y_column


def render_chart(df, chart):
    chart_type = chart["chart_type"]
    x_column = chart["x_column"]
    y_column = chart["y_column"]
    aggregation = chart["aggregation"]
    title = chart["title"]

    data, final_y = prepare_chart_data(df, x_column, y_column, aggregation)

    if chart_type == "bar":
        fig = px.bar(data, x=x_column, y=final_y, title=title, template="plotly_white")
    elif chart_type == "line":
        fig = px.line(data, x=x_column, y=final_y, title=title, template="plotly_white")
    elif chart_type == "pie":
        fig = px.pie(data, names=x_column, values=final_y, title=title)
    elif chart_type == "scatter":
        fig = px.scatter(data, x=x_column, y=final_y, title=title, template="plotly_white")
    else:
        return

    fig.update_layout(
        paper_bgcolor="rgba(255,255,255,0.96)",
        plot_bgcolor="rgba(255,255,255,0.96)",
        margin=dict(l=20, r=20, t=55, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)


# -----------------------------
# Custom UI (ALL TEXT BLACK)
# -----------------------------
st.markdown("""
<style>

/* FORCE ALL TEXT TO BLACK */
html, body, [class*="css"], p, span, div, label {
    color: #000000 !important;
}

/* Streamlit file uploader text */
[data-testid="stFileUploader"] * {
    color: #000000 !important;
}

/* Chat input text */
[data-testid="stChatInput"] * {
    color: #000000 !important;
}

/* Placeholder text */
::placeholder {
    color: #444444 !important;
}

/* Input fields */
input, textarea {
    color: #000000 !important;
}

/* Buttons keep white text */
div.stButton > button {
    border-radius: 999px !important;
    min-height: 52px !important;
    padding: 0 26px !important;

    background: linear-gradient(135deg, #6c72ff, #5a6cff) !important;
    color: #ffffff !important;

    border: none !important;
    font-weight: 600 !important;
    font-size: 16px !important;

    box-shadow: 0 6px 18px rgba(90,108,255,0.35) !important;
}
div.stButton > button:hover {
    background: linear-gradient(135deg, #5a6cff, #4f5fff) !important;
    box-shadow: 0 8px 22px rgba(90,108,255,0.45) !important;
}
/* App background */
.stApp {
    background:
        radial-gradient(circle at bottom left, rgba(194, 228, 255, 0.55), transparent 28%),
        radial-gradient(circle at bottom right, rgba(230, 210, 255, 0.45), transparent 28%),
        linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
}

/* Layout spacing */
.block-container {
    max-width: 1250px;
    padding-top: 5rem;
    padding-bottom: 2rem;
}

/* Header */
.app-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 22px;
}

.app-logo {
    width: 52px;
    height: 52px;
    border-radius: 16px;
    background: #0f172a;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
}

.app-title {
    font-size: 22px;
    font-weight: 700;
}

.app-subtitle {
    color: #000000;
    font-size: 15px;
}

.metric-card {
    background: rgba(255,255,255,0.92);
    border-radius: 22px;
    padding: 20px;
    text-align: center;
}

.metric-number {
    font-size: 30px;
    font-weight: 700;
}

.metric-label {
    margin-top: 6px;
}

.file-card {
    background: rgba(255,255,255,0.95);
    border-radius: 22px;
    padding: 18px 20px;
    margin-bottom: 16px;
}

.file-name {
    font-size: 22px;
    font-weight: 700;
}

.file-meta {
    font-size: 15px;
}

.insight-line {
    padding: 8px 0;
}

</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="app-header">
    <div class="app-logo">📊</div>
    <div>
        <div class="app-title">Data Analysis AI Agent</div>
        <div class="app-subtitle">Upload your data, generate insights, visualize trends, and ask follow-up questions</div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Upload section
# -----------------------------
uploaded_file = st.file_uploader(
    "Add Dataset",
    type=["csv", "xlsx"],
    help="Upload a CSV or Excel file"
)

if uploaded_file is None:
    if st.session_state.last_uploaded_name is not None:
        reset_app_state()
    st.info("Upload a dataset to begin.")
    st.stop()

if st.session_state.last_uploaded_name != uploaded_file.name:
    st.session_state.analysis_result = None
    st.session_state.chat_history = []
    st.session_state.last_uploaded_name = uploaded_file.name

try:
    df = load_data(uploaded_file)

    st.markdown(
        f'''
        <div class="file-card">
            <div class="file-name">{uploaded_file.name}</div>
            <div class="file-meta">{file_size_mb(uploaded_file)} MB • {df.shape[0]:,} rows • {df.shape[1]} columns</div>
        </div>
        ''',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-number">{df.shape[0]:,}</div><div class="metric-label">Rows</div></div>',
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-number">{df.shape[1]}</div><div class="metric-label">Columns</div></div>',
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-number">{min(10, len(df))}</div><div class="metric-label">Preview Rows</div></div>',
            unsafe_allow_html=True
        )

    st.markdown("## Data Preview")
    st.dataframe(df.head(10), use_container_width=True)

    if st.button("Generate Summary and Charts"):
        with st.spinner("Analyzing data..."):
            st.session_state.analysis_result = ask_agent_for_analysis(df)

    if st.session_state.analysis_result is not None:
        result = st.session_state.analysis_result
        summary = result["summary"]
        charts = result["charts"]

        st.markdown("## Analysis Summary")

        st.markdown("### Overview")
        st.write(summary["overview"])

        st.markdown("### Key Insights")
        for item in summary["key_insights"]:
            st.markdown(f'<div class="insight-line">• {item}</div>', unsafe_allow_html=True)

        st.markdown("### Recommendations")
        for item in summary["recommendations"]:
            st.markdown(f'<div class="insight-line">• {item}</div>', unsafe_allow_html=True)

        st.markdown("### Final Summary")
        st.write(summary["final_summary"])

        st.markdown("## Charts")

        cols = st.columns(2)

        for i, chart in enumerate(charts):
            with cols[i % 2]:
                render_chart(df, chart)

        st.markdown("## Ask Questions About Your Data")

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_question = st.chat_input("Ask a follow-up question about your dataset")

        if user_question:
            st.session_state.chat_history.append({"role": "user", "content": user_question})

            with st.chat_message("user"):
                st.write(user_question)

            with st.chat_message("assistant"):
                answer = ask_agent_question(df, result, user_question)
                st.write(answer)

            st.session_state.chat_history.append({"role": "assistant", "content": answer})

except Exception as e:
    st.error(f"Error: {e}")
