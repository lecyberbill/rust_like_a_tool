# data.scd

_Gère les dimensions à évolution lente (SCD Type 2) en comparant source et cible._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier source contenant les nouvelles données. |
| target | string | **Oui** | — | Le chemin du fichier cible existant (dimension historique). |
| keys | string | **Oui** | — | Les colonnes clés de jointure séparées par des virgules. |
| compare_columns | string | Non | — | Les colonnes à comparer pour détecter les changements (optionnel, toutes si vide). |
| destination | string | **Oui** | — | Le chemin du fichier de sortie avec la dimension versionnée. |
| valid_from_col | string | Non | valid_from | Nom de la colonne marquant le début de validité. |
| valid_to_col | string | Non | valid_to | Nom de la colonne marquant la fin de validité. |
| is_current_col | string | Non | is_current | Nom de la colonne indiquant si l'enregistrement est courant. |
| valid_from_value | string | Non | — | Valeur de début de validité (optionnel, ex: date du jour). |
