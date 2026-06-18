# core.loop

_Itère l'exécution d'une liste d'étapes sur des variables, des lignes de fichier ou des chemins de fichiers filtrés._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| loop_over | string | **Oui** | — | Type d'éléments à parcourir. (variables, files, rows) |
| items_source | string | **Oui** | — | Source des éléments (valeurs séparées par des virgules, chemin d'accès au dossier ou fichier). |
| pattern | string | Non | * | Optionnel (pour files) : Filtre de motif de glob (ex: *.csv). |
| max_age_hours | string | Non | — | Optionnel (pour files) : Âge maximum du fichier en heures (ex: '24' pour les fichiers modifiés dans les dernières 24h). |
| min_age_hours | string | Non | — | Optionnel (pour files) : Âge minimum / ancienneté en heures (ex: '72' pour exiger au moins 3 jours d'ancienneté). |
| min_size_mb | string | Non | — | Optionnel (pour files) : Taille minimale du fichier en Mo (ex: '0.5'). |
| max_size_mb | string | Non | — | Optionnel (pour files) : Taille maximale du fichier en Mo (ex: '10'). |
| steps | array | **Oui** | — | Liste d'étapes enfants à exécuter à chaque itération. |
