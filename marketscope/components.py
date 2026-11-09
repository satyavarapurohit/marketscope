"""
components.py - Reusable UI building blocks.

Each function draws one piece of the interface (a card, a table, the page
header ...). Pages are assembled from these, so the look stays consistent
and each page file stays short.
"""

from datetime import date, timedelta
from html import escape

import numpy as np
import pandas as pd
import streamlit as st

from marketscope import data
from marketscope.config import (APP_NAME, APP_TAGLINE, COLORS, DEFAULT_PERIOD, DEFAULT_STOCK,
                                NIFTY50_STOCKS, PERIODS)

# ---------------------------------------------------------------------------
# Icons (Lucide-style outline icons, inline SVG so no extra dependency)
# ---------------------------------------------------------------------------
_ICON_PATHS = {
    "chart": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 6-6"/>',
    "candles": '<path d="M7 3v4M7 17v4M17 3v2M17 15v6"/><rect x="5" y="7" width="4" height="10" rx="1"/><rect x="15" y="5" width="4" height="10" rx="1"/>',
    "bars": '<path d="M3 3v18h18"/><rect x="7" y="12" width="3" height="6"/><rect x="12" y="8" width="3" height="10"/><rect x="17" y="5" width="3" height="13"/>',
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "trend_up": '<path d="m22 7-8.5 8.5-5-5L2 17"/><path d="M16 7h6v6"/>',
    "trend_down": '<path d="m22 17-8.5-8.5-5 5L2 7"/><path d="M16 17h6v-6"/>',
    "brain": '<path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M12 5v13"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "layers": '<path d="m12 2 10 5-10 5L2 7z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    "table": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
    "volume": '<path d="M3 3v18h18"/><path d="M7 16v2M11 12v6M15 9v9M19 14v4"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    "zap": '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>',
    "flag": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><path d="M4 22v-7"/>',
    "gauge": '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    "wave": '<path d="M2 12c2-4 4-4 6 0s4 4 6 0 4-4 6 0"/>',
    "settings": '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4M12 17h.01"/>',
}


def icon(name: str, size: int = 16, color: str = "currentColor", stroke: float = 1.8) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="none" stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
            f'stroke-linejoin="round">{_ICON_PATHS.get(name, "")}</svg>')


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Number formatting
# ---------------------------------------------------------------------------
def fmt_num(x, decimals=2) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x:,.{decimals}f}"


def fmt_big(x) -> str:
    """Indian-style short form: 1.2 Cr, 35.4 L, 12.3 K."""
    if x is None or pd.isna(x):
        return "—"
    for div, suffix in ((1e7, " Cr"), (1e5, " L"), (1e3, " K")):
        if abs(x) >= div:
            return f"{x / div:,.2f}{suffix}"
    return f"{x:,.0f}"


def tone(x) -> str:
    if x is None or pd.isna(x) or x == 0:
        return "ms-neutral"
    return "ms-up" if x > 0 else "ms-down"


def chip(pct, abs_change=None, suffix="%") -> str:
    if pct is None or pd.isna(pct):
        return '<span class="ms-chip ms-neutral">—</span>'
    arrow = "▲" if pct > 0 else ("▼" if pct < 0 else "•")
    abs_txt = f"{abs_change:+,.2f} " if abs_change is not None else ""
    return f'<span class="ms-chip {tone(pct)}">{arrow} {abs_txt}({pct:+.2f}{suffix})</span>' if abs_txt \
        else f'<span class="ms-chip {tone(pct)}">{arrow} {pct:+.2f}{suffix}</span>'


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------
def card(key: str):
    """A white rounded card. Use as:  with card("x"): ..."""
    return st.container(key=f"card_{key}")


def section(title: str, subtitle: str = "", icon_name: str = "chart") -> None:
    sub = f'<div class="ms-section-sub">{subtitle}</div>' if subtitle else ""
    html(f'<div class="ms-section"><div class="ms-section-icon">{icon(icon_name, 16)}</div>'
         f'<div><div class="ms-section-title">{title}</div>{sub}</div></div>')


def note(text: str, kind: str = "info", icon_name: str | None = None) -> None:
    ic = icon(icon_name or {"warn": "alert", "good": "target"}.get(kind, "info"), 15)
    html(f'<div class="ms-note ms-note-{kind}"><span style="vertical-align:-2px">{ic}</span>&nbsp; {text}</div>')


def experimental_disclaimer() -> None:
    note("<b>Experimental estimates only.</b> Model outputs are produced for academic study of "
         "machine-learning methods on historical data. They are not guaranteed forecasts and are "
         "not investment advice.", "warn", "alert")


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------
def sparkline_svg(values, width=260, height=46, color=None) -> str:
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) < 2:
        return ""
    color = color or (COLORS["up"] if v[-1] >= v[0] else COLORS["down"])
    lo, hi = v.min(), v.max()
    rng = hi - lo or 1
    xs = np.linspace(0, width, len(v))
    ys = height - 3 - (v - lo) / rng * (height - 6)
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = f"0,{height} {pts} {width},{height}"
    return (f'<svg class="ms-spark" viewBox="0 0 {width} {height}" width="100%" height="{height}" '
            f'preserveAspectRatio="none"><polygon points="{area}" fill="{color}" fill-opacity="0.08"/>'
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.6" '
            f'vector-effect="non-scaling-stroke"/></svg>')


def index_card(name: str, df: pd.DataFrame, period_label: str) -> None:
    if df is None or len(df) < 2:
        html(f'<div class="ms-card"><div class="ms-kpi-label">{name}</div>'
             f'<div class="ms-kpi-foot">Data unavailable right now.</div></div>')
        return
    last, prev = df["Close"].iloc[-1], df["Close"].iloc[-2]
    chg, pct = last - prev, (last / prev - 1) * 100
    period_ret = (last / df["Close"].iloc[0] - 1) * 100
    html(f"""
    <div class="ms-card">
      <div class="ms-index-top">
        <div class="ms-kpi-label">{icon('activity', 14)} {name}</div>
        <span class="ms-co">{df.index[-1]:%d %b %Y}</span>
      </div>
      <div class="ms-kpi-value">{last:,.2f}</div>
      {chip(pct, chg)}
      {sparkline_svg(df['Close'].values)}
      <div class="ms-kpi-foot">{period_label}: <b class="{tone(period_ret)}">{period_ret:+.2f}%</b>
        &nbsp;·&nbsp; High {df['High'].max():,.0f} &nbsp;·&nbsp; Low {df['Low'].min():,.0f}</div>
    </div>""")


def kpi_card(label: str, value: str, foot: str = "", icon_name: str = "chart",
             delta=None, best: bool = False, tag: str = "") -> None:
    delta_html = chip(delta) if delta is not None else ""
    tag_html = f'<span class="ms-tag">{tag}</span>' if tag else ""
    html(f"""
    <div class="ms-card {'ms-best' if best else ''}">
      <div class="ms-index-top"><div class="ms-kpi-label">{icon(icon_name, 14)} {label}</div>{tag_html}</div>
      <div class="ms-kpi-value">{value}</div>{delta_html}
      <div class="ms-kpi-foot">{foot}</div>
    </div>""")


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
def html_table(rows: list[dict], columns: list[tuple]) -> None:
    """
    rows    : list of dicts
    columns : list of (header, key, kind) where kind is one of
              'stock', 'num', 'pct', 'big', 'text', 'pct_plain'
    """
    head = "".join(f'<th class="{"num" if k not in ("stock", "text") else ""}">{h}</th>'
                   for h, _, k in columns)
    body = []
    for r in rows:
        cells = []
        for _, key, kind in columns:
            v = r.get(key)
            if kind == "stock":
                cells.append(f'<td><div class="ms-sym">{escape(str(v))}</div>'
                             f'<div class="ms-co">{escape(str(r.get("Company", "")))}</div></td>')
            elif kind == "pct":
                cells.append(f'<td class="num">{chip(v)}</td>')
            elif kind == "pct_plain":
                cells.append(f'<td class="num {tone(v)}">{fmt_num(v)}%</td>')
            elif kind == "big":
                cells.append(f'<td class="num">{fmt_big(v)}</td>')
            elif kind == "num":
                cells.append(f'<td class="num">{fmt_num(v)}</td>')
            else:
                cells.append(f"<td>{escape(str(v))}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    html(f'<div class="ms-table-wrap"><table class="ms-table"><thead><tr>{head}</tr></thead>'
         f'<tbody>{"".join(body)}</tbody></table></div>')


def feed(items: list[dict]) -> None:
    """items: dicts with icon, color, bg, title, meta"""
    out = []
    for it in items:
        out.append(f'<div class="ms-feed-item"><div class="ms-feed-icon" style="background:{it["bg"]};'
                   f'color:{it["color"]}">{icon(it["icon"], 15)}</div><div>'
                   f'<div class="ms-feed-title">{escape(it["title"])}</div>'
                   f'<div class="ms-feed-meta">{escape(it["meta"])}</div></div></div>')
    html("".join(out) or '<div class="ms-feed-meta">No notable activity in this window.</div>')


# ---------------------------------------------------------------------------
# Shared selections (stock + date filter) kept in session_state so the choice
# follows the user from page to page.
# ---------------------------------------------------------------------------
PERIOD_DAYS = {"1mo": 31, "3mo": 92, "6mo": 183, "1y": 365, "2y": 730, "5y": 1826}


def init_state() -> None:
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("ticker", DEFAULT_STOCK)
    st.session_state.setdefault("period_label", DEFAULT_PERIOD)
    st.session_state.setdefault("custom_range", (date.today() - timedelta(days=365), date.today()))


def login_user(user: dict) -> None:
    """Start a session for this user and apply their saved preferences."""
    from marketscope import user_profile
    st.session_state.user = user
    st.session_state.profile = user_profile.load(user["username"], user)
    st.session_state.ticker = st.session_state.profile["default_stock"]
    st.session_state.period_label = st.session_state.profile["default_period"]


def logout() -> None:
    for k in ("user", "profile", "ml_run"):
        st.session_state.pop(k, None)
    st.session_state.user = None


def user_menu(key: str) -> None:
    """Avatar button (top-right of every page) with profile shortcut and log out."""
    from marketscope import nav, user_profile
    user = st.session_state.get("user")
    if not user:
        return
    prof = st.session_state.get("profile", {})
    name = prof.get("name") or user["name"]
    with st.popover(name.split()[0] if name else user["username"], icon=":material/account_circle:",
                    width="stretch"):
        html(f"""
        <div style="display:flex;gap:.7rem;align-items:center;margin-bottom:.6rem">
          <div style="width:42px;height:42px;border-radius:50%;background:{COLORS['navy']};color:#fff;display:flex;
            align-items:center;justify-content:center;font-weight:700;border:2px solid {COLORS['gold']}">
            {user_profile.initials(name)}</div>
          <div><div style="font-weight:650;color:{COLORS['navy']}">{escape(name)}</div>
            <div class="ms-co">@{escape(user['username'])} · {escape(prof.get('email') or user['email'])}</div></div>
        </div>""")
        if st.button("Profile & Account", icon=":material/person:", key=f"um_prof_{key}", width="stretch"):
            nav.go("account")
        if st.button("Log out", icon=":material/logout:", key=f"um_out_{key}", width="stretch"):
            logout()
            st.rerun()


def _copy(src, dst):
    st.session_state[dst] = st.session_state[src]


def stock_search(key: str, label: str = "Search stock") -> str:
    options = list(NIFTY50_STOCKS)
    st.selectbox(label, options, index=options.index(st.session_state.ticker), key=f"w_ticker_{key}",
                 format_func=lambda t: f"{t.replace('.NS', '')} · {NIFTY50_STOCKS[t]}",
                 on_change=_copy, args=(f"w_ticker_{key}", "ticker"))
    return st.session_state.ticker


def date_filter(key: str, allow_custom: bool = False) -> dict:
    """Returns {'label', 'start', 'end'} for the chosen window."""
    options = list(PERIODS) + (["Custom range"] if allow_custom else [])
    current = st.session_state.period_label
    if current not in options:
        current = DEFAULT_PERIOD
    st.selectbox("Date range", options, index=options.index(current), key=f"w_period_{key}",
                 on_change=_copy, args=(f"w_period_{key}", "period_label"))
    label = st.session_state.period_label if st.session_state.period_label in options else DEFAULT_PERIOD
    end = date.today()
    if label == "Custom range":
        rng = st.date_input("From – To", value=st.session_state.custom_range,
                            max_value=end, key=f"w_range_{key}")
        if isinstance(rng, (tuple, list)) and len(rng) == 2:
            st.session_state.custom_range = tuple(rng)
        start, end = st.session_state.custom_range
    else:
        start = end - timedelta(days=PERIOD_DAYS[PERIODS[label]])
    return {"label": label, "start": start, "end": end}


def page_header(eyebrow: str, title: str, subtitle: str, stock: bool = True,
                period: bool = True, allow_custom: bool = False, key: str = "hdr"):
    """Page title on the left; search + date filter on the right."""
    widths = [2.2] + ([1.3] if stock else []) + ([1] if period else []) + ([0.8] if not (stock or period) else [])
    left, *right = st.columns(widths + [0.62], vertical_alignment="bottom")
    with right[-1]:
        user_menu(key)
    with left:
        html(f'<div class="ms-eyebrow">{eyebrow}</div><div class="ms-title">{title}</div>'
             f'<div class="ms-subtitle">{subtitle}</div>')
    ticker, window = None, None
    i = 0
    if stock:
        with right[i]:
            ticker = stock_search(key)
        i += 1
    if period:
        with right[i]:
            window = date_filter(key, allow_custom)
    html('<div class="ms-divider"></div>')
    return ticker, window


def load_window(ticker: str, window: dict, warmup_days: int = 120):
    """
    Download the chosen window PLUS extra warm-up days, so indicators like
    SMA 50 are valid from the first visible day. Returns (full_df, start_ts).
    """
    start = pd.Timestamp(window["start"])
    df = data.load_history_range(ticker, start - pd.Timedelta(days=warmup_days), window["end"])
    return df, start


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def sidebar() -> None:
    """Logo + app name, drawn above the navigation."""
    with st.sidebar:
        html(f"""
        <div class="ms-brand">
          <div class="ms-brand-mark">{icon('trend_up', 20, '#0F2341', 2.2)}</div>
          <div><div class="ms-brand-name">{APP_NAME}</div><div class="ms-brand-tag">{APP_TAGLINE}</div></div>
        </div>""")


def sidebar_status() -> None:
    """Market status + mini index ticker, drawn below the navigation."""
    status = data.market_status()
    dot = COLORS["up"] if status["open"] else ("#C9A24A" if status["label"] == "Pre-Open" else "#8A97AB")
    idx = data.load_indices("5d")
    rows = ""
    for name, df in idx.items():
        if len(df) >= 2:
            pct = (df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100
            col = "#7FC4A2" if pct >= 0 else "#E39A92"
            rows += (f'<div class="ms-side-index"><span>{name}</span>'
                     f'<span style="color:{col};font-weight:600">{pct:+.2f}%</span></div>')
    with st.sidebar:
        html(f"""
        <div class="ms-side-label">Market Status · NSE</div>
        <div class="ms-status">
          <div class="ms-status-row"><span class="ms-dot" style="background:{dot}"></span>{status['label']}</div>
          <div class="ms-status-time">{status['time']}</div>
          <div class="ms-status-time">Regular session 09:15 – 15:30 IST</div>
        </div>
        <div class="ms-side-label">Indices · last session</div>
        <div>{rows or '<div class="ms-side-index">Data unavailable</div>'}</div>
        <div class="ms-side-foot">Data: Yahoo Finance (end-of-day, may be delayed).<br>
        Status uses the NSE schedule and does not account for exchange holidays.</div>
        """)
