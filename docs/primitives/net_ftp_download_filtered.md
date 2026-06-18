# net.ftp_download_filtered

_Télécharge sélectivement des fichiers depuis FTP selon l'âge et la taille (UTC)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| host | string | **Oui** | — | Hôte du serveur FTP. |
| port | string | Non | 21 | Port FTP. |
| user | string | **Oui** | — | Identifiant FTP. |
| password | string | **Oui** | — | Mot de passe FTP. |
| remote_dir | string | **Oui** | — | Dossier distant contenant les fichiers. |
| local_dir | string | **Oui** | — | Dossier local de destination. |
| max_age_hours | string | Non | — | Optionnel: âge maximal des fichiers en heures (ex: '24' pour modifier dans les dernières 24h) |
| min_age_hours | string | Non | — | Optionnel: âge minimal / ancienneté en heures (ex: '72' pour exiger 3 jours d'ancienneté) |
| min_size_mb | string | Non | — | Optionnel: taille minimale en Mo (ex: '0.1') |
| max_size_mb | string | Non | — | Optionnel: taille maximale en Mo (ex: '50') |
