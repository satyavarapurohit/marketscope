"""
MarketScope - Stock Market Trend Analysis
=========================================
Entry point. Run with:   streamlit run app.py

This file only sets up the page, the sidebar and navigation.
All real work lives in the marketscope/ package (see README.md).
"""

import streamlit as st

st.set_page_config(page_title="MarketScope · Stock Market Trend Analysis", page_icon="📈", layout="wide",
                   initial_sidebar_state="auto")  # open on desktop, tucked away on phones

from marketscope import components as ui  # noqa: E402  (must come after set_page_config)
from marketscope import nav  # noqa: E402
from marketscope.styles import inject_css  # noqa: E402

inject_css()
ui.init_state()

# ---- Not signed in: show only the login / sign-up page ------------------------
if not st.session_state.user:
    st.navigation([nav.login_page()], position="hidden").run()
    st.stop()

pages = nav.pages()
current = st.navigation(list(pages.values()), position="hidden")

# ---- Sidebar: logo -> navigation -> market status ---------------------------
ui.sidebar()
with st.sidebar:
    ui.html('<div class="ms-side-label">Analytics</div>')
    for key in ("dashboard", "stock", "technical"):
        st.page_link(pages[key])
    ui.html('<div class="ms-side-label">Research</div>')
    for key in ("ml", "about"):
        st.page_link(pages[key])
    ui.html('<div class="ms-side-label">Account</div>')
    st.page_link(pages["account"])
ui.sidebar_status()

current.run()
