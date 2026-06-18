# data.split

_Divise un jeu de données (CSV, JSON, Parquet) en plusieurs fichiers selon les valeurs uniques d'une colonne cible._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de données source. |
| destination_prefix | string | **Oui** | — | Le préfixe des fichiers créés (ex: outputs/user_split). |
| by_column | string | **Oui** | — | Le nom de la colonne sur laquelle effectuer la division. |
