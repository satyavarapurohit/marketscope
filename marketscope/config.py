"""
config.py - Central settings for MarketScope.

Everything that might need changing (tickers, colours, periods) lives here,
so the rest of the code never hard-codes these values.
"""

APP_NAME = "MarketScope"
APP_TAGLINE = "Stock Market Trend Analysis"

# ---------------------------------------------------------------------------
# Market indices shown on the dashboard (Yahoo Finance symbols)
# ---------------------------------------------------------------------------
INDICES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANK NIFTY": "^NSEBANK",
}

# ---------------------------------------------------------------------------
# NIFTY 50 constituents (NSE symbols need the ".NS" suffix on Yahoo Finance).
# Used for the stock search box and the gainers / losers table.
# ---------------------------------------------------------------------------
NIFTY50_STOCKS = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
    "INFY.NS": "Infosys",
    "BHARTIARTL.NS": "Bharti Airtel",
    "ITC.NS": "ITC",
    "SBIN.NS": "State Bank of India",
    "LT.NS": "Larsen & Toubro",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "BAJFINANCE.NS": "Bajaj Finance",
    "HCLTECH.NS": "HCL Technologies",
    "KOTAKBANK.NS": "Kotak Mahindra Bank",
    "AXISBANK.NS": "Axis Bank",
    "MARUTI.NS": "Maruti Suzuki",
    "SUNPHARMA.NS": "Sun Pharmaceutical",
    "M&M.NS": "Mahindra & Mahindra",
    "TITAN.NS": "Titan Company",
    "ULTRACEMCO.NS": "UltraTech Cement",
    "ASIANPAINT.NS": "Asian Paints",
    "NTPC.NS": "NTPC",
    "WIPRO.NS": "Wipro",
    "ONGC.NS": "Oil & Natural Gas Corp",
    "POWERGRID.NS": "Power Grid Corp",
    "TATASTEEL.NS": "Tata Steel",
    "NESTLEIND.NS": "Nestle India",
    "JSWSTEEL.NS": "JSW Steel",
    "ADANIENT.NS": "Adani Enterprises",
    "ADANIPORTS.NS": "Adani Ports",
    "COALINDIA.NS": "Coal India",
    "BAJAJFINSV.NS": "Bajaj Finserv",
    "TECHM.NS": "Tech Mahindra",
    "GRASIM.NS": "Grasim Industries",
    "HINDALCO.NS": "Hindalco Industries",
    "CIPLA.NS": "Cipla",
    "DRREDDY.NS": "Dr. Reddy's Laboratories",
    "EICHERMOT.NS": "Eicher Motors",
    "BRITANNIA.NS": "Britannia Industries",
    "HEROMOTOCO.NS": "Hero MotoCorp",
    "APOLLOHOSP.NS": "Apollo Hospitals",
    "BAJAJ-AUTO.NS": "Bajaj Auto",
    "INDUSINDBK.NS": "IndusInd Bank",
    "SBILIFE.NS": "SBI Life Insurance",
    "HDFCLIFE.NS": "HDFC Life Insurance",
    "TATACONSUM.NS": "Tata Consumer Products",
    "SHRIRAMFIN.NS": "Shriram Finance",
    "TRENT.NS": "Trent",
    "BEL.NS": "Bharat Electronics",
    "ETERNAL.NS": "Eternal (Zomato)",
    "JIOFIN.NS": "Jio Financial Services",
}

DEFAULT_STOCK = "RELIANCE.NS"

# Label shown in the date filter -> yfinance "period" string
PERIODS = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "2 Years": "2y",
    "5 Years": "5y",
}
DEFAULT_PERIOD = "1 Year"

# How long downloaded data stays cached (seconds)
CACHE_TTL = 15 * 60

# ---------------------------------------------------------------------------
# Design tokens - kept in sync with styles.py
# ---------------------------------------------------------------------------
COLORS = {
    "bg": "#F7F6F3",          # warm white page background
    "surface": "#FFFFFF",     # cards
    "border": "#E6E3DC",
    "navy": "#0F2341",        # sidebar + headings
    "navy_soft": "#1E3A5F",
    "text": "#1F2933",
    "muted": "#6B7280",
    "grid": "#EEEBE5",
    "up": "#2E7D5B",          # muted green
    "down": "#B5483F",        # muted red
    "up_soft": "#E6F2EC",
    "down_soft": "#F7E7E5",
    "accent": "#2F5D8A",      # steel blue
    "gold": "#B08A3E",
}

# Fixed colours for each series so a series looks the same on every chart
SERIES_COLORS = {
    "Close": "#0F2341",
    "SMA 20": "#2F5D8A",
    "SMA 50": "#B08A3E",
    "EMA 12": "#6A8E7F",
    "EMA 26": "#9C6B8E",
    "Actual": "#0F2341",
    "Random Forest": "#2F5D8A",
    "XGBoost": "#B08A3E",
    "LSTM": "#6A8E7F",
}
