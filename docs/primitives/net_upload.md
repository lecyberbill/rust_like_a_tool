# net.upload

_Téléverse un fichier local vers un serveur distant (HTTP/HTTPS)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| file_path | string | **Oui** | — | Le chemin du fichier local à téléverser. |
| url | string | **Oui** | — | L'URL HTTP ou HTTPS de destination. |
| method | string | Non | POST | Méthode HTTP à utiliser. (POST, PUT) |
| headers | string | Non | — | En-têtes additionnels au format JSON (ex: pour l'authentification). |
