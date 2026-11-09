"""
Technical Analysis page - one tab per indicator, each with a chart, a short
explanation and the current reading for the selected stock.
"""

import streamlit as st

from marketscope import charts as ch
from marketscope import components as ui
from marketscope import data
from marketscope import indicators as ind
from marketscope.charts import CHART_CONFIG

EXPLAIN = {
    "RSI": ("Relative Strength Index (14)",
            "RSI compares the size of recent gains with recent losses on a 0–100 scale. "
            "<b>Above 70</b> is commonly read as <i>overbought</i> (price rose fast), "
            "<b>below 30</b> as <i>oversold</i>. It measures momentum, not value."),
    "MACD": ("Moving Average Convergence Divergence",
             "<b>MACD line</b> = EMA 12 − EMA 26. <b>Signal line</b> = 9-day EMA of the MACD. "
             "The <b>histogram</b> is their difference. MACD crossing above the signal suggests "
             "strengthening upward momentum; crossing below suggests weakening."),
    "MA": ("Moving Averages",
           "Moving averages smooth out daily noise to show the trend. <b>SMA</b> weights every day "
           "equally; <b>EMA</b> weights recent days more. When the short average (SMA 20) is above the "
           "long one (SMA 50) the short-term trend is up — a cross is called a <i>golden</i> (up) or "
           "<i>death</i> (down) cross."),
    "RET": ("Daily Returns",
            "Daily return = today's close ÷ yesterday's close − 1. The bar chart shows each day's move; "
            "the histogram shows how returns are distributed. Most days cluster near 0%; the "
            "<i>tails</i> show how often large moves happen."),
    "VOL": ("Historical Volatility (20-day)",
            "Standard deviation of the last 20 daily returns, annualised by × √252 trading days. "
            "Higher values mean bigger, less predictable price swings — i.e. higher risk."),
    "SEAS": ("Monthly Returns Heatmap",
             "Each cell is the stock's return in one calendar month (last 5 years). Useful for spotting "
             "strong/weak periods at a glance. The current month is partial (month-to-date). "
             "Past patterns do not guarantee future results."),
}


def _explain(key: str, readings: list[tuple]) -> None:
    title, text = EXPLAIN[key]
    ui.section(title, "How to read this indicator", "info")
    reading_html = "".join(f"<div>{lab}<span class='{cls}'>{val}</span></div>" for lab, val, cls in readings)
    ui.html(f'<div class="ms-explain">{text}</div><div class="ms-reading">{reading_html}</div>')


def _layout(key, chart_fig, readings, extra_fig=None):
    left, right = st.columns([2.3, 1], gap="medium")
    with left, ui.card(f"tech_{key}"):
        st.plotly_chart(chart_fig, width="stretch", config=CHART_CONFIG)
        if extra_fig is not None:
            st.plotly_chart(extra_fig, width="stretch", config=CHART_CONFIG)
    with right, ui.card(f"tech_{key}_explain"):
        _explain(key, readings)


def render():
    ticker, window = ui.page_header("Indicators", "Technical Analysis",
                                    "Momentum, trend and risk indicators with plain-language explanations",
                                    allow_custom=True, key="tech")
    with st.spinner(f"Loading {ticker}…"):
        full, start = ui.load_window(ticker, window)
    if full.empty:
        ui.note(f"No data returned for {ticker}.", "warn")
        return
    df = ind.add_all(full).loc[start:]
    if len(df) < 5:
        ui.note("Not enough trading days in this range. Pick a wider date range.", "warn")
        return
    last = df.iloc[-1]

    # --- Signal summary ----------------------------------------------------------
    rsi_v = last["RSI"]
    rsi_state = "Overbought" if rsi_v > 70 else "Oversold" if rsi_v < 30 else "Neutral"
    macd_state = "Bullish" if last["MACD"] > last["Signal"] else "Bearish"
    trend_state = "Uptrend" if last["SMA 20"] > last["SMA 50"] else "Downtrend"
    vol_avg = df["Volatility 20"].mean()
    vol_state = "Elevated" if last["Volatility 20"] > vol_avg * 1.15 else \
        "Subdued" if last["Volatility 20"] < vol_avg * 0.85 else "Normal"

    k = st.columns(4)
    with k[0]:
        ui.kpi_card("RSI (14)", f"{rsi_v:.1f}", f"Momentum reading: <b>{rsi_state}</b>", "gauge")
    with k[1]:
        ui.kpi_card("MACD", f"{last['MACD']:.2f}", f"vs signal {last['Signal']:.2f}: <b>{macd_state}</b>",
                    "activity")
    with k[2]:
        ui.kpi_card("Trend (SMA 20 vs 50)", trend_state,
                    f"SMA 20 {last['SMA 20']:,.1f} · SMA 50 {last['SMA 50']:,.1f}",
                    "trend_up" if trend_state == "Uptrend" else "trend_down")
    with k[3]:
        ui.kpi_card("Volatility (20d)", f"{last['Volatility 20']:.1f}%",
                    f"Period avg {vol_avg:.1f}%: <b>{vol_state}</b>", "wave")
    ui.html('<div class="ms-subtitle" style="margin-top:.5rem">Readings are descriptive labels for '
            'study purposes, not buy/sell signals.</div>')

    tabs = st.tabs(["RSI", "MACD", "Moving Averages", "Daily Returns", "Volatility", "Monthly Heatmap"])
    with tabs[0]:
        _layout("RSI", ch.rsi_chart(df, 400),
                [("Current", f"{rsi_v:.1f}", ""), ("State", rsi_state, ""),
                 ("Days > 70", f"{(df['RSI'] > 70).sum()}", "ms-down"),
                 ("Days < 30", f"{(df['RSI'] < 30).sum()}", "ms-up")])
    with tabs[1]:
        crosses = ((df["MACD"] > df["Signal"]) != (df["MACD"] > df["Signal"]).shift()).iloc[1:].sum()
        _layout("MACD", ch.macd_chart(df, 400),
                [("MACD", f"{last['MACD']:.2f}", ""), ("Signal", f"{last['Signal']:.2f}", ""),
                 ("Histogram", f"{last['Histogram']:+.2f}", ui.tone(last["Histogram"])),
                 ("Crossovers", f"{crosses}", "")])
    with tabs[2]:
        _layout("MA", ch.ma_chart(df, 420),
                [("Close", f"{last['Close']:,.2f}", ""), ("SMA 20", f"{last['SMA 20']:,.2f}", ""),
                 ("SMA 50", f"{last['SMA 50']:,.2f}", ""), ("Trend", trend_state,
                                                            "ms-up" if trend_state == "Uptrend" else "ms-down")])
    with tabs[3]:
        r = df["Return"].dropna() * 100
        _layout("RET", ch.returns_chart(df, 280),
                [("Mean", f"{r.mean():+.3f}%", ui.tone(r.mean())), ("Std. dev.", f"{r.std():.2f}%", ""),
                 ("Best day", f"{r.max():+.2f}%", "ms-up"), ("Worst day", f"{r.min():+.2f}%", "ms-down"),
                 ("Skew", f"{r.skew():.2f}", ""), ("Kurtosis", f"{r.kurt():.2f}", "")],
                extra_fig=ch.returns_histogram(df, 260))
    with tabs[4]:
        _layout("VOL", ch.volatility_chart(df, 400),
                [("Current", f"{last['Volatility 20']:.1f}%", ""), ("Average", f"{vol_avg:.1f}%", ""),
                 ("Peak", f"{df['Volatility 20'].max():.1f}%", "ms-down"), ("Level", vol_state, "")])
    with tabs[5]:
        long_df = data.load_history(ticker, "5y")
        if len(long_df) < 60:
            st.info("Not enough history for a monthly heatmap.")
        else:
            m = long_df["Close"].resample("ME").last().pct_change().dropna() * 100
            _layout("SEAS", ch.monthly_returns_heatmap(long_df, 400),
                    [("Best month", f"{m.max():+.1f}%", "ms-up"), ("Worst month", f"{m.min():+.1f}%", "ms-down"),
                     ("Positive months", f"{(m > 0).mean() * 100:.0f}%", "")])
