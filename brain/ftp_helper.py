# [WFGY] Zone: SAFE | λ: 0.1 | Action: FTP download/upload helper script using built-in ftplib
import sys
import ftplib
import os

def main():
    if len(sys.argv) < 8:
        print("Usage: python ftp_helper.py <download|upload> <host> <port> <user> <password> <remote_path> <local_path>", file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1]
    host = sys.argv[2]
    port = int(sys.argv[3])
    user = sys.argv[4]
    password = sys.argv[5]
    remote_path = sys.argv[6]
    local_path = sys.argv[7]

    try:
        ftp = ftplib.FTP()
        ftp.connect(host, port, timeout=30)
        ftp.login(user, password)
        
        if action == "download":
            # Ensure local directory exists
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
                
            with open(local_path, "wb") as f:
                ftp.retrbinary(f"RETR {remote_path}", f.write)
            print(f"SUCCESS: Downloaded FTP '{remote_path}' to '{local_path}'")
            
        elif action == "upload":
            if not os.path.exists(local_path):
                print(f"Error: Local file '{local_path}' does not exist.", file=sys.stderr)
                sys.exit(1)
                
            with open(local_path, "rb") as f:
                ftp.storbinary(f"STOR {remote_path}", f)
            print(f"SUCCESS: Uploaded '{local_path}' to FTP '{remote_path}'")
            
        else:
            print(f"Error: Unknown action '{action}'", file=sys.stderr)
            sys.exit(1)
            
        ftp.quit()
        sys.exit(0)
    except Exception as e:
        print(f"FTP Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
