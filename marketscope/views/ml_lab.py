"""
Machine Learning Lab page.

Trains Random Forest, XGBoost and LSTM on real price history with a
chronological train/test split, then compares them against a naive
baseline with MAE, RMSE and directional accuracy.
Results are kept in st.session_state so they survive page switches, and the
training function is cached so re-running the same configuration is instant.
"""

import numpy as np
import pandas as pd
import streamlit as st

from marketscope import charts as ch
from marketscope import components as ui
from marketscope import data
from marketscope import models as M
from marketscope.charts import CHART_CONFIG
from marketscope.config import NIFTY50_STOCKS, SERIES_COLORS

MODEL_NAMES = ["Random Forest", "XGBoost", "LSTM"]
HISTORY = {"2 Years": "2y", "5 Years": "5y", "10 Years": "10y"}


# ---------------------------------------------------------------------------
# Training (cached: same inputs -> same results without retraining)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False, max_entries=20)
def run_experiment(ticker: str, history: str, test_size: float, model_names: tuple, params: dict):
    df = data.load_history(ticker, history)
    if len(df) < 200:
        raise ValueError(f"Only {len(df)} trading days available — need at least 200.")
    ds = M.prepare_dataset(df, test_size)
    results = {"Naive Baseline": M.naive_baseline(ds)}
    errors = {}
    for name in model_names:
        try:
            if name == "Random Forest":
                results[name] = M.train_random_forest(ds, **params["rf"])
            elif name == "XGBoost":
                results[name] = M.train_xgboost(ds, **params["xgb"])
            elif name == "LSTM":
                results[name] = M.train_lstm(ds, **params["lstm"])
        except Exception as exc:  # keep the other models if one fails
            errors[name] = str(exc)
    train_close = df["Close"].loc[ds.train_range[0]:ds.train_range[1]]
    info = {
        "ticker": ticker, "history": history, "test_size": test_size, "rows": len(df),
        "n_train": len(ds.y_train), "n_test": len(ds.y_test), "train_range": ds.train_range,
        "test_range": ds.test_range, "dates_test": ds.dates_test, "actual": ds.next_close_test,
        "close_t": ds.close_test, "train_tail": train_close.iloc[-120:],
        "latest_close": ds.latest_close, "latest_date": ds.latest_date,
    }
    return results, info, errors


# ---------------------------------------------------------------------------
# UI pieces
# ---------------------------------------------------------------------------
def _controls(ticker: str):
    with ui.card("ml_controls"):
        ui.section("Model training controls", "Configure the experiment, then train", "settings")
        with st.form("ml_form", border=False):
            c1, c2, c3 = st.columns([1, 1.2, 1.6])
            with c1:
                hist_label = st.selectbox("Training history", list(HISTORY), index=1,
                                          help="How many years of daily data to download.")
            with c2:
                test_pct = st.slider("Test set size (most recent %)", 10, 40, 20, 5,
                                     help="The LAST part of the timeline is held out for testing.")
            with c3:
                chosen = st.multiselect("Models", MODEL_NAMES, default=MODEL_NAMES)
            if not M.XGB_AVAILABLE:
                ui.note("XGBoost could not be loaded on this computer (OpenMP runtime missing). "
                        "On macOS run <span class='ms-mono'>brew install libomp</span> or start the app "
                        "with <span class='ms-mono'>./run.sh</span>. Other models still work.", "warn")
            with st.expander("Hyperparameters", icon=":material/tune:"):
                r, x, l = st.columns(3)
                with r:
                    st.markdown("**Random Forest**")
                    rf = {"n_estimators": st.slider("Trees", 50, 600, 300, 50, key="rf_n"),
                          "max_depth": st.slider("Max depth", 2, 15, 6, key="rf_d"),
                          "min_samples_leaf": st.slider("Min samples per leaf", 1, 30, 5, key="rf_l")}
                with x:
                    st.markdown("**XGBoost**")
                    xgb = {"n_estimators": st.slider("Boosting rounds", 50, 800, 300, 50, key="xgb_n"),
                           "max_depth": st.slider("Max depth", 2, 10, 3, key="xgb_d"),
                           "learning_rate": st.select_slider("Learning rate", [0.01, 0.03, 0.05, 0.1, 0.2],
                                                             0.03, key="xgb_lr")}
                with l:
                    st.markdown("**LSTM**")
                    lstm = {"window": st.slider("Look-back window (days)", 5, 60, 20, 5, key="lstm_w"),
                            "units": st.select_slider("LSTM units", [16, 32, 64, 128], 32, key="lstm_u"),
                            "epochs": st.slider("Max epochs (early stopping on)", 5, 100, 30, 5, key="lstm_e")}
            submitted = st.form_submit_button("Train & evaluate models", type="primary",
                                              icon=":material/play_arrow:", width="stretch")
    config = dict(ticker=ticker, history=HISTORY[hist_label], test_size=test_pct / 100,
                  model_names=tuple(m for m in MODEL_NAMES if m in chosen),
                  params={"rf": rf, "xgb": xgb, "lstm": lstm})
    return submitted, config


def _train(config):
    if not config["model_names"]:
        st.warning("Select at least one model.")
        return
    with st.status(f"Training on {config['ticker']} …", expanded=False) as status:
        status.write("Downloading history and engineering features")
        status.write(f"Training: {', '.join(config['model_names'])} (LSTM takes longest)")
        try:
            results, info, errors = run_experiment(**config)
        except Exception as exc:
            status.update(label=f"Training failed: {exc}", state="error")
            return
        status.update(label="Training complete", state="complete")
    st.session_state.ml_run = {"config": config, "results": results, "info": info, "errors": errors}


def _model_card(name, res, best_rmse, best_dir, baseline):
    m = res.metrics
    is_base = name == "Naive Baseline"
    color = SERIES_COLORS.get(name, "#6B7280")
    tags = []
    if not is_base and name == best_rmse:
        tags.append("Lowest RMSE")
    if not is_base and name == best_dir:
        tags.append("Best direction")
    tag_html = "".join(f'<span class="ms-tag" style="margin-right:4px">{t}</span>' for t in tags) \
        or '<span class="ms-tag" style="visibility:hidden">–</span>'
    vs = ""
    if not is_base:
        diff = (m["RMSE"] / baseline["RMSE"] - 1) * 100
        vs = (f'RMSE {abs(diff):.1f}% {"lower" if diff < 0 else "higher"} than naive baseline')
    else:
        vs = "Reference: assumes tomorrow's close = today's"
    dir_txt = "—" if np.isnan(m["Directional Accuracy %"]) else f"{m['Directional Accuracy %']:.1f}%"
    ui.html(f"""
    <div class="ms-card {'ms-best' if tags else ''}">
      <div class="ms-kpi-label"><span class="ms-dot" style="background:{color}"></span> {name}</div>
      <div style="margin-top:.35rem">{tag_html}</div>
      <div class="ms-reading" style="margin-top:.7rem">
        <div>MAE<span>₹{m['MAE']:,.2f}</span></div>
        <div>RMSE<span>₹{m['RMSE']:,.2f}</span></div>
        <div>Directional acc.<span>{dir_txt}</span></div>
      </div>
      <div class="ms-kpi-foot">{vs}<br>Training time {res.train_seconds:.2f}s</div>
    </div>""")


def _results(run):
    results, info, errors = run["results"], run["info"], run["errors"]
    trained = {k: v for k, v in results.items() if k != "Naive Baseline"}
    for name, err in errors.items():
        ui.note(f"<b>{name}</b> could not be trained: {err}", "warn")
    if not trained:
        return
    table = M.comparison_table(results)
    baseline = results["Naive Baseline"].metrics
    best_rmse = table.drop("Naive Baseline")["RMSE"].idxmin()
    best_dir = table.drop("Naive Baseline")["Directional Accuracy %"].idxmax()

    # --- Training / evaluation info --------------------------------------------
    st.write("")
    tr, te = info["train_range"], info["test_range"]
    k = st.columns(4)
    with k[0]:
        ui.kpi_card("Training set", f"{info['n_train']} days", f"{tr[0]:%d %b %Y} → {tr[1]:%d %b %Y}", "database")
    with k[1]:
        ui.kpi_card("Test set", f"{info['n_test']} days", f"{te[0]:%d %b %Y} → {te[1]:%d %b %Y}", "target")
    with k[2]:
        ui.kpi_card("Features", f"{len(M.FEATURES)}", "Lagged returns, MAs, RSI, MACD, volatility, volume", "layers")
    with k[3]:
        ui.kpi_card("Split", f"{100 - info['test_size'] * 100:.0f} / {info['test_size'] * 100:.0f}",
                    "Chronological · scaler fit on train only", "calendar")

    # --- Metric cards -------------------------------------------------------
    st.write("")
    ui.section("Model performance on the test set",
               f"{info['ticker']} · predicting next-day close · {info['n_test']} unseen trading days", "target")
    cols = st.columns(len(results))
    for col, (name, res) in zip(cols, results.items()):
        with col:
            _model_card(name, res, best_rmse, best_dir, baseline)

    # --- Actual vs predicted --------------------------------------------------
    st.write("")
    with ui.card("ml_avp"):
        h1, h2 = st.columns([1.2, 1], vertical_alignment="center")
        with h1:
            ui.section("Actual vs predicted closing price", "Test period · dotted lines are model estimates",
                       "chart")
        with h2:
            show = st.pills("Models shown", list(trained), selection_mode="multi", default=list(trained),
                            key="ml_show", label_visibility="collapsed")
        ctx = st.toggle("Show training-period context", value=True, key="ml_ctx")
        preds = {n: trained[n].pred_price for n in (show or [])}
        st.plotly_chart(ch.actual_vs_predicted(info["dates_test"], info["actual"], preds,
                                               info["train_tail"] if ctx else None, height=460),
                        width="stretch", config=CHART_CONFIG)

    # --- Comparison ---------------------------------------------------------------
    st.write("")
    with ui.card("ml_compare"):
        ui.section("Model comparison", "Gold bar = best model for that metric · grey = naive baseline", "bars")
        c = st.columns(3)
        for col, (metric, low) in zip(c, [("MAE", True), ("RMSE", True), ("Directional Accuracy %", False)]):
            with col:
                ui.html(f'<div class="ms-kpi-label" style="margin-top:.4rem">{metric} '
                        f'{"(lower is better)" if low else "(higher is better)"}</div>')
                st.plotly_chart(ch.metric_comparison(table, metric, 280, low), width="stretch",
                                config=CHART_CONFIG)
        rows = []
        for model, r in table.iterrows():
            star = lambda ok: " ★" if ok else ""  # noqa: E731  marks the best value per column
            dacc = r["Directional Accuracy %"]
            rows.append({
                "Model": model,
                "MAE": f"₹{r['MAE']:,.2f}{star(model == table['MAE'].idxmin())}",
                "RMSE": f"₹{r['RMSE']:,.2f}{star(model == table['RMSE'].idxmin())}",
                "MAPE": f"{r['MAPE %']:.3f}%{star(model == table['MAPE %'].idxmin())}",
                "Dir": "—" if pd.isna(dacc) else f"{dacc:.1f}%{star(model == best_dir)}",
                "Time": f"{r['Train Time (s)']:.2f}s",
            })
        ui.html_table(rows, [("Model", "Model", "text"), ("MAE", "MAE", "text"), ("RMSE", "RMSE", "text"),
                             ("MAPE", "MAPE", "text"), ("Directional accuracy", "Dir", "text"),
                             ("Train time", "Time", "text")])
        st.caption("★ = best value in that column (including the naive baseline).")

    # --- Feature importance + errors -------------------------------------------
    st.write("")
    left, right = st.columns([1.35, 1], gap="medium")
    with left, ui.card("ml_imp"):
        ui.section("Feature importance", "Which inputs each model relied on most", "layers")
        tabs = st.tabs(list(trained) + (["Compare all"] if len(trained) > 1 else []))
        for tab, (name, res) in zip(tabs, trained.items()):
            with tab:
                st.caption(f"Method: {res.importance_method}")
                st.plotly_chart(ch.feature_importance(res.importance, M.FEATURE_DESCRIPTIONS,
                                                      SERIES_COLORS.get(name), 400),
                                width="stretch", config=CHART_CONFIG)
        if len(trained) > 1:
            with tabs[-1]:
                st.caption("Each column normalised to sum to 1 so models can be compared.")
                st.plotly_chart(ch.importance_heatmap({n: r.importance for n, r in trained.items()},
                                                      M.FEATURE_DESCRIPTIONS, 400),
                                width="stretch", config=CHART_CONFIG)
    with right, ui.card("ml_err"):
        ui.section("Error analysis", "Predicted − actual close (₹) on test days", "target")
        st.plotly_chart(ch.error_distribution({n: r.pred_price - info["actual"] for n, r in trained.items()}, 260),
                        width="stretch", config=CHART_CONFIG)
        if "LSTM" in trained and trained["LSTM"].history:
            ui.html('<div class="ms-kpi-label" style="margin-top:.3rem">LSTM training curve</div>')
            st.plotly_chart(ch.loss_curve(trained["LSTM"].history, 200), width="stretch",
                            config=CHART_CONFIG)

    # --- Prediction table -------------------------------------------------------
    st.write("")
    with ui.card("ml_table"):
        ui.section("Prediction results", "Every test day · ✓ means the predicted direction was correct", "table")
        out = pd.DataFrame({"Date": pd.to_datetime(info["dates_test"]).date,
                            "Previous close": info["close_t"], "Actual close": info["actual"]})
        actual_dir = np.sign(info["actual"] - info["close_t"])
        for n, r in trained.items():
            out[f"{n}"] = r.pred_price
            out[f"{n} error"] = r.pred_price - info["actual"]
            out[f"{n} dir"] = np.where(np.sign(r.pred_ret) == actual_dir, "✓", "✗")
        out = out.iloc[::-1].reset_index(drop=True)
        fmt = {c: ("{:+,.2f}" if c.endswith("error") else "₹{:,.2f}")
               for c in out.columns if c != "Date" and not c.endswith("dir")}
        st.dataframe(out.style.format(fmt), width="stretch", height=380, hide_index=True)
        st.download_button("Download predictions (CSV)", out.to_csv(index=False).encode(),
                           f"{info['ticker']}_predictions.csv", "text/csv", icon=":material/download:")

    # --- Next session estimate --------------------------------------------------
    st.write("")
    with ui.card("ml_next"):
        ui.section("Next-session experimental estimate",
                   f"Based on data up to {info['latest_date']:%d %b %Y} (close ₹{info['latest_close']:,.2f})",
                   "flag")
        cols = st.columns(len(trained))
        for col, (n, r) in zip(cols, trained.items()):
            with col:
                est = info["latest_close"] * (1 + r.next_day_ret)
                ui.kpi_card(n, f"₹{est:,.2f}", f"Implied move {r.next_day_ret * 100:+.2f}% · test RMSE "
                            f"±₹{r.metrics['RMSE']:,.0f}", "brain")
        st.write("")
        ui.experimental_disclaimer()

    # --- Methodology -----------------------------------------------------------
    st.write("")
    with st.expander("Training & evaluation methodology", icon=":material/school:"):
        st.markdown(f"""
**Goal.** Estimate the next trading day's closing price of **{info['ticker']}** from information available today.

**Pipeline**
1. **Data** – {info['rows']} daily OHLCV rows from Yahoo Finance ({info['history']} of history, adjusted for splits/dividends).
2. **Features** – {len(M.FEATURES)} indicators computed only from data up to day *t* (table below).
3. **Target** – next-day return `r(t+1) = Close(t+1) / Close(t) − 1`; the price estimate is `Close(t) × (1 + r̂)`.
4. **Chronological split** – first {100 - info['test_size'] * 100:.0f}% of days for training, last {info['test_size'] * 100:.0f}% for testing. No shuffling.
5. **Leakage prevention** – `StandardScaler` is fitted on training rows only; LSTM training windows use only training rows; the target is the only forward-looking column and is never used as an input.
6. **Models** – Random Forest (bagged decision trees), XGBoost (gradient-boosted trees), LSTM (recurrent neural network over a look-back window). A **naive baseline** (tomorrow = today) is the benchmark every model must beat.
7. **Metrics** – **MAE** (average absolute ₹ error), **RMSE** (penalises large errors more), **Directional accuracy** (% of test days where the predicted up/down direction was correct; 50% ≈ coin flip).

**How to interpret.** Daily stock prices are close to a random walk, so the naive baseline is hard to beat on MAE/RMSE.
A model is genuinely useful only if it beats the baseline *and* has directional accuracy meaningfully above 50% on unseen data.
""")
        st.dataframe(pd.DataFrame({"Feature": M.FEATURES, "Description": M.FEATURE_DESCRIPTIONS.values()}),
                     hide_index=True, width="stretch")


def render():
    ticker, _ = ui.page_header("Machine Learning Lab", "Model Comparison",
                               "Random Forest vs XGBoost vs LSTM for next-day price estimation",
                               period=False, key="ml")
    ui.experimental_disclaimer()
    st.write("")
    submitted, config = _controls(ticker)

    run = st.session_state.get("ml_run")
    # Train when the button is pressed, or automatically the first time with default settings
    if submitted or run is None:
        _train(config)
        run = st.session_state.get("ml_run")
    elif run["config"]["ticker"] != ticker:
        ui.note(f"Showing results for <b>{run['config']['ticker']}</b>. Press "
                f"<b>Train & evaluate models</b> to run the experiment on {ticker.replace('.NS', '')} "
                f"({NIFTY50_STOCKS[ticker]}).", "info")
    if run:
        _results(run)
