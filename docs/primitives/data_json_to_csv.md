# data.json_to_csv

_Convertit un fichier structurÃ© JSON (tableau d'objets) en un fichier dÃ©limitÃ© CSV._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃ¨s au fichier JSON source. |
| destination | string | **Oui** | — | Le chemin du fichier CSV de destination. |
| delimiter | string | Non | , | DÃ©limiteur de champs (ex: , ou ;). |
| has_headers | boolean | Non | True | Indique s'il faut gÃ©nÃ©rer la premiÃ¨re ligne du fichier CSV avec les clÃ©s comme en-tÃªtes. |
