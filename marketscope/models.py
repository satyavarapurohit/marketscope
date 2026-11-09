"""
models.py - Machine Learning pipeline for next-day price estimation.

PIPELINE (explain this in your viva)
------------------------------------
1. Features  : built ONLY from information available at the end of day t
               (lagged returns, moving-average ratios, RSI, MACD, volatility,
               volume change).
2. Target    : the NEXT day's return  r(t+1) = Close(t+1) / Close(t) - 1.
               Predicting returns (not raw prices) lets tree models work on
               prices they have never seen. The predicted price is
               Close(t) * (1 + predicted return).
3. Split     : chronological. The first X% of days are training data, the
               last (100-X)% are test data. No shuffling, so the model never
               sees the future.
4. Scaling   : StandardScaler is fitted on the TRAINING rows only and then
               applied to the test rows (prevents data leakage).
5. Models    : Random Forest, XGBoost, LSTM, plus a naive baseline
               ("tomorrow's price = today's price") to compare against.
6. Metrics   : MAE and RMSE on price (in Rs.), directional accuracy
               (did we predict up/down correctly?).

All outputs are EXPERIMENTAL ESTIMATES for academic study, not forecasts
to trade on.
"""

import os
import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

from marketscope import indicators as ind

SEED = 42

# XGBoost needs the OpenMP runtime on macOS. If it is missing we keep the
# app working with the other models and show a clear message instead.
try:
    from xgboost import XGBRegressor
    XGB_AVAILABLE, XGB_ERROR = True, ""
except Exception as exc:  # pragma: no cover - depends on the machine
    XGBRegressor = None
    XGB_AVAILABLE, XGB_ERROR = False, str(exc).strip().splitlines()[0]

FEATURE_DESCRIPTIONS = {
    "ret_1": "Return today (t)",
    "ret_2": "Return on day t-1",
    "ret_3": "Return on day t-2",
    "ret_5": "Return on day t-4",
    "ret_5d": "Cumulative 5-day return",
    "close_sma20": "Close / SMA 20 - 1",
    "close_sma50": "Close / SMA 50 - 1",
    "ema12_ema26": "EMA 12 / EMA 26 - 1",
    "rsi": "RSI (14)",
    "macd_hist": "MACD histogram / Close",
    "vol_20": "20-day volatility",
    "hl_range": "(High - Low) / Close",
    "vol_change": "Volume / 20-day avg volume - 1",
}
FEATURES = list(FEATURE_DESCRIPTIONS)


# ---------------------------------------------------------------------------
# 1. Feature engineering
# ---------------------------------------------------------------------------
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a DataFrame with FEATURES, plus 'Close', 'target_ret'
    (next-day return) and 'next_close'. Every feature uses data up to day t only.
    """
    c, v = df["Close"], df["Volume"]
    r = c.pct_change()
    m = ind.macd(c)
    f = pd.DataFrame(index=df.index)
    f["ret_1"] = r
    f["ret_2"] = r.shift(1)
    f["ret_3"] = r.shift(2)
    f["ret_5"] = r.shift(4)
    f["ret_5d"] = c.pct_change(5)
    f["close_sma20"] = c / ind.sma(c, 20) - 1
    f["close_sma50"] = c / ind.sma(c, 50) - 1
    f["ema12_ema26"] = ind.ema(c, 12) / ind.ema(c, 26) - 1
    f["rsi"] = ind.rsi(c) / 100
    f["macd_hist"] = m["Histogram"] / c
    f["vol_20"] = r.rolling(20).std()
    f["hl_range"] = (df["High"] - df["Low"]) / c
    f["vol_change"] = v / v.rolling(20).mean() - 1
    f["Close"] = c
    # Target = what happens TOMORROW (shift -1). This is the only forward-looking column.
    f["next_close"] = c.shift(-1)
    f["target_ret"] = f["next_close"] / c - 1
    return f.replace([np.inf, -np.inf], np.nan)


# ---------------------------------------------------------------------------
# 2. Chronological split + scaling
# ---------------------------------------------------------------------------
@dataclass
class Dataset:
    X_train: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_test: np.ndarray
    close_test: np.ndarray        # Close on day t (base for the price estimate)
    next_close_test: np.ndarray   # Actual Close on day t+1
    dates_test: pd.DatetimeIndex  # Date t+1 (the day being predicted)
    train_range: tuple
    test_range: tuple
    scaler: StandardScaler
    X_all_scaled: np.ndarray      # all labelled rows, scaled (for LSTM windows)
    split_idx: int
    X_latest: np.ndarray          # latest unlabelled row(s) for the next-day estimate
    latest_close: float
    latest_date: pd.Timestamp


def prepare_dataset(df: pd.DataFrame, test_size: float = 0.2) -> Dataset:
    feats = build_features(df)
    feats = feats.dropna(subset=FEATURES)
    labelled = feats.dropna(subset=["target_ret"])
    latest = feats.iloc[[-1]]                       # today: features known, tomorrow unknown

    n = len(labelled)
    split = int(n * (1 - test_size))
    train, test = labelled.iloc[:split], labelled.iloc[split:]

    scaler = StandardScaler().fit(train[FEATURES])  # fit on TRAIN only
    X_all = scaler.transform(labelled[FEATURES])

    # the test row for day t predicts day t+1 -> label dates with the next trading day
    next_dates = labelled.index.to_series().shift(-1)
    next_dates.iloc[-1] = feats.index[feats.index.get_loc(labelled.index[-1]) + 1]

    return Dataset(
        X_train=X_all[:split], X_test=X_all[split:],
        y_train=train["target_ret"].values, y_test=test["target_ret"].values,
        close_test=test["Close"].values, next_close_test=test["next_close"].values,
        dates_test=pd.DatetimeIndex(next_dates.iloc[split:].values),
        train_range=(train.index[0], train.index[-1]),
        test_range=(test.index[0], test.index[-1]),
        scaler=scaler, X_all_scaled=X_all, split_idx=split,
        X_latest=scaler.transform(latest[FEATURES]),
        latest_close=float(latest["Close"].iloc[0]), latest_date=latest.index[0],
    )


# ---------------------------------------------------------------------------
# 3. Metrics
# ---------------------------------------------------------------------------
def evaluate(close_t, actual_next, pred_ret) -> dict:
    pred_price = close_t * (1 + pred_ret)
    actual_dir = np.sign(actual_next - close_t)
    pred_dir = np.sign(pred_ret)
    mask = actual_dir != 0
    return {
        "MAE": mean_absolute_error(actual_next, pred_price),
        "RMSE": float(np.sqrt(mean_squared_error(actual_next, pred_price))),
        "MAPE %": float(np.mean(np.abs(pred_price - actual_next) / actual_next) * 100),
        "Directional Accuracy %": float((pred_dir[mask] == actual_dir[mask]).mean() * 100),
    }


@dataclass
class ModelResult:
    name: str
    pred_ret: np.ndarray
    pred_price: np.ndarray
    metrics: dict
    importance: pd.Series
    importance_method: str
    train_seconds: float
    next_day_ret: float
    params: dict = field(default_factory=dict)
    history: dict | None = None   # LSTM training loss curve


def _result(name, ds, pred_ret, importance, method, secs, next_ret, params, history=None):
    return ModelResult(
        name=name, pred_ret=pred_ret, pred_price=ds.close_test * (1 + pred_ret),
        metrics=evaluate(ds.close_test, ds.next_close_test, pred_ret),
        importance=importance.sort_values(ascending=False), importance_method=method,
        train_seconds=secs, next_day_ret=float(next_ret), params=params, history=history,
    )


# ---------------------------------------------------------------------------
# 4. Models
# ---------------------------------------------------------------------------
def naive_baseline(ds: Dataset) -> ModelResult:
    """Tomorrow's price = today's price (predicted return = 0)."""
    zeros = np.zeros_like(ds.y_test)
    res = _result("Naive Baseline", ds, zeros, pd.Series(0.0, index=FEATURES),
                  "n/a", 0.0, 0.0, {"rule": "Close(t+1) = Close(t)"})
    res.metrics["Directional Accuracy %"] = float("nan")  # never predicts a direction
    return res


def train_random_forest(ds: Dataset, n_estimators=300, max_depth=6, min_samples_leaf=5) -> ModelResult:
    t0 = time.time()
    model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth,
                                  min_samples_leaf=min_samples_leaf, random_state=SEED, n_jobs=-1)
    model.fit(ds.X_train, ds.y_train)
    secs = time.time() - t0
    imp = pd.Series(model.feature_importances_, index=FEATURES)
    return _result("Random Forest", ds, model.predict(ds.X_test), imp,
                   "Impurity decrease (built-in)", secs, model.predict(ds.X_latest)[0],
                   {"n_estimators": n_estimators, "max_depth": max_depth,
                    "min_samples_leaf": min_samples_leaf})


def train_xgboost(ds: Dataset, n_estimators=300, max_depth=3, learning_rate=0.03) -> ModelResult:
    if not XGB_AVAILABLE:
        raise RuntimeError(f"XGBoost could not be loaded: {XGB_ERROR}")
    t0 = time.time()
    model = XGBRegressor(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate,
                         subsample=0.8, colsample_bytree=0.8, random_state=SEED, n_jobs=-1)
    model.fit(ds.X_train, ds.y_train)
    secs = time.time() - t0
    imp = pd.Series(model.feature_importances_, index=FEATURES)
    return _result("XGBoost", ds, model.predict(ds.X_test), imp,
                   "Gain-based (built-in)", secs, model.predict(ds.X_latest)[0],
                   {"n_estimators": n_estimators, "max_depth": max_depth,
                    "learning_rate": learning_rate})


def _windows(X: np.ndarray, end_rows: range, window: int) -> np.ndarray:
    """For each row i, stack rows (i-window+1 .. i) -> shape (n, window, features)."""
    return np.stack([X[i - window + 1:i + 1] for i in end_rows])


def train_lstm(ds: Dataset, window=20, units=32, epochs=30, batch_size=32) -> ModelResult:
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    import tensorflow as tf  # imported here because it is slow to load
    from tensorflow import keras

    tf.keras.utils.set_random_seed(SEED)
    X, split = ds.X_all_scaled, ds.split_idx
    # Training windows use only training rows. Test windows may look back into
    # earlier (training) rows - that is past data, so there is no leakage.
    train_rows = range(window - 1, split)
    test_rows = range(split, len(X))
    Xtr, Xte = _windows(X, train_rows, window), _windows(X, test_rows, window)
    ytr = ds.y_train[window - 1:]
    y_scale = ytr.std() or 1.0                      # scale the target so training is stable

    model = keras.Sequential([
        keras.layers.Input(shape=(window, X.shape[1])),
        keras.layers.LSTM(units),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(16, activation="relu"),
        keras.layers.Dense(1),
    ])
    model.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    t0 = time.time()
    hist = model.fit(Xtr, ytr / y_scale, epochs=epochs, batch_size=batch_size,
                     validation_split=0.1, shuffle=False, verbose=0,
                     callbacks=[keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)])
    secs = time.time() - t0

    pred = model.predict(Xte, verbose=0).ravel() * y_scale

    # Permutation importance on the test set: shuffle one feature, measure how much MAE grows.
    rng = np.random.default_rng(SEED)
    base_mae = np.mean(np.abs(pred - ds.y_test))
    imp = {}
    for j, name in enumerate(FEATURES):
        Xp = Xte.copy()
        Xp[:, :, j] = rng.permutation(Xp[:, :, j].ravel()).reshape(Xp.shape[0], window)
        p = model.predict(Xp, verbose=0).ravel() * y_scale
        imp[name] = max(np.mean(np.abs(p - ds.y_test)) - base_mae, 0)
    imp = pd.Series(imp)
    imp = imp / imp.sum() if imp.sum() > 0 else imp

    latest_window = np.vstack([X[-(window - 1):], ds.X_latest])[None, ...]
    next_ret = model.predict(latest_window, verbose=0).ravel()[0] * y_scale
    return _result("LSTM", ds, pred, imp, "Permutation (test set)", secs, next_ret,
                   {"window": window, "units": units, "epochs_run": len(hist.history["loss"]),
                    "max_epochs": epochs, "batch_size": batch_size},
                   history={"loss": hist.history["loss"], "val_loss": hist.history["val_loss"]})


def comparison_table(results: dict) -> pd.DataFrame:
    rows = []
    for name, r in results.items():
        rows.append({"Model": name, **r.metrics, "Train Time (s)": r.train_seconds})
    return pd.DataFrame(rows).set_index("Model")
