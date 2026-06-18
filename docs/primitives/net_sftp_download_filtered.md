# net.sftp_download_filtered

_TÃ©lÃ©charge sÃ©lectivement des fichiers depuis SFTP selon l'Ã¢ge et la taille (UTC)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| host | string | **Oui** | — | HÃ´te du serveur SFTP. |
| port | string | Non | 22 | Port SSH/SFTP. |
| user | string | **Oui** | — | Identifiant SSH. |
| password | string | Non | — | Mot de passe SSH (ou clÃ©). |
| key_path | string | Non | — | Optionnel: chemin clÃ© privÃ©e SSH. |
| key_passphrase | string | Non | — | Optionnel: passphrase de clÃ© privÃ©e. |
| remote_dir | string | **Oui** | — | Dossier distant contenant les fichiers. |
| local_dir | string | **Oui** | — | Dossier local de destination. |
| max_age_hours | string | Non | — | Optionnel: Ã¢ge maximal des fichiers en heures (ex: '24') |
| min_age_hours | string | Non | — | Optionnel: Ã¢ge minimal / anciennetÃ© en heures (ex: '72') |
| min_size_mb | string | Non | — | Optionnel: taille minimale en Mo (ex: '0.1') |
| max_size_mb | string | Non | — | Optionnel: taille maximale en Mo (ex: '50') |
