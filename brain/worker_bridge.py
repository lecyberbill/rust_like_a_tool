# [WFGY] Zone: SAFE | λ: 0.1 | Action: Worker bridge execution driver calling Rust primitives

import os
import asyncio
from pathlib import Path

import logging
log = logging.getLogger("wfgy.bridge")

# International Error Translation Mapping for Rust exit codes
ERROR_TRANSLATIONS = {
    1: "Erreur système générique ou argument invalide.",
    2: "Le fichier ou dossier source spécifié est introuvable.",
    3: "Permission refusée : accès interdit en lecture ou en écriture.",
    4: "Impossible de créer le répertoire cible de destination.",
    5: "Échec du déplacement physique inter-disques (le secours par copie a échoué).",
    6: "Impossible de déplacer l'élément dans la corbeille locale.",
    7: "Erreur réseau (téléchargement ou téléversement impossible).",
    8: "Argument obligatoire manquant.",
    9: "Valeur d'argument invalide.",
    10: "Échec de validation des données.",
    11: "Erreur d'entrée/sortie système.",
    12: "Erreur de parsing (JSON/CSV/XLSX).",
    13: "Primitive non supportée.",
    14: "Timeout d'exécution dépassé."
}

# Args that are metadata-only (orchestrator/UI) and must NOT be forwarded to Rust CLI
METADATA_ARGS = {
    "destination_variable", "ui", "depends_on", "retry",
    "loop_over", "items_source", "steps", "cases", "pattern",
    "then_steps", "else_steps", "expression", "duration",
    "max_age_hours", "min_age_hours", "max_size_mb", "min_size_mb",
    "format",  # routing hint for io.read_file; not understood by Rust io.copy handler
    "sheet_name",  # only meaningful for data.to_xlsx exporter
    "root_element", "row_element",  # only for json_to_xml
    "template",  # flow.report is handled in Python orchestrator
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

    async def execute(self, primitive_name: str, args: dict, timeout_seconds: int = 300) -> tuple[int, str, str]:
        """
        Executes a primitive by calling the Rust binary or falling back to cargo run.
        Filters metadata-only args (Phase 2c) and enforces timeout (Phase 2d).
        """
        if self.binary_path and self.binary_path.exists():
            cmd = [str(self.binary_path), primitive_name]
        else:
            root_dir = Path(__file__).parent
            base_dir = root_dir if (root_dir / "rust_muscle").exists() else root_dir.parent
            cargo_toml = base_dir / "rust_muscle" / "Cargo.toml"
            cmd = ["cargo", "run", "--manifest-path", str(cargo_toml), "--", primitive_name]

        # data.generate_fake : ne pas passer --destination au Rust — il output sur stdout
        filtered_args = {k: v for k, v in args.items()}
        if primitive_name == "data.generate_fake":
            filtered_args.pop("destination", None)

        for key, value in filtered_args.items():
            if key in METADATA_ARGS:
                log.debug("Filtered metadata arg", extra={"key": key})
                continue
            kebab_key = key.replace("_", "-")
            if isinstance(value, bool):
                val_str = str(value).lower()
            else:
                val_str = str(value)
            cmd.extend([f"--{kebab_key}", val_str])

        log.info("Executing primitive", extra={
            "primitive": primitive_name,
            "cmd": " ".join(cmd),
            "timeout": timeout_seconds
        })
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            log.error("Primitive timeout", extra={"primitive": primitive_name, "timeout": timeout_seconds})
            return 14, "", f"ERR_TIMEOUT: Primitive '{primitive_name}' exceeded {timeout_seconds}s timeout"

        return proc.returncode, stdout.decode('utf-8', errors='ignore'), stderr.decode('utf-8', errors='ignore')
