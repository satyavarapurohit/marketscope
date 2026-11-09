"""
Dashboard page - market-wide overview.

Sections: index cards, main index chart, performance overview, top gainers
/ losers, market volume (turnover + breadth), NIFTY 50 heatmap and a feed
of recent market activity derived from the latest session's real data.
"""

import streamlit as st

from marketscope import charts as ch
from marketscope import components as ui
from marketscope import data
from marketscope.charts import CHART_CONFIG
from marketscope.config import COLORS, INDICES, PERIODS


def _activity(indices: dict, snap, breadth) -> list[dict]:
    """Build the 'Recent market activity' feed from real data."""
    up = dict(icon="trend_up", color=COLORS["up"], bg=COLORS["up_soft"])
    down = dict(icon="trend_down", color=COLORS["down"], bg=COLORS["down_soft"])
    neutral = dict(icon="zap", color=COLORS["navy"], bg="#EEF2F7")
    gold = dict(icon="flag", color=COLORS["gold"], bg="#F7F0E1")
    items = []

    for name, df in indices.items():
        if len(df) >= 2:
            pct = (df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100
            verb = "gained" if pct >= 0 else "fell"
            items.append({**(up if pct >= 0 else down),
                          "title": f"{name} {verb} {abs(pct):.2f}% to {df['Close'].iloc[-1]:,.2f}",
                          "meta": f"Index close · {df.index[-1]:%d %b %Y}"})

    if not breadth.empty:
        last = breadth.iloc[-1]
        items.append({**neutral, "title": f"Breadth: {int(last['Advances'])} advances, "
                                          f"{int(last['Declines'])} declines in NIFTY 50",
                      "meta": f"Turnover ≈ ₹{last['Turnover']:,.0f} Cr · {breadth.index[-1]:%d %b %Y}"})

    if not snap.empty:
        top, bot = snap.loc[snap["Change %"].idxmax()], snap.loc[snap["Change %"].idxmin()]
        items.append({**up, "title": f"Top gainer: {top['Symbol']} {top['Change %']:+.2f}%",
                      "meta": f"{top['Company']} · ₹{top['Price']:,.2f}"})
        items.append({**down, "title": f"Top loser: {bot['Symbol']} {bot['Change %']:+.2f}%",
                      "meta": f"{bot['Company']} · ₹{bot['Price']:,.2f}"})
        for _, r in snap[snap["Rel. Volume"] >= 1.8].nlargest(3, "Rel. Volume").iterrows():
            items.append({**neutral, "icon": "volume",
                          "title": f"Volume spike in {r['Symbol']}: {r['Rel. Volume']:.1f}× its 20-day average",
                          "meta": f"{ui.fmt_big(r['Volume'])} shares · price {r['Change %']:+.2f}%"})
        for _, r in snap[snap["At Period High"]].nlargest(3, "Period Return %").iterrows():
            items.append({**gold, "title": f"{r['Symbol']} trading near its period high",
                          "meta": f"₹{r['Price']:,.2f} vs high ₹{r['Period High']:,.2f} · "
                                  f"period return {r['Period Return %']:+.2f}%"})
    return items


def render():
    ticker, window = ui.page_header("Market Overview", "Dashboard",
                                    "Indian equity market snapshot — NIFTY 50, SENSEX and BANK NIFTY",
                                    key="dash")
    period = PERIODS[window["label"]]

    with st.spinner("Loading market data…"):
        indices = data.load_indices(period)
        snap = data.load_nifty50_snapshot(period)
        breadth = data.load_nifty50_breadth(period)

    if not indices:
        ui.note("Could not reach Yahoo Finance. Check your internet connection and reload.", "warn")
        return

    # --- Search shortcut -----------------------------------------------------
    c1, c2 = st.columns([5, 1.2], vertical_alignment="center")
    with c1:
        ui.html(f'<div class="ms-subtitle">Selected stock: <b>{ticker.replace(".NS", "")}</b> — '
                'open it in the analysis pages for charts, indicators and ML models.</div>')
    with c2:
        if st.button("Analyse stock →", width="stretch", type="primary"):
            from marketscope import nav
            nav.go("stock")

    # --- 1. Index cards -----------------------------------------------------
    cols = st.columns(3)
    for col, name in zip(cols, INDICES):
        with col:
            ui.index_card(name, indices.get(name), window["label"])

    st.write("")

    # --- 2. Main chart + performance overview --------------------------------
    left, right = st.columns([1.9, 1], gap="medium")
    with left, ui.card("main_chart"):
        h1, h2 = st.columns([1.4, 1], vertical_alignment="center")
        with h1:
            ui.section("Index chart", f"Daily close and volume · {window['label']}", "candles")
        with h2:
            kind = st.segmented_control("Chart type", ["Area", "Line", "Candlestick"], default="Area",
                                        key="dash_kind", label_visibility="collapsed")
        choice = st.segmented_control("Index", list(indices), default=list(indices)[0], key="dash_index",
                                      label_visibility="collapsed")
        choice = choice or list(indices)[0]
        st.plotly_chart(ch.price_chart(indices[choice], choice, kind or "Area", height=430),
                        width="stretch", config=CHART_CONFIG)

    with right, ui.card("performance"):
        ui.section("Market performance", f"Return over {window['label'].lower()}", "bars")
        names = list(indices)
        rets = [(indices[n]["Close"].iloc[-1] / indices[n]["Close"].iloc[0] - 1) * 100 for n in names]
        st.plotly_chart(ch.return_bars(names, rets, height=170), width="stretch", config=CHART_CONFIG)
        st.plotly_chart(ch.normalised_performance({n: indices[n]["Close"] for n in names}, height=250),
                        width="stretch", config=CHART_CONFIG)
        if not breadth.empty:
            adv, dec = int(breadth["Advances"].iloc[-1]), int(breadth["Declines"].iloc[-1])
            ui.html(f'<div class="ms-reading"><div>Advances<span class="ms-up">{adv}</span></div>'
                    f'<div>Declines<span class="ms-down">{dec}</span></div>'
                    f'<div>A/D ratio<span>{adv / max(dec, 1):.2f}</span></div></div>')

    st.write("")

    # --- 3. Gainers / losers + recent activity --------------------------------
    left, right = st.columns([1.6, 1], gap="medium")
    with left, ui.card("movers"):
        ui.section("Top gainers & losers", "NIFTY 50 constituents · latest session", "table")
        basis = st.segmented_control("Rank by", ["Day change", f"{window['label']} return"],
                                     default="Day change", key="dash_rank", label_visibility="collapsed")
        sort_col = "Change %" if basis != f"{window['label']} return" else "Period Return %"
        cols = [("Stock", "Symbol", "stock"), ("Price ₹", "Price", "num"), ("Day", "Change %", "pct"),
                (window["label"], "Period Return %", "pct_plain"), ("Volume", "Volume", "big")]
        tab_g, tab_l = st.tabs(["Top gainers", "Top losers"])
        if snap.empty:
            st.info("Stock data unavailable right now.")
        else:
            with tab_g:
                ui.html_table(snap.nlargest(6, sort_col).to_dict("records"), cols)
            with tab_l:
                ui.html_table(snap.nsmallest(6, sort_col).to_dict("records"), cols)

    with right, ui.card("activity"):
        ui.section("Recent market activity", "Generated from the latest session data", "clock")
        ui.feed(_activity(indices, snap, breadth)[:9])

    st.write("")

    # --- 4. Market volume: turnover + breadth -----------------------------------
    left, right = st.columns(2, gap="medium")
    with left, ui.card("volume"):
        ui.section("Market volume", "Traded value of all NIFTY 50 stocks (Close × Volume)", "volume")
        if breadth.empty:
            st.info("Volume data unavailable right now.")
        else:
            st.plotly_chart(ch.turnover_chart(breadth, height=320), width="stretch", config=CHART_CONFIG)
    with right, ui.card("breadth"):
        ui.section("Market breadth", "How many NIFTY 50 stocks rose vs fell each day", "activity")
        if breadth.empty:
            st.info("Breadth data unavailable right now.")
        else:
            st.plotly_chart(ch.breadth_chart(breadth, height=320), width="stretch", config=CHART_CONFIG)

    st.write("")

    # --- 5. NIFTY 50 heatmap (full width so every tile is readable) -------------
    with ui.card("heatmap"):
        h1, h2 = st.columns([2, 1], vertical_alignment="center")
        with h1:
            ui.section("NIFTY 50 heatmap", "Each tile is one stock, coloured by its move · hover for details",
                       "grid")
        with h2:
            metric = st.segmented_control("Heatmap metric", ["Change %", "Period Return %"], default="Change %",
                                          key="dash_heat", label_visibility="collapsed",
                                          format_func=lambda m: "Day change" if m == "Change %"
                                          else f"{window['label']} return")
        if snap.empty:
            st.info("Stock data unavailable right now.")
        else:
            st.plotly_chart(ch.market_heatmap(snap, metric or "Change %", height=380),
                            width="stretch", config=CHART_CONFIG)
