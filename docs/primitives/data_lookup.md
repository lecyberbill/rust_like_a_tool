# data.lookup

_Recherche et joint des donnÃ©es depuis un rÃ©fÃ©rentiel externe (jointure gauche Polars)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃ©es principal (CSV/JSON/Parquet). |
| lookup_file | string | **Oui** | — | Le fichier dictionnaire / rÃ©fÃ©rentiel externe. |
| source_key | string | **Oui** | — | La clÃ© de liaison dans le fichier principal. |
| lookup_key | string | **Oui** | — | La clÃ© de liaison dans le fichier dictionnaire. |
| lookup_value | string | **Oui** | — | La colonne du dictionnaire Ã  ramener dans le fichier principal. |
| destination | string | **Oui** | — | Le fichier de destination enrichi. |
