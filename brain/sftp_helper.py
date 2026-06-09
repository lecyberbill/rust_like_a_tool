# [WFGY] Zone: SAFE | λ: 0.1 | Action: SFTP download/upload helper script using paramiko
import sys
import os
import paramiko

def main():
    if len(sys.argv) < 8:
        print("Usage: python sftp_helper.py <download|upload> <host> <port> <user> <password> <remote_path> <local_path> [key_path] [key_passphrase]", file=sys.stderr)
        sys.exit(1)

    action = sys.argv[1]
    host = sys.argv[2]
    port = int(sys.argv[3])
    user = sys.argv[4]
    password = sys.argv[5]
    remote_path = sys.argv[6]
    local_path = sys.argv[7]
    key_path = sys.argv[8] if len(sys.argv) > 8 else ""
    key_passphrase = sys.argv[9] if len(sys.argv) > 9 else ""

    try:
        # Initialiser le client SSH
        ssh = paramiko.SSHClient()
        # Auto-accepter la clé de l'hôte distant
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        pkey = None
        if key_path and key_path.strip():
            print(f"Loading private key from '{key_path}'...", flush=True)
            passphrase = key_passphrase if key_passphrase else None
            # Tenter de charger en tant que clé RSA, DSA, ECDSA ou Ed25519
            # DSSKey n'existe pas directement dans l'espace de noms paramiko sous ce nom ou est déprécié, on utilise DSSKey ou DSSKey d'origine si disponible
            keys_classes = []
            for name in ["RSAKey", "Ed25519Key", "ECDSAKey", "DSSKey"]:
                if hasattr(paramiko, name):
                    keys_classes.append(getattr(paramiko, name))
            for key_class in keys_classes:
                try:
                    pkey = key_class.from_private_key_file(key_path, password=passphrase)
                    print(f"Successfully loaded {key_class.__name__} private key.", flush=True)
                    break
                except Exception:
                    continue
            if pkey is None:
                print(f"Error: Failed to load private key file '{key_path}'. Check if file format matches supported SSH key formats or if passphrase is required.", file=sys.stderr)
                sys.exit(1)
        
        print(f"Connecting to SFTP server {host}:{port} as {user}...", flush=True)
        if pkey:
            ssh.connect(host, port=port, username=user, pkey=pkey, timeout=30)
        else:
            ssh.connect(host, port=port, username=user, password=password, timeout=30)
        
        sftp = ssh.open_sftp()
        
        if action == "download":
            # S'assurer que le répertoire local de destination existe
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
                
            print(f"Downloading remote file '{remote_path}' to '{local_path}'...", flush=True)
            sftp.get(remote_path, local_path)
            print(f"SUCCESS: SFTP downloaded '{remote_path}' to '{local_path}'", flush=True)
            
        elif action == "upload":
            if not os.path.exists(local_path):
                print(f"Error: Local file '{local_path}' does not exist.", file=sys.stderr)
                sys.exit(1)
                
            # S'assurer que le répertoire de destination à distance existe (facultatif ou assumé existant)
            print(f"Uploading local file '{local_path}' to '{remote_path}'...", flush=True)
            sftp.put(local_path, remote_path)
            print(f"SUCCESS: SFTP uploaded '{local_path}' to '{remote_path}'", flush=True)
            
        else:
            print(f"Error: Unknown action '{action}'", file=sys.stderr)
            sys.exit(1)
            
        sftp.close()
        ssh.close()
        sys.exit(0)
    except Exception as e:
        print(f"SFTP Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
