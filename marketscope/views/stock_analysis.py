"""
Stock Analysis page - candlestick chart with moving-average overlays,
volume panel, headline statistics and recent sessions.
"""

import streamlit as st

from marketscope import charts as ch
from marketscope import components as ui
from marketscope import indicators as ind
from marketscope.charts import CHART_CONFIG
from marketscope.config import NIFTY50_STOCKS

OVERLAYS = ["SMA 20", "SMA 50", "EMA 12", "EMA 26"]


def render():
    ticker, window = ui.page_header("Equity Research", "Stock Analysis",
                                    "Price action, moving averages and volume for a single NIFTY 50 stock",
                                    allow_custom=True, key="stock")
    name = NIFTY50_STOCKS[ticker]

    with st.spinner(f"Loading {ticker}…"):
        full, start = ui.load_window(ticker, window)
    if full.empty:
        ui.note(f"No data returned for {ticker}. Check your connection or try another stock.", "warn")
        return
    df = ind.add_all(full).loc[start:]           # indicators use warm-up data, display the window only
    if len(df) < 2:
        ui.note("Not enough trading days in this range. Pick a wider date range.", "warn")
        return

    stats = ind.summary_stats(df)
    last, prev = df["Close"].iloc[-1], df["Close"].iloc[-2]

    # --- KPI row ----------------------------------------------------------------
    k = st.columns(5)
    with k[0]:
        ui.kpi_card("Last close", f"₹{last:,.2f}", f"{df.index[-1]:%d %b %Y}", "activity",
                    delta=(last / prev - 1) * 100)
    with k[1]:
        ui.kpi_card("Period return", f"{stats['Period Return %']:+.2f}%",
                    f"{df.index[0]:%d %b %Y} → {df.index[-1]:%d %b %Y}",
                    "trend_up" if stats["Period Return %"] >= 0 else "trend_down")
    with k[2]:
        ui.kpi_card("Volatility (ann.)", f"{stats['Ann. Volatility %']:.1f}%", "Std. dev. of daily returns × √252",
                    "wave")
    with k[3]:
        ui.kpi_card("Max drawdown", f"{stats['Max Drawdown %']:.1f}%", "Largest peak-to-trough fall", "trend_down")
    with k[4]:
        ui.kpi_card("Avg volume", ui.fmt_big(stats["Avg Volume"]),
                    f"Range ₹{stats['Period Low']:,.0f} – ₹{stats['Period High']:,.0f}", "volume")

    st.write("")

    # --- Main chart -----------------------------------------------------------
    with ui.card("candles"):
        h1, h2 = st.columns([1.3, 1], vertical_alignment="center")
        with h1:
            ui.section(f"{ticker.replace('.NS', '')} · {name}",
                       f"Daily candlesticks · {window['label']} · hover for OHLC values", "candles")
        with h2:
            overlays = st.pills("Overlays", OVERLAYS, selection_mode="multi", default=["SMA 20", "SMA 50"],
                                key="stock_overlays", label_visibility="collapsed")
        st.plotly_chart(ch.candlestick_with_overlays(df, overlays or [], ticker.replace(".NS", ""), height=620),
                        width="stretch", config=CHART_CONFIG)
        ui.html('<div class="ms-explain"><b>SMA</b> = simple moving average (equal weight to each day). '
                '<b>EMA</b> = exponential moving average (more weight on recent days, reacts faster). '
                'Green candles closed above their open, red candles below.</div>')

    st.write("")

    # --- Stats + recent sessions -----------------------------------------------
    left, right = st.columns([1, 2], gap="medium")
    with left, ui.card("stats"):
        ui.section("Key statistics", window["label"], "database")
        trend = "Above" if last > df["SMA 50"].iloc[-1] else "Below"
        rows = [
            {"k": "Last close", "v": f"₹{last:,.2f}"},
            {"k": "Period high / low", "v": f"₹{stats['Period High']:,.2f} / ₹{stats['Period Low']:,.2f}"},
            {"k": "Period return", "v": f"{stats['Period Return %']:+.2f}%"},
            {"k": "Annualised volatility", "v": f"{stats['Ann. Volatility %']:.2f}%"},
            {"k": "Max drawdown", "v": f"{stats['Max Drawdown %']:.2f}%"},
            {"k": "Up days", "v": f"{stats['Up Days %']:.1f}%"},
            {"k": "Average volume", "v": ui.fmt_big(stats["Avg Volume"])},
            {"k": "Price vs SMA 50", "v": f"{trend} ({(last / df['SMA 50'].iloc[-1] - 1) * 100:+.2f}%)"},
            {"k": "Trading days", "v": f"{len(df)}"},
        ]
        ui.html_table(rows, [("Metric", "k", "text"), ("Value", "v", "text")])

    with right, ui.card("sessions"):
        ui.section("Recent sessions", "Last 12 trading days", "table")
        recent = df.tail(12).iloc[::-1].copy()
        recent["Chg %"] = df["Return"].tail(12).iloc[::-1] * 100
        recent["Date"] = recent.index.strftime("%d %b %Y")
        ui.html_table(recent.to_dict("records"),
                      [("Date", "Date", "text"), ("Open", "Open", "num"), ("High", "High", "num"),
                       ("Low", "Low", "num"), ("Close", "Close", "num"), ("Change", "Chg %", "pct"),
                       ("Volume", "Volume", "big")])
        csv = df[["Open", "High", "Low", "Close", "Volume"] + OVERLAYS].round(4).to_csv().encode()
        st.download_button("Download data (CSV)", csv, f"{ticker}_{window['label'].replace(' ', '_')}.csv",
                           "text/csv", icon=":material/download:")
