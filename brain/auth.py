"""User authentication, registration, JWT tokens, tenant isolation."""
import os
import json
import time
import sqlite3
import hashlib
import hmac
import base64
import secrets
from pathlib import Path

DB_PATH = Path(__file__).parent / "users.db"
JWT_SECRET = os.environ.get("JWT_SECRET") or "change-me-jwt-secret-2026"
JWT_TTL = int(os.environ.get("JWT_TTL", 86400))  # 24h default


def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            tenant_id TEXT UNIQUE NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)
    conn.commit()
    return conn


def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return key.hex(), salt


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _create_token(payload: dict) -> str:
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(JWT_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{_b64url(sig)}"


def _decode_token(token: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, body, sig_b64 = parts
        expected = hmac.new(JWT_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
        if _b64url(expected) != sig_b64:
            return None
        payload = json.loads(base64.urlsafe_b64decode(body + "=="))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


# ── API publique ───────────────────────────────────────────────

def register(username: str, password: str) -> dict:
    """Crée un compte. Retourne {"token": ..., "tenant_id": ...} ou lève ValueError."""
    if len(username) < 2:
        raise ValueError("Username must be at least 2 characters")
    if len(password) < 4:
        raise ValueError("Password must be at least 4 characters")

    conn = _get_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            raise ValueError("Username already taken")

        key_hash, salt = _hash_password(password)
        tenant_id = secrets.token_hex(8)
        now = int(time.time())
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, tenant_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, key_hash, salt, tenant_id, now),
        )
        conn.commit()

        token = _create_token({
            "sub": conn.execute("SELECT last_insert_rowid()").fetchone()[0],
            "username": username,
            "tenant_id": tenant_id,
            "iat": now,
            "exp": now + JWT_TTL,
        })
        return {"token": token, "tenant_id": tenant_id}
    finally:
        conn.close()


def login(username: str, password: str) -> dict:
    """Authentifie. Retourne {"token": ..., "tenant_id": ...} ou lève ValueError."""
    conn = _get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not row:
            raise ValueError("Invalid username or password")

        key_hash, _ = _hash_password(password, row["salt"])
        if key_hash != row["password_hash"]:
            raise ValueError("Invalid username or password")

        now = int(time.time())
        token = _create_token({
            "sub": row["id"],
            "username": row["username"],
            "tenant_id": row["tenant_id"],
            "iat": now,
            "exp": now + JWT_TTL,
        })
        return {"token": token, "tenant_id": row["tenant_id"]}
    finally:
        conn.close()


def validate_token(token: str) -> dict | None:
    """Valide un token JWT. Retourne le payload ou None."""
    return _decode_token(token)


def get_tenant_id(token: str) -> str | None:
    payload = _decode_token(token)
    if payload:
        return payload.get("tenant_id")
    return None
