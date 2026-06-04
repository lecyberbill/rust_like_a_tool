# [WFGY] Zone: SAFE | λ: 0.1 | Action: Worker bridge execution driver calling Rust primitives

import os
import asyncio
from pathlib import Path

# International Error Translation Mapping for Rust exit codes
ERROR_TRANSLATIONS = {
    1: "Erreur système générique ou argument invalide.",
    2: "Le fichier ou dossier source spécifié est introuvable.",
    3: "Permission refusée : accès interdit en lecture ou en écriture.",
    4: "Impossible de créer le répertoire cible de destination.",
    5: "Échec du déplacement physique inter-disques (le secours par copie a échoué).",
    6: "Impossible de déplacer l'élément dans la corbeille locale.",
    7: "Erreur réseau (téléchargement ou téléversement impossible)."
}

class WorkerBridge:
    """
    Bridge responsible for executing Rust Muscle primitives.
    """
    def __init__(self, env_config: dict = None, binary_path: str = None):
        root_dir = Path(__file__).parent
        base_dir = root_dir if (root_dir / "rust_muscle").exists() else root_dir.parent
        env_bin_path = env_config.get("RUST_BIN_PATH") if env_config else None
        
        if binary_path:
            self.binary_path = Path(binary_path)
        elif env_bin_path:
            self.binary_path = Path(env_bin_path)
        else:
            exe_ext = ".exe" if os.name == "nt" else ""
            debug_bin = base_dir / "rust_muscle" / "target" / "debug" / f"rust_muscle{exe_ext}"
            if debug_bin.exists():
                self.binary_path = debug_bin
            else:
                self.binary_path = None

    async def execute(self, primitive_name: str, args: dict) -> tuple[int, str, str]:
        """
        Executes a primitive by calling the Rust binary or falling back to cargo run.
        """
        if self.binary_path and self.binary_path.exists():
            cmd = [str(self.binary_path), primitive_name]
        else:
            root_dir = Path(__file__).parent
            base_dir = root_dir if (root_dir / "rust_muscle").exists() else root_dir.parent
            cargo_toml = base_dir / "rust_muscle" / "Cargo.toml"
            cmd = ["cargo", "run", "--manifest-path", str(cargo_toml), "--", primitive_name]

        for key, value in args.items():
            kebab_key = key.replace("_", "-")
            if isinstance(value, bool):
                val_str = str(value).lower()
            else:
                val_str = str(value)
            cmd.extend([f"--{kebab_key}", val_str])

        print(f"[ORCHESTRATOR] Executing: {' '.join(cmd)}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return proc.returncode, stdout.decode('utf-8', errors='ignore'), stderr.decode('utf-8', errors='ignore')
