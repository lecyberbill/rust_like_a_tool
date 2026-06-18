# data.chunk_cumulative

_DÃ©coupe sÃ©quentiellement un jeu de donnÃ©es en plusieurs fichiers (parts) dÃ¨s qu'un seuil cumulÃ© sur une colonne est franchi._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃ©es source. |
| destination_prefix | string | **Oui** | — | Le prÃ©fixe des fichiers crÃ©Ã©s (ex: outputs/part). |
| accumulate_column | string | **Oui** | — | Le nom de la colonne numÃ©rique sur laquelle faire le cumul. |
| threshold | number | **Oui** | — | Le seuil d'accumulation pour dÃ©clencher la sauvegarde d'un fichier partition. |
