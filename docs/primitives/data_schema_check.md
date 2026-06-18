# data.schema_check

_Verifie la conformite du schema d'un dataset face a un schema attendu._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Fichier CSV/JSON a verifier. |
| expected_schema | string | **Oui** | — | Schema attendu: colonne1,colonne2. |
| destination | string | Non | — | Rapport de verification (JSON). |
