"""
auth.py - Copilot service account authentication
Handles login, token caching, and auto-refresh
Python call FMS spring boot api using jwt
"""

import httpx
import threading
from datetime import datetime
from config import FINANCE_API_BASE_URL, COPILOT_USERNAME, COPILOT_PASSWORD

_token: str | None = None
_expires_at: datetime | None = None
_lock = threading.Lock()

REFRESH_THRESHOLD_SECONDS = 3600

# ── Login ─────────────────────────────────────────────────────
def _login() -> str:
    """
    Login to FMS and get a fresh JWT token.
    Called on first request or after token expires.
    """
    global _token, _expires_at

    response = httpx.post(
        f"{FINANCE_API_BASE_URL}/copilot/auth/login",
        json={
            "username": COPILOT_USERNAME,
            "password": COPILOT_PASSWORD
        },
        timeout=10.0
    )
    response.raise_for_status()
    data = response.json()

    _token      = data["token"]
    _expires_at = datetime.fromisoformat(data["expiresAt"])

    print(f"[Auth] Logged in as copilot_service. "
          f"Token expires at {_expires_at}")

    return _token


# ── Refresh ───────────────────────────────────────────────────
def _refresh() -> str:
    """
    Refresh the token when it's close to expiry.
    """
    global _token, _expires_at

    response = httpx.post(
        f"{FINANCE_API_BASE_URL}/copilot/auth/refresh",
        headers={"Authorization": f"Bearer {_token}"},
        timeout=10.0
    )
    response.raise_for_status()
    data = response.json()

    _token      = data["token"]
    _expires_at = datetime.fromisoformat(
        # calculate expiresAt from expiresIn if not returned
        data.get("expiresAt") or
        datetime.utcnow().replace(microsecond=0).isoformat()
    )

    print(f"[Auth] Token refreshed. "
          f"Expires in {data['expiresIn']} seconds")

    return _token


# ── Check token validity ──────────────────────────────────────
def _needs_refresh() -> bool:
    """
    Returns True if token is missing or expiring soon.
    """
    if _token is None or _expires_at is None:
        return True

    seconds_remaining = (_expires_at - datetime.utcnow()).total_seconds()
    return seconds_remaining < REFRESH_THRESHOLD_SECONDS


# ── Public function — get valid token ─────────────────────────
def get_token() -> str:
    """
    Returns a valid JWT token.
    Automatically logs in or refreshes as needed.
    Thread-safe.

    Usage in tools:
        from auth import get_token
        headers = {"Authorization": f"Bearer {get_token()}"}
    """
    with _lock:
        if _token is None:
            # First time — login
            return _login()

        if _needs_refresh():
            # Token expiring soon — try refresh
            try:
                return _refresh()
            except Exception as e:
                print(f"[Auth] Refresh failed: {e} — re-logging in")
                return _login()

        return _token


# ── Startup check ─────────────────────────────────────────────
def verify_auth() -> bool:
    """
    Called on FastAPI startup to verify credentials work.
    Returns True if login succeeds.
    """
    try:
        token = get_token()
        # Optionally call /check endpoint
        response = httpx.get(
            f"{FINANCE_API_BASE_URL}/copilot/auth/check",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        data = response.json()
        print(f"[Auth] Token valid. "
              f"Seconds remaining: {data.get('secondsRemaining')}")
        return data.get("valid", False)
    except Exception as e:
        print(f"[Auth] Startup auth check failed: {e}")
        return False
