# data.split

_Divise un jeu de donnÃ©es (CSV, JSON, Parquet) en plusieurs fichiers selon les valeurs uniques d'une colonne cible._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃ©es source. |
| destination_prefix | string | **Oui** | — | Le prÃ©fixe des fichiers crÃ©Ã©s (ex: outputs/user_split). |
| by_column | string | **Oui** | — | Le nom de la colonne sur laquelle effectuer la division. |
