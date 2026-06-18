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
- Invariant 10 [FTP/SFTP Transfer Compatibility]: System must support downloading from and uploading to remote FTP/SFTP servers natively using arguments defined in the registry.
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
- **Invariant 26 [Data Pivot Table Structure]:** System must support pivoting tables from long to wide format using Polars eager method (`data.pivot`).
- **Invariant 27 [Data Unpivot Melt Structure]:** System must support melting tables from wide to long format using Polars `melt` method (`data.unpivot`).
- Invariant 29 [Google Sheets Integration]: System must support reading and writing Google Sheets (`google.sheets_read` and `google.sheets_write`) delegating to a python helper.
- Invariant 30 [MongoDB Integration]: System must support extracting and inserting MongoDB documents (`mongodb.find` and `mongodb.insert`) delegating to a python helper using pymongo.
- Invariant 31 [Manual Recipe Visual Editing]: System must support manual visual step insertion from a sidebar Primitive Catalog and manual drawing of dependencies on the workbench.
- Invariant 32 [Node Deletion Cleanup]: System must support manual deletion of recipe steps, cascading dependency removals to maintain DAG structural integrity.

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
- Invariant 10 [FTP/SFTP Transfer Compatibility]: SUCCESS (Implemented `net.ftp_download`, `net.ftp_upload`, `net.sftp_download`, and `net.sftp_upload` primitives with parameter schemas registered and executed via python helpers to maintain offline rust compilation compatibility)
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
- Invariant 26 [Data Pivot Table Structure]: SUCCESS
- Invariant 27 [Data Unpivot Melt Structure]: SUCCESS
- Invariant 29 [Google Sheets Integration]: SUCCESS (Implemented google.sheets_read and google.sheets_write delegating to python google_sheets_helper.py, verified via mock integration tests)
- Invariant 30 [MongoDB Integration]: SUCCESS (Implemented mongodb.find and mongodb.insert delegating to python mongodb_helper.py, verified via mock tests and real Atlas database tests)
- Invariant 31 [Manual Recipe Visual Editing]: SUCCESS (Implemented sliding left sidebar Primitive Catalog with 35+ primitives, added node creation and visual rendering, verified manually)
- Invariant 32 [Node Deletion Cleanup]: SUCCESS (Implemented step deletion button in the editor panel with dependency cascade, verified manually)
- Invariant 33 [Multi-format Read/Write/Convert]: SUCCESS (Implemented `data.read`, `data.write`, `data.convert` in Rust via analytical_engine public API, registered in registry.json and frontend catalog. Supports CSV/JSON/Parquet/JSONL/NDJSON, 26 unit tests pass)
- Invariant 34 [Zero Generic Error Handlers]: SUCCESS (600+ `MuscleError::Generic` replaced across all handler files by typed variants: MissingArg, InvalidArg, IoError, ParseError, etc. Zéro Generic restant hors definition)
- Invariant 35 [Prometheus Metrics Endpoint]: SUCCESS (Metrics registry exposes 6 metric types on port 8766, dashboard Grafana importable dans `grafana/`)
- Invariant 36 [Docker Multi-stage Build]: SUCCESS (Image Rust → Python, binaire 53MB, port 8765/8766)

---

## 18. Jointures Relationnelles et Configuration Visuelle (AiMapper)

Nous avons implémenté les jointures relationnelles double-source (`left`, `inner`, `outer`) directement dans la primitive `data.clean` en Polars et configurables de façon interactive depuis le workbench AiMapper.

### Fonctionnalités de Jointure :
- **Jointure en Mémoire Optimisée** : La jointure s'exécute de manière optimisée à l'entrée de la pipeline Lazy Polars (avant les projections, expressions calculées, filtres, renommages et dédoublonnages), maximisant le Query Planner de Polars.
- **Interface Interactive AiMapper** :
  - Un champ permet de saisir ou choisir la table de jointure de droite (`right_source`).
  - Dès la saisie, un événement WebSocket `GET_SCHEMA` demande les en-têtes de cette table secondaire.
  - La colonne latérale gauche du modal liste de manière distincte les colonnes de la Table A (Source principale) et de la Table B (Jointure).
  - Des listes déroulantes de liaison permettent de sélectionner les clés respectives de la jointure (`left_on` et `right_on`) ainsi que le type de jointure (`how_join`).
  - L'autocomplétion globale du mappage (datalist) et l'éditeur de formule `ƒx` proposent et intègrent dynamiquement les colonnes des deux tables.

### Validation :
Le script d'intégration [test_aimapper_join.py](file:///d:/image_to_text/RUST_LIKE_A_TOOL/test_results/test_aimapper_join.py) a validé avec succès les jointures LEFT et INNER :
```
=== RUNNING DATA.CLEAN RELATION JOIN INTEGRATION TEST ===
Created users dataset at 'D:\image_to_text\RUST_LIKE_A_TOOL\test_results\users.csv'
Created roles dataset at 'D:\image_to_text\RUST_LIKE_A_TOOL\test_results\roles.csv'

--- Testing LEFT JOIN ---
Executing: D:\image_to_text\RUST_LIKE_A_TOOL\rust_muscle\target\debug\rust_muscle.exe data.clean ...
Exit code: 0
Left Join Result:
id,name,role_id,role_name,clearance
1,Jean,10,Admin,High
2,Marie,20,User,Medium
3,Pierre,99,Unknown,None
4,Sophie,10,Admin,High
5,Lucas,30,Guest,Low

--- Testing INNER JOIN ---
Executing: D:\image_to_text\RUST_LIKE_A_TOOL\rust_muscle\target\debug\rust_muscle.exe data.clean ...
Exit code: 0
Inner Join Result:
id,name,role_name
1,Jean,Admin
2,Marie,User
4,Sophie,Admin
5,Lucas,Guest

INTEGRATION TESTS PASSED SUCCESSFULLY!
```

[VERIFICATION_GATE]
- Invariant 28 [AiMapper Relation Join]: SUCCESS

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
- **2026-06-05:** Implemented `data.pivot` and `data.unpivot` analytical primitives in Rust Muscle using Polars, parsing arguments inside CLI handler, and routing calls via the main executable dispatcher. Enabled Polars "pivot" feature flag in analytical_engine workspace, and verified using automated integration tests.
- **2026-06-06:** Implemented Google Sheets integration primitives `google.sheets_read` and `google.sheets_write` delegating to python `google_sheets_helper.py`, verified via mock integration tests.
- **2026-06-06:** Implemented MongoDB integration primitives `mongodb.find` and `mongodb.insert` delegating to python `mongodb_helper.py`, verified via mock tests and real Atlas cluster tests.
- **2026-06-06:** Implemented Interactive Manual Editing with Left Sidebar Primitive Catalog (35+ functions), manual node insertion/drawing, dependency check-boxes linking, and step deletion with dependency cascade.
- **2026-06-06:** Implemented Visual Node Link Drawing (drag-and-drop handles connecting nodes), link selection (prompt dialog), naming/labeling along paths, and link deletion with auto-saving to registry.
- **2026-06-06:** Implemented Modern Light Theme switch (Black & White style with subtle shadows) and Zoom controls tool in Workbench UI.
- **2026-06-07:** Implemented visual node duplication button, search box on canvas toolbar, deep topological cycle validation to prevent loop dependencies, and global Undo/Redo history stack with keyboard shortcuts (Ctrl+Z/Ctrl+Y).
- **2026-06-07:** Implemented advanced ETL primitives `data.delta` (Change Data Capture / incremental sync) and `data.type_cast` (strict schema conversion and date formatting) with full Polars backend logic, CLI handlers, JSON schema validation, frontend catalog integration, and python integration tests.

## Invariant 33 [Visual Connection Handles and Link Labels]
- **Invariant 33 [Visual Connection Handles and Link Labels]:** System must support creating connections visually by dragging from an output handle to another node/input handle, selecting connection lines to either label them or remove the link, and displaying connection names along the paths.

## Invariant 34 [UI Theme Management & Zoom Controls]
- **Invariant 34 [UI Theme Management & Zoom Controls]:** System must support toggling between dark mode and a modern light theme (characterized by subtle card shadows, black/white accents), as well as interactive canvas zooming (zoom in, zoom out, fit screen zoom reset).

## Invariant 35 [Canvas Node Search & Duplication Primitives]
- **Invariant 35 [Canvas Node Search & Duplication Primitives]:** System must support filtering and highlighting nodes on the canvas via a real-time text query box, and duplicating an existing step (including parameters) through an explicit button.

## Invariant 36 [Topological Loop Verification & Undo/Redo State Engine]
- **Invariant 36 [Topological Loop Verification & Undo/Redo State Engine]:** System must dynamically check for any direct or complex cyclical dependencies (loops) on connection creation to reject them, and maintain a historical state log allowing users to undo (Ctrl+Z) or redo (Ctrl+Y) structural flow modifications.

## Invariant 37 [Incremental Data Delta Sync]
- **Invariant 37 [Incremental Data Delta Sync]:** System must support comparing a source dataset with a target dataset on primary keys to generate deletes, upserts, and synced results using Polars (`data.delta`).

## Invariant 38 [Advanced Type Casting]
- **Invariant 38 [Advanced Type Casting]:** System must support casting column data types strictly to target types (integer, float, boolean, string, date/datetime) with custom date formats using Polars (`data.type_cast`).

[VERIFICATION_GATE]
- Invariant 33 [Visual Connection Handles and Link Labels]: SUCCESS (Link drawing, renaming/labeling, and deletion are fully operational and verified visually)
- Invariant 34 [UI Theme Management & Zoom Controls]: SUCCESS (Theme toggling state and interactive canvas scaling are fully operational)
- Invariant 35 [Canvas Node Search & Duplication Primitives]: SUCCESS (Search highlight and node cloning are operational)
- Invariant 36 [Topological Loop Verification & Undo/Redo State Engine]: SUCCESS (Topological graph traversal successfully rejects cycles, and Undo/Redo state actions restore flow states correctly)
- Invariant 37 [Incremental Data Delta Sync]: SUCCESS (Validated via `test_advanced_etl.py` executing the Rust Muscle binary)
- Invariant 38 [Advanced Type Casting]: SUCCESS (Validated via `test_advanced_etl.py` executing type casting with date parsing format constraints)
- Invariant 39 [Idempotent DB Upsert]: SUCCESS (Implemented SQLite, Postgres, and MySQL batch upserts in `db.upsert` with conflict key handling, verified via `test_n8n_features.py`)
- Invariant 40 [JSON/String Array Explode]: SUCCESS (Implemented Polars-based list and array exploding in `data.split_out`, verified via `test_n8n_features.py`)
- Invariant 41 [File Archive Compression]: SUCCESS (Implemented zip/unzip operations in `data.zip`/`data.unzip` delegating to python archive helper, verified via `test_n8n_features.py`)
- Invariant 42 [Conditional Dynamic Switch Routing]: SUCCESS (Implemented conditional multi-branch routing in `core.switch` inside orchestrator executing case sub-graphs, verified via `test_n8n_features.py`)
- Invariant 43 [Wait/Retention Sleep Primitive]: SUCCESS (Implemented `core.wait` handling flexible duration notation like HH:MM:SS or raw seconds directly in python orchestrator asynchronously)
- Invariant 44 [Local File Loop Age and Size Filters]: SUCCESS (Integrated metadata age and size validation inside `core.loop` file iterations)
- Invariant 45 [UTC Timezone Alignment FTP Transfers]: SUCCESS (Implemented `net.ftp_download_filtered` with timezone-aware UTC comparison and fallback options)
- Invariant 46 [UTC Timezone Alignment SFTP Transfers]: SUCCESS (Implemented `net.sftp_download_filtered` using paramiko st_mtime epoch comparisons)
- Invariant 47 [Visual Data Lineage Mode]: SUCCESS (Dotted curves drawn dynamically based on `GET_DATA_LINEAGE` payloads on SVG canvas, showing file basenames)
- Invariant 48 [Immutable Audit Trail Logs]: SUCCESS (Audit JSON structures populated on run completion and displayed in UI list and details modals, verified via `test_observability_lot_b.py`)
- Invariant 49 [AI Recipe Planner Stress Test Suite]: SUCCESS (Successfully executed all 5 scenario prompts covering simple pipelines, nested loops, AI inference, CDC delta syncs, and edge cases, validating schema compliance and DAG cycle prevention, and outputting the report to `test_results/stress_test_report.md`)
- Invariant 56 [JWT User Authentication & Multi-tenant Vault]: SUCCESS (Implemented `auth.py` with SQLite user storage, PBKDF2 password hashing, HMAC-SHA256 JWT tokens, and `POST /api/register`/`POST /api/login` HTTP endpoints. Chromatix `TenantVault` isolé par `tenant_id`, migration automatique depuis legacy vault. 54 tests Python verts)
- Invariant 57 [WebSocket Token Auth via URL Query]: SUCCESS (WebSocket handler extrait le token JWT du query string `?token=xxx`, valide via `validate_token`, isole le vault par tenant. Fallback `default` sans token. Plus de consommation du premier message — `LIST_WORKSPACES` et `GET_RUN_HISTORY` ne sont plus perdus)
- Invariant 58 [Frontend Auth UI & Admin First-setup Flow]: SUCCESS (Modal login/register intégré à la Vitrine. `GET /api/setup-status` détecte l'absence de comptes et propose la création admin. Token stocké dans `localStorage`, WebSocket reconnecté avec `?token=`. Bouton déconnexion dans le header. 54/54 tests Python)
- Invariant 59 [Autonomous Fake Data Generation]: SUCCESS (Implémenté `data.generate_fake` avec 18 types de génération (id, integer, float, boolean, date, datetime, time, first_name, last_name, full_name, email, phone, country, city, address, postal_code, text, pattern `#AaXx?`), export CSV/JSON. Handler Rust → Python helper `brain/fake_gen_helper.py`. Registry et catalogue frontend préexistants. Recette `recipe_fake_data.json` auto-suffisante sans fichier externe)
- Invariant 60 [Fake Data Stdout Stream & Visual Column Modal]: SUCCESS (Destination rendu optionnel — le muscle output sur stdout, l'orchestrator matérialise dans le fichier auto-généré pour la pipeline. Modal visuel `#fakegen-modal` dans la Vitrine : 18 types avec champs de config dynamiques, ajout/suppression colonnes, pattern `#AaXx?`. L'éditeur de noeud `data.generate_fake` affiche un bouton "Configurer le générateur" au lieu des champs standards)

## Invariant 43 [Wait/Retention Sleep Primitive]
- **Invariant 43 [Wait/Retention Sleep Primitive]:** System must support pausing flow execution for a configurable duration using flexible time formats (HH:MM:SS, MM:SS, or seconds) via `core.wait`.

## Invariant 44 [Local File Loop Age and Size Filters]
- **Invariant 44 [Local File Loop Age and Size Filters]:** System must support filtering local files in directory loops based on maximum file age and minimum/maximum size limits via `core.loop`.

## Invariant 45 [UTC Timezone Alignment FTP Transfers]
- **Invariant 45 [UTC Timezone Alignment FTP Transfers]:** System must support downloading filtered files from remote FTP servers using timezone-aware UTC modification time and size constraints via `net.ftp_download_filtered`.

## Invariant 46 [UTC Timezone Alignment SFTP Transfers]
- **Invariant 46 [UTC Timezone Alignment SFTP Transfers]:** System must support downloading filtered files from remote SFTP servers using timezone-aware UTC modification time and size constraints via `net.sftp_download_filtered`.

## Invariant 47 [Visual Data Lineage Mode]
- **Invariant 47 [Visual Data Lineage Mode]:** Highlights physical data flow paths (file production/consumption links) on SVG canvas using cyan dashed lines and shows file names.

## Invariant 48 [Immutable Audit Trail Logs]
- **Invariant 48 [Immutable Audit Trail Logs]:** Saves metadata (timestamp, host, OS, status, steps, lineage) of executed jobs in `audit_trail.json` and renders in dedicated audit list and details modals.

## Invariant 49 [AI Recipe Planner Stress Test Suite]
- **Invariant 49 [AI Recipe Planner Stress Test Suite]:** System must provide a dedicated test script (`test_planner_stress.py`) to run and validate workflow generation using local or simulated LLM APIs, checking JSON schemas and ensuring dependency graphs do not contain cyclical execution loops.

## Invariant 56 [JWT User Authentication & Multi-tenant Vault]
- **Invariant 56 [JWT User Authentication & Multi-tenant Vault]:** Système d'authentification complet avec comptes utilisateurs stockés en SQLite (`brain/users.db`), hash PBKDF2-SHA256 + sel, tokens JWT HMAC-SHA256 sans dépendance externe. Chaque utilisateur possède un `tenant_id` unique, isolant son vault Chromatix. Endpoints HTTP `POST /api/register` et `POST /api/login` sur le port 8766. Clés d'environnement : `JWT_SECRET` (défaut `change-me-jwt-secret-2026`), `JWT_TTL` (défaut 86400s/24h).

## Invariant 57 [WebSocket Token Auth via URL Query]
- **Invariant 57 [WebSocket Token Auth via URL Query]:** L'authentification WebSocket s'effectue via le query string de l'URL : `ws://host:8765/?token=xxx`. Le handler extrait le token JWT, le valide via `validate_token()`, et isole le `StealthVault` par `tenant_id`. En l'absence de token, le tenant `"default"` est utilisé. Le bug précédent (consommation du premier message `LIST_WORKSPACES` comme tentative d'auth) est corrigé — aucun message n'est perdu.

## Invariant 58 [Frontend Auth UI & Admin First-setup Flow]
- **Invariant 58 [Frontend Auth UI & Admin First-setup Flow]:** Modal d'authentification intégré à la Vitrine (`#auth-modal`). À l'initialisation, `GET /api/setup-status` détermine si des comptes existent : si aucun → formulaire de création du compte administrateur ; si des comptes existent → formulaire de login. Le token JWT est stocké dans `localStorage` et passé en query string à la WebSocket. Bouton de déconnexion dans le header. Après login, l'admin peut créer des comptes supplémentaires via le lien "Créer un nouveau compte".

## Invariant 59 [Autonomous Fake Data Generation]
- **Invariant 59 [Autonomous Fake Data Generation]:** Générateur de données factices autonome (`data.generate_fake`) délégué à `brain/fake_gen_helper.py`. Supporte 18 types de colonnes : id (start/step), integer (min/max), float (min/max/decimals), boolean, date (min/max/format), datetime (min/max/format), time (minHour/maxHour/minMinute/maxMinute/format), first_name, last_name, full_name, email, phone (prefix), country (format name/code), city, address, postal_code (country-aware via 20 masques), text (minWords/maxWords lorem-ipsum), pattern (`#` chiffre, `A` majuscule, `a` minuscule, `X` hex/upper, `x` hex/lower, `?` lettre). Export CSV ou JSON. La recette `recipe_fake_data.json` est désormais auto-suffisante : generation → clean → filter → db.insert.

## Invariant 60 [Fake Data Stdout Stream & Visual Column Modal]
- **Invariant 60 [Fake Data Stdout Stream & Visual Column Modal]:** `data.generate_fake` n'écrit plus de fichier directement — le helper Python dump les données sur stdout. Le worker_bridge filtre `--destination` des args Rust. L'orchestrator capture le stdout et le matérialise dans le chemin auto-généré (`workspace/output/step_N_generate_fake.csv`) pour la pipeline (auto-resolution). Frontend : modal `#fakegen-modal` ouvert depuis l'éditeur de nœud via un bouton "Configurer le générateur". Le modal liste les colonnes avec ajout/suppression, sélecteur de type (18 types), et champs de config dynamiques qui changent selon le type sélectionné (min/max pour integer, format pour date, pattern pour pattern, etc.). Les champs standards (columns, count, format) sont remplacés par l'interface dédiée. 58 tests Python, build Rust OK.

---

## Audit de Cohérence des Primitives (2026-06-08)

À l'occasion d'une revue systématique du système, un audit transversal a été mené pour vérifier l'alignement sémantique entre les trois couches : **registry.json** (définition publique), **Rust Muscle** (dispatch et handlers), et **Vitrine** (catalogue frontend `primitiveCatalogData`).

### Problèmes identifiés

#### 1. Noms d'arguments divergents entre le frontend et les handlers Rust
13 primitives envoyaient des noms de paramètres que le Rust ne reconnaissait pas, causant des échecs silencieux ou des erreurs `Unknown argument` :

| Primitive | Ancien nom (cassé) | Nom corrigé |
|-----------|-------------------|-------------|
| `io.write_file` | `destination` | `path` |
| `io.copy` / `io.move` | `overwrite` (bool) | `conflict` (string enum) |
| `io.delete` | `secure_retention` (bool) | `secure` + `retention_days` |
| `data.groupby` | `keys`, `aggregations` | `groupby_columns`, `aggregate_column`, `operation` |
| `data.metrics` | `columns`, `destination` | `column_name`, `operation`, `destination_variable` |
| `data.lookup` | `lookup_source`, `left_on`, `right_on`, `select_columns` | `lookup_file`, `source_key`, `lookup_key`, `lookup_value`, `destination` |
| `data.anonymize` | `columns` | `rules` |
| `data.deduplicate` | `keys` | `subset` |
| `data.filter` | `field` | `column_name` |
| `ai.summarize` | `text_column`, `summary_column` | `column`, `target_column` |
| `ai.extract` | `text_column` | `column` |

#### 2. Types incompatibles (bool vs enum)
Les champs enum (ex : `conflict: [overwrite/skip/newer]`, `secure: [trash/permanent]`) étaient représentés par des booléens dans le frontend, rendant inaccessibles les valeurs autres que la valeur par défaut.

#### 3. Paramètres manquants dans le catalogue frontend
- `delimiter` et `has_headers` absents de `data.csv_to_json` et `data.json_to_csv`
- `min_age_hours` absent de `net.ftp_download_filtered`, `net.sftp_download_filtered`, `core.loop`
- `schema_drift` absent de `db.insert`
- `prompt` absent de `ai.summarize` et `ai.extract`
- `destination_variable` absent de `data.metrics`

#### 4. Définition dupliquée dans registry.json
`core.loop` apparaissait deux fois (lignes 1225 et 1561) — la seconde définition (riche en filtres) écrasait la première.

#### 5. Primitives Rust sans entrée registry
`google.sheets_read`, `google.sheets_write`, `data.scd`, `data.partition` sont implémentées dans Rust mais absentes de `registry.json`.

### Corrections appliquées

#### Invariant 50 [Auto-résolution de source depuis les dépendances]
- **Fichier :** `brain/orchestrator.py`
- **Mécanisme :** Avant l'exécution de chaque étape, si `source` est vide et que l'étape a une dépendance, le `destination` de l'étape parente est automatiquement injecté dans `args["source"]`.
- **Destination auto-générée :** Si `destination` est vide, un chemin est généré automatiquement (`workspace/output/step_{N}_{primitive}.csv`).
- **Indexation :** Un `step_map` indexé par numéro d'étape est construit avant le lancement des tâches concurrentes pour résoudre les dépendances sans appels coûteux.

#### Invariant 51 [Nouvelle primitive io.read_file]
- **Fichiers :** `brain/registry.json`, `rust_muscle/src/main.rs`, `vitrine/js/app.js`
- **Description :** Lit un fichier CSV/JSON/XLSX/Parquet et le met à disposition des étapes suivantes. Dispatché sur `handle_io_copy` dans Rust (copie source → destination).
- **Paramètres :** `source` (required), `destination`, `format` (enum: auto/csv/json/xlsx/parquet)

#### Invariant 52 [Alignement des noms d'arguments frontend ↔ Rust]
- **Fichier :** `vitrine/js/app.js` — `primitiveCatalogData`
- Tous les noms d'arguments dans le catalogue frontend ont été alignés sur ce que les handlers Rust analysent réellement.

#### Invariant 53 [Menus déroulants pour les champs enum]
- **Fichier :** `vitrine/js/app.js` (nouvelle map `primitiveEnums`), `vitrine/js/editor.js` (rendu conditionnel `<select>`)
- **Portée :** 19 champs enum couvrant 16 primitives (mode, conflict, secure, format, operator, how, how_join, operation, aggregate, keep, model_provider, loop_over, method, type)
- **Comportement :** L'éditeur détecte si l'argument courant a des valeurs enum définies ; si oui, il rend un `<select>` au lieu d'un `<input text>`.

#### Invariant 54 [Indicateur visuel de source héritée]
- **Fichier :** `vitrine/js/editor.js`
- **Comportement :** Si `source` est vide et qu'une dépendance existe, affiche `↳ hérité depuis « Étape X »` sous le champ. Si `destination` est vide, affiche `↳ auto-généré si vide`.

#### Invariant 55 [Dédoublonnage core.loop dans registry.json]
- Définition redondante supprimée (lignes 1225-1253). La définition riche (avec filtres max_age_hours, min_age_hours, min_size_mb, max_size_mb) est conservée.

### Fichiers modifiés (session du 2026-06-08)

| Fichier | Modifications |
|---------|--------------|
| `brain/orchestrator.py` | `step_map`, auto-résolution source/destination |
| `brain/registry.json` | Ajout `io.read_file`, suppression doublon `core.loop` |
| `rust_muscle/src/main.rs` | Ajout dispatch `io.read_file` → `handle_io_copy` |
| `vitrine/js/app.js` | Correction `primitiveCatalogData` (13 primitives), ajout `primitiveEnums` (19 champs), ajout `io.read_file` |
| `vitrine/js/editor.js` | Rendu `<select>` pour enums, indicateurs visuels source/destination |

### Fichiers modifiés (session du 2026-06-09 — Auth & Multi-tenant)

| Fichier | Modifications |
|---------|--------------|
| `brain/auth.py` | Module complet : `register()`, `login()`, `validate_token()`, `_get_db()`, `_hash_password()`, `_create_token()`, `_decode_token()`, `get_tenant_id()` |
| `brain/vault.py` | `StealthVault` adapté pour `TenantVault` multi‑tenant via `chromatix_cps`. Migration legacy depuis `etl_vault.png`/`.json`. API `get(key, env)`, `set(key, value, env)`, `delete(key, env)`, `list(env)` |
| `brain/orchestrator.py` | WebSocket handler : retiré `asyncio.wait_for(websocket.recv())` (consommait le premier message). Extraction du token JWT depuis `path` (query string `?token=xxx`). `StealthVault(vault_key, tenant_id=tenant_id)` |
| `brain/scheduler.py` | Ajout route `GET /api/setup-status` → `{"has_users": bool}` |
| `vitrine/index.html` | Modal `#auth-modal` (login/register/admin creation), bouton `#logout-btn` dans le header |
| `vitrine/js/app.js` | `AUTH_TOKEN`, `checkAuthStatus()`, `authSubmit()`, `toggleAuthMode()`, `logout()`. WebSocket connecté avec `?token=${AUTH_TOKEN}`. Auth check au `DOMContentLoaded` |

### Invariants non résolus
- `google.sheets_read`, `google.sheets_write`, `data.scd`, `data.partition` toujours absents de `registry.json`

## Changelog
- **2026-05-31:** Initial ingestion of the modular ETL agent architecture (v2).
- **2026-05-31:** Transitioned to V3. Added front-end workbench architectural specification and WebSocket real-time state streaming.
- **2026-05-31:** Implemented LLM integration architecture (llm_client, planner) supporting local OpenAI-compatible and Gemini API.
- **2026-05-31:** Added recipe saving/loading (persistence), progressive incremental workflow modification, and secure vault credentials resolution.
- **2026-06-01:** Established modules roadmap ([ROADMAP_MODULES.md](file:///d:/image_to_text/RUST_LIKE_A_TOOL/ROADMAP_MODULES.md)) categorizing core, intermediate, and specialized components.
- **2026-06-01:** Added recursive and fallback folder management capabilities (`io.move` cross-disk fallback, `io.delete` secure retention, `io.metadata` retrieval, and base `net.download`).
- **2026-06-02:** Restructured the Rust tool into a Cargo Workspace by isolating library logic under `libs/analytical_engine` and adding multi-format (CSV, JSON, Parquet) support using Polars for relation join and groupby aggregations.
- **2026-06-03:** Refactored the monolithic `rust_muscle/src/main.rs` by splitting all core primitives into dedicated modules under `src/primitives/`.
- **2026-06-04:** Refactored the orchestrator.py script into 5 single-responsibility submodules (vault.py, worker_bridge.py, schema_validator.py, registry.py, scheduler.py).
- **2026-06-05:** Optimized AiMapper visual overlay layout to make it resizable and significantly denser. Added Formula Editor Modal.
- **2026-06-06:** Implemented Visual Node Link Drawing, Modern Light Theme switch, and Zoom controls.
- **2026-06-07:** Implemented visual node duplication, search, topological cycle validation, and global Undo/Redo stack.
- **2026-06-07:** Implemented advanced ETL primitives `data.delta` and `data.type_cast`.
- **2026-06-07:** Implemented n8n-inspired ETL components: `db.upsert`, `data.split_out`, `data.zip`/`data.unzip`, and `core.switch`. Verified all components with `test_n8n_features.py`.
- **2026-06-07:** Implemented `core.wait` sleep primitive with flexible duration parser (HH:MM:SS), local folder loop filters (max_age_hours, min_size_mb, max_size_mb), and timezone-aligned remote filtered downloads (`net.ftp_download_filtered` and `net.sftp_download_filtered`) using UTC-aware epoch times.
- **2026-06-07:** Implemented Lot B (Observability & Data Lineage): Added backend lineage solver and audit trail serialization, designed frontend visual lineage mode and details drawer modals, and validated all logic using automated test script `test_observability_lot_b.py`.
- **2026-06-07:** Refactored the monolithic frontend `vitrine/js/app.js` (3000+ lines) by splitting visual rendering, mapping inputs (AiMapper), node settings editing, modal controllers, and outgoing WebSocket APIs into dedicated modular scripts (`canvas.js`, `aimapper.js`, `editor.js`, `modals.js`, `api.js`) loaded sequentially in `index.html`.
- **2026-06-07:** Implemented a robust AI Planner stress test suite (`test_planner_stress.py`) validating 5 complex recipe scenarios including schema validation, nested structures, and cycle checking with offline simulation fallback.
- **2026-06-07:** Created `run_e2e_postgres_test.py` for end-to-end stress testing of 20,000 lines processing, filtering, masking, and inserting into PostgreSQL.
- **2026-06-07:** Fixed a critical nested loop context-override bug in `orchestrator.py` by saving and restoring iteration scopes, verified by `test_nested_loops_bug.py`.
- **2026-06-08:** Audit de cohérence des primitives (registry ↔ Rust ↔ frontend). Correction de 13 noms d'arguments divergents et 5 paramètres manquants. Ajout de l'auto-résolution de `source` depuis les dépendances. Ajout de `io.read_file`. Implémentation de menus déroulants pour 19 champs enum. Suppression du doublon `core.loop` dans registry.json. Indicateurs visuels de source héritée et destination auto-générée dans l'éditeur.
- **2026-06-09:** Nettoyage final `data_format.rs` (~55 `MuscleError::Generic` → typed variants). Ajout `data.read`, `data.write`, `data.convert` (multi-format via analytical_engine). Support JSON Lines (`.jsonl`/`.ndjson`). Retrait Avro (API incompatible Polars 0.37). Dashboard Grafana (`grafana/wfgy_dashboard.json`). Documentation README.md étendue (WebSocket, HTTP, Prometheus, Docker, installation sources). 26/26 tests Rust, build release OK.
- **2026-06-09:** Correction bug WebSocket : retiré `asyncio.wait_for(websocket.recv(), timeout=10)` qui consommait le premier message — `LIST_WORKSPACES` était perdu. Authentification déplacée dans l'URL (`?token=xxx`). Implémentation `GET /api/setup-status` pour détection comptes. Modal login/register avec création admin first-setup. Token JWT stocké dans `localStorage`. Bouton déconnexion. Vault multi-tenant isolé par tenant_id. 54/54 tests Python verts.
- **2026-06-17:** Implémentation `data.generate_fake` complète (Rust → Python helper `brain/fake_gen_helper.py`). 18 types de génération (id, integer, float, boolean, date, datetime, time, first_name, last_name, full_name, email, phone, country, city, address, postal_code, text, pattern `#AaXx?`). Masques postaux pour 20 pays. Export CSV/JSON. Recette `recipe_fake_data.json` réécrite autonome (generate → clean → filter → db.insert). Fix import `TenantVault` dans `vault.py`. Fix `bytes/str` dans le body parser HTTP de `scheduler.py`.
- **2026-06-17:** `data.generate_fake` : destination optionnel, output sur stdout, matérialisation par l'orchestrator dans le fichier auto-généré. Modal visuel `#fakegen-modal` (18 types, champs dynamiques, ajout/suppression colonnes). Bouton "Configurer le générateur" dans l'éditeur. `worker_bridge` filtre `--destination` pour `data.generate_fake`. `generator_path` retiré du registry, du Rust et du helper (seed data embarquée). Tests : 58 Python, Rust build OK.















