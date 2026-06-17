# [WFGY] Zone: SAFE | λ: 0.3 | Action: Multi‑tenant vault using Chromatix TenantVault

import os
import sys
import json
from pathlib import Path

sys.path.append(str(Path("d:/image_to_text/chromatix")))

try:
    from chromatix_cps.vault import TenantVault
    from PIL import Image
    HAS_CHROMATIX = True
except ImportError:
    HAS_CHROMATIX = False

class StealthVault:
    """
    Vault multi‑tenant. Chaque tenant (ex: default, dev, test, prod,
    ou un ID utilisateur JWT) possède son propre fichier .vault.png
    chiffré via Chromatix TenantVault.
    """

    def __init__(self, key: str, tenant_id: str = "default"):
        if not HAS_CHROMATIX:
            raise RuntimeError(
                "Chromatix CPS vault not available. "
                "Ensure chromatix_cps is installed (D:/image_to_text/chromatix)."
            )
        self.key = key
        self.tenant_id = tenant_id
        self.vaults_dir = Path(__file__).parent / "vaults"
        self._tv = TenantVault(vaults_dir=str(self.vaults_dir), derive_key=key)

    # ── Migration depuis l'ancien vault monolithique ────────────
    def _migrate_legacy(self):
        legacy_png = Path(__file__).parent / "etl_vault.png"
        legacy_json = Path(__file__).parent / "etl_vault.json"
        migrated = False

        for legacy in [legacy_png, legacy_json]:
            if not legacy.exists():
                continue
            try:
                if legacy.suffix == ".png" and HAS_CHROMATIX:
                    from chromatix_cps.core import CPSPacket
                    cps = CPSPacket(self.key)
                    data = json.loads(cps.decode_raw_bytes(Image.open(legacy)).decode("utf-8"))
                else:
                    data = json.loads(legacy.read_text(encoding="utf-8"))

                for env_name, secrets in data.items():
                    if isinstance(secrets, dict):
                        for k, v in secrets.items():
                            self._tv.set(env_name, k, str(v))
                legacy.unlink()
                migrated = True
                print(f"[VAULT] Migrated legacy vault '{legacy.name}' → per‑tenant vaults.")
            except Exception as e:
                print(f"[VAULT] Legacy migration skipped ({legacy.name}): {e}")
        return migrated

    # ── API StealthVault (compatible ascendante) ────────────────
    def save_secrets(self, env_data: dict) -> bool:
        """
        Sauvegarde les secrets pour TOUS les environnements.
        env_data = {"dev": {"KEY": "val"}, "test": {"KEY": "val"}, ...}
        Chaque environnement devient un tenant dans TenantVault.
        """
        try:
            for env_name, secrets in env_data.items():
                if isinstance(secrets, dict):
                    for k, v in secrets.items():
                        self._tv.set(env_name, k, str(v))
            return True
        except Exception as e:
            print(f"[VAULT ERROR] save_secrets: {e}")
            return False

    def load_secrets(self) -> dict:
        """
        Reconstruit le dictionnaire multi‑environnement depuis les vaults
        individuels. Retourne {"dev": {...}, "test": {...}, "prod": {...}}.
        """
        self._migrate_legacy()
        result = {}
        for tid in self._tv.list_tenants():
            try:
                keys = self._tv.list(tid)
                result[tid] = {k: self._tv.get(tid, k) for k in keys}
            except Exception:
                result[tid] = {}
        # Ensure dev/test/prod exist
        for env in ("dev", "test", "prod"):
            result.setdefault(env, {})
        return result

    def get(self, key: str, env: str = None) -> str:
        """Raccourci pour lire un secret du tenant courant ou d'un env précis."""
        tid = env or self.tenant_id
        return self._tv.get(tid, key)

    def set(self, key: str, value: str, env: str = None):
        tid = env or self.tenant_id
        self._tv.set(tid, key, value)

    def delete(self, key: str, env: str = None):
        tid = env or self.tenant_id
        self._tv.delete(tid, key)

    def list(self, env: str = None) -> list:
        tid = env or self.tenant_id
        return self._tv.list(tid)
