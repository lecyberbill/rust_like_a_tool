# net.http_request

_Exécute une requête HTTP (GET, POST, etc.) avec support d'en-têtes, écriture optionnelle vers un fichier de destination, ou extraction regex du corps de la réponse._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| url | string | **Oui** | — | L'URL de la requête. |
| method | string | Non | GET | Méthode HTTP à utiliser. (GET, POST, PUT, DELETE) |
| destination | string | Non | — | Chemin de fichier local optionnel pour enregistrer la réponse brute. |
| headers | string | Non | — | En-têtes HTTP au format JSON. |
| body | string | Non | — | Corps optionnel de la requête. |
| extract_regex | string | Non | — | Regex optionnelle pour extraire des éléments du corps (ex: liens d'images). |
| extract_destination | string | Non | — | Fichier JSON optionnel pour sauvegarder les correspondances de la regex (tableau). |
