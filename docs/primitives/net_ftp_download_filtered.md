# net.ftp_download_filtered

_TÃ©lÃ©charge sÃ©lectivement des fichiers depuis FTP selon l'Ã¢ge et la taille (UTC)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| host | string | **Oui** | — | HÃ´te du serveur FTP. |
| port | string | Non | 21 | Port FTP. |
| user | string | **Oui** | — | Identifiant FTP. |
| password | string | **Oui** | — | Mot de passe FTP. |
| remote_dir | string | **Oui** | — | Dossier distant contenant les fichiers. |
| local_dir | string | **Oui** | — | Dossier local de destination. |
| max_age_hours | string | Non | — | Optionnel: Ã¢ge maximal des fichiers en heures (ex: '24' pour modifier dans les derniÃ¨res 24h) |
| min_age_hours | string | Non | — | Optionnel: Ã¢ge minimal / anciennetÃ© en heures (ex: '72' pour exiger 3 jours d'anciennetÃ©) |
| min_size_mb | string | Non | — | Optionnel: taille minimale en Mo (ex: '0.1') |
| max_size_mb | string | Non | — | Optionnel: taille maximale en Mo (ex: '50') |
