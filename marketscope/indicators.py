"""
indicators.py - Technical indicators computed with Pandas.

Every function takes a price DataFrame (or Series) and returns a new
Series/DataFrame. Formulas are written out plainly so they are easy to
explain:

  SMA(n)        = mean of the last n closes
  EMA(n)        = exponentially weighted mean, span n
  RSI(14)       = 100 - 100 / (1 + avg_gain / avg_loss)   (Wilder smoothing)
  MACD          = EMA12 - EMA26 ; Signal = EMA9(MACD) ; Histogram = MACD - Signal
  Daily return  = Close_t / Close_{t-1} - 1
  Volatility    = std(daily returns over n days) * sqrt(252)   (annualised)
"""

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def sma(close: pd.Series, n: int) -> pd.Series:
    return close.rolling(n).mean()


def ema(close: pd.Series, n: int) -> pd.Series:
    return close.ewm(span=n, adjust=False).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    avg_loss = loss.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    return out.fillna(100).where(avg_loss.notna())


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    line = ema(close, fast) - ema(close, slow)
    sig = line.ewm(span=signal, adjust=False).mean()
    return pd.DataFrame({"MACD": line, "Signal": sig, "Histogram": line - sig})


def daily_returns(close: pd.Series) -> pd.Series:
    return close.pct_change()


def volatility(close: pd.Series, n: int = 20) -> pd.Series:
    """Annualised rolling historical volatility (in %)."""
    return daily_returns(close).rolling(n).std() * np.sqrt(TRADING_DAYS) * 100


def add_all(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with every indicator column added."""
    out = df.copy()
    c = out["Close"]
    out["SMA 20"] = sma(c, 20)
    out["SMA 50"] = sma(c, 50)
    out["EMA 12"] = ema(c, 12)
    out["EMA 26"] = ema(c, 26)
    out["RSI"] = rsi(c)
    out = out.join(macd(c))
    out["Return"] = daily_returns(c)
    out["Volatility 20"] = volatility(c, 20)
    return out


def summary_stats(df: pd.DataFrame) -> dict:
    """Headline statistics for a price history."""
    c = df["Close"]
    r = daily_returns(c).dropna()
    peak = c.cummax()
    return {
        "Last Close": c.iloc[-1],
        "Period Return %": (c.iloc[-1] / c.iloc[0] - 1) * 100,
        "Ann. Volatility %": r.std() * np.sqrt(TRADING_DAYS) * 100 if len(r) > 1 else np.nan,
        "Max Drawdown %": ((c / peak - 1).min()) * 100,
        "Period High": df["High"].max(),
        "Period Low": df["Low"].min(),
        "Avg Volume": df["Volume"].mean(),
        "Up Days %": (r > 0).mean() * 100 if len(r) else np.nan,
    }
