"""
data.py - Real market data collection from Yahoo Finance (via yfinance).

Downloads are cached with st.cache_data so the same request is not
downloaded again on every click (failed downloads are never cached). No fake/sample data is ever generated:
if a download fails, the function returns an empty DataFrame and the UI
shows a clear message instead.
"""

from datetime import datetime, time, timedelta, timezone

import pandas as pd
import streamlit as st
import yfinance as yf

from marketscope.config import CACHE_TTL, INDICES, NIFTY50_STOCKS

OHLCV = ["Open", "High", "Low", "Close", "Volume"]
IST = timezone(timedelta(hours=5, minutes=30))


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Keep OHLCV columns, drop empty rows, make the index timezone-naive."""
    if df is None or df.empty:
        return pd.DataFrame(columns=OHLCV)
    if isinstance(df.columns, pd.MultiIndex):          # single ticker can still be multi-index
        df.columns = df.columns.get_level_values(0)
    df = df[[c for c in OHLCV if c in df.columns]].copy()
    df = df.dropna(subset=["Close"])
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "Date"
    return df


class NoDataError(Exception):
    """Raised inside cached functions so that failed/empty downloads are NOT cached."""


# The _fetch_* functions are cached. They raise on failure, and st.cache_data never
# caches an exception - so after a network blip the next request simply retries,
# instead of showing "no data" for the whole cache period.
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _fetch_history(ticker: str, period: str | None, start, end) -> pd.DataFrame:
    kwargs = {"period": period} if period else {"start": start, "end": pd.Timestamp(end) + pd.Timedelta(days=1)}
    df = _clean(yf.download(ticker, interval="1d", auto_adjust=True, progress=False, threads=False, **kwargs))
    if df.empty:
        raise NoDataError(ticker)
    return df


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _fetch_many(tickers: tuple, period: str) -> dict:
    raw = yf.download(list(tickers), period=period, interval="1d", auto_adjust=True,
                      group_by="ticker", progress=False, threads=True)
    out = {}
    for t in tickers:
        if isinstance(raw.columns, pd.MultiIndex) and t in raw.columns.get_level_values(0):
            df = _clean(raw[t])
            if not df.empty:
                out[t] = df
    if not out:
        raise NoDataError(",".join(tickers))
    return out


def load_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Daily OHLCV history for one ticker (empty DataFrame if unavailable)."""
    try:
        return _fetch_history(ticker, period, None, None)
    except Exception:
        return pd.DataFrame(columns=OHLCV)


def load_history_range(ticker: str, start, end) -> pd.DataFrame:
    """Daily OHLCV history between two dates, end inclusive (empty if unavailable)."""
    try:
        return _fetch_history(ticker, None, start, end)
    except Exception:
        return pd.DataFrame(columns=OHLCV)


def load_many(tickers: tuple, period: str = "1mo") -> dict:
    """Download several tickers in ONE request. Returns {ticker: DataFrame} ({} if unavailable)."""
    try:
        return _fetch_many(tuple(tickers), period)
    except Exception:
        return {}


def load_indices(period: str = "1y") -> dict:
    """History for NIFTY 50, SENSEX and BANK NIFTY keyed by display name."""
    data = load_many(tuple(INDICES.values()), period)
    return {name: data[sym] for name, sym in INDICES.items() if sym in data}


def load_nifty50_snapshot(period: str = "3mo") -> pd.DataFrame:
    """
    One row per NIFTY 50 stock with its latest price, daily change, volume
    and period return. Used for the gainers/losers table and heatmap.
    """
    data = load_many(tuple(NIFTY50_STOCKS.keys()), period)
    rows = []
    for t, df in data.items():
        if len(df) < 2:
            continue
        last, prev = df.iloc[-1], df.iloc[-2]
        avg_vol = df["Volume"].iloc[-21:-1].mean()
        rows.append({
            "Symbol": t.replace(".NS", ""),
            "Ticker": t,
            "Company": NIFTY50_STOCKS[t],
            "Price": last["Close"],
            "Change": last["Close"] - prev["Close"],
            "Change %": (last["Close"] / prev["Close"] - 1) * 100,
            "Volume": last["Volume"],
            "Rel. Volume": last["Volume"] / avg_vol if avg_vol else float("nan"),
            "Period Return %": (last["Close"] / df["Close"].iloc[0] - 1) * 100,
            "Period High": df["High"].max(),
            "At Period High": last["Close"] >= df["High"].max() * 0.995,
            "Date": df.index[-1],
        })
    return pd.DataFrame(rows)


def load_nifty50_breadth(period: str = "3mo") -> pd.DataFrame:
    """
    Daily totals across all NIFTY 50 stocks:
      Volume    - shares traded
      Turnover  - Close x Volume, in Rs. crore (approximate traded value)
      Advances / Declines - how many stocks closed up / down that day
    """
    data = load_many(tuple(NIFTY50_STOCKS.keys()), period)
    if not data:
        return pd.DataFrame()
    vol = pd.DataFrame({t: d["Volume"] for t, d in data.items()})
    close = pd.DataFrame({t: d["Close"] for t, d in data.items()})
    chg = close.pct_change()
    out = pd.DataFrame({
        "Volume": vol.sum(axis=1),
        "Turnover": (vol * close).sum(axis=1) / 1e7,
        "Advances": (chg > 0).sum(axis=1),
        "Declines": (chg < 0).sum(axis=1),
    }).iloc[1:]
    return out[out["Volume"] > 0]


def market_status(now: datetime | None = None) -> dict:
    """
    NSE timetable (IST): pre-open session 09:00-09:15, regular session 09:15-15:30, Mon-Fri.
    Exchange holidays are not included, so this is a schedule-based estimate.
    """
    now = (now or datetime.now(IST)).astimezone(IST)
    pre_t, open_t, close_t = time(9, 0), time(9, 15), time(15, 30)
    is_weekday = now.weekday() < 5
    if is_weekday and open_t <= now.time() < close_t:
        label, is_open = "Market Open", True
    elif is_weekday and pre_t <= now.time() < open_t:
        label, is_open = "Pre-Open", False
    else:
        label, is_open = "Market Closed", False
    return {"label": label, "open": is_open, "time": now.strftime("%d %b %Y, %H:%M IST")}
