"""Notification configuration — save, load, test SMTP/webhook."""
import os
import json
import smtplib
import urllib.request
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "notif_config.json"

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"smtp_host": "", "smtp_port": "25", "smtp_user": "", "smtp_pass": "", "smtp_from": "", "smtp_to": "", "webhook_url": ""}

def save_config(config: dict) -> dict:
    required = ["smtp_host", "smtp_port", "smtp_user", "smtp_pass", "smtp_from", "smtp_to", "webhook_url"]
    for k in required:
        if k not in config:
            config[k] = ""
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return {"ok": True}

def test_email(config: dict) -> str:
    host = config.get("smtp_host", "")
    port = int(config.get("smtp_port", 25))
    user = config.get("smtp_user", "")
    password = config.get("smtp_pass", "")
    from_addr = config.get("smtp_from", "")
    to_addr = config.get("smtp_to", "")
    if not host or not to_addr:
        return "SMTP not configured"
    try:
        server = smtplib.SMTP(host, port, timeout=10)
        if user:
            server.login(user, password)
        msg = f"From: {from_addr}\r\nTo: {to_addr}\r\nSubject: WFGY Test Notification\r\n\r\nCeci est un test de configuration SMTP depuis WFGY-Core."
        server.sendmail(from_addr, [to_addr], msg.encode("utf-8"))
        server.quit()
        return "OK"
    except Exception as e:
        return f"SMTP error: {e}"

def test_webhook(config: dict) -> str:
    url = config.get("webhook_url", "")
    if not url:
        return "Webhook URL not configured"
    try:
        payload = json.dumps({"type": "test", "source": "wfgy-core", "message": "Test de notification WFGY-Core"}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return "OK"
    except Exception as e:
        return f"Webhook error: {e}"
