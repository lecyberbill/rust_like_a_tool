# data.scd

_GÃ¨re les dimensions Ã  Ã©volution lente (SCD Type 2) en comparant source et cible._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier source contenant les nouvelles donnÃ©es. |
| target | string | **Oui** | — | Le chemin du fichier cible existant (dimension historique). |
| keys | string | **Oui** | — | Les colonnes clÃ©s de jointure sÃ©parÃ©es par des virgules. |
| compare_columns | string | Non | — | Les colonnes Ã  comparer pour dÃ©tecter les changements (optionnel, toutes si vide). |
| destination | string | **Oui** | — | Le chemin du fichier de sortie avec la dimension versionnÃ©e. |
| valid_from_col | string | Non | valid_from | Nom de la colonne marquant le dÃ©but de validitÃ©. |
| valid_to_col | string | Non | valid_to | Nom de la colonne marquant la fin de validitÃ©. |
| is_current_col | string | Non | is_current | Nom de la colonne indiquant si l'enregistrement est courant. |
| valid_from_value | string | Non | — | Valeur de dÃ©but de validitÃ© (optionnel, ex: date du jour). |
