# data.lookup

_Recherche et joint des données depuis un référentiel externe (jointure gauche Polars)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de données principal (CSV/JSON/Parquet). |
| lookup_file | string | **Oui** | — | Le fichier dictionnaire / référentiel externe. |
| source_key | string | **Oui** | — | La clé de liaison dans le fichier principal. |
| lookup_key | string | **Oui** | — | La clé de liaison dans le fichier dictionnaire. |
| lookup_value | string | **Oui** | — | La colonne du dictionnaire à ramener dans le fichier principal. |
| destination | string | **Oui** | — | Le fichier de destination enrichi. |
