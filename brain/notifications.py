"""Notification configuration — save, load, test SMTP/webhook. Globale + par workspace.
Les mots de passe SMTP sont stockés dans le vault chiffré (Chromatix)."""
import os
import json
import smtplib
import urllib.request
from pathlib import Path
from registry import load_workspaces_registry, save_workspaces_registry

CONFIG_FILE = Path(__file__).parent / "notif_config.json"
VAULT_KEY_PLACEHOLDER = "${VAULT_SMTP_PASS}"

def _get_vault():
    from vault import StealthVault
    vault_key = os.environ.get("SECRET_VAULT_KEY") or ""
    return StealthVault(vault_key)

def _store_password(raw_pass: str):
    """Stocke le mot de passe dans le vault et retourne le placeholder."""
    if not raw_pass:
        return ""
    vault = _get_vault()
    vault.set("smtp_pass", raw_pass, "notif")
    return VAULT_KEY_PLACEHOLDER

def _resolve_password(config: dict) -> str:
    """Résout le mot de passe depuis le vault si placeholder."""
    pwd = config.get("smtp_pass", "")
    if pwd == VAULT_KEY_PLACEHOLDER:
        try:
            vault = _get_vault()
            return vault.get("smtp_pass", "notif")
        except Exception:
            return ""
    return pwd

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            cfg["smtp_pass"] = _resolve_password(cfg)
            return cfg
        except Exception:
            pass
    return {"smtp_host": "", "smtp_port": "25", "smtp_user": "", "smtp_pass": "", "smtp_from": "", "smtp_to": "", "webhook_url": ""}

def save_config(config: dict) -> dict:
    for k in ["smtp_host","smtp_port","smtp_user","smtp_pass","smtp_from","smtp_to","webhook_url"]:
        config.setdefault(k, "")
    if config.get("smtp_pass"):
        config["smtp_pass"] = _store_password(config["smtp_pass"])
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return {"ok": True}

def load_workspace_config(workspace_id: str) -> dict:
    reg = load_workspaces_registry()
    ws = reg.get("workspaces", {}).get(workspace_id, {})
    cfg = ws.get("notifications", {})
    cfg["smtp_pass"] = _resolve_password(cfg)
    return cfg

def save_workspace_config(workspace_id: str, config: dict) -> dict:
    reg = load_workspaces_registry()
    ws = reg.setdefault("workspaces", {}).setdefault(workspace_id, {})
    cfg = {k: config.get(k, "") for k in ["enabled","smtp_host","smtp_port","smtp_user","smtp_pass","smtp_from","smtp_to","webhook_url"]}
    if cfg.get("smtp_pass"):
        cfg["smtp_pass"] = _store_password(cfg["smtp_pass"])
    ws["notifications"] = cfg
    save_workspaces_registry(reg)
    return {"ok": True}

def resolve_config(workspace_id: str = None) -> dict:
    if workspace_id:
        wc = load_workspace_config(workspace_id)
        if wc.get("enabled") and wc.get("smtp_to"):
            wc["smtp_pass"] = _resolve_password(wc)
            return wc
    cfg = load_config()
    cfg["smtp_pass"] = _resolve_password(cfg)
    return cfg

def send_notification(workspace_id: str, subject: str, body: str):
    cfg = resolve_config(workspace_id)
    if cfg.get("smtp_to"):
        _send_email(cfg, subject, body)
    if cfg.get("webhook_url"):
        _send_webhook(cfg, subject, body)

def _send_email(config: dict, subject: str, body: str):
    host = config.get("smtp_host", "")
    port = int(config.get("smtp_port", 25))
    user = config.get("smtp_user", "")
    password = _resolve_password(config)
    from_addr = config.get("smtp_from", "")
    to_addr = config.get("smtp_to", "")
    if not host or not to_addr: return
    try:
        if int(port) == 465:
            server = smtplib.SMTP_SSL(host, int(port), timeout=10)
        else:
            server = smtplib.SMTP(host, int(port), timeout=10)
            if user and int(port) == 587:
                server.ehlo(); server.starttls(); server.ehlo()
        if user: server.login(user, password)
        msg = f"From: {from_addr}\r\nTo: {to_addr}\r\nSubject: {subject}\r\n\r\n{body}"
        server.sendmail(from_addr, [to_addr], msg.encode("utf-8"))
        server.quit()
    except Exception as e:
        print(f"[NOTIF ERROR] SMTP: {e}")

def _send_webhook(config: dict, subject: str, body: str):
    url = config.get("webhook_url", "")
    if not url: return
    try:
        payload = json.dumps({"type": "alert", "subject": subject, "message": body}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"[NOTIF ERROR] Webhook: {e}")

def test_email(config: dict, dry_run: bool = False) -> str:
    host = config.get("smtp_host", "")
    port = int(config.get("smtp_port", 25))
    if dry_run: return f"DRY-RUN: SMTP {host}:{port}"
    user = config.get("smtp_user", "")
    password = _resolve_password(config)
    from_addr = config.get("smtp_from", "")
    to_addr = config.get("smtp_to", "")
    if not host or not to_addr: return "SMTP not configured"
    try:
        if int(port) == 465:
            server = smtplib.SMTP_SSL(host, int(port), timeout=10)
        else:
            server = smtplib.SMTP(host, int(port), timeout=10)
            if user and int(port) == 587:
                server.ehlo(); server.starttls(); server.ehlo()
        if user: server.login(user, password)
        msg = f"From: {from_addr}\r\nTo: {to_addr}\r\nSubject: WFGY Test Notification\r\n\r\nTest de notification WFGY-Core."
        server.sendmail(from_addr, [to_addr], msg.encode("utf-8"))
        server.quit()
        return "OK"
    except Exception as e:
        return f"SMTP error: {e}"

def test_webhook(config: dict) -> str:
    url = config.get("webhook_url", "")
    if not url: return "Webhook URL not configured"
    try:
        payload = json.dumps({"type": "test", "source": "wfgy-core", "message": "Test WFGY-Core"}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return "OK"
    except Exception as e:
        return f"Webhook error: {e}"
