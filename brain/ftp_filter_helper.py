# [WFGY] Zone: SAFE | λ: 0.2 | Action: Create FTP and SFTP filtering helper script comparing times in UTC with min_age_hours support
import sys
import ftplib
import os
import time
from datetime import datetime, timezone

def parse_mdtm_to_utc_epoch(ftp, remote_file):
    """
    Queries FTP server MDTM command and returns timezone-aware epoch timestamp.
    """
    try:
        # MDTM response format is generally: 213 YYYYMMDDHHMMSS[.xxx]
        response = ftp.sendcmd(f"MDTM {remote_file}")
        if response.startswith("213"):
            time_str = response[4:].strip()
            # Truncate fractional seconds if present
            if "." in time_str:
                time_str = time_str.split(".")[0]
            # MDTM is universally UTC according to RFC 3659
            dt = datetime.strptime(time_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            return dt.timestamp()
    except Exception:
        pass
    return None

def parse_sftp_attr_to_utc_epoch(sftp_file_attr):
    """
    Given a paramiko SFTPAttributes object, returns the modification epoch time in UTC.
    Paramiko st_mtime is already returned as an integer epoch timestamp in UTC.
    """
    return sftp_file_attr.st_mtime

def filter_file(mtime_epoch, size_bytes, max_age_hours, min_age_hours, min_size_mb, max_size_mb):
    """
    Performs UTC filtering checks based on age and size.
    """
    now_utc = datetime.now(timezone.utc).timestamp()
    size_mb = size_bytes / (1024 * 1024)

    # Calcul de l'âge du fichier en heures
    age_hours = (now_utc - mtime_epoch) / 3600.0

    if max_age_hours is not None:
        if age_hours > float(max_age_hours):
            return False

    if min_age_hours is not None:
        if age_hours < float(min_age_hours):
            return False

    if min_size_mb is not None:
        if size_mb < float(min_size_mb):
            return False

    if max_size_mb is not None:
        if size_mb > float(max_size_mb):
            return False

    return True

def run_ftp_filtered(host, port, user, password, remote_dir, local_dir, max_age_hours, min_age_hours, min_size_mb, max_size_mb):
    print(f"[FTP FILTER] Connecting to {host}:{port} in UTC mode...")
    ftp = ftplib.FTP()
    ftp.connect(host, port, timeout=30)
    ftp.login(user, password)
    
    # Switch to remote directory
    ftp.cwd(remote_dir)
    
    # Gather list of items
    files_to_download = []
    
    # Use MLSD if supported, else fall back to NLST + MDTM/SIZE
    use_fallback = False
    try:
        for name, attrs in ftp.mlsd():
            if attrs.get("type") == "file":
                # MLSD timestamp format: YYYYMMDDHHMMSS.xxx or YYYYMMDDHHMMSS
                modify_str = attrs.get("modify")
                if modify_str:
                    if "." in modify_str:
                        modify_str = modify_str.split(".")[0]
                    mtime_epoch = datetime.strptime(modify_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).timestamp()
                    size_bytes = int(attrs.get("size", 0))
                    
                    if filter_file(mtime_epoch, size_bytes, max_age_hours, min_age_hours, min_size_mb, max_size_mb):
                        files_to_download.append(name)
    except Exception as e:
        print(f"[FTP FILTER] MLSD not supported or failed ({e}), falling back to NLST/MDTM...")
        use_fallback = True

    if use_fallback:
        try:
            file_names = ftp.nlst()
            for name in file_names:
                # Need to verify if it is indeed a file and retrieve size
                try:
                    size_bytes = ftp.size(name)
                except Exception:
                    # Likely a directory
                    continue
                
                mtime_epoch = parse_mdtm_to_utc_epoch(ftp, name)
                if mtime_epoch is None:
                    # If we cannot get mtime, we fallback to local current time to skip age filter
                    mtime_epoch = datetime.now(timezone.utc).timestamp()
                
                if filter_file(mtime_epoch, size_bytes, max_age_hours, min_age_hours, min_size_mb, max_size_mb):
                    files_to_download.append(name)
        except Exception as e:
            print(f"[FTP FILTER] Failed to list files via fallback: {e}", file=sys.stderr)
            ftp.quit()
            return False

    os.makedirs(local_dir, exist_ok=True)
    downloaded_count = 0
    for name in files_to_download:
        local_path = os.path.join(local_dir, name)
        print(f"[FTP FILTER] Downloading filtered file: {name} -> {local_path}")
        with open(local_path, "wb") as f:
            ftp.retrbinary(f"RETR {name}", f.write)
        downloaded_count += 1
        
    ftp.quit()
    print(f"SUCCESS: FTP download finished. Total files downloaded: {downloaded_count}")
    return True

def run_sftp_filtered(host, port, user, password, key_path, key_passphrase, remote_dir, local_dir, max_age_hours, min_age_hours, min_size_mb, max_size_mb):
    print(f"[SFTP FILTER] Connecting to {host}:{port}...")
    import paramiko
    
    transport = paramiko.Transport((host, port))
    
    if key_path and os.path.exists(key_path):
        pkey = None
        # Try different key types
        for pkey_class in [paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey, paramiko.DSSKey]:
            try:
                pkey = pkey_class.from_private_key_file(key_path, password=key_passphrase if key_passphrase else None)
                break
            except Exception:
                continue
        if not pkey:
            print("[SFTP FILTER] Failed to load private key file.", file=sys.stderr)
            return False
        transport.connect(username=user, pkey=pkey)
    else:
        transport.connect(username=user, password=password)
        
    sftp = paramiko.SFTPClient.from_transport(transport)
    
    # Read files in remote directory
    try:
        dir_items = sftp.listdir_attr(remote_dir)
    except Exception as e:
        print(f"[SFTP FILTER] Failed to list directory {remote_dir}: {e}", file=sys.stderr)
        sftp.close()
        transport.close()
        return False
        
    files_to_download = []
    for item in dir_items:
        # Verify it's a file
        import stat
        if stat.S_ISREG(item.st_mode):
            mtime_epoch = parse_sftp_attr_to_utc_epoch(item)
            size_bytes = item.st_size
            
            if filter_file(mtime_epoch, size_bytes, max_age_hours, min_age_hours, min_size_mb, max_size_mb):
                files_to_download.append(item.filename)
                
    os.makedirs(local_dir, exist_ok=True)
    downloaded_count = 0
    for name in files_to_download:
        remote_path = os.path.join(remote_dir, name).replace("\\", "/")
        local_path = os.path.join(local_dir, name)
        print(f"[SFTP FILTER] Downloading filtered file: {remote_path} -> {local_path}")
        sftp.get(remote_path, local_path)
        downloaded_count += 1
        
    sftp.close()
    transport.close()
    print(f"SUCCESS: SFTP download finished. Total files downloaded: {downloaded_count}")
    return True

def main():
    if len(sys.argv) < 11:
        print("Usage: python ftp_filter_helper.py <ftp|sftp> <host> <port> <user> <password/key_path> <key_passphrase> <remote_dir> <local_dir> <max_age_hours> <min_age_hours> <min_size_mb> <max_size_mb>", file=sys.stderr)
        sys.exit(1)
        
    proto = sys.argv[1].lower()
    host = sys.argv[2]
    port = int(sys.argv[3])
    user = sys.argv[4]
    secret = sys.argv[5] # Password or key_path
    key_passphrase = sys.argv[6]
    remote_dir = sys.argv[7]
    local_dir = sys.argv[8]
    
    def parse_float_opt(val):
        if not val or val.lower() == "none" or val.lower() == "null" or val == '""' or val == "''":
            return None
        try:
            return float(val)
        except ValueError:
            return None
            
    max_age_hours = parse_float_opt(sys.argv[9])
    min_age_hours = parse_float_opt(sys.argv[10])
    min_size_mb = parse_float_opt(sys.argv[11])
    max_size_mb = parse_float_opt(sys.argv[12])
    
    if proto == "ftp":
        success = run_ftp_filtered(host, port, user, secret, remote_dir, local_dir, max_age_hours, min_age_hours, min_size_mb, max_size_mb)
    elif proto == "sftp":
        # In sftp arguments, secret is key_path if it points to a file, otherwise it's the password
        key_path = secret if os.path.exists(secret) else ""
        password = "" if key_path else secret
        success = run_sftp_filtered(host, port, user, password, key_path, key_passphrase, remote_dir, local_dir, max_age_hours, min_age_hours, min_size_mb, max_size_mb)
    else:
        print(f"Error: Unknown protocol '{proto}'", file=sys.stderr)
        sys.exit(1)
        
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
