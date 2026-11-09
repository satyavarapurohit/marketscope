"""
Profile & Account page.

- Profile card (avatar initials, name, role, institution, project)
- Edit profile form
- Preferences: default stock, default date range, watchlist
- Account & data: storage details, export, reset
- Watchlist with live prices + shortcuts to the analysis pages
- Session activity (current selection, last ML experiment)

Profiles are saved per account by user_profile.py; login details by auth.py.
"""

import json
from html import escape

import streamlit as st

from marketscope import auth
from marketscope import components as ui
from marketscope import data
from marketscope import nav
from marketscope import user_profile as up
from marketscope.config import COLORS, NIFTY50_STOCKS, PERIODS

PAGE_CSS = f"""
<style>
.ms-avatar {{ width:72px; height:72px; border-radius:50%; background:{COLORS['navy']}; color:#fff;
  display:flex; align-items:center; justify-content:center; font-size:1.6rem; font-weight:700;
  border:3px solid {COLORS['gold']}; margin-bottom:.8rem; }}
.ms-pname {{ color:{COLORS['navy']}; font-size:1.25rem; font-weight:700; }}
.ms-prole {{ color:{COLORS['muted']}; font-size:.85rem; margin-bottom:.8rem; }}
.ms-prow {{ display:flex; gap:.55rem; align-items:flex-start; font-size:.84rem; color:{COLORS['text']};
  padding:.45rem 0; border-top:1px solid #F0EEE9; }}
.ms-prow svg {{ flex-shrink:0; margin-top:2px; color:{COLORS['muted']}; }}
/* Destructive action: red, not the normal navy primary button */
.st-key-delete_account_btn button {{ background:{COLORS['down']} !important;
  border-color:{COLORS['down']} !important; color:#fff !important; }}
.st-key-delete_account_btn button:hover {{ background:#9C3C34 !important; border-color:#9C3C34 !important; }}
.ms-bio {{ font-size:.83rem; color:#3E4B5B; line-height:1.5; margin:.6rem 0 .2rem; }}
</style>
"""


def _profile_card(p: dict) -> None:
    name = p["name"].strip() or "Guest user"
    role = p["role"] + (f" · {escape(p['institution'])}" if p["institution"].strip() else "")

    def row(icon_name, text):
        return f'<div class="ms-prow">{ui.icon(icon_name, 15)}<div>{text}</div></div>'

    rows = [
        row("info", escape(p["email"]) if p["email"].strip() else "<i>No email added</i>"),
        row("brain", escape(p["project_title"]) or "<i>No project title</i>"),
        row("candles", f"Default stock: <b>{p['default_stock'].replace('.NS', '')}</b> · "
                       f"range <b>{p['default_period']}</b>"),
        row("table", f"Watchlist: <b>{len(p['watchlist'])}</b> stocks"),
        row("calendar", f"Member since {p['created']}" if p["created"] else "Profile not saved yet"),
    ]
    bio = f'<div class="ms-bio">{escape(p["bio"])}</div>' if p["bio"].strip() else ""
    ui.html(f"""
    <div class="ms-card">
      <div class="ms-avatar">{up.initials(p['name'])}</div>
      <div class="ms-pname">{escape(name)}</div>
      <div class="ms-prole">{role}</div>
      {bio}
      {''.join(rows)}
      <div class="ms-kpi-foot">{('Last updated ' + p['updated']) if p['updated'] else ''}</div>
    </div>""")


def _save(p: dict, message: str) -> None:
    st.session_state.profile = up.save(st.session_state.user["username"], p)
    st.toast(message, icon=":material/check_circle:")
    st.rerun()


def _edit_profile(p: dict) -> None:
    with st.form("profile_form", border=False):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full name *", p["name"], max_chars=60)
        email = c2.text_input("Email", p["email"], max_chars=80, placeholder="you@college.edu")
        role = c1.selectbox("Role", up.ROLES, index=up.ROLES.index(p["role"]))
        institution = c2.text_input("College / institution", p["institution"], max_chars=80)
        project = st.text_input("Project title", p["project_title"], max_chars=100)
        bio = st.text_area("Short bio", p["bio"], max_chars=300, height=90,
                           placeholder="e.g. Final-year B.Tech student interested in data science and finance.")
        if st.form_submit_button("Save profile", type="primary", icon=":material/save:"):
            new = {**p, "name": name.strip(), "email": email.strip(), "role": role,
                   "institution": institution.strip(), "project_title": project.strip(), "bio": bio.strip()}
            errors = up.validate(new)
            if not errors:  # keep the login account's name/email in sync with the profile
                err = auth.update_details(st.session_state.user["username"], new["name"], new["email"])
                if err:
                    errors.append(err)
                else:
                    st.session_state.user.update(name=new["name"], email=new["email"].lower() or
                                                 st.session_state.user["email"])
            if errors:
                for e in errors:
                    st.error(e)
            else:
                _save(new, "Profile saved")


def _preferences(p: dict) -> None:
    stocks = list(NIFTY50_STOCKS)
    label = lambda t: f"{t.replace('.NS', '')} · {NIFTY50_STOCKS[t]}"  # noqa: E731
    with st.form("prefs_form", border=False):
        c1, c2 = st.columns(2)
        stock = c1.selectbox("Default stock", stocks, index=stocks.index(p["default_stock"]), format_func=label,
                             help="Selected automatically when the app opens.")
        period = c2.selectbox("Default date range", list(PERIODS), index=list(PERIODS).index(p["default_period"]))
        watch = st.multiselect("Watchlist (up to 12 stocks)", stocks, default=p["watchlist"], format_func=label,
                               max_selections=12)
        apply_now = st.checkbox("Also switch to the default stock and range now", value=True)
        if st.form_submit_button("Save preferences", type="primary", icon=":material/save:"):
            if apply_now:
                st.session_state.ticker = stock
                st.session_state.period_label = period
            _save({**p, "default_stock": stock, "default_period": period, "watchlist": watch},
                  "Preferences saved")


def _account(p: dict) -> None:
    user = st.session_state.user
    rows = [
        {"k": "Username", "v": "@" + user["username"]},
        {"k": "Login email", "v": user["email"]},
        {"k": "Account created", "v": user.get("created") or "—"},
        {"k": "Profile last updated", "v": p["updated"] or "Not saved yet"},
        {"k": "Account type", "v": "Local account (stored on this computer)"},
        {"k": "Password storage", "v": "Hashed with PBKDF2-SHA256 + salt"},
    ]
    ui.html_table(rows, [("Detail", "k", "text"), ("Value", "v", "text")])

    st.write("")
    with st.expander("Change password", icon=":material/key:"):
        with st.form("pw_form", border=False, clear_on_submit=True):
            current = st.text_input("Current password", type="password")
            c1, c2 = st.columns(2)
            new = c1.text_input("New password", type="password", help="At least 8 characters with a letter and a number.")
            confirm = c2.text_input("Confirm new password", type="password")
            if st.form_submit_button("Update password", type="primary"):
                err = auth.change_password(user["username"], current, new, confirm)
                if err:
                    st.error(err)
                else:
                    st.success("Password updated.")

    with st.expander("Danger zone", icon=":material/warning:"):
        st.markdown("**Reset profile** — restores default preferences and clears your bio, college and "
                    "watchlist changes. Your login stays the same.")
        confirm = st.checkbox("I understand — reset my profile", key="acct_reset_ok")
        if st.button("Reset profile", icon=":material/restart_alt:", disabled=not confirm, key="acct_reset"):
            st.session_state.profile = up.reset(user["username"], user)
            st.toast("Profile reset to defaults", icon=":material/restart_alt:")
            st.rerun()
        st.divider()
        st.markdown("**Delete account** — permanently removes your login and saved profile from this "
                    "computer. This cannot be undone.")
        with st.form("delete_form", border=False, clear_on_submit=True, enter_to_submit=False):
            pw = st.text_input("Enter your password to confirm", type="password")
            if st.form_submit_button("Delete my account", icon=":material/delete_forever:", key="delete_account_btn"):
                err = auth.delete_user(user["username"], pw)
                if err:
                    st.error(err)
                else:
                    up.delete(user["username"])
                    ui.logout()
                    st.rerun()

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Export profile", json.dumps(p, indent=2).encode(),
                           f"marketscope_{user['username']}_profile.json", "application/json",
                           icon=":material/download:", width="stretch")
    with c2:
        if st.button("Log out", icon=":material/logout:", width="stretch", key="acct_logout"):
            ui.logout()
            st.rerun()


def _watchlist(p: dict) -> None:
    ui.section("My watchlist", "Latest session prices for your saved stocks", "table")
    if not p["watchlist"]:
        st.info("Your watchlist is empty. Add stocks in the Preferences tab.")
        return
    with st.spinner("Loading watchlist prices…"):
        hist = data.load_many(tuple(p["watchlist"]), "1mo")
    rows = []
    for t in p["watchlist"]:
        df = hist.get(t)
        if df is None or len(df) < 2:
            continue
        last, prev = df["Close"].iloc[-1], df["Close"].iloc[-2]
        rows.append({"Symbol": t.replace(".NS", ""), "Company": NIFTY50_STOCKS[t], "Price": last,
                     "Day": (last / prev - 1) * 100, "Month": (last / df["Close"].iloc[0] - 1) * 100,
                     "Volume": df["Volume"].iloc[-1]})
    if not rows:
        st.info("Prices are unavailable right now. Check your internet connection.")
        return
    ui.html_table(rows, [("Stock", "Symbol", "stock"), ("Price ₹", "Price", "num"), ("Day", "Day", "pct"),
                         ("1 Month", "Month", "pct_plain"), ("Volume", "Volume", "big")])
    st.write("")
    c1, c2, c3 = st.columns([1.6, 1, 1], vertical_alignment="bottom")
    pick = c1.selectbox("Open a watchlist stock", p["watchlist"],
                        format_func=lambda t: f"{t.replace('.NS', '')} · {NIFTY50_STOCKS[t]}")
    if c2.button("Stock Analysis →", width="stretch", type="primary"):
        st.session_state.ticker = pick
        nav.go("stock")
    if c3.button("ML Lab →", width="stretch"):
        st.session_state.ticker = pick
        nav.go("ml")


def _activity() -> None:
    ui.section("Session activity", "What you are working on right now", "clock")
    run = st.session_state.get("ml_run")
    rows = [
        {"k": "Selected stock", "v": f"{st.session_state.ticker.replace('.NS', '')} · "
                                    f"{NIFTY50_STOCKS[st.session_state.ticker]}"},
        {"k": "Date range", "v": st.session_state.period_label},
    ]
    if run:
        trained = [m for m in run["results"] if m != "Naive Baseline"]
        best = min(trained, key=lambda m: run["results"][m].metrics["RMSE"]) if trained else "—"
        cfg = run["config"]
        rows += [
            {"k": "Last ML experiment", "v": cfg["ticker"].replace(".NS", "")},
            {"k": "Models trained", "v": ", ".join(trained) or "—"},
            {"k": "Lowest RMSE", "v": best},
            {"k": "History / test split", "v": f"{cfg['history']} · {cfg['test_size'] * 100:.0f}% test"},
        ]
    else:
        rows.append({"k": "Last ML experiment", "v": "None yet in this session"})
    ui.html_table(rows, [("Item", "k", "text"), ("Value", "v", "text")])


def render():
    ui.html(PAGE_CSS)
    ui.page_header("Account", "Profile & Account",
                   "Your details, saved preferences and watchlist", stock=False, period=False, key="acct")
    p = st.session_state.profile
    if not p["name"].strip():
        ui.note("Welcome! Add your name and details in <b>Edit profile</b> to personalise MarketScope.", "info")
        st.write("")

    left, right = st.columns([1, 2], gap="medium")
    with left:
        _profile_card(p)
    with right, ui.card("acct_tabs"):
        t1, t2, t3 = st.tabs(["Edit profile", "Preferences", "Account & data"])
        with t1:
            _edit_profile(p)
        with t2:
            _preferences(p)
        with t3:
            _account(p)

    st.write("")
    left, right = st.columns([1.7, 1], gap="medium")
    with left, ui.card("acct_watch"):
        _watchlist(p)
    with right, ui.card("acct_activity"):
        _activity()
