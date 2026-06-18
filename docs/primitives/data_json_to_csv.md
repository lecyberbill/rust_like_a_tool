# data.json_to_csv

_Convertit un fichier structuré JSON (tableau d'objets) en un fichier délimité CSV._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accès au fichier JSON source. |
| destination | string | **Oui** | — | Le chemin du fichier CSV de destination. |
| delimiter | string | Non | , | Délimiteur de champs (ex: , ou ;). |
| has_headers | boolean | Non | True | Indique s'il faut générer la première ligne du fichier CSV avec les clés comme en-têtes. |
