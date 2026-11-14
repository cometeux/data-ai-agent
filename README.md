# Datara — Data Analysis Workspace

A Streamlit prototype for exploring CSV and Excel datasets, checking data quality, and generating AI-assisted summaries and chart suggestions.

## What you can do

- Upload a CSV or XLSX file and inspect a preview.
- Review missing values, duplicate rows, column types, and a heuristic readiness score.
- Request a summary and up to two validated chart suggestions.
- Ask follow-up questions and export an executive report as Markdown.

## Run locally

Requires Python 3.10 or newer and an OpenAI API key for AI features.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p .streamlit
```

Create `.streamlit/secrets.toml` locally:

```toml
OPENAI_API_KEY = "your-key-here"
```

Then run:

```bash
streamlit run app.py
```

Never commit a real API key or the secrets file. Use synthetic or non-sensitive datasets.

## How it works

`Upload → pandas profile → model proposes summary/chart specifications → column/type validation → Plotly rendering`

Data profiling and chart aggregation run in Python. Generated narrative uses the OpenAI Responses API. The current code requests `gpt-4.1-mini`; availability depends on the API account.

## Data handling and limits

- AI analysis sends column metadata and the first **12 rows** to the model provider. Follow-up answers receive the first **15 rows** and the generated summary.
- Questions and chart explanations also use the model provider. This is **not an offline or private-data analysis system**.
- Narrative conclusions are based on a sample, not a full statistical analysis. Validate claims against the complete dataset.
- The readiness score is a heuristic, not a validated accuracy or quality measure.
- This repository contains a prototype; it does not establish production readiness, model-training experience, or measured business impact.

## Repository map

| File | Purpose |
|---|---|
| `app.py` | Upload flow, profiling, AI requests, charts and reports |
| `theme.py` | Visual styling |
| `state.py` | Supporting state utilities |
| `requirements.txt` | Python dependencies |
| `run.sh` | Launch helper |

Related exploration: [ai-data-agent](https://github.com/cometeux/ai-data-agent), a fork of [InnovationSJ/ai-data-agent](https://github.com/InnovationSJ/ai-data-agent). Repository location alone does not establish original authorship; inspect history when assessing contributions.
