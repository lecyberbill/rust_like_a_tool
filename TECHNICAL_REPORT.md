# Technical Report - Modular ETL Orchestrator Agent (WFGY-Core V3)

## Context & Core Axiom
This system is an intent-based ETL orchestrator:
- **Planner (LLM):** Parses user queries to generate structured execution Recipes (JSON) containing visualization metadata, supporting local models (LM Studio, Ollama) and external APIs (Gemini).
- **Brain (Python):** Coordinates the execution, validates steps, manages the execution state, and communicates with the frontend via WebSockets.
- **Muscle (Rust):** Executes performance-critical atomic primitives.
- **Vitrine (Vanilla JS):** Real-time reactive flow graph visualizing the execution steps.

## Stack & Topology
- **Languages:** Python (Orchestration/Parsing/WebSockets/LLM Clients), Rust (Atomic Execution Workers), HTML/CSS/Vanilla JS (Visual Workbench).
- **Topology:** Directed Acyclic Graph (DAG) / Sequential execution plan of steps.

## Structural Invariants & Healthchecks
- **Invariant 1 [Recipe Schema Validation]:** Recipes must conform strictly to the specified JSON schema.
- **Invariant 2 [Separation of Concerns]:** Execution logic remains purely in Rust, control logic in Python, and presentation in Vanilla JS.
- **Invariant 3 [Primitive Atomic Independence]:** Primitives run independently of each other.
- **Invariant 4 [WebSocket State Streaming]:** Execution states are streamed via full-duplex WebSockets to the workbench.
- **Invariant 5 [LLM Interoperability]:** The planner must support local OpenAI-compatible endpoints (LM Studio/Ollama) and API endpoints (Gemini) via uniform interfaces.
- **Invariant 6 [Secrets Vault Injection]:** Sensitive credentials must be represented as placeholders ("${SECRET_XXX}") in recipes and resolved at runtime by the Orchestrator, preventing plaintext exposure in saved JSON files.
- **Invariant 7 [Background Daemon & Webhook Triggers]:** Automated scheduler tasks (Cron checks, directory scanner, and HTTP Webhook server) run persistently.
- **Invariant 8 [Workspace Metadata Registry]:** All workspace flows and trigger specifications are recorded in `workspaces.json`.
- **Invariant 9 [AiMapper visual matching overlay]:** The visual mapping interface resolves schemas over WebSocket and maps visual connections to `data.clean` arguments.

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
- **2026-06-02:** Implemented generic database primitives (`db.query`, `db.insert`) in Rust Muscle supporting SQLite, Postgres, MySQL, Snowflake REST and ODBC, fully integrated into registry and validated by tests.
- **2026-06-02:** Implemented `s3.upload` and `s3.download` object storage primitives in Rust Muscle supporting AWS S3 and MinIO local custom endpoints, fully compiled, schema registered and validated via integration test.
- **2026-06-02:** Added the missing `submitIntent` Javascript function in `interface_du_moteur_etl.html` and bound the submit button and keypress events to it, resolving issues with prompt submissions.
- **2026-06-02:** Implemented `data.json_to_csv` format converter primitive in Rust Muscle using `csv` crate, registered it in schema registry, and verified conversion of heterogeneous JSON objects with a Python verification script.
- **2026-06-03:** Refactored the monolithic `rust_muscle/src/main.rs` (2300+ lines) by splitting all core primitives into dedicated modules under `src/primitives/` (io, net, data_format, data_transform, analytical, db, s3) and isolating MuscleError inside `error.rs` for clean maintainability.
- **2026-06-03:** Added a landing Tableau de Bord (Dashboard) view containing registered flows status, next execution timer, and inline trigger configuration. Created background daemon loops for Cron matching, directory File Watcher scan, and port 8766 HTTP Webhook API receiver.
- **2026-06-04:** Refactored the orchestrator.py script into 5 single-responsibility submodules (vault.py, worker_bridge.py, schema_validator.py, registry.py, scheduler.py) to accommodate future auth integrations.
- **2026-06-04:** Committed modular refactoring of Python submodules and Dashboard UI, successfully merged branch `dev` into `main`, and pushed updates to remote origin repository.
- **2026-06-04:** Implemented the `data.clean` dataset-cleaning primitive in Rust Muscle utilizing Polars, including a custom AST compiler translating IF-THEN-ELSE and arithmetic expressions into native Polars Expr operations.
- **2026-06-04:** Implemented **AiMapper**, a Talend-like visual mapping interface overlay modal with column highlight support, dynamically resolved via `GET_SCHEMA` WebSocket message handler and parsed to Polars `data.clean` arguments.










