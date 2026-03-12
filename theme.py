# -*- coding: utf-8 -*-
"""
Datara UI theme — literal design-system CSS from the provided HTML.
Do not reinterpret; preserve layout, spacing, typography, colors, and shadows.
"""

# Font links (injected first so Streamlit applies them)
FONT_LINKS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">"""


def get_theme_css():
    """Return full CSS: design tokens + layout + Streamlit overrides for fidelity."""
    return """<style>
:root {
    --bg-base: #0a0812;
    --bg-panel: #120e1d;
    --bg-panel-solid: #120e1d;
    --bg-surface: #1c162b;
    --border-dim: rgba(245, 240, 255, 0.05);
    --border-medium: rgba(245, 240, 255, 0.1);
    --border-bright: rgba(245, 240, 255, 0.2);
    --accent-primary: #a78bfa;
    --accent-glow: #8b5cf6;
    --accent-secondary: #7c3aed;
    --text-primary: #F5F0FF;
    --text-secondary: #c4b5e0;
    --text-muted: #807a9e;
    --status-blue: #60a5fa;
    --status-purple: #a78bfa;
    --status-amber: #f59e0b;
    --status-red: #ef4444;
    --status-green: #10b981;
    --font-sans: 'Inter', -apple-system, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    --radius-sm: 12px;
    --radius-md: 18px;
    --radius-lg: 24px;
    --spacing-xs: 4px;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stSidebar"] { display: none !important; }

[data-testid="stAppViewContainer"] {
    background: var(--bg-base) !important;
    background-image: radial-gradient(circle at 50% 30%, #1c1432 0%, #0a0812 70%) !important;
    color: var(--text-secondary);
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    min-height: 100vh;
}

.block-container {
    max-width: 1400px;
    padding: 0 var(--spacing-xl);
    padding-bottom: 64px;
}
.stApp .main { background: transparent !important; }
.stApp .main .block-container { font-family: var(--font-sans); color: var(--text-secondary); }

/* Hero = title + caption */
.stApp h1 {
    font-size: 28px !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    margin-bottom: 8px !important;
    letter-spacing: -0.5px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.5);
}
.stApp .stCaption, .stApp [data-testid="stMarkdown"] p { color: var(--text-secondary) !important; font-size: 15px !important; }
.stApp h2, .stApp h3 { font-size: 15px !important; font-weight: 500 !important; color: var(--text-secondary) !important; }

/* Upload zone — design: panel, inset shadow, radius-lg */
[data-testid="stFileUploader"] { margin: 0.5rem 0 !important; }
[data-testid="stFileUploader"] section {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-medium) !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.3) !important;
    border-radius: var(--radius-lg) !important;
    padding: var(--spacing-xl) !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: var(--accent-primary) !important;
    background: var(--bg-surface) !important;
}
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] {
    font-size: 15px !important; font-weight: 500 !important; color: var(--text-primary) !important;
}
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] + span {
    font-size: 13px !important; color: var(--text-muted) !important;
}

/* KPI grid — design: kpi-card with kpi-label, kpi-value */
[data-testid="stMetric"],
[data-testid="metric-container"] {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-dim) !important;
    box-shadow: inset 0 1px 2px rgba(255,255,255,0.05) !important;
    border-radius: var(--radius-lg) !important;
    padding: 24px !important;
    gap: 12px;
}
[data-testid="stMetric"] label,
[data-testid="stMetricLabel"],
[data-testid="metric-container"] label {
    font-size: 14px !important; font-weight: 500 !important;
    color: var(--text-muted) !important;
    display: block !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--font-sans) !important;
    font-size: 32px !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    letter-spacing: -1px;
}
[data-testid="stMetric"]:nth-of-type(3) [data-testid="stMetricValue"],
[data-testid="metric-container"]:nth-of-type(3) [data-testid="stMetricValue"] {
    color: var(--accent-primary) !important;
}

/* Primary button — design: btn-primary */
.stButton > button {
    font-family: var(--font-sans) !important;
    background: var(--accent-primary) !important;
    color: #120e1d !important;
    border: none !important;
    border-radius: 999px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    padding: 16px !important;
    width: 100%;
    max-width: 100%;
    box-shadow: 0 4px 20px rgba(167, 139, 250, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1) !important;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 25px rgba(167, 139, 250, 0.4) !important;
}

/* Expander — design: details.expander */
.stExpander { background: transparent !important; border: none !important; }
.streamlit-expanderHeader {
    background: transparent !important;
    font-size: 14px !important;
    color: var(--text-muted) !important;
    padding: 12px 0 !important;
}
.streamlit-expanderContent {
    border-top: 1px solid var(--border-dim) !important;
    color: var(--text-muted) !important;
    font-size: 14px !important;
    padding: 10px 0 !important;
}

/* Tabs — design: tab-list, tab-btn, active underline */
[data-testid="stTabs"] { margin-top: var(--spacing-md); }
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid var(--border-dim) !important;
    gap: var(--spacing-xl) !important;
}
[data-testid="stTabs"] [role="tab"] {
    font-family: var(--font-sans) !important;
    padding: 12px 0 !important;
    color: var(--text-muted) !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    background: none !important;
    border: none !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -1px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--text-primary) !important;
    border-bottom-color: var(--accent-primary) !important;
    box-shadow: 0 0 10px var(--accent-glow);
}

/* Table / dataframe — design: table-container */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border-dim) !important;
    border-radius: var(--radius-lg) !important;
    background: var(--bg-panel) !important;
    overflow: hidden !important;
}

/* Alerts */
[data-testid="stAlert"] {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-medium) !important;
    border-radius: var(--radius-lg) !important;
}
[data-testid="stAlert"] [data-testid="stMarkdown"] { color: var(--text-secondary) !important; }

/* Chat — design: bubble, chat-input, send-btn */
[data-testid="stChatMessage"] {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: var(--radius-lg) !important;
    color: var(--text-secondary) !important;
}
[data-testid="stChatInput"] {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-medium) !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.2) !important;
    border-radius: 999px !important;
}
[data-testid="stChatInput"] textarea { color: var(--text-primary) !important; }

/* Tab-inner buttons — design: pill-btn */
[data-testid="stTabs"] .stButton > button {
    max-width: none; width: auto;
    font-size: 12px !important;
    padding: 10px 16px !important;
    background: var(--bg-panel) !important;
    color: var(--text-muted) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: 999px !important;
    box-shadow: none !important;
    transform: none !important;
}
[data-testid="stTabs"] .stButton > button:hover {
    border-color: var(--accent-primary) !important;
    color: var(--text-primary) !important;
}

/* Download buttons — design: btn-secondary */
[data-testid="stDownloadButton"] button {
    background: rgba(245, 240, 255, 0.08) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-medium) !important;
    border-radius: 999px !important;
    font-size: 13px !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: rgba(245, 240, 255, 0.15) !important;
    border-color: var(--border-bright) !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--bg-surface); border-radius: 8px; }
</style>
"""
