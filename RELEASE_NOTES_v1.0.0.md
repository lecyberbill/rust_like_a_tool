# RLAT v1.0.0 — Rust Like A Tool

**Modular ETL Orchestrator | Le 80% des besoins, 50× plus rapide**

---

## Pourquoi RLAT ?

Parce que la plupart des projets ETL n'ont pas besoin de 500 connecteurs Talend. Ils ont besoin de **clean, filter, join, metrics, db** — vite, simplement, sans infrastructure lourde.

**Et parce que décrire son flux en français est plus rapide que le coder.**

RLAT intègre un **Planner LLM** : écrivez votre intention en langage naturel, l'IA génère la recette et l'exécute. Supporte les modèles locaux (LM Studio, Ollama) et l'API Gemini.

RLAT exécute **1 million de lignes** (clean + derive IF/ELSE + filtre + moyenne) en **2.4 secondes**. Soit **416 000 lignes par seconde** en pur Rust columnar via Polars.

## Chiffres clés

| Métrique | Valeur |
|----------|--------|
| Primitives | **68** |
| Tests | **76** (unitaires + intégration + PostgreSQL + MongoDB) |
| Traitement | **416 000 lignes/s** (1M lignes : clean + derive + filtre + moyenne = 2.4s) |
| **Pilotage LLM** | **Gemini, LM Studio, Ollama** — intention → recette → exécution |
| Binaire Rust | 51.8 MB |
| Distribution | 16.8 MB (zippée) |
| Dépendances | Python 3.10+ | Rust 1.82+ | Chromatix Pixel Standard |

## 68 Primitives

| Domaine | Primitives |
|---------|-----------|
| 📁 Fichiers | `io.copy`, `io.move`, `io.delete`, `io.metadata`, `io.read_file`, `io.write_file` |
| 🌐 Réseau | `net.download`, `net.upload`, `net.http_request`, `net.notify`, `net.ftp`, `net.sftp` |
| 📊 Data | `data.filter`, `data.clean`, `data.metrics`, `data.profile`, `data.schema_check`, `data.groupby`, `data.join`, `data.lookup`, `data.deduplicate`, `data.anonymize`, `data.pivot`, `data.unpivot`, `data.delta`, `data.type_cast`, `data.generate_fake`, `data.read`, `data.write`, `data.convert`, `data.sync`, `data.to_db` |
| 🗄️ Bases | `db.query`, `db.insert`, `db.upsert` — PostgreSQL, MySQL, SQLite, MongoDB |
| 🔄 Orchestration | `core.sub_flow`, `core.loop`, `core.switch`, `core.wait`, `flow.report` |
| 📧 Formats | `data.csv_to_json`, `data.json_to_csv`, `data.xml_to_json`, `data.json_to_xml`, `data.to_xlsx`, `data.zip`, `data.unzip` |

## Cas d'usage

| Scénario | Pipeline |
|----------|----------|
| Import CSV → Base | `io.copy → data.deduplicate → db.insert` |
| Génération → Analyse | `data.generate_fake → data.filter → data.metrics` |
| Alerte email | `io.copy → net.notify` (SMTP/Webhook avec pièce jointe) |
| Rapport automatique | `data.generate_fake → flow.report` |
| Sync bidirectionnelle | `data.sync` (CSV ↔ SQL) |
| Profiling dataset | `data.profile` (stats, nulls, distribution) |

## Démarrage en 5 minutes

```bash
# 1. Cloner Chromatix (vault)
git clone https://github.com/lecyberbill/Chromatix-Pixel-Standard.git ../chromatix

# 2. Installer
scripts/install.bat        # Windows
chmod +x scripts/install.sh && ./scripts/install.sh  # Linux

# 3. Configurer .env (copie de .env.example)
#    SECRET_VAULT_KEY et JWT_SECRET sont obligatoires

# 4. Lancer
python brain/orchestrator.py --server

# 5. Ouvrir
#    http://localhost:8766
```

## Installation Docker

```bash
docker build -t wfgy-core-v3 .
docker run -d --name wfgy-etl -p 8765:8765 -p 8766:8766 \
  -v "$(pwd)/.env:/app/.env" wfgy-core-v3
```

## Sécurité

- 🔐 Authentification JWT HMAC-SHA256 avec rôles (admin/operator/viewer)
- 🔒 Vault Chromatix pour le chiffrement des secrets
- 🛡️ Protection path traversal, SSRF, logs filtrés
- ⚠️ `SECRET_VAULT_KEY` et `JWT_SECRET` obligatoires au démarrage

## Assets

| Fichier | Taille |
|---------|--------|
| `rlat_v1.0.0.zip` | 16.8 MB (distribution complète + binaire Rust pré-compilé) |
| Source code (zip) | — |
| Source code (tar.gz) | — |

---

**128 commits · 1 contributeur · 8 juin → 18 juin 2026**
