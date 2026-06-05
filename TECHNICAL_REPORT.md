# Technical Report - Modular ETL Orchestrator Agent (WFGY-Core V3)

## Context & Core Axiom
This system is an intent-based ETL orchestrator:
- **Planner (LLM):** Parses user queries to generate structured execution Recipes (JSON) containing visualization metadata, supporting local models (LM Studio, Ollama) and external APIs (Gemini).
- **Brain (Python):** Coordinates the execution, validates steps, manages the execution state, and communicates with the frontend via WebSockets.
- **Muscle (Rust):** Executes performance-critical atomic primitives.
- **Vitrine (Vanilla JS):** Real-time reactive flow graph visualizing the execution steps, split into separate index.html, css/style.css, and js/app.js.

## Stack & Topology
- **Languages:** Python (Orchestration/Parsing/WebSockets/LLM Clients, Static Web Server), Rust (Atomic Execution Workers), HTML/CSS/Vanilla JS (Visual Workbench).
- **Topology:** Directed Acyclic Graph (DAG) / Sequential execution plan of steps.

## Structural Invariants & Healthchecks
- Invariant 1 [Recipe Schema Validation]: Recipes must conform strictly to the specified JSON schema.
- Invariant 2 [Separation of Concerns]: Execution logic remains purely in Rust, control logic in Python, and presentation in Vanilla JS.
- Invariant 3 [Primitive Atomic Independence]: Primitives run independently of each other.
- Invariant 4 [WebSocket State Streaming]: Execution states are streamed via full-duplex WebSockets to the workbench.
- Invariant 5 [LLM Interoperability]: The planner must support local OpenAI-compatible endpoints (LM Studio/Ollama) and API endpoints (Gemini) via uniform interfaces.
- Invariant 6 [Secrets Vault Injection]: Sensitive credentials must be represented as placeholders ("${SECRET_XXX}") in recipes and resolved at runtime by the Orchestrator, preventing plaintext exposure in saved JSON files.
- Invariant 7 [Background Daemon & Webhook Triggers]: Automated scheduler tasks (Cron checks, directory scanner, and HTTP Webhook server) run persistently.
- Invariant 8 [Workspace Metadata Registry]: All workspace flows and trigger specifications are recorded in `workspaces.json`.
- Invariant 9 [AiMapper visual matching overlay]: The visual mapping interface resolves schemas over WebSocket and maps visual connections to `data.clean` arguments.
- Invariant 10 [FTP Transfer Compatibility]: System must support downloading from and uploading to remote FTP servers natively using arguments defined in the registry.
- Invariant 11 [Data Quality & Quarantine (DLQ)]:\ System must support row-level Data Quality validation rules and automatically isolate rejected records into a quarantine path.
- Invariant 12 [SMTP & Webhook Télémétrie/Alertes]: System must support sending job status alerts via SMTP Email or HTTP Webhook POST requests.
- Invariant 13 [Agentic Model Context Protocol (MCP)]:\ System must expose a pure Python standard-I/O JSON-RPC Model Context Protocol (MCP) server allowing external AI agents to discover workspaces, retrieve recipe structures, and run flows on different environments.
- Invariant 14 [Excel XLSX Export Primitive]: System must support exporting a JSON or CSV dataset into a formatted Microsoft Excel (.xlsx) spreadsheet with customizable sheet naming.
- Invariant 15 [XML Document Generation Primitive]: System must support exporting a JSON or CSV dataset into a structured XML document under a customizable root element and row tag names.
- **Invariant 16 [Static File Web Server]:** The orchestrator must serve the divided web frontend files (`index.html`, CSS, JS) natively over the HTTP API port (`8766`) to eliminate direct file access dependencies.
- **Invariant 17 [Live Data Preview]:** System must support real-time data previewing of steps' datasets (CSV/JSON), retrieving up to the first 10 rows over WebSockets on node click.
- **Invariant 18 [AI Inference NLP Primitives]:** System must support native `ai.summarize` and `ai.extract` primitives, enabling granular per-step model override configuration (API local/Cloud Gemini) for secure data processing.

- **Invariant 19 [Run Performance Telemetry]:** System must measure global recipe and granular step execution times, persist them to `run_history.json`, stream live performance results over WebSockets via `RUN_HISTORY_UPDATE`, and render timeline performance bar charts.

- **Invariant 20 [Nested Sub-Flow Execution]:** Orchestrator must support nested sub-graphs within recipes using the `core.sub_flow` primitive, allowing recursive workflow execution and maintaining dependency constraints.

- **Invariant 21 [Execution Loop Engine]:** Orchestrator must support loop iterations using `core.loop`, iterating over files, data rows, or variables, and injecting dynamic iteration contexts `${ITER_ITEM}`.

- **Invariant 22 [Workbench Visual Drill-down Navigation]:** Workbench UI must provide breadcrumb visual navigation and drill-down/drill-up views to edit steps nested inside `core.sub_flow` and `core.loop` blocks.
- **Invariant 23 [Data Lookup Dictionary Join]:** System must support left-joining reference dictionary datasets via Polars (`data.lookup`).
- **Invariant 24 [Dataset Deduplication]:** System must support dropping duplicate rows based on subset keys (`data.deduplicate`).
- **Invariant 25 [Data Anonymization]:** System must support anonymizing dataset columns using masking, hashing, and replacement strategies (`data.anonymize`).

## Verification Gate
- Invariant 1 [Recipe Schema Validation]: SUCCESS (`SchemaValidator` implements JSON schema validation against registry specifications)
- Invariant 2 [Separation of Concerns]: SUCCESS (Python Orchestrator parses recipes, Rust Muscle executes the binary)
- Invariant 3 [Primitive Atomic Independence]: SUCCESS (`io.copy` acts as an independent worker subcommand)
- Invariant 4 [WebSocket State Streaming]: SUCCESS (Real-time bi-directional WebSocket state streaming tested successfully)
- Invariant 5 [LLM Interoperability]: SUCCESS (LLM clients written for both OpenAI-compatible and Gemini endpoints, integrated with planner)
- Invariant 6 [Secrets Vault Injection]: SUCCESS (Credentials placeholders resolved at runtime via .env / env variables)
- Invariant 7 [Background Daemon & Webhook Triggers]: SUCCESS (Lightweight Cron, File Watcher scanner, and port 8766 HTTP Webhook API validated)
- Invariant 8 [Workspace Metadata Registry]: SUCCESS (`workspaces.json` registry file loaded and managed dynamically by WebSocket commands)
- Invariant 9 [AiMapper visual matching overlay]: SUCCESS (AiMapper overlay dynamically loads schemas over WebSocket, supports interactive mapping highlights, and correctly serializes settings into `data.clean` arguments)
- Invariant 10 [FTP Transfer Compatibility]: SUCCESS (Implemented `net.ftp_download` and `net.ftp_upload` primitives with parameter schemas registered and executed via python's native ftplib to maintain offline rust compilation compatibility)
- Invariant 11 [Data Quality & Quarantine (DLQ)]: SUCCESS (Implemented `data.validate` primitive in Rust Muscle using Polars to evaluate assertions and route rejets to a quarantine file, verified by integration tests)
- Invariant 12 [SMTP & Webhook Télémétrie/Alertes]: SUCCESS (Implemented `net.notify` primitive in Rust Muscle executing a python helper using built-in `smtplib` and `urllib.request`, verified by integration tests)
- Invariant 13 [Agentic Model Context Protocol (MCP)]: SUCCESS (Implemented `mcp_server.py` supporting stdin/stdout JSON-RPC handshake, `list_flows`, `get_flow_details`, and `run_flow` tools, verified by integration tests)
- Invariant 14 [Excel XLSX Export Primitive]: SUCCESS (Implemented `data.to_xlsx` executing a python helper utilizing the `openpyxl` library inside the local virtual environment, verified via integration tests)
- Invariant 15 [XML Document Generation Primitive]: SUCCESS (Implemented `data.json_to_xml` executing a python helper utilizing `xml.etree.ElementTree` and `xml.dom.minidom` for formatted output, verified via integration tests)
- Invariant 16 [Static File Web Server]: SUCCESS (Separated monolithic UI into modular static resources under `vitrine/` and added static file routing inside the async HTTP webhook server, serving the portal dynamically on `http://localhost:8766/`)
- Invariant 17 [Live Data Preview]: SUCCESS (Implemented `extract_file_preview` in Orchestrator, registered `GET_DATA_PREVIEW` WebSocket message handler, and added/styled a bottom-docked tabular preview pane on the Workbench served dynamically)
- Invariant 18 [AI Inference NLP Primitives]: SUCCESS (Implemented `ai_helper.py` reusing LLM clients, added Rust Muscle handlers in `ai.rs` invoking python sub-processes, registered parameter schemas in registry, and fully validated via `test_ai_primitives.py`)
- Invariant 19 [Run Performance Telemetry]: SUCCESS (Implemented execution timing in `run_recipe` inside `orchestrator.py` saving records to `run_history.json`, added `GET_RUN_HISTORY` WS handler, created timeline display and pure CSS performance bars container inside `index.html` styled in `style.css` and rendered in `app.js` dynamically)
- Invariant 20 [Nested Sub-Flow Execution]: SUCCESS (Implemented primitive `core.sub_flow` inside the orchestrator recursively invoking `run_recipe`, validated via integration tests `test_sub_flow.py`)
- Invariant 21 [Execution Loop Engine]: SUCCESS (Implemented loop executor `core.loop` in orchestrator.py evaluating files, CSV/JSON rows and variables, resolved via iteration token parsing and validated via `test_loops.py`)
- Invariant 22 [Workbench Visual Drill-down Navigation]: SUCCESS (Integrated navigation paths, SVG Breadcrumbs, drill-down/drill-up navigation triggers, and recursive step bindings inside index.html, style.css, and app.js)
- Invariant 23 [Data Lookup Dictionary Join]: SUCCESS (Implemented left-join reference dictionaries in Rust using Polars via `data.lookup` primitive, fully verified by integration tests)
- Invariant 24 [Dataset Deduplication]: SUCCESS (Implemented Polars deduplication inside `data.deduplicate` primitive, supporting first/last occurrence strategies, verified by integration tests)
- Invariant 25 [Data Anonymization]: SUCCESS (Implemented dataset anonymization strategies (replace, hash, mask, mask_email) in Rust using Polars via `data.anonymize` primitive, fully verified by integration tests)

## Exit Codes & Standard Error Resolution
To preserve internationalization and separate concerns, the Rust Muscle binary returns strict numeric exit codes. The Python Orchestrator intercepts these codes and translates them to the target local language via `ERROR_TRANSLATIONS`.

| Exit Code | Error Tag | Description | Local Translation |
| :--- | :--- | :--- | :--- |
| **0** | `SUCCESS` | L'opération s'est déroulée avec succès. | Succès |
| **1** | `ERR_GENERIC` | Erreur système générique ou argument manquant. | Erreur système générique ou argument invalide. |
| **2** | `ERR_SOURCE_NOT_FOUND` | Fichier/dossier source introuvable. | Le fichier ou dossier source spécifié est introuvable. |
| **3** | `ERR_PERMISSION_DENIED` | Erreur d'accès ou droits insuffisants (lecture/écriture). | Permission refusée : accès interdit en lecture ou en écriture. |
| **4** | `ERR_DEST_DIR_CREATION` | Échec de la création du dossier cible de destination. | Impossible de créer le répertoire cible de destination. |
| **5** | `ERR_CROSS_VOLUME_FAIL` | Échec du déplacement physique inter-disques. | Échec du déplacement physique inter-disques. |
| **6** | `ERR_TRASH_CREATION` | Échec d'écriture dans la corbeille locale `.trash/`. | Impossible de déplacer l'élément dans la corbeille locale. |
| **7** | `ERR_NETWORK_ERROR` | Échec de la requête réseau ou HTTP. | Erreur réseau (téléchargement ou téléversement impossible). |

## Changelog
- **2026-05-31:** Initial ingestion of the modular ETL agent architecture (v2).
- **2026-05-31:** Transitioned to V3. Added front-end workbench architectural specification and WebSocket real-time state streaming.
- **2026-05-31:** Implemented LLM integration architecture (llm_client, planner) supporting local LM Studio and Gemini API.
- **2026-05-31:** Added recipe saving/loading (persistence), progressive incremental workflow modification, and secure vault credentials resolution.
- **2026-05-31:** Implemented interactive conflict resolution for `io.copy` using WebSockets, supporting a 120s timeout fallback to 'skip', connection-drop cleanup, and a sleek HTML/CSS glassmorphism modal on the Workbench.
- **2026-06-01:** Established modules roadmap ([ROADMAP_MODULES.md](file:///d:/image_to_text/RUST_LIKE_A_TOOL/ROADMAP_MODULES.md)) categorizing core, intermediate, and specialized components.
- **2026-06-01:** Added recursive and fallback folder management capabilities (`io.move` cross-disk fallback, `io.delete` secure retention, `io.metadata` retrieval, and base `net.download`).
- **2026-06-01:** Implemented `net.upload` primitive in Rust Muscle utilizing `reqwest` for HTTP POST/PUT file uploads, added JSON custom headers parsing, updated registry configuration, and documented exit code 7.
- **2026-06-01:** Implemented `data.filter` primitive in Rust Muscle incorporating field-based evaluations (contains, equals, starts_with, ends_with, greater_than, less_than) and regular expressions (via `regex` crate).
- **2026-06-01:** Integrated format converter primitives `data.csv_to_json` (row-based struct parser) and `data.xml_to_json` (hierarchical DOM tree parser using the fast `quick-xml` crate) into Rust Muscle and schema registry.
- **2026-06-01:** Implemented `net.http_request` primitive in Rust Muscle replacing the ad-hoc image downloader, providing global header, payload support, and relative regex link extraction, fully integrated in test scripts.
- **2026-06-02:** Restructured the Rust tool into a Cargo Workspace by isolating library logic under `libs/analytical_engine` and adding multi-format (CSV, JSON, Parquet) support using Polars for relation join and groupby aggregations.
- **2026-06-02:** Implemented `data.metrics` statistical primitive and `data.chunk_cumulative` partition layout primitive in Rust using Polars, and enabled context propagation in Python orchestrator.
- **2026-06-02:** Implemented Parallel DAG scheduling with dependency resolution and cycle detection, alongside an automatic retry/backoff mechanism in Python orchestrator.
- **2026-06-02:** Implemented generic database primitives (`db.query`, `db.insert`) in Rust Muscle supporting SQLite, Postgres, and MySQL. Snowflake REST and ODBC are integrated as mock/compatibility modules and deferred to the roadmap.
- **2026-06-02:** Implemented `s3.upload` and `s3.download` object storage primitives in Rust Muscle supporting AWS S3 and MinIO local custom endpoints, fully compiled, schema registered and validated via integration test.
- **2026-06-02:** Added the missing `submitIntent` Javascript function in `interface_du_moteur_etl.html` and bound the submit button and keypress events to it, resolving issues with prompt submissions.
- **2026-06-02:** Implemented `data.json_to_csv` format converter primitive in Rust Muscle using `csv` crate, registered it in schema registry, and verified conversion of heterogeneous JSON objects with a Python verification script.
- **2026-06-03:** Refactored the monolithic `rust_muscle/src/main.rs` (2300+ lines) by splitting all core primitives into dedicated modules under `src/primitives/` (io, net, data_format, data_transform, analytical, db, s3) and isolating MuscleError inside `error.rs` for clean maintainability.
- **2026-06-03:** Added a landing Tableau de Bord (Dashboard) view containing registered flows status, next execution timer, and inline trigger configuration. Created background daemon loops for Cron matching, directory File Watcher scan, and port 8766 HTTP Webhook API receiver.
- **2026-06-04:** Refactored the orchestrator.py script into 5 single-responsibility submodules (vault.py, worker_bridge.py, schema_validator.py, registry.py, scheduler.py) to accommodate future auth integrations.
- **2026-06-04:** Committed modular refactoring of Python submodules and Dashboard UI, successfully merged branch `dev` into `main`, and pushed updates to remote origin repository.
- **2026-06-04:** Implemented the `data.clean` dataset-cleaning primitive in Rust Muscle utilizing Polars, including a custom AST compiler translating IF-THEN-ELSE and arithmetic expressions into native Polars Expr operations.
- **2026-06-04:** Implemented **AiMapper**, a Talend-like visual mapping interface overlay modal with column highlight support, dynamically resolved via `GET_SCHEMA` WebSocket message handler and parsed to Polars `data.clean` arguments.
- **2026-06-04:** Fixed RFC 4180 CSV parser inside `data.filter` primitive using the `csv` crate, resolving the double-quoted field column shifting issue.
- **2026-06-04:** Fixed CLI `run_recipe` async execution by adding the missing `await` inside `orchestrator.py`.
- **2026-06-05:** Added automatic schema inference and table creation (`CREATE TABLE IF NOT EXISTS`) in `insert_postgres` inside `db_connector.rs` before truncation/insertions, and quoted column names to handle reserved SQL keywords.
- **2026-06-05:** Implemented chunked batch inserts for SQLite (999 parameter limit), PostgreSQL (65000 parameter limit), and MySQL (65000 parameter limit) in `db_connector.rs` to optimize insertion performance for large datasets (e.g. 1M+ rows) down from individual row-by-row insertions.
- **2026-06-05:** Optimized AiMapper visual overlay layout to make it resizable (resize handle on modal container) and significantly denser (reduced font sizes, smaller table padding, and more compact column widths).
- **2026-06-05:** Unified AiMapper inputs by replacing the dropdown select list and separate expression inputs with a single text field 'Colonne Entrée / Formule' powered by a dynamic `<datalist>` autocomplete matching source columns and local variables.
- **2026-06-05:** Integrated a nested Formula Editor Modal popup (`#aimapper-formula-modal`) triggered by a custom inline `ƒx` button next to each input row, providing syntax autocomplete for fields/variables, logic/operator quick-insert keys, and ready-to-use syntax templates.
- **2026-06-05:** Implemented `net.ftp_download` and `net.ftp_upload` FTP transfer primitives in Rust Muscle, delegating socket execution to Python's standard `ftplib` via `ftp_helper.py` to preserve offline compilation capability. Registered parameter schemas in registry and successfully verified via multi-threaded loopback integration tests.
- **2026-06-05:** Implemented row-level Data Quality validation `data.validate` primitive in Rust Muscle utilizing Polars expression engine to filter valid records and isolate rejets into a quarantine DLQ file, verified via automated integration tests.
- **2026-06-05:** Implemented `net.notify` primitive in Rust Muscle supporting SMTP Email and Webhook alerts, delegating socket execution to Python standard library helper to maintain offline environment compatibility, verified via socket loopback integration tests.
- **2026-06-05:** Implemented `data.lookup` and `data.deduplicate` analytical primitives in Rust Muscle using Polars, parsing arguments inside CLI handler, and routing calls via the main executable dispatcher. Verified correct lookup joins and row deduplication using automated integration tests.
- **2026-06-05:** Implemented `data.anonymize` utility primitive in Rust Muscle using Polars expressions, supporting FNV-1a hashing, custom string masking, local-part email masking, and replacement strategies. Created integration test script `test_anonymize.py`.














