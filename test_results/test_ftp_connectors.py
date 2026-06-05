# [WFGY] Zone: SAFE | λ: 0.2 | Action: Python integration test for FTP primitives
import os
import subprocess
import time
import socket
import threading

TEST_FTP_HOST = "127.0.0.1"
TEST_FTP_PORT = 2121
TEST_USER = "testuser"
TEST_PASS = "testpass"

class MockFTPServer:
    def __init__(self, host=TEST_FTP_HOST, port=TEST_FTP_PORT):
        self.host = host
        self.port = port
        self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.control_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.control_sock.bind((self.host, self.port))
        self.control_sock.listen(5)
        self.running = True
        self.files = {
            "test_remote.csv": b"id,name,age\n1,Alice,30\n2,Bob,25\n"
        }
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        # Give it a tiny moment to bind
        time.sleep(0.2)

    def _run(self):
        while self.running:
            try:
                conn, addr = self.control_sock.accept()
                conn.sendall(b"220 Mock FTP Server Ready\r\n")
                t = threading.Thread(target=self._handle_client, args=(conn,))
                t.daemon = True
                t.start()
            except Exception:
                if not self.running:
                    break

    def _handle_client(self, conn):
        data_port = None
        data_sock = None
        
        while self.running:
            try:
                line = conn.recv(1024)
                if not line:
                    break
                line_str = line.decode('utf-8')
                print(f"[MOCK FTP] Client: {line_str.strip()}")
                parts = line_str.split()
                cmd = parts[0].upper() if parts else ""
                args = parts[1] if len(parts) > 1 else ""
                
                if cmd == 'USER':
                    conn.sendall(b"331 User name okay, need password.\r\n")
                elif cmd == 'PASS':
                    conn.sendall(b"230 User logged in, proceed.\r\n")
                elif cmd == 'SYST':
                    conn.sendall(b"215 UNIX Type: L8\r\n")
                elif cmd == 'TYPE':
                    conn.sendall(b"200 Type set to I.\r\n")
                elif cmd == 'PASV':
                    # Bind a data socket on an ephemeral port
                    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    data_sock.bind((self.host, 0))
                    data_sock.listen(1)
                    data_port = data_sock.getsockname()[1]
                    p1 = data_port // 256
                    p2 = data_port % 256
                    h_parts = self.host.replace('.', ',')
                    conn.sendall(f"227 Entering Passive Mode ({h_parts},{p1},{p2})\r\n".encode())
                elif cmd == 'RETR':
                    conn.sendall(b"150 File status okay; about to open data connection.\r\n")
                    if data_sock:
                        try:
                            pasv_conn, _ = data_sock.accept()
                            file_data = self.files.get(args, b"mock file data")
                            pasv_conn.sendall(file_data)
                            pasv_conn.close()
                        finally:
                            data_sock.close()
                    conn.sendall(b"226 Closing data connection. Requested file action successful.\r\n")
                elif cmd == 'STOR':
                    conn.sendall(b"150 File status okay; about to open data connection.\r\n")
                    if data_sock:
                        try:
                            pasv_conn, _ = data_sock.accept()
                            received = b""
                            while True:
                                chunk = pasv_conn.recv(4096)
                                if not chunk:
                                    break
                                received += chunk
                            self.files[args] = received
                            pasv_conn.close()
                        finally:
                            data_sock.close()
                    conn.sendall(b"226 Closing data connection. File upload successful.\r\n")
                elif cmd == 'QUIT':
                    conn.sendall(b"221 Goodbye.\r\n")
                    conn.close()
                    break
                else:
                    conn.sendall(b"200 OK\r\n")
            except Exception as e:
                print(f"[MOCK FTP] Error in client loop: {e}")
                break

    def stop(self):
        self.running = False
        try:
            self.control_sock.close()
        except:
            pass
        if self.thread:
            self.thread.join(timeout=2)

def run_rust_muscle(args):
    bin_path = os.path.join("rust_muscle", "target", "debug", "rust_muscle.exe")
    if not os.path.exists(bin_path):
        # build first
        print("[TEST] Building rust_muscle...")
        subprocess.run(["cargo", "build", "--manifest-path", "rust_muscle/Cargo.toml"], check=True)
    
    cmd = [bin_path] + args
    print(f"[TEST] Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Stdout:\n{res.stdout}")
    print(f"Stderr:\n{res.stderr}")
    return res.returncode

def main():
    server = MockFTPServer()
    server.start()
    print("[TEST] Mock FTP Server started on port 2121.")

    local_download_dest = "test_results/ftp_downloaded.csv"
    local_upload_src = "test_results/ftp_upload_src.csv"

    # Ensure clean state
    for path in [local_download_dest, local_upload_src]:
        if os.path.exists(path):
            os.remove(path)

    try:
        # Test 1: Download file via rust_muscle net.ftp_download
        download_args = [
            "net.ftp_download",
            "--host", TEST_FTP_HOST,
            "--port", str(TEST_FTP_PORT),
            "--user", TEST_USER,
            "--password", TEST_PASS,
            "--remote-path", "test_remote.csv",
            "--local-path", local_download_dest
        ]
        
        rc = run_rust_muscle(download_args)
        assert rc == 0, f"Download command failed with return code {rc}"
        assert os.path.exists(local_download_dest), "Downloaded file does not exist!"
        
        with open(local_download_dest, "rb") as f:
            downloaded_data = f.read()
        assert downloaded_data == b"id,name,age\n1,Alice,30\n2,Bob,25\n", f"Downloaded data mismatch: {downloaded_data}"
        print("[TEST] net.ftp_download verification: SUCCESS")

        # Test 2: Upload file via rust_muscle net.ftp_upload
        upload_content = b"id,val\n99,uploaded_via_rust\n"
        with open(local_upload_src, "wb") as f:
            f.write(upload_content)

        upload_args = [
            "net.ftp_upload",
            "--host", TEST_FTP_HOST,
            "--port", str(TEST_FTP_PORT),
            "--user", TEST_USER,
            "--password", TEST_PASS,
            "--remote-path", "test_uploaded.csv",
            "--local-path", local_upload_src
        ]

        rc = run_rust_muscle(upload_args)
        assert rc == 0, f"Upload command failed with return code {rc}"
        
        # Verify the file is in the mock server's memory
        assert "test_uploaded.csv" in server.files, "Uploaded file not found on server!"
        uploaded_data = server.files["test_uploaded.csv"]
        assert uploaded_data == upload_content, f"Uploaded data mismatch: {uploaded_data}"
        print("[TEST] net.ftp_upload verification: SUCCESS")

        print("\n[VERIFICATION_GATE]")
        print("- Invariant 10 [FTP Download and Upload Primitives]: SUCCESS")

    finally:
        # Clean up files
        for path in [local_download_dest, local_upload_src]:
            if os.path.exists(path):
                os.remove(path)
        server.stop()
        print("[TEST] Mock FTP Server stopped.")

if __name__ == "__main__":
    main()
