# MarketScope — Stock Market Trend Analysis

An academic Data Science project: a professional research-style dashboard for the Indian stock market
built with **Python, Streamlit and Plotly**, using **real market data from Yahoo Finance** and comparing
**Random Forest, XGBoost and LSTM** models for next-day price estimation.

> Model outputs are **experimental estimates** for studying ML methods — not guaranteed forecasts or investment advice.

---

## 1. Features

| Page | What it shows |
|---|---|
| **Dashboard** | NIFTY 50 / SENSEX / BANK NIFTY cards with sparklines, interactive index chart (Area / Line / Candlestick + volume), market performance (period returns + rebased comparison), top gainers & losers, recent market activity feed, NIFTY 50 turnover, market breadth (advances vs declines), NIFTY 50 heatmap |
| **Stock Analysis** | Large candlestick chart with SMA 20 / SMA 50 / EMA 12 / EMA 26 overlays, volume panel, range buttons, KPI cards, key statistics, recent sessions, CSV download |
| **Technical Analysis** | Separate tabs for RSI, MACD, Moving Averages, Daily Returns (+ distribution), Historical Volatility and a Monthly Returns heatmap — each with a plain-language explanation and the current reading |
| **ML Lab** | Training controls + hyperparameters, train/test info, MAE / RMSE / directional-accuracy cards, actual-vs-predicted chart, model comparison charts + table, feature importance (per model and heatmap), error analysis, LSTM loss curve, full prediction table (CSV), next-session experimental estimate, methodology |
| **About Project** | Summary, tech stack and code structure for evaluators |
| **Login / Sign up** | Sign in with username or email, or create an account (shown before the dashboard) |
| **Profile & Account** | Profile card, edit details, preferences (default stock, date range, watchlist), live watchlist, session activity, change password, export, log out |

The stock search and date filter in the page header are shared: pick a stock once and every page uses it.
The avatar button in the top-right corner of every page opens your profile or logs you out.

### Accounts
- The first time you open the app, choose **Create account**.
- Accounts are stored locally in `data/users.json`; passwords are **hashed** (PBKDF2-SHA256 with a random salt), never stored as text.
- Each user's profile and preferences are saved in `data/profiles/<username>.json`.
- Login lasts for the browser session — refreshing the page asks you to sign in again.
- You can change your password, export your profile, reset it, or **delete your account** (password required) under **Profile & Account → Account & data**.
- To remove all accounts at once, delete the `data/` folder.

---

## 2. Setup

### Requirements
- Python **3.10 – 3.12** (TensorFlow does not yet support every newer version)
- Internet connection (data is downloaded live from Yahoo Finance)

### Install

**macOS / Linux**
```bash
cd MarketScope
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell)**
```powershell
cd MarketScope
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS only — XGBoost needs OpenMP
Either install it once with Homebrew:
```bash
brew install libomp
```
…or simply start the app with `./run.sh` (below), which automatically reuses the OpenMP library bundled
with scikit-learn. If neither is done, the app still runs — XGBoost is just marked unavailable in the ML Lab.

---

## 3. Run

```bash
streamlit run app.py
```
or on macOS/Linux:
```bash
./run.sh
```
Then open **http://localhost:8501**.

First load takes ~10 s (downloading data for 50 stocks). The ML Lab trains all three models automatically on
first visit (~20 s, mostly TensorFlow start-up). Data is cached for 15 minutes and repeated training runs with the
same settings are instant.

---

## 4. Project structure

```
MarketScope/
├── app.py                    # Entry point: page config, sidebar, navigation
├── run.sh                    # Launcher (handles the macOS OpenMP issue)
├── requirements.txt
├── .streamlit/config.toml    # Theme: colours, Inter font, navy sidebar
└── marketscope/
    ├── config.py             # Tickers, periods, colour palette
    ├── data.py               # Yahoo Finance downloads (cached), market status
    ├── indicators.py         # SMA, EMA, RSI, MACD, returns, volatility
    ├── models.py             # Features, chronological split, RF / XGBoost / LSTM, metrics
    ├── charts.py             # Every Plotly chart, one shared style
    ├── components.py         # Cards, tables, header (search + date filter), sidebar
    ├── styles.py             # Reusable CSS (ms-* classes)
    ├── nav.py                # Page list used by the sidebar and buttons
    ├── auth.py               # Sign up / log in / change password (hashed passwords)
    ├── user_profile.py       # Per-user profile + preferences (JSON)
    └── views/                # One file per page
        ├── dashboard.py
        ├── stock_analysis.py
        ├── technical.py
        ├── ml_lab.py
        ├── about.py
        ├── login.py          # Sign in / create account
        └── account.py        # Profile & Account
```

**Flow:** `data.py` downloads prices → `indicators.py` / `models.py` compute results →
`charts.py` + `components.py` draw them → `views/*.py` arrange them into pages → `app.py` ties pages together.

---

## 5. Machine-learning methodology (for your viva)

1. **Data** — daily OHLCV from Yahoo Finance (2, 5 or 10 years; split/dividend adjusted).
2. **Features (13)** — computed only from data up to day *t*: returns for the last few days, 5-day return,
   Close/SMA20, Close/SMA50, EMA12/EMA26, RSI, MACD histogram, 20-day volatility, high-low range, volume vs average.
3. **Target** — next-day return `r(t+1) = Close(t+1)/Close(t) − 1`. Predicted price = `Close(t) × (1 + r̂)`.
   Predicting returns instead of raw prices lets tree models handle price levels they never saw in training.
4. **Chronological split** — first 80 % of days train, last 20 % test (adjustable). No shuffling.
5. **No data leakage** — the scaler is fitted on training rows only; LSTM training windows only use training rows;
   the target is never used as an input.
6. **Models**
   - *Random Forest* — many decision trees on random subsets, averaged.
   - *XGBoost* — trees built one after another, each correcting the previous errors (gradient boosting).
   - *LSTM* — recurrent neural network reading a sliding window (default 20 days) of features; early stopping on a validation split.
   - *Naive baseline* — "tomorrow's close = today's close". Every model must be compared to this.
7. **Metrics** — MAE and RMSE in ₹, MAPE, and **directional accuracy** (did the model get up/down right?).
8. **Interpretability** — built-in importance for RF/XGBoost, permutation importance for LSTM.

**Expected result:** daily prices behave close to a random walk, so all models usually land near the naive baseline
and around 50 % directional accuracy. That is a correct, honest finding — explaining *why* is a strong point in an evaluation.

---

## 6. Notes & limitations
- Data is end-of-day from Yahoo Finance and may be delayed; it is not a live tick feed.
- Market status follows the NSE timetable (pre-open 09:00–09:15, session 09:15–15:30 IST, Mon–Fri) and does not include exchange holidays.
- Yahoo Finance occasionally adds or removes the most recent day's bar, so the "latest" date can differ by a day between data requests. The app shows exactly what the source returns.
- Charts hide weekends **and** market holidays, so candles sit side by side.
- If the internet drops, every page shows a clear "data unavailable" message; failed downloads are not cached, so data returns as soon as the connection does.
- "Recent market activity" is generated from real latest-session data (index moves, breadth, top movers,
  volume spikes, stocks near period highs) — it is not a news feed.
- NIFTY 50 constituents are listed in `marketscope/config.py`; update the list if the index composition changes.

---

## 7. Deploy online (Streamlit Community Cloud, free)

1. Push this repository to GitHub (`data/` and `.venv/` are git-ignored, so no accounts or passwords are uploaded).
2. Go to **share.streamlit.io**, sign in with GitHub and click **Create app**.
3. Choose the repository, branch `main` and main file `app.py`. Under **Advanced settings** pick **Python 3.12**.
4. Click **Deploy** (first build ≈ 5–10 min — TensorFlow is large).

`requirements.txt` installs the smaller CPU-only builds of TensorFlow and XGBoost on Linux servers automatically.

**Notes for the deployed version**
- Accounts are saved to the server's temporary disk, so they reset when the app restarts or is redeployed — fine for demos; a permanent version would need a database.
- Anyone with the link can create an account; don't reuse a real password.
- If the ML Lab runs out of memory on the free tier, use 2 years of history, or deploy on Hugging Face Spaces (Docker → Streamlit template), which offers more memory.
