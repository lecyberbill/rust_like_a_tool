"""Notification configuration — save, load, test SMTP/webhook. Globale + par workspace."""
import os
import json
import smtplib
import urllib.request
from pathlib import Path
from registry import load_workspaces_registry, save_workspaces_registry

CONFIG_FILE = Path(__file__).parent / "notif_config.json"

def load_config() -> dict:
    """Charge la config globale de notification."""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"smtp_host": "", "smtp_port": "25", "smtp_user": "", "smtp_pass": "", "smtp_from": "", "smtp_to": "", "webhook_url": ""}

def save_config(config: dict) -> dict:
    """Sauvegarde la config globale."""
    for k in ["smtp_host","smtp_port","smtp_user","smtp_pass","smtp_from","smtp_to","webhook_url"]:
        config.setdefault(k, "")
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return {"ok": True}

def load_workspace_config(workspace_id: str) -> dict:
    """Charge la config notif d'un workspace. Retourne vide si non configurée."""
    reg = load_workspaces_registry()
    ws = reg.get("workspaces", {}).get(workspace_id, {})
    return ws.get("notifications", {})

def save_workspace_config(workspace_id: str, config: dict) -> dict:
    """Sauvegarde la config notif d'un workspace dans le registre."""
    reg = load_workspaces_registry()
    ws = reg.setdefault("workspaces", {}).setdefault(workspace_id, {})
    ws["notifications"] = {k: config.get(k, "") for k in ["enabled","smtp_host","smtp_port","smtp_user","smtp_pass","smtp_from","smtp_to","webhook_url"]}
    save_workspaces_registry(reg)
    return {"ok": True}

def resolve_config(workspace_id: str = None) -> dict:
    """Config effective : workspace si configurée, sinon globale."""
    if workspace_id:
        wc = load_workspace_config(workspace_id)
        if wc.get("enabled") and wc.get("smtp_to"):
            return wc
    return load_config()

def send_notification(workspace_id: str, subject: str, body: str):
    """Envoie une notification (SMTP + webhook) selon la config du workspace ou globale."""
    cfg = resolve_config(workspace_id)
    if cfg.get("smtp_to"):
        _send_email(cfg, subject, body)
    if cfg.get("webhook_url"):
        _send_webhook(cfg, subject, body)

def _send_email(config: dict, subject: str, body: str):
    host = config.get("smtp_host", "")
    port = int(config.get("smtp_port", 25))
    user = config.get("smtp_user", "")
    password = config.get("smtp_pass", "")
    from_addr = config.get("smtp_from", "")
    to_addr = config.get("smtp_to", "")
    if not host or not to_addr:
        return
    try:
        server = smtplib.SMTP(host, port, timeout=10)
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

def test_email(config: dict) -> str:
    host = config.get("smtp_host", "")
    port = int(config.get("smtp_port", 25))
    user = config.get("smtp_user", "")
    password = config.get("smtp_pass", "")
    from_addr = config.get("smtp_from", "")
    to_addr = config.get("smtp_to", "")
    if not host or not to_addr: return "SMTP not configured"
    try:
        server = smtplib.SMTP(host, port, timeout=10)
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
