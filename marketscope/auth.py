"""
auth.py - Local user accounts (sign up, log in, change password).

Accounts are stored in data/users.json on this computer. Passwords are never
saved as plain text: each one is hashed with PBKDF2-HMAC-SHA256 and a random
salt (Python's built-in hashlib), and checked with a constant-time compare.

This is suitable for a local / academic project. A public deployment would
use a proper identity provider instead.
"""

import hashlib
import hmac
import json
import re
import secrets
from datetime import datetime
from pathlib import Path

USERS_PATH = Path(__file__).resolve().parent.parent / "data" / "users.json"
ITERATIONS = 200_000

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
def _load() -> dict:
    try:
        return json.loads(USERS_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save(users: dict) -> None:
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    USERS_PATH.write_text(json.dumps(users, indent=2))


def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS).hex()


def _public(username: str, u: dict) -> dict:
    """User details that are safe to keep in the session (no hash/salt)."""
    return {"username": username, "name": u["name"], "email": u["email"], "created": u["created"]}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def password_problems(password: str) -> list[str]:
    problems = []
    if len(password) < 8:
        problems.append("at least 8 characters")
    if not re.search(r"[A-Za-z]", password):
        problems.append("a letter")
    if not re.search(r"\d", password):
        problems.append("a number")
    return problems


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def create_user(username: str, name: str, email: str, password: str, confirm: str):
    """Returns (user_dict, None) on success or (None, error_message)."""
    username, name, email = username.strip(), name.strip(), email.strip().lower()
    users = _load()
    if not name:
        return None, "Please enter your full name."
    if not USERNAME_RE.match(username):
        return None, "Username must be 3–20 characters: letters, numbers or underscore."
    if username.lower() in (u.lower() for u in users):
        return None, "That username is already taken."
    if not EMAIL_RE.match(email):
        return None, "Please enter a valid email address."
    if any(u["email"] == email for u in users.values()):
        return None, "An account with this email already exists."
    problems = password_problems(password)
    if problems:
        return None, "Password needs " + ", ".join(problems) + "."
    if password != confirm:
        return None, "Passwords do not match."
    salt = secrets.token_hex(16)
    users[username] = {"name": name, "email": email, "salt": salt, "hash": _hash(password, salt),
                       "created": datetime.now().strftime("%d %b %Y, %H:%M")}
    _save(users)
    return _public(username, users[username]), None


def authenticate(login: str, password: str):
    """Log in with username OR email. Returns user dict or None."""
    login = login.strip()
    users = _load()
    for username, u in users.items():
        if username.lower() == login.lower() or u["email"] == login.lower():
            if hmac.compare_digest(_hash(password, u["salt"]), u["hash"]):
                return _public(username, u)
            return None
    return None


def change_password(username: str, current: str, new: str, confirm: str):
    """Returns None on success or an error message."""
    users = _load()
    u = users.get(username)
    if not u or not hmac.compare_digest(_hash(current, u["salt"]), u["hash"]):
        return "Current password is incorrect."
    problems = password_problems(new)
    if problems:
        return "New password needs " + ", ".join(problems) + "."
    if new != confirm:
        return "New passwords do not match."
    u["salt"] = secrets.token_hex(16)
    u["hash"] = _hash(new, u["salt"])
    _save(users)
    return None


def update_details(username: str, name: str, email: str):
    """Keep account name/email in sync with the profile. Returns error or None."""
    users = _load()
    email = email.strip().lower()
    if username not in users:
        return "Account not found."
    if email and any(k != username and u["email"] == email for k, u in users.items()):
        return "Another account already uses this email."
    users[username]["name"] = name.strip()
    if email:
        users[username]["email"] = email
    _save(users)
    return None


def user_count() -> int:
    return len(_load())


def delete_user(username: str, password: str):
    """Permanently delete an account (password required). Returns error or None."""
    users = _load()
    u = users.get(username)
    if not u or not hmac.compare_digest(_hash(password, u["salt"]), u["hash"]):
        return "Password is incorrect."
    del users[username]
    _save(users)
    return None
