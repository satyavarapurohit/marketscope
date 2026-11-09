"""
nav.py - The list of pages. Kept in one place so app.py (sidebar links) and
pages (e.g. the dashboard's "Analyse stock" button) use the same objects.
"""

import streamlit as st

_PAGES = {}


def pages() -> dict:
    if not _PAGES:
        from marketscope.views import about, account, dashboard, ml_lab, stock_analysis, technical
        _PAGES.update({
            "dashboard": st.Page(dashboard.render, title="Dashboard", icon=":material/space_dashboard:",
                                 default=True),
            "stock": st.Page(stock_analysis.render, title="Stock Analysis", icon=":material/candlestick_chart:",
                             url_path="stock-analysis"),
            "technical": st.Page(technical.render, title="Technical Analysis", icon=":material/monitoring:",
                                 url_path="technical-analysis"),
            "ml": st.Page(ml_lab.render, title="ML Lab", icon=":material/model_training:", url_path="ml-lab"),
            "about": st.Page(about.render, title="About Project", icon=":material/info:", url_path="about"),
            "account": st.Page(account.render, title="Profile & Account", icon=":material/account_circle:",
                               url_path="account"),
        })
    return _PAGES


_LOGIN = {}


def login_page():
    if not _LOGIN:
        from marketscope.views import login
        _LOGIN["page"] = st.Page(login.render, title="Sign in", icon=":material/login:", url_path="login",
                                 default=True)
    return _LOGIN["page"]


def go(key: str) -> None:
    st.switch_page(pages()[key])
