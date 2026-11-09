"""
styles.py - Reusable CSS for MarketScope.

One stylesheet is injected once per page run. Component classes start with
"ms-" so they never clash with Streamlit's own classes.
Containers created with components.card() get a key starting with "card",
which Streamlit turns into a CSS class "st-key-card...", styled below.
"""

import streamlit as st

from marketscope.config import COLORS as C

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {{
  --ms-bg: {C['bg']}; --ms-surface: {C['surface']}; --ms-border: {C['border']};
  --ms-navy: {C['navy']}; --ms-text: {C['text']}; --ms-muted: {C['muted']};
  --ms-up: {C['up']}; --ms-down: {C['down']};
  --ms-up-soft: {C['up_soft']}; --ms-down-soft: {C['down_soft']};
  --ms-accent: {C['accent']}; --ms-gold: {C['gold']};
  --ms-shadow: 0 1px 2px rgba(15,35,65,.04), 0 2px 8px rgba(15,35,65,.04);
}}

html, body, [class*="css"], .stApp {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: var(--ms-bg); }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1440px; }}
h1, h2, h3, h4 {{ color: var(--ms-navy); letter-spacing: -0.01em; }}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {{ border-right: none; }}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {{
  border-radius: 8px; padding: .45rem .7rem; margin: 1px 0;
}}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] span {{ color: #C9D3E3; font-weight: 500; }}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {{ background: rgba(255,255,255,.06); }}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {{
  background: rgba(255,255,255,.10); box-shadow: inset 3px 0 0 {C['gold']};
}}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] span {{ color: #FFFFFF; }}
section[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {{ border-color: rgba(255,255,255,.08); }}

.ms-brand {{ display:flex; align-items:center; gap:.65rem; padding:.2rem 0 1rem 0; }}
.ms-brand-mark {{ width:38px; height:38px; border-radius:10px; background:{C['gold']};
  display:flex; align-items:center; justify-content:center; }}
.ms-brand-name {{ color:#fff; font-weight:700; font-size:1.15rem; line-height:1.1; }}
.ms-brand-tag {{ color:#93A3BC; font-size:.72rem; letter-spacing:.04em; text-transform:uppercase; }}

.ms-side-label {{ color:#7F90AA; font-size:.68rem; font-weight:600; letter-spacing:.08em;
  text-transform:uppercase; margin:1.2rem 0 .5rem; }}
.ms-status {{ background: rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.08);
  border-radius:10px; padding:.75rem .85rem; }}
.ms-status-row {{ display:flex; align-items:center; gap:.5rem; color:#fff; font-weight:600; font-size:.9rem; }}
.ms-dot {{ width:8px; height:8px; border-radius:50%; display:inline-block; }}
.ms-status-time {{ color:#93A3BC; font-size:.75rem; margin-top:.25rem; }}
.ms-side-index {{ display:flex; justify-content:space-between; font-size:.8rem; padding:.3rem 0;
  color:#C9D3E3; border-bottom:1px solid rgba(255,255,255,.06); }}
.ms-side-index:last-child {{ border-bottom:none; }}
.ms-side-foot {{ color:#7F90AA; font-size:.7rem; margin-top:1.4rem; line-height:1.5; }}

/* ---------- Page header ---------- */
.ms-eyebrow {{ color: var(--ms-gold); font-size:.72rem; font-weight:600; letter-spacing:.1em; text-transform:uppercase; }}
.ms-title {{ color: var(--ms-navy); font-size:1.75rem; font-weight:700; margin:.1rem 0 .15rem; letter-spacing:-.02em; }}
.ms-subtitle {{ color: var(--ms-muted); font-size:.92rem; margin-bottom:.4rem; }}
.ms-divider {{ height:1px; background: var(--ms-border); margin:.6rem 0 1.2rem; }}

/* ---------- Cards ---------- */
[class*="st-key-card"] {{
  background: var(--ms-surface); border:1px solid var(--ms-border) !important;
  border-radius:12px; box-shadow: var(--ms-shadow); padding: 1.05rem 1.15rem 1rem;
}}
.ms-card {{ background: var(--ms-surface); border:1px solid var(--ms-border); border-radius:12px;
  box-shadow: var(--ms-shadow); padding:1rem 1.1rem; height:100%; }}
.ms-section {{ display:flex; align-items:flex-start; gap:.6rem; margin-bottom:.35rem; }}
.ms-section-icon {{ width:30px; height:30px; border-radius:8px; background:#EEF2F7; color:var(--ms-navy);
  display:flex; align-items:center; justify-content:center; flex-shrink:0; }}
.ms-section-title {{ color:var(--ms-navy); font-weight:650; font-size:1rem; line-height:1.3; }}
.ms-section-sub {{ color:var(--ms-muted); font-size:.8rem; }}

/* KPI / index cards */
.ms-kpi-label {{ color:var(--ms-muted); font-size:.75rem; font-weight:600; letter-spacing:.05em; text-transform:uppercase;
  display:flex; align-items:center; gap:.4rem; }}
.ms-kpi-value {{ color:var(--ms-navy); font-size:1.55rem; font-weight:700; margin:.25rem 0 .1rem;
  font-variant-numeric: tabular-nums; letter-spacing:-.01em; }}
.ms-kpi-foot {{ color:var(--ms-muted); font-size:.76rem; margin-top:.35rem; }}
.ms-chip {{ display:inline-flex; align-items:center; gap:.2rem; padding:.12rem .5rem; border-radius:999px;
  font-size:.78rem; font-weight:600; font-variant-numeric: tabular-nums; }}
.ms-up {{ color:var(--ms-up); }} .ms-down {{ color:var(--ms-down); }}
.ms-chip.ms-up {{ background:var(--ms-up-soft); }} .ms-chip.ms-down {{ background:var(--ms-down-soft); }}
.ms-chip.ms-neutral {{ background:#EEF2F7; color:var(--ms-navy); }}
.ms-index-top {{ display:flex; justify-content:space-between; align-items:flex-start; }}
.ms-spark {{ margin-top:.5rem; }}
.ms-best {{ border-color: var(--ms-gold) !important; box-shadow: 0 0 0 1px var(--ms-gold), var(--ms-shadow); }}
.ms-tag {{ font-size:.65rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:var(--ms-gold);
  border:1px solid var(--ms-gold); border-radius:4px; padding:.05rem .35rem; }}

/* ---------- Tables ---------- */
.ms-table-wrap {{ overflow-x:auto; }}
table.ms-table {{ width:100%; border-collapse:collapse; font-size:.84rem; font-variant-numeric: tabular-nums; }}
table.ms-table th {{ text-align:left; color:var(--ms-muted); font-weight:600; font-size:.7rem; letter-spacing:.06em;
  text-transform:uppercase; padding:.5rem .6rem; border-bottom:1px solid var(--ms-border); background:#FAF9F6; white-space:nowrap; }}
table.ms-table td {{ padding:.55rem .5rem; border-bottom:1px solid #F0EEE9; color:var(--ms-text); white-space:nowrap; }}
table.ms-table tr:last-child td {{ border-bottom:none; }}
table.ms-table tr:hover td {{ background:#FBFAF8; }}
table.ms-table th.num, table.ms-table td.num {{ text-align:right; }}
.ms-sym {{ font-weight:650; color:var(--ms-navy); }}
.ms-co {{ color:var(--ms-muted); font-size:.75rem; }}

/* ---------- Activity feed ---------- */
.ms-feed-item {{ display:flex; gap:.75rem; padding:.6rem 0; border-bottom:1px solid #F0EEE9; }}
.ms-feed-item:last-child {{ border-bottom:none; }}
.ms-feed-icon {{ width:30px; height:30px; border-radius:8px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }}
.ms-feed-title {{ font-size:.86rem; color:var(--ms-text); font-weight:550; }}
.ms-feed-meta {{ font-size:.75rem; color:var(--ms-muted); }}

/* ---------- Callouts ---------- */
.ms-note {{ border-radius:10px; padding:.8rem 1rem; font-size:.84rem; line-height:1.5; border:1px solid; }}
.ms-note b {{ color: inherit; }}
.ms-note-info {{ background:#F1F5FA; border-color:#D9E3EF; color:#24405F; }}
.ms-note-warn {{ background:#FBF6EC; border-color:#EADDBE; color:#6B5320; }}
.ms-note-good {{ background:var(--ms-up-soft); border-color:#CBE3D6; color:#245F46; }}
.ms-explain {{ font-size:.84rem; color:#3E4B5B; line-height:1.55; }}
.ms-explain b {{ color:var(--ms-navy); }}
.ms-reading {{ display:flex; gap:1.4rem; flex-wrap:wrap; margin-top:.6rem; }}
.ms-reading div {{ font-size:.75rem; color:var(--ms-muted); }}
.ms-reading span {{ display:block; font-size:1.05rem; font-weight:650; color:var(--ms-navy); font-variant-numeric: tabular-nums; }}
.ms-mono {{ font-family:'IBM Plex Mono', monospace; font-size:.8rem; }}

/* ---------- Streamlit widget polish ---------- */
div[data-testid="stTabs"] button[role="tab"] p {{ font-weight:600; font-size:.88rem; }}
div[data-testid="stMetric"] {{ background: var(--ms-surface); }}
/* Only PRIMARY buttons are navy. (Styling every form button navy made secondary buttons'
   dark label unreadable.) */
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primaryFormSubmit"] {{
  background: var(--ms-navy); border-color: var(--ms-navy); font-weight:600; color:#fff;
}}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primaryFormSubmit"]:hover {{
  background:#1E3A5F; border-color:#1E3A5F; color:#fff;
}}
div[data-testid="stExpander"] details {{ background: var(--ms-surface); border-radius:10px; }}
[data-testid="stDataFrame"] {{ border:1px solid var(--ms-border); border-radius:10px; }}

/* Form fields (all pages): Streamlit's "Press Enter to submit form" hint overlapped
   typed text in narrow fields, and placeholders looked like real input. */
[data-testid="InputInstructions"] {{ display:none !important; }}
.stTextInput input, .stTextArea textarea {{ color: var(--ms-text) !important; font-weight:500; }}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {{ color:#A3A9B3 !important; font-weight:400; opacity:1; }}
.stTextInput [data-baseweb="input"], .stTextArea [data-baseweb="textarea"] {{ border:1px solid var(--ms-border) !important; }}
.stTextInput [data-baseweb="input"]:focus-within, .stTextArea [data-baseweb="textarea"]:focus-within {{
  border-color: var(--ms-navy) !important; box-shadow:0 0 0 3px rgba(15,35,65,.08);
}}

/* Subtle, consistent hover feedback */
.ms-card, [class*="st-key-card"] {{ transition: border-color .15s ease, box-shadow .15s ease; }}
.ms-card:hover {{ border-color:#D8D4CB; box-shadow: 0 1px 2px rgba(15,35,65,.05), 0 4px 14px rgba(15,35,65,.06); }}
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
  border-radius:8px; transition: background .15s ease, border-color .15s ease, transform .05s ease;
}}
.stButton > button:active, .stFormSubmitButton > button:active {{ transform: translateY(1px); }}
.stButton > button:not([kind="primary"]):hover, .stDownloadButton > button:hover,
.stFormSubmitButton > button[kind="secondaryFormSubmit"]:hover {{
  border-color: var(--ms-navy); color: var(--ms-navy);
}}

@media (max-width: 900px) {{
  .ms-title {{ font-size:1.4rem; }}
  .ms-kpi-value {{ font-size:1.3rem; }}
}}
/* Phones: Streamlit's top bar overlays the page, so leave room for the page label */
@media (max-width: 640px) {{
  .block-container {{ padding-top:3.6rem; padding-left:1rem; padding-right:1rem; }}
  [class*="st-key-card"] {{ padding:.9rem .85rem .8rem; }}
}}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
