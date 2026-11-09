"""
user_profile.py - Save and load each user's profile and preferences.

Every account gets its own JSON file: data/profiles/<username>.json, so the
profile and preferences are kept after the app restarts. Account login
details (password hashes) live separately in auth.py / data/users.json.
"""

import json
import re
from datetime import datetime
from pathlib import Path

from marketscope.config import DEFAULT_PERIOD, DEFAULT_STOCK, NIFTY50_STOCKS, PERIODS

PROFILE_DIR = Path(__file__).resolve().parent.parent / "data" / "profiles"

ROLES = ["Student", "Researcher", "Faculty / Mentor", "Analyst", "Other"]

DEFAULTS = {
    "name": "",
    "email": "",
    "role": "Student",
    "institution": "",
    "project_title": "MarketScope – Stock Market Trend Analysis",
    "bio": "",
    "default_stock": DEFAULT_STOCK,
    "default_period": DEFAULT_PERIOD,
    "watchlist": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"],
    "created": None,
    "updated": None,
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _now() -> str:
    return datetime.now().strftime("%d %b %Y, %H:%M")


def _path(username: str) -> Path:
    return PROFILE_DIR / f"{username}.json"


def _clean(p: dict) -> dict:
    """Fill missing keys and drop values that are no longer valid."""
    out = {**DEFAULTS, **{k: v for k, v in p.items() if k in DEFAULTS}}
    if out["default_stock"] not in NIFTY50_STOCKS:
        out["default_stock"] = DEFAULT_STOCK
    if out["default_period"] not in PERIODS:
        out["default_period"] = DEFAULT_PERIOD
    out["watchlist"] = [t for t in out.get("watchlist") or [] if t in NIFTY50_STOCKS]
    if out["role"] not in ROLES:
        out["role"] = "Other"
    return out


def load(username: str, user: dict | None = None) -> dict:
    """Load a user's profile; a new user starts from defaults + their account details."""
    try:
        return _clean(json.loads(_path(username).read_text()))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        p = dict(DEFAULTS)
        if user:
            p.update(name=user.get("name", ""), email=user.get("email", ""), created=user.get("created"))
        return p


def save(username: str, profile: dict) -> dict:
    p = _clean(profile)
    p["created"] = p["created"] or _now()
    p["updated"] = _now()
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    _path(username).write_text(json.dumps(p, indent=2))
    return p


def reset(username: str, user: dict | None = None) -> dict:
    """Reset preferences and profile details back to the account defaults."""
    try:
        _path(username).unlink()
    except FileNotFoundError:
        pass
    return load(username, user)


def validate(p: dict) -> list[str]:
    errors = []
    if not p["name"].strip():
        errors.append("Please enter your name.")
    if p["email"].strip() and not EMAIL_RE.match(p["email"].strip()):
        errors.append("Email address doesn't look valid.")
    return errors


def initials(name: str) -> str:
    parts = [w for w in name.split() if w]
    if not parts:
        return "?"
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


def delete(username: str) -> None:
    """Remove a user's saved profile file (used when the account is deleted)."""
    try:
        _path(username).unlink()
    except FileNotFoundError:
        pass
