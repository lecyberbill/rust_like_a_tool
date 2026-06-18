# data.partition

_Partitionne un dataset en plusieurs fichiers selon les valeurs d'une ou plusieurs colonnes._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accès au fichier source (CSV/JSON/Parquet). |
| destination_dir | string | **Oui** | — | Le répertoire de destination pour les fichiers partitionnés. |
| by_columns | string | **Oui** | — | Les colonnes de partitionnement séparées par des virgules. |
