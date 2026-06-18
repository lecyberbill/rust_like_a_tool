# data.merge

_Fusionne verticalement plusieurs fichiers de données (CSV, JSON, Parquet) de structure identique en un unique fichier cible._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| sources | string | **Oui** | — | Liste des chemins de fichiers sources séparés par des virgules (ex: file1.csv,file2.csv). |
| destination | string | **Oui** | — | Le fichier de destination consolidé. |
