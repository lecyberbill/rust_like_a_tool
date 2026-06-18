# data.groupby

_Groupe les lignes d'un jeu de données (CSV, JSON, Parquet) et calcule des agrégations (somme, moyenne, min, max, count)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Fichier source (CSV, JSON ou Parquet). |
| destination | string | **Oui** | — | Fichier de destination pour stocker le résultat de l'agrégation. |
| groupby_columns | string | **Oui** | — | Noms des colonnes de regroupement séparés par des virgules (ex: status,country). |
| aggregate_column | string | **Oui** | — | Nom de la colonne numérique sur laquelle calculer l'agrégat. |
| operation | string | **Oui** | — | Opération d'agrégation à réaliser. (sum, mean, min, max, count) |
