# data.groupby

_Groupe les lignes d'un jeu de donnÃ©es (CSV, JSON, Parquet) et calcule des agrÃ©gations (somme, moyenne, min, max, count)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Fichier source (CSV, JSON ou Parquet). |
| destination | string | **Oui** | — | Fichier de destination pour stocker le rÃ©sultat de l'agrÃ©gation. |
| groupby_columns | string | **Oui** | — | Noms des colonnes de regroupement sÃ©parÃ©s par des virgules (ex: status,country). |
| aggregate_column | string | **Oui** | — | Nom de la colonne numÃ©rique sur laquelle calculer l'agrÃ©gat. |
| operation | string | **Oui** | — | OpÃ©ration d'agrÃ©gation Ã  rÃ©aliser. (sum, mean, min, max, count) |
