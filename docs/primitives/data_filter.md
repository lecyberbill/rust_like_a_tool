# data.filter

_Filtre les lignes d'un fichier texte structuré (CSV) selon une règle logique sur une colonne._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accès au fichier source. |
| destination | string | **Oui** | — | Le chemin du fichier de destination filtré. |
| delimiter | string | Non | , | Délimiteur de champs (ex: , ou ;). |
| column_index | integer | Non | — | Index 0-based de la colonne à filtrer (utilisé si pas d'en-tête). |
| column_name | string | Non | — | Nom de la colonne à filtrer (nécessite has_headers=true). |
| operator | string | **Oui** | — | Opérateur de comparaison logique. (equals, not_equals, contains, not_contains, starts_with, ends_with, regex, greater_than, greater_or_equal, less_than, less_or_equal, is_null, is_not_null, in, not_in) |
| value | string | **Oui** | — | La valeur cible de comparaison. |
| has_headers | boolean | Non | False | Indique si la première ligne du fichier contient les en-têtes. |
