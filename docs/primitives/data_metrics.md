# data.metrics

_Calcule une métrique statistique ou textuelle (somme, moyenne, min, max, count, null_count, n_unique, match_regex, non_match_regex) sur une colonne._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de données source (CSV, JSON, Parquet). |
| column_name | string | **Oui** | — | Le nom de la colonne cible. |
| operation | string | **Oui** | — | Le type de métrique à calculer. (sum, mean, min, max, count, null_count, n_unique, match_regex, non_match_regex) |
| regex_pattern | string | Non | — | Expression régulière utilisée si l'opération est match_regex ou non_match_regex. |
| limit_rows | integer | Non | — | Optionnel: limiter les N premières lignes pour le calcul. |
| destination_variable | string | **Oui** | — | Le nom de la variable dans l'orchestrateur pour stocker le résultat. |
