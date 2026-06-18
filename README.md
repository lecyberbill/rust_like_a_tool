# 📊 Rust Like A Tool (RLAT) - Modular ETL Orchestrator (WFGY-Core V3)

**Rust Like A Tool (RLAT)** is an industrial-grade, intent-driven hybrid ETL framework. It combines the flexibility of an asynchronous **Python** orchestrator (the *Brain*) with the raw performance of atomic primitives written in **Rust** (the *Muscle*), all controllable in real-time through a premium reactive user interface (the *Vitrine*).

---

## 🛠️ Architecture & Core Principles

The RLAT architecture is built on a strict segregation of concerns:

1. **The Brain (Python 3.10+)**: 
   - Receives natural language intents and generates structured execution recipes (DAGs in JSON) using an LLM Planner (supporting Gemini API, LM Studio, Ollama).
   - Validates execution steps against registered primitives specifications.
   - Manages asynchronous routing of DAG steps, resolving dependencies, and handling errors with custom retry policies.
   - Runs persistent background daemons (Cron Scheduler, File Watcher, HTTP Webhook server).
    - Secures environment variables and secrets using a chiffrated vault (**Stealth Vault** integrated with Chromatix PNG or legacy fallback).
    - Authenticates users via JWT HMAC-SHA256 tokens (SQLite accounts, PBKDF2 password hashing) and isolates secrets per tenant (`POST /api/register` / `POST /api/login`).
2. **The Muscle (Rust)**:
   - A high-performance compiled binary executing atomic steps (I/O, network requests, format conversions, SQL queries, S3 object transfers).
   - Communicates using standardized numeric exit codes, translated dynamically into localized error messages by the Python orchestrator.
3. **The Vitrine (Vanilla HTML/CSS/JS)**:
   - A sleek Tableau de Bord (Dashboard) for tracking active scheduler triggers, run logs, and execution performance telemetry timeline.
   - An interactive workbench interface for visualizing the real-time execution of steps via bi-directional WebSockets.
   - **Visual Connection Handles**: Draw connections dynamically by dragging output handles to input handles.
   - **Canvas Node Search**: Instantly filter and highlight workflow nodes by name on the fly.
   - **Node Duplication**: Clone existing nodes with all their configured parameters.
   - **Cycle Prevention**: Live topological DAG verification rejecting loops on link creation.
   - **Undo/Redo Engine**: History state stack allowing structural modifications rollback (via toolbar or shortcuts `Ctrl+Z` / `Ctrl+Y`).
    - **Zoom & Theme Controls**: Switch between dark and light modes, and adjust canvas scale (zoom in, out, reset to fit).
    - **User Authentication Modal**: Login/register/admin first-setup flow with JWT token stored in localStorage and passed to WebSocket.

---

## 📂 Repository Layout

The workspace is organized into clean, dedicated directories to keep the root directory clutter-free:

```
/ (project root)
├── README.md                     <-- This technical overview
├── ROADMAP_MODULES.md            <-- Module implementation roadmap
├── TECHNICAL_REPORT.md           <-- Structural invariants and changelog
├── start_etl_server.bat          <-- Windows batch script launcher
├── requirements.txt              <-- Python package dependencies
├── .env / .env.test              <-- Local environment configurations (ignored)
├── brain/                        <-- The Brain (Python orchestration modules)
│   ├── __init__.py
│   ├── orchestrator.py           <-- WebSocket server and main loop
│   ├── planner.py                <-- LLM intent-to-recipe translator
│   ├── llm_client.py             <-- API adapters (Gemini / OpenAI-compatible)
│   ├── scheduler.py              <-- Cron scheduler, File Watcher, and port 8766 Webhook API
│   ├── registry.py               <-- Metadata registry database loader
│   ├── schema_validator.py       <-- Recipe argument validator
│   ├── vault.py                  <-- Secret keeper (Stealth Vault multi‑tenant resolver)
│   ├── auth.py                   <-- User accounts, JWT tokens, tenant isolation
│   ├── metrics.py                <-- Prometheus metrics registry
│   ├── checkpoint.py             <-- Execution checkpoint SQLite persistence
│   ├── worker_bridge.py          <-- Rust subprocess bridge and argument filtering
│   ├── logger.py                 <-- JSON logging utility
│   ├── registry.json             <-- Primitive specifications JSON Schema
│   ├── workspaces.json           <-- Active workflow configurations
│   ├── users.db                  <-- SQLite user accounts (créé automatiquement)
│   └── history_recipes/          <-- Local history of generated JSON recipes
├── vitrine/                      <-- The Vitrine (Frontend Client modularized)
│   ├── index.html                <-- UI Entrypoint served on port 8766
│   ├── css/style.css             <-- Premium Glassmorphism styling sheets
│   └── js/                       <-- Frontend JavaScript modules
│       ├── canvas.js             <-- Canvas drawing, zoom, themes, and cycles
│       ├── aimapper.js           <-- Schema mapping and formula popup logic
│       ├── editor.js             <-- Node parameters sidebar configuration
│       ├── modals.js             <-- Modal popups and audit view controllers
│       ├── api.js                <-- WebSocket outgoing client API commands
│       └── app.js                <-- Global states, custom element, and routing
├── rust_muscle/                  <-- The Muscle (Rust Primitives Engine)
│   ├── Cargo.toml
│   ├── src/
│   │   ├── main.rs               <-- CLI parser entry point
│   │   ├── error.rs              <-- Unified error codes (1 to 7)
│   │   └── primitives/           <-- Atomic task modules (io, net, data, db, s3)
│   └── libs/
│       └── analytical_engine/    <-- Polars-based analytics engine library
└── test_results/                 <-- Integration tests and test datasets (ignored on main)
```

---

## ⚡ Primitives Catalog (Rust Muscle)

The Rust binary executes performance-critical tasks categorized by domain:

- **File System (`io.*`)**:
  - `io.copy`: Duplicate files with WebSocket interactive conflict resolution (Overwrite / Skip / Newer).
  - `io.move`: Move files with fallback for physical cross-disk operations.
  - `io.delete`: Safe file deletion.
  - `io.metadata`: Retrieve file size, type, and existence.
  - `io.write_file`: Write data to files (e.g. dynamic XSLT stylesheets).
- **Networking & Web (`net.*`)**:
  - `net.download`: Asynchronous downloading of remote files.
  - `net.upload`: Multipart file upload with custom headers.
  - `net.http_request`: General-purpose HTTP requests with Regex links extraction.
  - `net.ftp_download` & `net.ftp_upload`: Transfer files to/from FTP servers (delegated to Python `ftplib` helper).
  - `net.notify`: SMTP Email and Webhook telemetry alert dispatches.
- **Data & Formatting (`data.*`)**:
  - `data.generate_fake`: Génère des données factices autonomes (18 types : id, prénom, email, date, pattern `#Aa`, etc.) avec export CSV/JSON.
    <details><summary>Exemples de colonnes</summary>

    | Type | Descriptif | Exemple |
    |------|-----------|---------|
    | `id` | Auto-incrément (start=1, step=1) | `id:id` → 1, 2, 3... |
    | `first_name` | Prénom aléatoire | `prenom:first_name` → Jean, Marie |
    | `last_name` | Nom aléatoire | `nom:last_name` → Martin, Bernard |
    | `email` | Email automatique | `email:email` → jean.martin@gmail.com |
    | `date` | Date formatée (min, max, format) | `naissance:date` → 1990-03-15 |
    | `integer` | Entier (min, max) | `age:integer` → 42 |
    | `float` | Décimal (min, max, decimals) | `prix:float` → 19.99 |
    | `boolean` | Booléen aléatoire | `actif:boolean` → true |
    | `phone` | Téléphone (prefix) | `tel:phone` → 0612345678 |
    | `country` | Pays (format: name/code) | `pays:country` → France |
    | `city` | Ville aléatoire | `ville:city` → Paris |
    | `address` | Adresse complète | `adresse:address` → 42, Rue de la Paix |
    | `postal_code` | Code postal (country) | `cp:postal_code` → 75001 |
    | `pattern` | Pattern `#AaXx?` | `sku:pattern` → USR-123-ABC |
    | `text` | Texte lorem (min/max mots) | `desc:text` → lorem ipsum... |

    Format court : `colonne:type, col2:type2` (ex: `id:id,prenom:first_name,email:email,age:integer,date_naissance:date`)
    Format JSON : `[{"name":"id","type":"id"},{"name":"email","type":"email"}]`
    </details>
  - `data.csv_to_json` & `data.json_to_csv`: High-speed format converters.
  - `data.xml_to_json`: High-speed hierarchical XML parser using `quick-xml`.
  - `data.filter`: Filter dataset rows based on regular expressions and comparison operators.
  - `data.metrics`: Compute aggregates (sum, mean, min, max) using **Polars**.
  - `data.chunk_cumulative`: Partition files and compute running cumulative aggregates using **Polars**.
  - `data.clean`: Clean datasets, reorder schemas, rename columns and compile IF-THEN-ELSE/arithmetic formulas via Polars.
  - `data.validate`: Evaluate row assertions and direct rejets to a Quarantine (DLQ) path.
  - `data.lookup`: Join external dictionary reference files using Polars left joins.
  - `data.deduplicate`: Eliminate duplicate rows based on subset keys (first/last strategy).
  - `data.to_xlsx`: Format and export JSON/CSV to Microsoft Excel using `openpyxl`.
  - `data.json_to_xml`: Structure datasets into formatted XML files.
  - `data.delta`: Compare datasets on primary keys to calculate incremental changes (Change Data Capture) and synced results.
  - `data.type_cast`: Convert and format column data types strictly (integer, float, boolean, string, date/datetime) with format parsing.
- **AI & NLP (`ai.*`)**:
  - `ai.summarize` & `ai.extract`: Perform LLM summary and structural entity extraction (overriding models per step).
- **Databases (`db.*`)**:
  - `db.query` & `db.insert`: Unified queries and high-performance chunked batch insertions (SQLite, PostgreSQL, MySQL).
- **Cloud Storage (`s3.*`)**:
  - `s3.upload` & `s3.download`: File transfers supporting AWS S3 and MinIO.
- **Orchestration / Flow (`core.*`)**:
  - `core.sub_flow`: Nest sub-graphs recursively inside execution plans.
  - `core.loop`: Iterate workflows over files, rows, or variables injecting `${ITER_ITEM}`.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** (with `pip` installed)
- **Rust / Cargo** (for compilation or running tests)
- **Chromatix Pixel Standard** — vault encryption engine
  ```
  git clone https://github.com/lecyberbill/Chromatix-Pixel-Standard.git ../chromatix
  ```

### 1. Installation automatique

**Windows :**
```bash
scripts\install.bat
```

**Linux / macOS :**
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

L'installeur configure automatiquement :
- L'environnement virtuel Python (`.venv/`)
- Les dépendances Python
- Chromatix Pixel Standard (cloné depuis GitHub)
- Le binaire Rust (compilation `cargo build --release`)
- Le fichier `.env` depuis `.env.example`
- Les dossiers `workspace/output/`, `brain/vaults/`, `brain/logs/`

### 1. Configuration
Create a `.env` file in the root directory (or copy from `.env.example`):
```ini
PORT=8765
LLM_PROVIDER=openai_compatible  # or 'gemini'
LLM_MODEL=gemma
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=your_llm_api_key

# Secrets obligatoires (generer des cles fortes)
SECRET_VAULT_KEY=your_vault_encryption_key
JWT_SECRET=your_jwt_secret
```

> **IMPORTANT SECURITY** : Les variables `SECRET_VAULT_KEY` et `JWT_SECRET` sont **obligatoires**.
> Le serveur refusera de demarrer si elles ne sont pas definies.
> Generer des cles fortes :
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 2. Run the Orchestration Server
On Windows, simply run the launcher script:
```bash
.\start_etl_server.bat
```
This script automatically:
1. Creates and configures the `.venv` virtual environment if it does not exist.
2. Installs required python packages from `requirements.txt`.
3. Launches the Python orchestrator (WebSocket on port `8765` and HTTP API on port `8766`).

### 3. Open the UI
Access the workbench in your browser at: **`http://localhost:8766/`** (served dynamically by the integrated web server).

---

## 🕒 Triggers & Background Daemon API

The server actively polls configured workflow schedules:
- **Cron**: Run recipes based on Cron expressions (e.g. `*/5 * * * *` to run every 5 minutes).
- **File Watcher**: Scans directory folders and triggers a run when matching file formats are added.
   - **Webhook API**: Fire execution runs instantly by sending HTTP requests:
   ```bash
   curl "http://localhost:8766/trigger?workspace=default_workflow"
   ```

---

## 📡 API Documentation

### WebSocket API (port 8765)

Le Brain expose un serveur WebSocket pour la communication temps réel avec la Vitrine.

**Connexion :**
```
ws://localhost:8765?token=<jwt_token>
```
> Le token JWT est optionnel. Sans token, le tenant `"default"` est utilisé.
> Obtenez un token via `POST /api/login` ou `POST /api/register` (port 8766).

**Messages reçus (Brain → Client) :**

| Type | Payload | Description |
|------|---------|-------------|
| `system_info` | `{ orchestrator, version, os, primitives, enums }` | État du serveur et catalogue complet |
| `step_status` | `{ step_id, status, output? }` | Mise à jour d'une étape en cours |
| `plan_complete` | `{ plan_id, status, results }` | Fin d'exécution d'un plan |
| `plan_error` | `{ plan_id, error }` | Erreur fatale lors de l'exécution |
| `log` | `{ level, message, step_id? }` | Log temps réel |
| `error` | `{ message, code }` | Erreur générique |
| `current_state` | `{ state, workspace? }` | État de connexion |

**Messages envoyés (Client → Brain) :**

| Commande | Payload | Description |
|----------|---------|-------------|
| `execute_plan` | `{ plan_id, steps, workspace }` | Lancer un plan ETL |
| `cancel_plan` | `{ plan_id }` | Annuler un plan en cours |
| `get_system_info` | `{}` | Demander le catalogue primitives |
| `get_plans` | `{}` | Lister les plans historiques |
| `get_workspaces` | `{}` | Lister les workspaces |
| `save_workspace` | `{ name, steps, connections }` | Sauvegarder un workspace |
| `delete_workspace` | `{ name }` | Supprimer un workspace |
| `load_workspace` | `{ name }` | Charger un workspace |

### HTTP API (port 8766)

Endpoint REST pour les déclencheurs externes et les métriques.

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/` | Servir la Vitrine (index.html) |
| `GET` | `/api/setup-status` | Vérifier si des comptes existent (`{"has_users": bool}`) |
| `POST` | `/api/register` | Créer un compte (`{"username", "password"}` → `{"token", "tenant_id"}`) |
| `POST` | `/api/login` | Se connecter (`{"username", "password"}` → `{"token", "tenant_id"}`) |
| `GET` | `/trigger?workspace=<nom>` | Déclencher un workspace |
| `GET` | `/cancel` | Annuler le plan en cours |
| `GET` | `/metrics` | Endpoint Prometheus |

#### Authentification

Créer un compte administrateur (première utilisation) :
```bash
curl -X POST http://localhost:8766/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret123"}'
```

Se connecter :
```bash
curl -X POST http://localhost:8766/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secret123"}'
```

Les deux endpoints retournent un token JWT à passer à la WebSocket :

#### Exemple de flux complet (génération → rapport → email avec pièce jointe)
```json
{
  "steps": [
    {"step": 1, "primitive": "data.generate_fake", "args": {"columns": "id:id,nom:last_name,email:email", "count": "10", "format": "csv"}},
    {"step": 2, "primitive": "flow.report", "depends_on": [1], "args": {
      "template": "Rapport du flux ${FLOW.START_TIME}\nÉtape 1: ${STEPS.1.STATUS} (${STEPS.1.DURATION_MS}ms)\nFichier: ${STEPS.1.DESTINATION}",
      "destination": "workspace/output/rapport.txt"
    }},
    {"step": 3, "primitive": "net.notify", "depends_on": [2], "args": {
      "type": "email", "to": "admin@exemple.com",
      "smtp_host": "${SECRET_SMTP_HOST}", "smtp_user": "${SECRET_SMTP_USER}", "smtp_pass": "${SECRET_SMTP_PASS}",
      "subject": "Rapport ETL", "message": "Flux terminé avec succès.",
      "attachment": "workspace/output/step_1_data_generate_fake.csv"
    }}
  ]
}
```
```json
{"token": "eyJ...", "tenant_id": "a1b2c3d4"}
```

> Le vault (`SECRET_VAULT_KEY`) est isolé par `tenant_id` — chaque utilisateur possède son propre coffre chiffré Chromatix.

### Métriques Prometheus exposées

| Métrique | Type | Labels | Description |
|----------|------|--------|-------------|
| `wfgy_plan_runs_total` | counter | `target_env` | Nombre total de plans exécutés |
| `wfgy_steps_total` | counter | `primitive, status` | Nombre total d'étapes exécutées |
| `wfgy_step_failures_total` | counter | `primitive, code` | Nombre total d'échecs d'étapes |
| `wfgy_validation_errors_total` | counter | `primitive, step` | Erreurs de validation de recette |
| `wfgy_step_duration_seconds` | histogram | `primitive` | Durée d'exécution des étapes (buckets: 0.01s à 60s) |
| `wfgy_active_connections` | gauge | — | Connexions WebSocket actives |

## 🐳 Installation Docker

```bash
# 1. Construire l'image
docker build -t wfgy-core-v3 .

# 2. Créer le fichier .env (cf. Configuration ci-dessus)

# 3. Lancer le conteneur
docker run -d --name wfgy-etl \
  -p 8765:8765 -p 8766:8766 \
  -v "$(pwd)/.env:/app/.env" \
  -v "$(pwd)/workspace:/app/workspace" \
  wfgy-core-v3

# 4. Ouvrir http://localhost:8766/
```

## 📊 Monitoring Grafana

1. Ajouter une source Prometheus pointant vers `http://localhost:8766/metrics`
2. Importer le dashboard : `grafana/wfgy_dashboard.json`
3. Le dashboard expose 10 panneaux :
   - **Statistiques instantanées** : connexions actives, plans, échecs, erreurs de validation
   - **Série temporelle** : latence P50/P95/P99 des étapes
   - **Répartition** : étapes par primitive, taux succès/échec
   - **Détail** : échecs par primitive, plans par environnement, erreurs de validation par primitive

## 🔧 Installation depuis les sources

### Prérequis
- **Rust** 1.82+ (build muscle)
- **Python** 3.10+ (brain)
- **Cargo** (pour la compilation)

### Étapes

```bash
# 1. Compiler le moteur Rust
cd rust_muscle
cargo build --release
cp target/release/rust_muscle /usr/local/bin/

# 2. Installer les dépendances Python
cd ..
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate sous Windows
pip install -r requirements.txt

# 3. Configurer l'environnement
cp .env.prod .env
# Éditer .env avec vos paramètres (LLM, ports, etc.)

# 4. Lancer le serveur
python brain/orchestrator.py --server
```

### Tests

```bash
# Rust (26 tests unitaires)
cd rust_muscle && cargo test

# Python (76 tests)
cd .. && pytest brain/tests/ -v

# Volume test (1M lignes, clean + derive + filtre + metrique)
python test_results/volume_1m.py

# Suite complète cross-platform
./run_all_tests.py
```

## 📦 Dépendances

### Python (requirements.txt)
| Paquet | Utilité |
|--------|---------|
| `websockets` | Serveur WebSocket temps réel |
| `jsonschema` | Validation des recettes |
| `Pillow` | Dechiffrement vault Chromatix (images PNG) |
| `psycopg2-binary` | Connecteur PostgreSQL |
| `pymongo` | Connecteur MongoDB |
| `polars` | Moteur d'analyse (Rust) |
| `Faker` | Génération de données de test |

### Chromatix Pixel Standard
Le vault utilise **Chromatix Pixel Standard** pour le chiffrement des secrets.
```bash
git clone https://github.com/lecyberbill/Chromatix-Pixel-Standard.git ../chromatix
```
Le module est automatiquement détecté s'il se trouve dans :
- Le répertoire parent (`../chromatix/`)
- La variable d'environnement `CHROMATIX_PATH`

### Rust
Le binaire `rust_muscle` compile avec **Rust 1.82+** et la librairie **Polars** (moteur columnar vectorisé).

## 🏗️ Références complémentaires

- `PRIMITIVE_REFERENCE.md` — Documentation exhaustive des 68 primitives
- `docs/primitives/*.md` — Fiches individuelles par primitive
- `TECHNICAL_REPORT.md` — Invariants structurels et changelog
