#!/usr/bin/env bash
# Run the Data Analysis AI Agent app (Streamlit)
cd "$(dirname "$0")"
echo "Starting Streamlit on http://localhost:8501"
echo "If you already have the app open, do a hard refresh (Cmd+Shift+R / Ctrl+Shift+R) to see changes."
python3 -m streamlit run app.py --server.port 8501
