"""About page - project summary for evaluators."""

import streamlit as st

from marketscope import components as ui


def render():
    ui.page_header("Project", "About MarketScope",
                   "An academic Data Science project on stock market trend analysis", stock=False, period=False)
    left, right = st.columns([1.4, 1], gap="medium")
    with left, ui.card("about_main"):
        ui.section("What this project does", "", "info")
        st.markdown("""
MarketScope collects **real daily market data** for Indian indices and NIFTY 50 stocks, analyses trends with
classical **technical indicators**, and compares three **machine-learning models** for next-day price estimation.

| Page | Purpose |
|---|---|
| **Dashboard** | Market snapshot: indices, gainers/losers, volume, breadth, heatmap, activity feed |
| **Stock Analysis** | Candlestick chart with SMA/EMA overlays, volume, key statistics |
| **Technical Analysis** | RSI, MACD, moving averages, daily returns, volatility, monthly seasonality |
| **ML Lab** | Random Forest vs XGBoost vs LSTM with a chronological split and a naive baseline |

**Key Data Science ideas demonstrated**
- Feature engineering from time series (lags, rolling windows, momentum indicators)
- Chronological train/test split and **data-leakage prevention**
- Comparing models against a **baseline**, using several error metrics
- Model interpretability via **feature importance** (built-in and permutation)
""")
    with right, ui.card("about_stack"):
        ui.section("Technology stack", "", "layers")
        ui.html_table([
            {"a": "Interface", "b": "Streamlit"},
            {"a": "Charts", "b": "Plotly"},
            {"a": "Data", "b": "yfinance (Yahoo Finance), Pandas, NumPy"},
            {"a": "Classical ML", "b": "scikit-learn (Random Forest)"},
            {"a": "Boosting", "b": "XGBoost"},
            {"a": "Deep learning", "b": "TensorFlow / Keras (LSTM)"},
        ], [("Layer", "a", "text"), ("Tools", "b", "text")])
        st.write("")
        ui.section("Code structure", "", "grid")
        st.code("""app.py                 entry point + navigation
marketscope/
  config.py            tickers, colours, settings
  data.py              data download + caching
  indicators.py        SMA, EMA, RSI, MACD, volatility
  models.py            features, split, RF/XGB/LSTM
  charts.py            Plotly figures
  components.py        cards, tables, header, sidebar
  styles.py            CSS theme
  views/               one file per page""", language="text")
    st.write("")
    ui.experimental_disclaimer()
