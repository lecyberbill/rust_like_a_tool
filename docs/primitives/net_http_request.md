# net.http_request

_ExÃ©cute une requÃªte HTTP (GET, POST, etc.) avec support d'en-tÃªtes, Ã©criture optionnelle vers un fichier de destination, ou extraction regex du corps de la rÃ©ponse._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| url | string | **Oui** | — | L'URL de la requÃªte. |
| method | string | Non | GET | MÃ©thode HTTP Ã  utiliser. (GET, POST, PUT, DELETE) |
| destination | string | Non | — | Chemin de fichier local optionnel pour enregistrer la rÃ©ponse brute. |
| headers | string | Non | — | En-tÃªtes HTTP au format JSON. |
| body | string | Non | — | Corps optionnel de la requÃªte. |
| extract_regex | string | Non | — | Regex optionnelle pour extraire des Ã©lÃ©ments du corps (ex: liens d'images). |
| extract_destination | string | Non | — | Fichier JSON optionnel pour sauvegarder les correspondances de la regex (tableau). |
