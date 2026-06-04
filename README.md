# 📊 Rust Like A Tool (RLAT) - Modular ETL Orchestrator (WFGY-Core V3)

**Rust Like A Tool (RLAT)** est un framework ETL hybride de niveau industriel piloté par l'intention (via LLM). Il combine la flexibilité d'un orchestrateur asynchrone en **Python** (le *Cerveau*) et la performance brute de primitives autonomes écrites en **Rust** (le *Muscle*), le tout pilotable en temps réel via une interface réactive moderne (la *Vitrine*).

---

## 🛠️ Architecture & Principes Fondamentaux

L'architecture RLAT repose sur la ségrégation stricte des responsabilités :

1. **Le Cerveau (Brain - Python 3.10+)** : 
   - Reçoit l'intention en langage naturel et génère une recette d'exécution structurée (DAG en JSON) via un planificateur LLM (compatible Gemini API, LM Studio, Ollama).
   - Valide les schémas d'exécution par rapport aux spécifications de primitives enregistrées.
   - Gère le routage parallèle des étapes du DAG en résolvant les dépendances et en gérant les pannes avec retry.
   - Exécute les démons d'arrière-plan (Cron scheduler, File Watcher, Webhook API HTTP).
   - Sécurise les credentials à l'aide d'un coffre-fort d'environnement chiffré (**Stealth Vault** intégré à Chromatix).
2. **Le Muscle (Muscle - Rust)** :
   - Un binaire compilé ultra-rapide exécutant les tâches atomiques (I/O, requêtes réseau, conversions de formats, requêtes SQL, transferts S3).
   - Renvoie des codes d'erreur numériques standardisés, traduits à la volée par l'orchestrateur.
3. **La Vitrine (Vitrine - HTML/CSS/JS)** :
   - Un tableau de bord interactif (Dashboard) pour suivre les daemons et déclencheurs.
   - Un workbench graphique permettant de visualiser l'état d'exécution du DAG en temps réel via des flux WebSockets bi-directionnels.

---

## 📂 Structure du Projet

Le dépôt est organisé de manière modulaire et épurée pour éviter toute pollution :

```
/ (project root)
├── README.md                     <-- Cette documentation
├── ROADMAP_MODULES.md            <-- Suivi de l'implémentation des modules
├── TECHNICAL_REPORT.md           <-- Invariants et changelog technique
├── start_etl_server.bat          <-- Lanceur Windows rapide du serveur d'orchestration
├── requirements.txt              <-- Dépendances Python
├── .env / .env.test              <-- Configurations d'environnements locales (ignorées)
├── brain/                        <-- Le Cerveau (Packages d'Orchestration Python)
│   ├── __init__.py
│   ├── orchestrator.py           <-- Serveur WebSocket & boucle principale
│   ├── planner.py                <-- Traducteur d'intention LLM en Recette
│   ├── llm_client.py             <-- Client d'API LLM (Gemini / OpenAI-compatible)
│   ├── scheduler.py              <-- Démons Cron, File Watcher et Webhook HTTP (port 8766)
│   ├── registry.py               <-- Gestionnaire du catalogue workspaces.json
│   ├── schema_validator.py       <-- Validateur d'arguments de recette
│   ├── vault.py                  <-- Résolveur de secrets Stealth Vault
│   ├── registry.json             <-- Spécification JSON Schema des primitives
│   ├── workspaces.json           <-- Registre persistant des flux configurés
│   └── history_recipes/          <-- Historique des recettes JSON générées
├── vitrine/                      <-- La Vitrine (Interface Utilisateur)
│   └── interface_du_moteur_etl.html <-- Workbench d'atelier et Dashboard dépoli
├── rust_muscle/                  <-- Le Muscle (Moteur de Primitives Rust)
│   ├── Cargo.toml
│   ├── src/
│   │   ├── main.rs               <-- Point d'entrée CLI du Muscle
│   │   ├── error.rs              <-- Gestionnaire d'erreurs MuscleError (codes 1 à 7)
│   │   └── primitives/           <-- Modules de tâches atomiques (io, net, data, db, s3)
│   └── libs/
│       └── analytical_engine/    <-- Moteur d'analyse performant basé sur Polars
└── test_results/                 <-- Espace de tests et jeux de données locaux (ignoré sur main)
```

---

## ⚡ Catalogue des Primitives (Rust Muscle)

Le binaire Rust prend en charge une large collection de primitives regroupées par domaines :

- **Système de fichiers (`io.*`)** :
  - `io.copy` : Copie de fichiers avec gestion interactive des conflits (Écraser / Ignorer / Plus récent).
  - `io.move` : Déplacement physique avec fallback inter-disques.
  - `io.delete` : Suppression sécurisée.
  - `io.metadata` : Récupération des informations de taille et d'existence.
  - `io.write_file` : Écriture de fichiers (ex: feuilles de style XSLT dynamiques).
- **Réseau & Web (`net.*`)** :
  - `net.download` : Téléchargement asynchrone de fichiers distants.
  - `net.upload` : Téléversement multipartite avec en-têtes personnalisés.
  - `net.http_request` : Requêtes HTTP GET/POST génériques et extraction de liens par Regex.
- **Data & Formats (`data.*`)** :
  - `data.csv_to_json` & `data.json_to_csv` : Convertisseurs bidirectionnels à haute performance.
  - `data.xml_to_json` : Analyseur d'arborescences XML hiérarchiques (`quick-xml`).
  - `data.filter` : Filtrage de lignes par expressions régulières et opérateurs arithmétiques.
  - `data.metrics` : Calculs statistiques (somme, moyenne, min, max) via **Polars**.
  - `data.chunk_cumulative` : Partitionnement et cumulatifs glissants via **Polars**.
- **Bases de données (`db.*`)** :
  - `db.query` & `db.insert` : Primitives d'intégration unifiées supportant SQLite, PostgreSQL, MySQL, Snowflake REST, et les connecteurs ODBC.
- **Stockage Cloud (`s3.*`)** :
  - `s3.upload` & `s3.download` : Support natif d'Amazon S3 et des instances MinIO locales.

---

## 🚀 Démarrage Rapide

### Prérequis
- **Python 3.10+** (avec `pip` installé)
- **Rust / Cargo** (si compilation ou exécution de code source du Muscle requise)

### 1. Configuration
Créez un fichier `.env` à la racine pour y stocker vos configurations globales :
```ini
PORT=8765
LLM_PROVIDER=openai_compatible  # ou 'gemini'
LLM_MODEL=gemma
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=votre_cle_ici
SECRET_API_KEY=cle_chiffrement_du_vault
```

### 2. Lancement du Serveur d'Orchestration
Sur Windows, lancez simplement le script batch :
```bash
.\start_etl_server.bat
```
Celui-ci va automatiquement :
1. Créer et activer l'environnement virtuel `.venv` s'il n'existe pas.
2. Installer/Mettre à jour les dépendances listées dans `requirements.txt`.
3. Lancer le serveur d'orchestration (WebSocket sur le port `8765`, Webhook API sur le port `8766`).

### 3. Accès au Tableau de Bord et à l'Atelier
Ouvrez le fichier local [interface_du_moteur_etl.html](file:///d:/image_to_text/RUST_LIKE_A_TOOL/vitrine/interface_du_moteur_etl.html) dans votre navigateur web préféré.

---

## 🕒 Triggers & Démonstration d'Arrière-Plan

Le serveur d'orchestration écoute et déclenche automatiquement vos flux enregistrés :
- **Cron** : Ajoute un déclencheur temporel au format Cron standard (ex : `*/5 * * * *` pour toutes les 5 minutes).
- **File Watcher** : Surveille un répertoire local et exécute automatiquement la recette lorsqu'un fichier correspondant au pattern y est déposé.
- **Webhook API** : Utilisez `curl` ou votre navigateur pour déclencher immédiatement un flux :
  ```bash
  curl "http://localhost:8766/trigger?workspace=default_workflow"
  ```
