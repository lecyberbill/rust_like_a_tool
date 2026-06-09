# [WFGY] Zone: TEST | λ: 0.15 | Action: Python integration test for SFTP primitives with mock server
import os
import sys
import subprocess
import time
import socket
import threading
import shutil
import paramiko

TEST_SFTP_HOST = "127.0.0.1"
TEST_SFTP_PORT = 2222
TEST_USER = "sftpuser"
TEST_PASS = "sftppass"

# Generate a temporary host key for the mock server
HOST_KEY_FILE = "test_results/test_sftp_host.key"

class MockSFTPServerInterface(paramiko.SFTPServerInterface):
    def __init__(self, server, *args, **kwargs):
        self.server = server
        super().__init__(server, *args, **kwargs)

    def open(self, path, flags, attr):
        # Translate to local path
        local_path = os.path.join("test_results/sftp_root", path.lstrip("/"))
        try:
            # S'assurer que le dossier parent existe pour l'écriture
            if (flags & os.O_CREAT) != 0:
                parent = os.path.dirname(local_path)
                if parent:
                    os.makedirs(parent, exist_ok=True)
            f = paramiko.SFTPHandle(flags)
            f.readfile = open(local_path, "rb" if (flags & os.O_WRONLY) == 0 else "wb")
            f.writefile = open(local_path, "wb" if (flags & os.O_WRONLY) != 0 else "rb")
            return f
        except Exception as e:
            print(f"[MOCK SFTP] open error: {e}")
            return paramiko.SFTP_NO_SUCH_FILE

    def listdir(self, path):
        local_path = os.path.join("test_results/sftp_root", path.lstrip("/"))
        try:
            return [paramiko.SFTPAttributes.from_stat(os.stat(os.path.join(local_path, f)), f) for f in os.listdir(local_path)]
        except Exception:
            return paramiko.SFTP_NO_SUCH_FILE

    def stat(self, path):
        local_path = os.path.join("test_results/sftp_root", path.lstrip("/"))
        try:
            return paramiko.SFTPAttributes.from_stat(os.stat(local_path))
        except Exception:
            return paramiko.SFTP_NO_SUCH_FILE

class MockSSHServer(paramiko.ServerInterface):
    def check_auth_password(self, username, password):
        if username == TEST_USER and password == TEST_PASS:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        # Pour les tests, on accepte n'importe quelle clé publique valide du bon utilisateur
        if username == TEST_USER:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "password,publickey"

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

class MockSFTPServerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((TEST_SFTP_HOST, TEST_SFTP_PORT))
        self.sock.listen(5)
        self.running = True

        # Ensure root directory exists
        shutil.rmtree("test_results/sftp_root", ignore_errors=True)
        os.makedirs("test_results/sftp_root", exist_ok=True)
        
        # Write test seed file
        with open("test_results/sftp_root/remote_test.csv", "w", encoding="utf-8") as f:
            f.write("id,name,clearance\n101,SystemA,Secure\n")

        # Load or generate key
        if not os.path.exists(HOST_KEY_FILE):
            key = paramiko.RSAKey.generate(2048)
            key.write_private_key_file(HOST_KEY_FILE)
        self.host_key = paramiko.RSAKey(filename=HOST_KEY_FILE)

    def run(self):
        while self.running:
            try:
                client_sock, addr = self.sock.accept()
                t = paramiko.Transport(client_sock)
                t.add_server_key(self.host_key)
                t.set_subsystem_handler("sftp", paramiko.SFTPServer, MockSFTPServerInterface)
                server = MockSSHServer()
                t.start_server(server=server)
            except Exception:
                break

    def stop(self):
        self.running = False
        self.sock.close()

def run_rust_muscle(args):
    exe_ext = ".exe" if os.name == "nt" else ""
    bin_path = os.path.join("rust_muscle", "target", "debug", f"rust_muscle{exe_ext}")
    cmd = [bin_path] + args
    print(f"[TEST] Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    print(f"Stdout:\n{res.stdout}")
    print(f"Stderr:\n{res.stderr}")
    return res.returncode

def main():
    server = MockSFTPServerThread()
    server.start()
    print(f"[TEST] Mock SFTP Server running on port {TEST_SFTP_PORT}...")
    time.sleep(0.5)

    local_download_dest = "test_results/sftp_downloaded.csv"
    local_upload_src = "test_results/sftp_upload_src.csv"

    # Clean previous test files
    for p in [local_download_dest, local_upload_src]:
        if os.path.exists(p):
            os.remove(p)

    try:
        # Test 1: Download with Password
        print("\n--- Test 1: Password Download ---")
        dl_args = [
            "net.sftp_download",
            "--host", TEST_SFTP_HOST,
            "--port", str(TEST_SFTP_PORT),
            "--user", TEST_USER,
            "--password", TEST_PASS,
            "--remote-path", "remote_test.csv",
            "--local-path", local_download_dest
        ]
        
        rc = run_rust_muscle(dl_args)
        assert rc == 0, f"net.sftp_download password failed: exit code {rc}"
        assert os.path.exists(local_download_dest), "Download dest file not created"
        os.remove(local_download_dest)
        print("[TEST] Password Download: SUCCESS")

        # Test 2: Upload with Password
        print("\n--- Test 2: Password Upload ---")
        with open(local_upload_src, "w", encoding="utf-8") as f:
            f.write("id,event\n202,SFTP_UPLOAD_OK\n")

        ul_args = [
            "net.sftp_upload",
            "--host", TEST_SFTP_HOST,
            "--port", str(TEST_SFTP_PORT),
            "--user", TEST_USER,
            "--password", TEST_PASS,
            "--remote-path", "uploaded_test.csv",
            "--local-path", local_upload_src
        ]

        rc = run_rust_muscle(ul_args)
        assert rc == 0, f"net.sftp_upload password failed: exit code {rc}"
        print("[TEST] Password Upload: SUCCESS")

        # Test 3: Download with SSH Key
        print("\n--- Test 3: SSH Key Download ---")
        dl_key_args = [
            "net.sftp_download",
            "--host", TEST_SFTP_HOST,
            "--port", str(TEST_SFTP_PORT),
            "--user", TEST_USER,
            "--key-path", HOST_KEY_FILE,
            "--remote-path", "remote_test.csv",
            "--local-path", local_download_dest
        ]
        
        rc = run_rust_muscle(dl_key_args)
        assert rc == 0, f"net.sftp_download key failed: exit code {rc}"
        assert os.path.exists(local_download_dest), "Download dest file not created"
        with open(local_download_dest, "r", encoding="utf-8") as f:
            content = f.read()
        assert "SystemA" in content, f"Downloaded content incorrect: {content}"
        os.remove(local_download_dest)
        print("[TEST] SSH Key Download: SUCCESS")

        # Test 4: Upload with SSH Key
        print("\n--- Test 4: SSH Key Upload ---")
        ul_key_args = [
            "net.sftp_upload",
            "--host", TEST_SFTP_HOST,
            "--port", str(TEST_SFTP_PORT),
            "--user", TEST_USER,
            "--key-path", HOST_KEY_FILE,
            "--remote-path", "uploaded_key_test.csv",
            "--local-path", local_upload_src
        ]

        rc = run_rust_muscle(ul_key_args)
        assert rc == 0, f"net.sftp_upload key failed: exit code {rc}"
        server_copy = "test_results/sftp_root/uploaded_key_test.csv"
        assert os.path.exists(server_copy), "Uploaded key file not found on server"
        print("[TEST] SSH Key Upload: SUCCESS")

        print("\n[VERIFICATION_GATE]")
        print("- Invariant 10 [FTP/SFTP Transfer Compatibility]: SUCCESS")

    finally:
        # Clean up files
        for p in [local_download_dest, local_upload_src]:
            if os.path.exists(p):
                os.remove(p)
        shutil.rmtree("test_results/sftp_root", ignore_errors=True)
        server.stop()
        print("[TEST] Mock SFTP Server stopped.")

if __name__ == "__main__":
    main()
