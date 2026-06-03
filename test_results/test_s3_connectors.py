# [WFGY] Zone: SAFE | λ: 0.2 | Action: Python integration test for S3 primitive
import os
import subprocess
import time
import json
import urllib.request

TEST_BUCKET = "test-bucket"
OBJECT_KEY = "test_data/hello.txt"
UPLOAD_SOURCE = "s3_upload_source.txt"
DOWNLOAD_DEST = "s3_downloaded_dest.txt"
MINIO_CONTAINER_NAME = "minio_s3_test"

ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
REGION = "us-east-1"
ENDPOINT = "http://127.0.0.1:9000"

def is_minio_responsive():
    try:
        # Check health endpoint or API page
        with urllib.request.urlopen(f"{ENDPOINT}/minio/health/live") as response:
            return response.status == 200
    except Exception:
        return False

def start_minio():
    print("[TEST] Checking if MinIO container is already running...")
    # Is it already running?
    check_run = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name={MINIO_CONTAINER_NAME}"],
        capture_output=True, text=True
    )
    if check_run.stdout.strip():
        print("[TEST] MinIO container is already running.")
        return False

    # Is it stopped?
    check_all = subprocess.run(
        ["docker", "ps", "-a", "-q", "-f", f"name={MINIO_CONTAINER_NAME}"],
        capture_output=True, text=True
    )
    if check_all.stdout.strip():
        print("[TEST] Starting existing stopped MinIO container...")
        subprocess.run(["docker", "start", MINIO_CONTAINER_NAME], check=True)
    else:
        print("[TEST] Starting new MinIO container...")
        subprocess.run([
            "docker", "run", "-d",
            "-p", "9000:9000", "-p", "9001:9001",
            "--name", MINIO_CONTAINER_NAME,
            "minio/minio", "server", "/data", "--console-address", ":9001"
        ], check=True)

    print("[TEST] Waiting for MinIO to start...")
    for _ in range(30):
        if is_minio_responsive():
            print("[TEST] MinIO is ready.")
            break
        time.sleep(1)
    else:
        raise RuntimeError("MinIO container failed to become responsive within 30 seconds.")
    
    return True

def create_local_test_file():
    with open(UPLOAD_SOURCE, "w") as f:
        f.write("Hello from automated S3/MinIO integration test! Timestamp: " + str(time.time()))

def clean_up_files():
    for f in [UPLOAD_SOURCE, DOWNLOAD_DEST]:
        if os.path.exists(f):
            os.remove(f)

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
    started_by_us = False
    try:
        started_by_us = start_minio()
        
        # 1. Create a dummy file
        create_local_test_file()
        
        # Read the test data to compare later
        with open(UPLOAD_SOURCE, "r") as f:
            original_content = f.read()

        # 2. Upload using rust_muscle s3.upload
        upload_args = [
            "s3.upload",
            "--bucket", TEST_BUCKET,
            "--file-path", UPLOAD_SOURCE,
            "--object-key", OBJECT_KEY,
            "--aws-access-key-id", ACCESS_KEY,
            "--aws-secret-access-key", SECRET_KEY,
            "--region", REGION,
            "--endpoint", ENDPOINT
        ]
        
        # The rust-s3 crate might fail if bucket doesn't exist, MinIO automatically creates it on put_object sometimes,
        # or we might need to verify if the bucket creation is handled. If it fails, let's see.
        rc = run_rust_muscle(upload_args)
        if rc != 0:
            print("[TEST] Upload failed. Trying to check bucket creation or other error.")
            exit(rc)

        # 3. Download using rust_muscle s3.download
        download_args = [
            "s3.download",
            "--bucket", TEST_BUCKET,
            "--object-key", OBJECT_KEY,
            "--destination", DOWNLOAD_DEST,
            "--aws-access-key-id", ACCESS_KEY,
            "--aws-secret-access-key", SECRET_KEY,
            "--region", REGION,
            "--endpoint", ENDPOINT
        ]
        rc = run_rust_muscle(download_args)
        if rc != 0:
            print("[TEST] Download failed.")
            exit(rc)

        # 4. Assert correctness
        if not os.path.exists(DOWNLOAD_DEST):
            raise AssertionError("Downloaded file not found!")
            
        with open(DOWNLOAD_DEST, "r") as f:
            downloaded_content = f.read()
            
        assert original_content == downloaded_content, f"Content mismatch! Original: {original_content}, Downloaded: {downloaded_content}"
        print("\n[VERIFICATION_GATE]")
        print("- Invariant 1 [S3 Upload and Download Primitives]: SUCCESS")
        
    finally:
        clean_up_files()
        if started_by_us:
            print("[TEST] Stopping MinIO container...")
            subprocess.run(["docker", "stop", MINIO_CONTAINER_NAME], capture_output=True)
            subprocess.run(["docker", "rm", MINIO_CONTAINER_NAME], capture_output=True)
            print("[TEST] MinIO container stopped and cleaned up.")

if __name__ == "__main__":
    main()
