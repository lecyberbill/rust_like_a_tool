# data.csv_to_json

_Convertit un fichier délimité (CSV) en un fichier structuré JSON (tableau d'objets)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accès au fichier CSV source. |
| destination | string | **Oui** | — | Le chemin du fichier JSON de destination. |
| delimiter | string | Non | , | Délimiteur de champs (ex: , ou ;). |
| has_headers | boolean | Non | True | Indique si la première ligne contient les clés du dictionnaire JSON. |
