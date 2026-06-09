# [WFGY] Zone: TEST | λ: 0.2 | Action: Python integration test for net.notify (SMTP & Webhook)
import os
import sys
import time
import socket
import threading
import json
import http.server
import subprocess
from pathlib import Path

# Config
MOCK_SMTP_PORT = 1025
MOCK_HTTP_PORT = 8085

received_emails = []
received_webhooks = []

class MockSMTPServer:
    def __init__(self, port=MOCK_SMTP_PORT):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", self.port))
        self.sock.listen(5)
        self.running = True
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        time.sleep(0.2)

    def _run(self):
        while self.running:
            try:
                conn, addr = self.sock.accept()
                conn.sendall(b"220 Mock SMTP Server Ready\r\n")
                t = threading.Thread(target=self._handle_client, args=(conn,))
                t.daemon = True
                t.start()
            except Exception:
                if not self.running:
                    break

    def _handle_client(self, conn):
        email_data = b""
        in_data = False
        while self.running:
            try:
                line = conn.recv(4096)
                if not line:
                    break
                
                if in_data:
                    email_data += line
                    if b"\r\n.\r\n" in email_data or email_data.endswith(b"\n.\n") or email_data.endswith(b"\r\n.\r\n"):
                        conn.sendall(b"250 OK Message accepted for delivery\r\n")
                        in_data = False
                        received_emails.append(email_data.decode('utf-8', errors='ignore'))
                else:
                    cmd_line = line.decode('utf-8').strip()
                    print(f"[MOCK SMTP] Client: {cmd_line}")
                    parts = cmd_line.split()
                    cmd = parts[0].upper() if parts else ""
                    
                    if cmd in ['HELO', 'EHLO']:
                        conn.sendall(b"250-localhost Hello\r\n250-AUTH LOGIN\r\n250 OK\r\n")
                    elif cmd == 'AUTH':
                        # Simple auth mock
                        conn.sendall(b"334 VXNlcm5hbWU6\r\n") # Username prompt
                        user_resp = conn.recv(1024)
                        conn.sendall(b"334 UGFzc3dvcmQ6\r\n") # Password prompt
                        pass_resp = conn.recv(1024)
                        conn.sendall(b"235 Authentication successful\r\n")
                    elif cmd == 'MAIL':
                        conn.sendall(b"250 OK\r\n")
                    elif cmd == 'RCPT':
                        conn.sendall(b"250 OK\r\n")
                    elif cmd == 'DATA':
                        conn.sendall(b"354 Start mail input; end with <CRLF>.<CRLF>\r\n")
                        in_data = True
                    elif cmd == 'QUIT':
                        conn.sendall(b"221 Bye\r\n")
                        conn.close()
                        break
                    else:
                        conn.sendall(b"250 OK\r\n")
            except Exception as e:
                print(f"[MOCK SMTP] Connection error: {e}")
                break

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
        if self.thread:
            self.thread.join(timeout=2)

class WebhookHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress logging to console
        return

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        received_webhooks.append(post_data.decode('utf-8'))
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"received"}')

class MockHTTPServer:
    def __init__(self, port=MOCK_HTTP_PORT):
        self.port = port
        self.server = http.server.HTTPServer(("127.0.0.1", self.port), WebhookHandler)
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        time.sleep(0.2)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        if self.thread:
            self.thread.join(timeout=2)

def run_rust_muscle(args):
    exe_ext = ".exe" if os.name == "nt" else ""
    bin_path = Path(__file__).parent.parent / "rust_muscle" / "target" / "debug" / f"rust_muscle{exe_ext}"
    if not bin_path.exists():
        print("[TEST] Building rust_muscle...")
        subprocess.run(["cargo", "build", "--manifest-path", "rust_muscle/Cargo.toml"], check=True)
    
    cmd = [str(bin_path)] + args
    print(f"[TEST] Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print(f"Stdout:\n{res.stdout}")
    print(f"Stderr:\n{res.stderr}")
    return res.returncode

def main():
    smtp_server = MockSMTPServer()
    http_server = MockHTTPServer()
    
    smtp_server.start()
    http_server.start()
    
    print(f"[TEST] Servers started. SMTP on 1025, Webhook on 8085.")
    
    try:
        # Test 1: Webhook notification
        webhook_args = [
            "net.notify",
            "--type", "webhook",
            "--url", f"http://127.0.0.1:{MOCK_HTTP_PORT}/webhook",
            "--message", '{"event": "job_success", "status": "prod"}'
        ]
        
        rc = run_rust_muscle(webhook_args)
        assert rc == 0, f"Webhook command failed with return code {rc}"
        assert len(received_webhooks) == 1, "Webhook not received by mock HTTP server"
        
        webhook_payload = json.loads(received_webhooks[0])
        assert webhook_payload["event"] == "job_success", f"Invalid webhook payload: {webhook_payload}"
        print("[TEST] net.notify (Webhook) verification: SUCCESS")

        # Test 2: Email SMTP notification
        email_args = [
            "net.notify",
            "--type", "email",
            "--smtp-host", "127.0.0.1",
            "--smtp-port", str(MOCK_SMTP_PORT),
            "--smtp-user", "alert@company.com",
            "--smtp-pass", "secretpass",
            "--to", "admin@company.com",
            "--subject", "Alert: Dev Environment Pipeline Complete",
            "--message", "The ETL workflow was executed successfully."
        ]
        
        rc = run_rust_muscle(email_args)
        assert rc == 0, f"Email command failed with return code {rc}"
        assert len(received_emails) == 1, "Email not received by mock SMTP server"
        
        email_content = received_emails[0]
        import email as email_parser
        msg = email_parser.message_from_string(email_content)
        decoded_body = msg.get_payload(decode=True).decode('utf-8')
        
        assert "The ETL workflow was executed successfully." in decoded_body, f"Email body mismatch. Got: {decoded_body}"
        assert "Alert: Dev Environment Pipeline Complete" in msg["Subject"], f"Email subject mismatch. Got: {msg['Subject']}"
        print("[TEST] net.notify (Email) verification: SUCCESS")
        
        print("\n[VERIFICATION_GATE]")
        print("- Invariant 12 [SMTP & Webhook Télémétrie/Alertes]: SUCCESS")

    finally:
        smtp_server.stop()
        http_server.stop()
        print("[TEST] Mock servers stopped.")

if __name__ == "__main__":
    main()
