# data.partition

_Partitionne un dataset en plusieurs fichiers selon les valeurs d'une ou plusieurs colonnes._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃ¨s au fichier source (CSV/JSON/Parquet). |
| destination_dir | string | **Oui** | — | Le rÃ©pertoire de destination pour les fichiers partitionnÃ©s. |
| by_columns | string | **Oui** | — | Les colonnes de partitionnement sÃ©parÃ©es par des virgules. |
