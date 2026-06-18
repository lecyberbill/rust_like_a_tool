"""User authentication, registration, JWT tokens, tenant isolation, roles."""
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
JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET environment variable is required. "
        "Generate a strong secret: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
JWT_TTL = int(os.environ.get("JWT_TTL", 86400))
ROLES = ("admin", "operator", "viewer")

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
            role TEXT NOT NULL DEFAULT 'operator',
            created_at INTEGER NOT NULL
        )
    """)
    # Migration : ajouter colonne role si absente
    cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "role" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'operator'")
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
        if len(parts) != 3: return None
        header, body, sig_b64 = parts
        expected = hmac.new(JWT_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url(expected), sig_b64):
            return None
        payload = json.loads(base64.urlsafe_b64decode(body + "=="))
        if payload.get("exp", 0) < time.time(): return None
        return payload
    except Exception:
        return None

def register(username: str, password: str) -> dict:
    if len(username) < 2: raise ValueError("Username must be at least 2 characters")
    if len(password) < 4: raise ValueError("Password must be at least 4 characters")
    conn = _get_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing: raise ValueError("Username already taken")
        user_count = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"]
        role = "admin" if user_count == 0 else "operator"
        key_hash, salt = _hash_password(password)
        tenant_id = secrets.token_hex(8)
        now = int(time.time())
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, tenant_id, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (username, key_hash, salt, tenant_id, role, now),
        )
        conn.commit()
        uid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        token = _create_token({"sub": uid, "username": username, "role": role, "tenant_id": tenant_id, "iat": now, "exp": now + JWT_TTL})
        return {"token": token, "tenant_id": tenant_id, "role": role}
    finally:
        conn.close()

def login(username: str, password: str) -> dict:
    conn = _get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not row: raise ValueError("Invalid username or password")
        key_hash, _ = _hash_password(password, row["salt"])
        if key_hash != row["password_hash"]: raise ValueError("Invalid username or password")
        now = int(time.time())
        token = _create_token({"sub": row["id"], "username": row["username"], "role": row["role"], "tenant_id": row["tenant_id"], "iat": now, "exp": now + JWT_TTL})
        return {"token": token, "tenant_id": row["tenant_id"], "role": row["role"]}
    finally:
        conn.close()

def validate_token(token: str) -> dict | None:
    return _decode_token(token)

def get_tenant_id(token: str) -> str | None:
    payload = _decode_token(token)
    return payload.get("tenant_id") if payload else None

def require_role(token: str, min_role: str) -> dict:
    """Vérifie le rôle. admin > operator > viewer. Retourne le payload ou lève ValueError."""
    payload = validate_token(token)
    if not payload: raise ValueError("Invalid token")
    role = payload.get("role")
    # Fallback tokens legacy sans role : interroger la DB
    if not role:
        uid = payload.get("sub")
        if uid:
            conn = _get_db()
            row = conn.execute("SELECT role FROM users WHERE id = ?", (uid,)).fetchone()
            conn.close()
            if row: role = row["role"]
    if not role:
        role = "viewer"
    hierarchy = {"admin": 2, "operator": 1, "viewer": 0}
    if hierarchy.get(role, 0) < hierarchy.get(min_role, 0):
        raise ValueError(f"Role {role} insufficient, requires {min_role}")
    payload["role"] = role
    return payload

def list_users(token: str) -> list[dict]:
    require_role(token, "admin")
    conn = _get_db()
    try:
        rows = conn.execute("SELECT id, username, role, tenant_id, created_at FROM users ORDER BY id").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def update_role(token: str, user_id: int, new_role: str):
    payload = require_role(token, "admin")
    if new_role not in ROLES: raise ValueError(f"Invalid role: {new_role}")
    conn = _get_db()
    try:
        target = conn.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target: raise ValueError("User not found")
        if target["id"] == payload["sub"]: raise ValueError("Cannot change your own role")
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        conn.commit()
    finally:
        conn.close()

def delete_user(token: str, user_id: int):
    payload = require_role(token, "admin")
    conn = _get_db()
    try:
        target = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target: raise ValueError("User not found")
        if target["id"] == payload["sub"]: raise ValueError("Cannot delete yourself")
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()
