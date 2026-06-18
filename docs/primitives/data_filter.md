# data.filter

_Filtre les lignes d'un fichier texte structurÃ© (CSV) selon une rÃ¨gle logique sur une colonne._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃ¨s au fichier source. |
| destination | string | **Oui** | — | Le chemin du fichier de destination filtrÃ©. |
| delimiter | string | Non | , | DÃ©limiteur de champs (ex: , ou ;). |
| column_index | integer | Non | — | Index 0-based de la colonne Ã  filtrer (utilisÃ© si pas d'en-tÃªte). |
| column_name | string | Non | — | Nom de la colonne Ã  filtrer (nÃ©cessite has_headers=true). |
| operator | string | **Oui** | — | OpÃ©rateur de comparaison logique. Valeurs: equals, not_equals, contains, not_contains, starts_with, ends_with, regex, greater_than, greater_or_equal, less_than, less_or_equal, is_null, is_not_null, in, not_in |
| value | string | **Oui** | — | La valeur cible de comparaison. |
| has_headers | boolean | Non | False | Indique si la premiÃ¨re ligne du fichier contient les en-tÃªtes. |
