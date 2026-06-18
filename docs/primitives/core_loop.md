# core.loop

_ItÃ¨re l'exÃ©cution d'une liste d'Ã©tapes sur des variables, des lignes de fichier ou des chemins de fichiers filtrÃ©s._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| loop_over | string | **Oui** | — | Type d'Ã©lÃ©ments Ã  parcourir. (variables, files, rows) |
| items_source | string | **Oui** | — | Source des Ã©lÃ©ments (valeurs sÃ©parÃ©es par des virgules, chemin d'accÃ¨s au dossier ou fichier). |
| pattern | string | Non | * | Optionnel (pour files) : Filtre de motif de glob (ex: *.csv). |
| max_age_hours | string | Non | — | Optionnel (pour files) : Ã‚ge maximum du fichier en heures (ex: '24' pour les fichiers modifiÃ©s dans les derniÃ¨res 24h). |
| min_age_hours | string | Non | — | Optionnel (pour files) : Ã‚ge minimum / anciennetÃ© en heures (ex: '72' pour exiger au moins 3 jours d'anciennetÃ©). |
| min_size_mb | string | Non | — | Optionnel (pour files) : Taille minimale du fichier en Mo (ex: '0.5'). |
| max_size_mb | string | Non | — | Optionnel (pour files) : Taille maximale du fichier en Mo (ex: '10'). |
| steps | array | **Oui** | — | Liste d'Ã©tapes enfants Ã  exÃ©cuter Ã  chaque itÃ©ration. |
