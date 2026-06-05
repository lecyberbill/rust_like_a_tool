# [WFGY] Zone: SAFE | λ: 0.1 | Action: Notification dispatcher (SMTP & Webhooks)
import sys
import smtplib
import urllib.request
import json
from email.mime.text import MIMEText

def main():
    if len(sys.argv) < 3:
        print("Usage: python notify_helper.py <email|webhook> <args...>", file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1]

    if action == "email":
        if len(sys.argv) < 9:
            print("Usage: python notify_helper.py email <host> <port> <user> <password> <to> <subject> <body>", file=sys.stderr)
            sys.exit(1)
        
        host = sys.argv[2]
        port = int(sys.argv[3])
        user = sys.argv[4]
        password = sys.argv[5]
        to = sys.argv[6]
        subject = sys.argv[7]
        body = sys.argv[8]

        try:
            msg = MIMEText(body, 'plain', 'utf-8')
            msg['Subject'] = subject
            msg['From'] = user
            msg['To'] = to

            # Connect and send
            server = smtplib.SMTP(host, port, timeout=10)
            if user and password:
                server.ehlo()
                # Use starttls if not local test port
                if port != 1025 and port != 25:
                    try:
                        server.starttls()
                        server.ehlo()
                    except Exception as te:
                        print(f"SMTP Warning: STARTTLS failed: {te}", file=sys.stderr)
                server.login(user, password)
            
            server.sendmail(user, [to], msg.as_string())
            server.quit()
            print(f"SUCCESS: Email sent to '{to}' via '{host}'")
            sys.exit(0)
        except Exception as e:
            print(f"SMTP Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif action == "webhook":
        if len(sys.argv) < 4:
            print("Usage: python notify_helper.py webhook <url> <body>", file=sys.stderr)
            sys.exit(1)
            
        url = sys.argv[2]
        body = sys.argv[3]

        try:
            # Check if body is valid JSON, if not send as raw text inside a JSON wrapper
            try:
                json_payload = json.loads(body)
            except ValueError:
                json_payload = {"text": body}

            req_data = json.dumps(json_payload).encode('utf-8')
            req = urllib.request.Request(
                url, 
                data=req_data,
                headers={'Content-Type': 'application/json', 'User-Agent': 'ETL-Orchestrator-Agent'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                status = response.status
                resp_body = response.read().decode('utf-8')
                print(f"SUCCESS: Webhook POST returned status {status}")
                sys.exit(0)
        except Exception as e:
            print(f"Webhook Error: {e}", file=sys.stderr)
            sys.exit(1)
            
    else:
        print(f"Error: Unknown action '{action}'", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
