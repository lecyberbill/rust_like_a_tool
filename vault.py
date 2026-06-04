# [WFGY] Zone: SAFE | λ: 0.1 | Action: Secrets management vault wrapper inside Chromatix CPS PNG images

import os
import sys
import json
from pathlib import Path

# Dynamically add Chromatix path to sys.path
sys.path.append(str(Path("d:/image_to_text/chromatix")))

try:
    from chromatix_cps.core import CPSPacket
    from PIL import Image
    HAS_CHROMATIX = True
    print("[STEALTH VAULT] Chromatix Pixel Standard Engine successfully loaded.")
except ImportError:
    HAS_CHROMATIX = False
    print("[STEALTH VAULT] Chromatix Engine not found. Running in legacy flat-file fallback mode.")

class StealthVault:
    """
    Stealth Vault that encrypts and stores flow secrets inside a Chromatix PNG image.
    """
    def __init__(self, key: str):
        self.key = key or "default-stealth-key-99"
        self.vault_path = Path(__file__).parent / "etl_vault.png"
        self.fallback_path = Path(__file__).parent / "etl_vault.json"

    def save_secrets(self, env_data: dict) -> bool:
        try:
            raw_bytes = json.dumps(env_data, ensure_ascii=False).encode('utf-8')
            if HAS_CHROMATIX:
                cps = CPSPacket(self.key)
                img = cps.encode_raw_bytes(raw_bytes, epoch_id=999)
                img.save(self.vault_path)
                print(f"[STEALTH VAULT] Secrets successfully hidden inside '{self.vault_path.name}'.")
                if self.fallback_path.exists():
                    self.fallback_path.unlink()
                return True
            else:
                with open(self.fallback_path, "w", encoding="utf-8") as f:
                    json.dump(env_data, f, indent=2, ensure_ascii=False)
                print(f"[STEALTH VAULT] Legacy mode: Secrets saved in plaintext to '{self.fallback_path.name}'.")
                return True
        except Exception as e:
            print(f"[STEALTH VAULT ERROR] Failed to save secrets: {e}")
            return False

    def load_secrets(self) -> dict:
        try:
            if HAS_CHROMATIX and self.vault_path.exists():
                cps = CPSPacket(self.key)
                img = Image.open(self.vault_path)
                decoded_bytes = cps.decode_raw_bytes(img, epoch_id=999)
                return json.loads(decoded_bytes.decode('utf-8'))
            elif self.fallback_path.exists():
                with open(self.fallback_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[STEALTH VAULT ERROR] Failed to load secrets: {e}")
        return {"dev": {}, "test": {}, "prod": {}}
