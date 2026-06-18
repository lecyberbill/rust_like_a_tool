# data.chunk_cumulative

_Découpe séquentiellement un jeu de données en plusieurs fichiers (parts) dès qu'un seuil cumulé sur une colonne est franchi._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de données source. |
| destination_prefix | string | **Oui** | — | Le préfixe des fichiers créés (ex: outputs/part). |
| accumulate_column | string | **Oui** | — | Le nom de la colonne numérique sur laquelle faire le cumul. |
| threshold | number | **Oui** | — | Le seuil d'accumulation pour déclencher la sauvegarde d'un fichier partition. |
