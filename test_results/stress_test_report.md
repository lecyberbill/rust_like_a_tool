# Rapport de Stress Test de l'IA Planner (WFGY-Core V3)

Généré le : 2026-06-07 21:47:40
Modèle d'IA : `openai_compatible / lfm2.5-1.2b-instruct`
Mode d'exécution : `Simulation Hors-ligne`

## Table des Résultats

| Scénario | Statut | Durée (s) | Erreurs détectées |
| :--- | :--- | :--- | :--- |
| Pipeline Simple (I/O, Filtre, Conversion) | **PASSED** | 0.30s | Aucune |
| Boucle Complexe (core.loop sur fichiers, data.clean, io.copy) | **PASSED** | 0.30s | Aucune |
| Inférence IA, RGPD & Base de Données (ai.summarize, data.anonymize, db.insert) | **PASSED** | 0.30s | Aucune |
| Réconciliation Delta CDC & Type Casting Strict | **PASSED** | 0.30s | Aucune |
| Edge-case (Intention absurde ou bruitée) | **PASSED** | 0.30s | Aucune |

## Détails des Recettes Générées

### Pipeline Simple (I/O, Filtre, Conversion)
**Prompt:** *"Copier le fichier source.csv vers destination.csv, puis filtrer la colonne 'age' supérieure à 18 (has_headers=true, operator='greater_than'), et enfin convertir le résultat au format JSON destination_json.json."*

**Statut:** PASSED

**Durée:** 0.30s

```json
{
  "plan_id": "mock_simple_pipeline",
  "intent_analysis": "Copie, filtrage et conversion d'un fichier CSV",
  "steps": [
    {
      "step": 1,
      "primitive": "io.copy",
      "depends_on": [],
      "ui": {
        "label": "Copie source",
        "color": "#4A90E2",
        "position": {
          "x": 150,
          "y": 200
        }
      },
      "args": {
        "source": "source.csv",
        "destination": "destination.csv",
        "overwrite": true
      }
    },
    {
      "step": 2,
      "primitive": "data.filter",
      "depends_on": [
        1
      ],
      "ui": {
        "label": "Filtrage age",
        "color": "#4A90E2",
        "position": {
          "x": 350,
          "y": 200
        }
      },
      "args": {
        "source": "destination.csv",
        "destination": "filtered.csv",
        "field": "age",
        "operator": "greater_than",
        "value": "18"
      }
    },
    {
      "step": 3,
      "primitive": "data.csv_to_json",
      "depends_on": [
        2
      ],
      "ui": {
        "label": "Conversion JSON",
        "color": "#4A90E2",
        "position": {
          "x": 550,
          "y": 200
        }
      },
      "args": {
        "source": "filtered.csv",
        "destination": "destination_json.json"
      }
    }
  ]
}
```

### Boucle Complexe (core.loop sur fichiers, data.clean, io.copy)
**Prompt:** *"Pour chaque fichier CSV dans le répertoire '/data/inbox' correspondant au pattern '*.csv', exécuter un nettoyage de données (data.clean) pour renommer la colonne 'tel' en 'telephone', puis copier le fichier résultant dans le dossier '/data/processed' en utilisant le nom du fichier courant."*

**Statut:** PASSED

**Durée:** 0.30s

```json
{
  "plan_id": "mock_loop_pipeline",
  "intent_analysis": "Parcours et nettoyage des fichiers inbox",
  "steps": [
    {
      "step": 1,
      "primitive": "core.loop",
      "depends_on": [],
      "ui": {
        "label": "Boucle Fichiers",
        "color": "#4A90E2",
        "position": {
          "x": 150,
          "y": 200
        }
      },
      "args": {
        "loop_over": "files",
        "items_source": "/data/inbox",
        "pattern": "*.csv",
        "steps": [
          {
            "step": 2,
            "primitive": "data.clean",
            "depends_on": [],
            "ui": {
              "label": "Nettoyage et mapping",
              "color": "#4A90E2",
              "position": {
                "x": 300,
                "y": 200
              }
            },
            "args": {
              "source": "${ITER_ITEM}",
              "destination": "temp_clean.csv",
              "select_columns": "telephone",
              "rename_columns": "tel:telephone",
              "derive_columns": "",
              "fill_na": ""
            }
          },
          {
            "step": 3,
            "primitive": "io.copy",
            "depends_on": [
              2
            ],
            "ui": {
              "label": "Copie archive",
              "color": "#4A90E2",
              "position": {
                "x": 450,
                "y": 200
              }
            },
            "args": {
              "source": "temp_clean.csv",
              "destination": "/data/processed/output.csv",
              "overwrite": true
            }
          }
        ]
      }
    }
  ]
}
```

### Inférence IA, RGPD & Base de Données (ai.summarize, data.anonymize, db.insert)
**Prompt:** *"Prendre le fichier 'customer_reviews.csv'. Utiliser un LLM pour résumer la colonne 'feedback' dans une nouvelle colonne 'summary', puis anonymiser la colonne 'name' par hashage et la colonne 'email' par masquage, et enfin insérer le tout dans une base de données MySQL table 'reviews'."*

**Statut:** PASSED

**Durée:** 0.30s

```json
{
  "plan_id": "mock_ai_rgpd",
  "intent_analysis": "Résumé LLM, anonymisation RGPD et insertion SQL",
  "steps": [
    {
      "step": 1,
      "primitive": "ai.summarize",
      "depends_on": [],
      "ui": {
        "label": "Résumé IA",
        "color": "#4A90E2",
        "position": {
          "x": 150,
          "y": 200
        }
      },
      "args": {
        "source": "customer_reviews.csv",
        "destination": "reviews_summary.csv",
        "column": "feedback",
        "target_column": "summary",
        "model_provider": "gemini",
        "model_id": "gemini-2.5-flash",
        "base_url": ""
      }
    },
    {
      "step": 2,
      "primitive": "data.anonymize",
      "depends_on": [
        1
      ],
      "ui": {
        "label": "Masquage RGPD",
        "color": "#4A90E2",
        "position": {
          "x": 350,
          "y": 200
        }
      },
      "args": {
        "source": "reviews_summary.csv",
        "destination": "reviews_anonymized.csv",
        "rules": "name:hash,email:mask_email"
      }
    },
    {
      "step": 3,
      "primitive": "db.insert",
      "depends_on": [
        2
      ],
      "ui": {
        "label": "Insertion MySQL",
        "color": "#4A90E2",
        "position": {
          "x": 550,
          "y": 200
        }
      },
      "args": {
        "connection_string": "mysql://root:${SECRET_MYSQL_PASSWORD}@localhost/db",
        "table_name": "reviews",
        "source": "reviews_anonymized.csv",
        "mode": "insert"
      }
    }
  ]
}
```

### Réconciliation Delta CDC & Type Casting Strict
**Prompt:** *"Faire une réconciliation delta CDC (Change Data Capture) entre le fichier source 'users_new.csv' et le fichier cible 'users_old.csv' avec les clés primaires 'id'. Envoyer les modifications (upserts) dans 'upserts.csv', et forcer le type de la colonne 'date_joined' au format de date YYYY-MM-DD."*

**Statut:** PASSED

**Durée:** 0.30s

```json
{
  "plan_id": "mock_cdc_cast",
  "intent_analysis": "CDC Delta et Casting de types",
  "steps": [
    {
      "step": 1,
      "primitive": "data.delta",
      "depends_on": [],
      "ui": {
        "label": "Delta CDC",
        "color": "#4A90E2",
        "position": {
          "x": 150,
          "y": 200
        }
      },
      "args": {
        "source": "users_new.csv",
        "target": "users_old.csv",
        "keys": "id",
        "destination_upsert": "upserts.csv",
        "destination_delete": "deletes.csv",
        "destination_sync": "synced.csv"
      }
    },
    {
      "step": 2,
      "primitive": "data.type_cast",
      "depends_on": [
        1
      ],
      "ui": {
        "label": "Casting strict",
        "color": "#4A90E2",
        "position": {
          "x": 350,
          "y": 200
        }
      },
      "args": {
        "source": "upserts.csv",
        "destination": "upserts_cast.csv",
        "casts": "{\"date_joined\": \"date\"}"
      }
    }
  ]
}
```

### Edge-case (Intention absurde ou bruitée)
**Prompt:** *"Faire chanter le fichier 'chanson.mp3' et envoyer un pigeon voyageur."*

**Statut:** PASSED

**Durée:** 0.30s

```json
{
  "plan_id": "empty_recipe",
  "intent_analysis": "Aucune primitive ETL reconnue.",
  "steps": []
}
```

