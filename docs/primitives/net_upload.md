# net.upload

_TÃ©lÃ©verse un fichier local vers un serveur distant (HTTP/HTTPS)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| file_path | string | **Oui** | — | Le chemin du fichier local Ã  tÃ©lÃ©verser. |
| url | string | **Oui** | — | L'URL HTTP ou HTTPS de destination. |
| method | string | Non | POST | MÃ©thode HTTP Ã  utiliser. Valeurs: POST, PUT |
| headers | string | Non | — | En-tÃªtes additionnels au format JSON (ex: pour l'authentification). |
