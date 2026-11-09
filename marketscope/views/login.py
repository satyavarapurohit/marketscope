"""
Login page - sign in or create an account before using MarketScope.

Left: brand + Sign in / Create account forms.
Right: a live market preview (real index data) so the page feels like part
of the product. The sidebar is hidden on this page.
"""

from datetime import datetime

import streamlit as st

from marketscope import auth
from marketscope import components as ui
from marketscope import data
from marketscope.config import APP_NAME, APP_TAGLINE, COLORS

LOGIN_CSS = f"""
<style>
section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"], header[data-testid="stHeader"] {{ display:none !important; }}
.block-container {{ max-width:1120px; padding-top:3rem; }}
.st-key-card_login_form, .st-key-card_login_side {{ min-height:660px; }}
.st-key-card_login_form {{ padding:2rem 2.2rem 1.6rem !important; }}
.st-key-card_login_side {{ background:#FAF9F6 !important; padding:2rem 2rem 1.6rem !important; }}
.ms-login-brand {{ display:flex; align-items:center; gap:.6rem; margin-bottom:1.8rem; }}
.ms-login-mark {{ width:36px; height:36px; border-radius:10px; background:{COLORS['navy']};
  display:flex; align-items:center; justify-content:center; }}
.ms-login-name {{ font-weight:700; color:{COLORS['navy']}; font-size:1.1rem; line-height:1.1; }}
.ms-login-tag {{ color:{COLORS['muted']}; font-size:.7rem; letter-spacing:.05em; text-transform:uppercase; }}
.ms-login-h {{ color:{COLORS['navy']}; font-size:1.65rem; font-weight:700; letter-spacing:-.02em; margin:0; }}
.ms-login-sub {{ color:{COLORS['muted']}; font-size:.9rem; margin:.25rem 0 1.1rem; }}
.ms-mini {{ background:#fff; border:1px solid {COLORS['border']}; border-radius:12px; padding:.75rem .9rem;
  margin-bottom:.6rem; }}
.ms-mini-top {{ display:flex; justify-content:space-between; align-items:baseline; }}
.ms-mini-name {{ font-size:.72rem; font-weight:600; color:{COLORS['muted']}; letter-spacing:.05em; text-transform:uppercase; }}
.ms-mini-val {{ font-size:1.15rem; font-weight:700; color:{COLORS['navy']}; font-variant-numeric:tabular-nums; }}
.ms-feat {{ display:flex; gap:.6rem; align-items:flex-start; font-size:.84rem; color:#3E4B5B; margin:.55rem 0; }}
.ms-feat-ic {{ width:28px; height:28px; border-radius:8px; background:#EEF2F7; color:{COLORS['navy']};
  display:flex; align-items:center; justify-content:center; flex-shrink:0; }}
.ms-login-foot {{ color:{COLORS['muted']}; font-size:.75rem; margin-top:1.2rem; display:flex;
  justify-content:space-between; flex-wrap:wrap; gap:.5rem; }}
</style>
"""


def _brand() -> None:
    ui.html(f"""
    <div class="ms-login-brand">
      <div class="ms-login-mark">{ui.icon('trend_up', 19, COLORS['gold'], 2.2)}</div>
      <div><div class="ms-login-name">{APP_NAME}</div><div class="ms-login-tag">{APP_TAGLINE}</div></div>
    </div>""")


def _sign_in() -> None:
    ui.html('<div class="ms-login-h">Welcome back</div>'
            '<div class="ms-login-sub">Sign in to continue to your market research dashboard.</div>')
    with st.form("signin_form", border=False):
        login = st.text_input("Username or email", placeholder="e.g. rohit_s or you@college.edu")
        password = st.text_input("Password", type="password", placeholder="Your password")
        if st.form_submit_button("Sign in", type="primary", icon=":material/login:", width="stretch"):
            if not login.strip() or not password:
                st.error("Enter your username (or email) and password.")
            else:
                user = auth.authenticate(login, password)
                if user:
                    ui.login_user(user)
                    st.rerun()
                else:
                    st.error("Incorrect username/email or password.")
    if auth.user_count() == 0:
        ui.note("No accounts yet — choose <b>Create account</b> above to get started.", "info")


def _sign_up() -> None:
    ui.html('<div class="ms-login-h">Create your account</div>'
            '<div class="ms-login-sub">Set up a profile to save your watchlist and preferences.</div>')
    with st.form("signup_form", border=False):
        name = st.text_input("Full name", placeholder="e.g. Rohit Satyavarapu")
        username = st.text_input("Username", placeholder="e.g. rohit_s (letters, numbers, _)")
        email = st.text_input("Email", placeholder="e.g. you@college.edu")
        c3, c4 = st.columns(2)
        password = c3.text_input("Password", type="password", help="At least 8 characters with a letter and a number.")
        confirm = c4.text_input("Confirm password", type="password")
        if st.form_submit_button("Create account", type="primary", icon=":material/person_add:", width="stretch"):
            user, err = auth.create_user(username, name, email, password, confirm)
            if err:
                st.error(err)
            else:
                ui.login_user(user)
                st.toast(f"Welcome to {APP_NAME}, {user['name'].split()[0]}!", icon=":material/celebration:")
                st.rerun()


def _market_preview() -> None:
    ui.section("Market today", "Live preview · Yahoo Finance end-of-day data", "activity")
    idx = data.load_indices("1mo")
    if not idx:
        st.caption("Market preview unavailable — check your internet connection.")
    for name, df in idx.items():
        if len(df) < 2:
            continue
        last, prev = df["Close"].iloc[-1], df["Close"].iloc[-2]
        pct = (last / prev - 1) * 100
        ui.html(f"""
        <div class="ms-mini">
          <div class="ms-mini-top"><span class="ms-mini-name">{name}</span>{ui.chip(pct)}</div>
          <div class="ms-mini-val">{last:,.2f}</div>
          {ui.sparkline_svg(df['Close'].values, height=34)}
        </div>""")
    feats = [
        ("candles", "Candlestick charts with SMA / EMA overlays and volume"),
        ("gauge", "RSI, MACD, volatility and return analysis with explanations"),
        ("brain", "Random Forest vs XGBoost vs LSTM model comparison"),
    ]
    ui.html("".join(f'<div class="ms-feat"><div class="ms-feat-ic">{ui.icon(i, 15)}</div><div>{t}</div></div>'
                    for i, t in feats))


def render():
    ui.html(LOGIN_CSS)
    left, right = st.columns([1.15, 1], gap="small")
    with left, ui.card("login_form"):
        _brand()
        mode = st.segmented_control("Mode", ["Sign in", "Create account"], default="Sign in",
                                    key="login_mode", label_visibility="collapsed", width="stretch")
        st.write("")
        if mode == "Create account":
            _sign_up()
        else:
            _sign_in()
        ui.html('<div class="ms-login-foot"><span>🔒 Accounts are stored on this computer; '
                'passwords are hashed (PBKDF2-SHA256).</span></div>')
    with right, ui.card("login_side"):
        _market_preview()
    ui.html(f'<div class="ms-login-foot" style="padding:0 .3rem"><span>Market data: Yahoo Finance (end-of-day, may be delayed)'
            f'</span><span>© {datetime.now().year} {APP_NAME} · Academic Data Science project</span></div>')
