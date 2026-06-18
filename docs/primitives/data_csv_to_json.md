# data.csv_to_json

_Convertit un fichier dÃ©limitÃ© (CSV) en un fichier structurÃ© JSON (tableau d'objets)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃ¨s au fichier CSV source. |
| destination | string | **Oui** | — | Le chemin du fichier JSON de destination. |
| delimiter | string | Non | , | DÃ©limiteur de champs (ex: , ou ;). |
| has_headers | boolean | Non | True | Indique si la premiÃ¨re ligne contient les clÃ©s du dictionnaire JSON. |
