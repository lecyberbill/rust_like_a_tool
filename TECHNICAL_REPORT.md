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

## Verification Gate
- Invariant 1 [Recipe Schema Validation]: SUCCESS (`SchemaValidator` implements JSON schema validation against registry specifications)
- Invariant 2 [Separation of Concerns]: SUCCESS (Python Orchestrator parses recipes, Rust Muscle executes the binary)
- Invariant 3 [Primitive Atomic Independence]: SUCCESS (`io.copy` acts as an independent worker subcommand)
- Invariant 4 [WebSocket State Streaming]: SUCCESS (Real-time bi-directional WebSocket state streaming tested successfully)
- Invariant 5 [LLM Interoperability]: SUCCESS (LLM clients written for both OpenAI-compatible and Gemini endpoints, integrated with planner)
- Invariant 6 [Secrets Vault Injection]: SUCCESS (Credentials placeholders resolved at runtime via .env / env variables)

## Changelog
- **2026-05-31:** Initial ingestion of the modular ETL agent architecture (v2).
- **2026-05-31:** Transitioned to V3. Added front-end workbench architectural specification and WebSocket real-time state streaming.
- **2026-05-31:** Implemented LLM integration architecture (llm_client, planner) supporting local LM Studio and Gemini API.
- **2026-05-31:** Added recipe saving/loading (persistence), progressive incremental workflow modification, and secure vault credentials resolution.
- **2026-05-31:** Implemented interactive conflict resolution for `io.copy` using WebSockets, supporting a 120s timeout fallback to 'skip', connection-drop cleanup, and a sleek HTML/CSS glassmorphism modal on the Workbench.


