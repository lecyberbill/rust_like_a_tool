# data.metrics

_Calcule une mÃ©trique statistique ou textuelle (somme, moyenne, min, max, count, null_count, n_unique, match_regex, non_match_regex) sur une colonne._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃ©es source (CSV, JSON, Parquet). |
| column_name | string | **Oui** | — | Le nom de la colonne cible. |
| operation | string | **Oui** | — | Le type de mÃ©trique Ã  calculer. (sum, mean, min, max, count, null_count, n_unique, match_regex, non_match_regex) |
| regex_pattern | string | Non | — | Expression rÃ©guliÃ¨re utilisÃ©e si l'opÃ©ration est match_regex ou non_match_regex. |
| limit_rows | integer | Non | — | Optionnel: limiter les N premiÃ¨res lignes pour le calcul. |
| destination_variable | string | **Oui** | — | Le nom de la variable dans l'orchestrateur pour stocker le rÃ©sultat. |
