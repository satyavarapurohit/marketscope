"""
charts.py - All Plotly figures used in MarketScope.

style() applies one consistent look (fonts, grid, hover labels, legend), so
every chart in the app looks like part of the same product.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from marketscope.config import COLORS as C
from marketscope.config import SERIES_COLORS as S

FONT = "Inter, sans-serif"
CHART_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
                "toImageButtonOptions": {"format": "png", "scale": 2}}


def style(fig: go.Figure, height: int = 380, legend: bool = True, hover: str = "x unified") -> go.Figure:
    fig.update_layout(
        height=height, template="plotly_white",
        font=dict(family=FONT, size=12, color=C["text"]),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=36 if legend else 12, b=8),
        hovermode=hover,
        hoverlabel=dict(bgcolor="white", bordercolor=C["border"], font=dict(family=FONT, size=12, color=C["text"])),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11.5)) if legend else dict(),
        showlegend=legend,
    )
    fig.update_xaxes(showgrid=False, linecolor=C["border"], ticks="outside", tickcolor=C["border"],
                     tickfont=dict(color=C["muted"], size=11))
    fig.update_yaxes(gridcolor=C["grid"], zeroline=False, linecolor=C["border"],
                     tickfont=dict(color=C["muted"], size=11))
    return fig


def _rangebreaks(fig, index):
    """Hide weekends AND exchange holidays (weekdays with no trading) so candles sit side by side."""
    if len(index) < 2:
        return
    idx = pd.DatetimeIndex(index).normalize()
    holidays = pd.bdate_range(idx.min(), idx.max()).difference(idx)
    breaks = [dict(bounds=["sat", "mon"])]
    if len(holidays):
        breaks.append(dict(values=holidays.strftime("%Y-%m-%d").tolist()))
    fig.update_xaxes(rangebreaks=breaks)


# ---------------------------------------------------------------------------
# Price charts
# ---------------------------------------------------------------------------
def price_chart(df: pd.DataFrame, name: str, kind: str = "Area", height: int = 420) -> go.Figure:
    """Dashboard main chart: Area / Line / Candlestick with volume underneath."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.78, 0.22], vertical_spacing=0.03)
    up = df["Close"].iloc[-1] >= df["Close"].iloc[0]
    color = C["up"] if up else C["down"]
    if kind == "Candlestick":
        fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"],
                                     close=df["Close"], name=name,
                                     increasing=dict(line=dict(color=C["up"]), fillcolor=C["up"]),
                                     decreasing=dict(line=dict(color=C["down"]), fillcolor=C["down"])), 1, 1)
    else:
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name=name, mode="lines",
                                 line=dict(color=C["navy"] if kind == "Line" else color, width=1.8),
                                 fill="tozeroy" if kind == "Area" else None,
                                 fillcolor=f"rgba{_rgba(color, 0.08)}",
                                 hovertemplate="%{y:,.2f}<extra>Close</extra>"), 1, 1)
        lo, hi = df["Close"].min(), df["Close"].max()
        pad = (hi - lo) * 0.08
        fig.update_yaxes(range=[lo - pad, hi + pad], row=1, col=1)
    _volume_trace(fig, df, row=2)
    style(fig, height, legend=False)
    fig.update_xaxes(rangeslider_visible=False)
    fig.update_yaxes(title_text=None, row=2, col=1, showticklabels=False)
    _rangebreaks(fig, df.index)
    return fig


def _rgba(hex_color: str, a: float):
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def _volume_trace(fig, df, row):
    colors = np.where(df["Close"].diff().fillna(0) >= 0, C["up"], C["down"])
    if df["Volume"].fillna(0).sum() == 0:
        return
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=colors, marker_opacity=0.55,
                         name="Volume", hovertemplate="%{y:,.0f}<extra>Volume</extra>"), row, 1)


def candlestick_with_overlays(df: pd.DataFrame, overlays: list[str], name: str, height: int = 600) -> go.Figure:
    """Stock Analysis: candlestick + chosen moving averages, volume panel below."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.76, 0.24], vertical_spacing=0.025)
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name=name,
        increasing=dict(line=dict(color=C["up"], width=1), fillcolor=C["up"]),
        decreasing=dict(line=dict(color=C["down"], width=1), fillcolor=C["down"])), 1, 1)
    for col in overlays:
        if col in df:
            fig.add_trace(go.Scatter(x=df.index, y=df[col], name=col, mode="lines",
                                     line=dict(color=S[col], width=1.5, dash="dot" if col.startswith("EMA") else None),
                                     hovertemplate="%{y:,.2f}"), 1, 1)
    _volume_trace(fig, df, row=2)
    style(fig, height)
    fig.update_layout(xaxis_rangeslider_visible=False)
    fig.update_yaxes(title_text="Price (₹)", row=1, col=1, title_font=dict(size=11, color=C["muted"]))
    fig.update_yaxes(title_text="Volume", row=2, col=1, title_font=dict(size=11, color=C["muted"]))
    fig.update_xaxes(rangeselector=dict(
        buttons=[dict(count=1, label="1M", step="month", stepmode="backward"),
                 dict(count=3, label="3M", step="month", stepmode="backward"),
                 dict(count=6, label="6M", step="month", stepmode="backward"),
                 dict(step="all", label="All")],
        bgcolor="#F1F0EC", activecolor="#DCE3EC", font=dict(size=11), x=1, xanchor="right", y=1.06),
        row=1, col=1)
    _rangebreaks(fig, df.index)
    return fig


# ---------------------------------------------------------------------------
# Dashboard charts
# ---------------------------------------------------------------------------
def normalised_performance(series: dict, height=320) -> go.Figure:
    """Rebase several price series to 100 to compare performance."""
    palette = [C["navy"], C["gold"], C["accent"]]
    fig = go.Figure()
    for (name, s), col in zip(series.items(), palette):
        fig.add_trace(go.Scatter(x=s.index, y=s / s.iloc[0] * 100, name=name, mode="lines",
                                 line=dict(color=col, width=1.8), hovertemplate="%{y:.1f}"))
    fig.add_hline(y=100, line=dict(color=C["muted"], width=1, dash="dot"))
    style(fig, height)
    fig.update_layout(legend=dict(font=dict(size=10.5), itemwidth=30))
    fig.update_yaxes(title_text="Rebased to 100", title_font=dict(size=11, color=C["muted"]))
    return fig


def return_bars(labels, values, height=320, title_x="Return (%)") -> go.Figure:
    colors = [C["up"] if v >= 0 else C["down"] for v in values]
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=colors,
                           text=[f"{v:+.2f}%" for v in values], textposition="outside",
                           cliponaxis=False, hovertemplate="%{y}: %{x:+.2f}%<extra></extra>"))
    style(fig, height, legend=False, hover="closest")
    # leave room on both sides so the value labels never overlap the axis labels
    lim = max(abs(v) for v in values) * 1.7 or 1
    lo = -lim if min(values) < 0 else 0
    hi = lim if max(values) > 0 else 0
    fig.update_xaxes(range=[lo, hi], showgrid=True, gridcolor=C["grid"], zeroline=True,
                     zerolinecolor=C["muted"], ticksuffix="%", title_text=None)
    fig.update_yaxes(showgrid=False, autorange="reversed", ticklabelstandoff=8)
    fig.update_layout(margin=dict(l=8, r=8, t=8, b=8), bargap=0.35)
    return fig


def volume_chart(df: pd.DataFrame, name: str, height=300) -> go.Figure:
    """Volume bars + 20-day average volume line."""
    fig = go.Figure()
    colors = np.where(df["Close"].diff().fillna(0) >= 0, C["up"], C["down"])
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=colors, marker_opacity=0.6, name="Daily volume",
                         hovertemplate="%{y:,.0f}"))
    fig.add_trace(go.Scatter(x=df.index, y=df["Volume"].rolling(20).mean(), name="20-day average",
                             line=dict(color=C["navy"], width=1.6), hovertemplate="%{y:,.0f}"))
    style(fig, height)
    _rangebreaks(fig, df.index)
    return fig


def turnover_chart(breadth: pd.DataFrame, height=300) -> go.Figure:
    """NIFTY 50 aggregate traded value (bars) + 20-day average."""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=breadth.index, y=breadth["Turnover"], name="Turnover (₹ Cr)",
                         marker_color=C["accent"], marker_opacity=0.55, hovertemplate="₹%{y:,.0f} Cr"))
    fig.add_trace(go.Scatter(x=breadth.index, y=breadth["Turnover"].rolling(20, min_periods=5).mean(),
                             name="20-day average", line=dict(color=C["navy"], width=1.6),
                             hovertemplate="₹%{y:,.0f} Cr"))
    style(fig, height)
    fig.update_yaxes(title_text="₹ Crore", title_font=dict(size=11, color=C["muted"]))
    _rangebreaks(fig, breadth.index)
    return fig


def breadth_chart(breadth: pd.DataFrame, height=300) -> go.Figure:
    """Advances vs declines among NIFTY 50 stocks each day."""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=breadth.index, y=breadth["Advances"], name="Advances", marker_color=C["up"],
                         marker_opacity=0.8, hovertemplate="%{y} up"))
    fig.add_trace(go.Bar(x=breadth.index, y=-breadth["Declines"], name="Declines", marker_color=C["down"],
                         marker_opacity=0.8, customdata=breadth["Declines"], hovertemplate="%{customdata} down"))
    style(fig, height)
    fig.update_layout(barmode="relative", bargap=0.15)
    fig.update_yaxes(title_text="Stocks", title_font=dict(size=11, color=C["muted"]))
    _rangebreaks(fig, breadth.index)
    return fig


def market_heatmap(snap: pd.DataFrame, value_col="Change %", height=380) -> go.Figure:
    """NIFTY 50 grid heatmap: each tile is one stock coloured by % change."""
    s = snap.sort_values(value_col, ascending=False).reset_index(drop=True)
    ncols = 10
    nrows = int(np.ceil(len(s) / ncols))
    z = np.full((nrows, ncols), np.nan)
    text = np.full((nrows, ncols), "", dtype=object)
    hover = np.full((nrows, ncols), "", dtype=object)
    for i, r in s.iterrows():
        rr, cc = divmod(i, ncols)
        z[rr, cc] = r[value_col]
        text[rr, cc] = f"<b>{r['Symbol']}</b><br>{r[value_col]:+.2f}%"
        hover[rr, cc] = f"{r['Company']}<br>Price ₹{r['Price']:,.2f}<br>{value_col}: {r[value_col]:+.2f}%"
    lim = max(abs(np.nanmin(z)), abs(np.nanmax(z)), 0.5)
    fig = go.Figure(go.Heatmap(
        z=z, text=text, texttemplate="%{text}", customdata=hover, hovertemplate="%{customdata}<extra></extra>",
        colorscale=[[0, C["down"]], [0.5, "#F4F2EE"], [1, C["up"]]], zmin=-lim, zmax=lim,
        xgap=3, ygap=3, showscale=True, textfont=dict(size=10.5, family=FONT),
        colorbar=dict(thickness=10, outlinewidth=0, ticksuffix="%", len=0.9)))
    style(fig, height, legend=False, hover="closest")
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, autorange="reversed")
    return fig


# ---------------------------------------------------------------------------
# Technical indicator charts
# ---------------------------------------------------------------------------
def rsi_chart(df, height=300) -> go.Figure:
    fig = go.Figure()
    fig.add_hrect(y0=70, y1=100, fillcolor=C["down"], opacity=0.06, line_width=0)
    fig.add_hrect(y0=0, y1=30, fillcolor=C["up"], opacity=0.06, line_width=0)
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI (14)", line=dict(color=C["navy"], width=1.6),
                             hovertemplate="%{y:.1f}"))
    for lvl, lab in ((70, "Overbought 70"), (30, "Oversold 30")):
        fig.add_hline(y=lvl, line=dict(color=C["muted"], width=1, dash="dot"),
                      annotation_text=lab, annotation_position="top left",
                      annotation_font=dict(size=10, color=C["muted"]))
    style(fig, height)
    fig.update_yaxes(range=[0, 100])
    _rangebreaks(fig, df.index)
    return fig


def macd_chart(df, height=320) -> go.Figure:
    fig = go.Figure()
    colors = np.where(df["Histogram"] >= 0, C["up"], C["down"])
    fig.add_trace(go.Bar(x=df.index, y=df["Histogram"], name="Histogram", marker_color=colors,
                         marker_opacity=0.55, hovertemplate="%{y:.2f}"))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD", line=dict(color=C["navy"], width=1.6),
                             hovertemplate="%{y:.2f}"))
    fig.add_trace(go.Scatter(x=df.index, y=df["Signal"], name="Signal (9)", line=dict(color=C["gold"], width=1.6),
                             hovertemplate="%{y:.2f}"))
    style(fig, height)
    _rangebreaks(fig, df.index)
    return fig


def ma_chart(df, height=360) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Close", line=dict(color="#9AA5B4", width=1.3),
                             hovertemplate="%{y:,.2f}"))
    for col in ("SMA 20", "SMA 50", "EMA 12", "EMA 26"):
        fig.add_trace(go.Scatter(x=df.index, y=df[col], name=col, hovertemplate="%{y:,.2f}",
                                 line=dict(color=S[col], width=1.6, dash="dot" if col.startswith("EMA") else None)))
    style(fig, height)
    _rangebreaks(fig, df.index)
    return fig


def returns_chart(df, height=300) -> go.Figure:
    r = df["Return"] * 100
    fig = go.Figure(go.Bar(x=df.index, y=r, marker_color=np.where(r >= 0, C["up"], C["down"]),
                           marker_opacity=0.75, name="Daily return", hovertemplate="%{y:+.2f}%<extra></extra>"))
    style(fig, height, legend=False)
    fig.update_yaxes(ticksuffix="%")
    _rangebreaks(fig, df.index)
    return fig


def returns_histogram(df, height=300) -> go.Figure:
    r = (df["Return"] * 100).dropna()
    fig = go.Figure(go.Histogram(x=r, nbinsx=40, marker_color=C["accent"], marker_opacity=0.75,
                                 marker_line=dict(color="white", width=0.5), name="Days",
                                 hovertemplate="%{x}: %{y} days<extra></extra>"))
    fig.add_vline(x=r.mean(), line=dict(color=C["gold"], width=1.5, dash="dash"),
                  annotation_text=f"Mean {r.mean():+.2f}%", annotation_font=dict(size=10, color=C["gold"]))
    style(fig, height, legend=False, hover="closest")
    fig.update_xaxes(ticksuffix="%", title_text="Daily return", title_font=dict(size=11, color=C["muted"]))
    fig.update_yaxes(title_text="Number of days", title_font=dict(size=11, color=C["muted"]))
    return fig


def volatility_chart(df, height=300) -> go.Figure:
    fig = go.Figure(go.Scatter(x=df.index, y=df["Volatility 20"], name="20-day annualised volatility",
                               mode="lines", line=dict(color=C["gold"], width=1.6), fill="tozeroy",
                               fillcolor=f"rgba{_rgba(C['gold'], 0.10)}", hovertemplate="%{y:.1f}%"))
    avg = df["Volatility 20"].mean()
    fig.add_hline(y=avg, line=dict(color=C["muted"], width=1, dash="dot"),
                  annotation_text=f"Period average {avg:.1f}%", annotation_font=dict(size=10, color=C["muted"]))
    style(fig, height, legend=False)
    fig.update_yaxes(ticksuffix="%")
    _rangebreaks(fig, df.index)
    return fig


def monthly_returns_heatmap(df, height=340) -> go.Figure:
    """Year x Month heatmap of monthly returns."""
    m = df["Close"].resample("ME").last().pct_change().dropna() * 100
    tbl = pd.DataFrame({"Year": m.index.year, "Month": m.index.month, "Ret": m.values})
    piv = tbl.pivot(index="Year", columns="Month", values="Ret").reindex(columns=range(1, 13))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    lim = np.nanmax(np.abs(piv.values)) if piv.size else 1
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=months, y=[str(y) for y in piv.index],
        text=[[("" if pd.isna(v) else f"{v:+.1f}%") for v in row] for row in piv.values],
        texttemplate="%{text}", textfont=dict(size=10.5),
        colorscale=[[0, C["down"]], [0.5, "#F4F2EE"], [1, C["up"]]], zmin=-lim, zmax=lim,
        xgap=2, ygap=2, hovertemplate="%{y} %{x}: %{z:+.2f}%<extra></extra>",
        colorbar=dict(thickness=10, outlinewidth=0, ticksuffix="%")))
    style(fig, height, legend=False, hover="closest")
    fig.update_yaxes(autorange="reversed", showgrid=False, type="category")
    return fig


# ---------------------------------------------------------------------------
# Machine-learning charts
# ---------------------------------------------------------------------------
def actual_vs_predicted(dates, actual, preds: dict, train_tail=None, height=440) -> go.Figure:
    fig = go.Figure()
    if train_tail is not None and len(train_tail):
        fig.add_trace(go.Scatter(x=train_tail.index, y=train_tail.values, name="Training period (actual)",
                                 line=dict(color="#B8C0CC", width=1.3), hovertemplate="%{y:,.2f}"))
        fig.add_vrect(x0=train_tail.index[0], x1=dates[0], fillcolor="#EEF1F5", opacity=0.5, line_width=0,
                      annotation_text="Train", annotation_position="top left",
                      annotation_font=dict(size=10, color=C["muted"]))
        fig.add_vline(x=dates[0], line=dict(color=C["muted"], width=1, dash="dash"))
    fig.add_trace(go.Scatter(x=dates, y=actual, name="Actual", line=dict(color=S["Actual"], width=2.2),
                             hovertemplate="%{y:,.2f}"))
    for name, p in preds.items():
        fig.add_trace(go.Scatter(x=dates, y=p, name=name, hovertemplate="%{y:,.2f}",
                                 line=dict(color=S.get(name, C["muted"]), width=1.5, dash="dot")))
    style(fig, height)
    fig.update_yaxes(title_text="Close price (₹)", title_font=dict(size=11, color=C["muted"]))
    return fig


def metric_comparison(table: pd.DataFrame, metric: str, height=300, lower_is_better=True) -> go.Figure:
    t = table[metric].dropna()
    best = t.idxmin() if lower_is_better else t.idxmax()
    colors = [C["gold"] if m == best else (C["muted"] if m == "Naive Baseline" else C["navy"]) for m in t.index]
    suffix = "%" if "%" in metric else ""
    fig = go.Figure(go.Bar(x=t.index, y=t.values, marker_color=colors, marker_opacity=0.9,
                           text=[f"{v:,.2f}{suffix}" for v in t.values], textposition="outside", cliponaxis=False,
                           hovertemplate="%{x}: %{y:,.3f}<extra></extra>"))
    style(fig, height, legend=False, hover="closest")
    fig.update_layout(margin=dict(l=8, r=8, t=24, b=8))
    fig.update_xaxes(tickangle=0, tickfont=dict(size=10.5),
                     ticktext=[n.replace("Naive Baseline", "Baseline") for n in t.index], tickvals=list(t.index))
    if metric == "Directional Accuracy %":
        fig.add_hline(y=50, line=dict(color=C["muted"], width=1, dash="dot"),
                      annotation_text="50% = coin flip", annotation_position="bottom left",
                      annotation_font=dict(size=10, color=C["muted"]))
    return fig


def feature_importance(imp: pd.Series, labels: dict, color=None, height=380) -> go.Figure:
    imp = imp.sort_values()
    fig = go.Figure(go.Bar(x=imp.values, y=[labels.get(i, i) for i in imp.index], orientation="h",
                           marker_color=color or C["navy"], marker_opacity=0.85,
                           hovertemplate="%{y}: %{x:.3f}<extra></extra>"))
    style(fig, height, legend=False, hover="closest")
    fig.update_xaxes(showgrid=True, gridcolor=C["grid"], title_text="Relative importance",
                     title_font=dict(size=11, color=C["muted"]))
    fig.update_yaxes(showgrid=False)
    return fig


def importance_heatmap(imps: dict, labels: dict, height=380) -> go.Figure:
    df = pd.DataFrame(imps).fillna(0)
    df = df / df.sum()  # normalise each model to sum to 1
    df = df.loc[df.mean(axis=1).sort_values(ascending=False).index]
    fig = go.Figure(go.Heatmap(z=df.values, x=df.columns, y=[labels.get(i, i) for i in df.index],
                               colorscale=[[0, "#F6F4EF"], [1, C["navy"]]], xgap=2, ygap=2,
                               text=np.round(df.values, 3), texttemplate="%{text:.2f}", textfont=dict(size=10),
                               hovertemplate="%{y} · %{x}: %{z:.3f}<extra></extra>",
                               colorbar=dict(thickness=10, outlinewidth=0)))
    style(fig, height, legend=False, hover="closest")
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return fig


def error_distribution(errors: dict, height=300) -> go.Figure:
    fig = go.Figure()
    for name, e in errors.items():
        fig.add_trace(go.Box(y=e, name=name, marker_color=S.get(name, C["muted"]), boxmean=True,
                             line=dict(width=1.3), hovertemplate="%{y:,.2f}"))
    style(fig, height, legend=False, hover="closest")
    fig.update_yaxes(title_text="Prediction error (₹)", title_font=dict(size=11, color=C["muted"]),
                     zeroline=True, zerolinecolor=C["muted"])
    return fig


def loss_curve(history: dict, height=280) -> go.Figure:
    ep = list(range(1, len(history["loss"]) + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ep, y=history["loss"], name="Training loss", line=dict(color=C["navy"], width=1.8)))
    fig.add_trace(go.Scatter(x=ep, y=history["val_loss"], name="Validation loss",
                             line=dict(color=C["gold"], width=1.8, dash="dot")))
    style(fig, height)
    fig.update_xaxes(title_text="Epoch", title_font=dict(size=11, color=C["muted"]), dtick=max(1, len(ep) // 10))
    fig.update_yaxes(title_text="MSE (scaled)", title_font=dict(size=11, color=C["muted"]))
    return fig
