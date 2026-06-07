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
│   ├── vault.py                  <-- Secret keeper (Stealth Vault resolver)
│   ├── registry.json             <-- Primitive specifications JSON Schema
│   ├── workspaces.json           <-- Active workflow configurations
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

### 1. Configuration
Create a `.env` file in the root directory to store your global credentials and preferences:
```ini
PORT=8765
LLM_PROVIDER=openai_compatible  # or 'gemini'
LLM_MODEL=gemma
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=your_llm_api_key
SECRET_VAULT_KEY=your_vault_encryption_key
```

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
