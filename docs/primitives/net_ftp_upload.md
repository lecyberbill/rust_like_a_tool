# net.ftp_upload

_TÃ©lÃ©verse un fichier local vers un serveur FTP._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| host | string | **Oui** | — | L'adresse IP ou nom d'hÃ´te du serveur FTP. |
| port | string | Non | 21 | Le port du serveur FTP. |
| user | string | **Oui** | — | L'identifiant de connexion FTP. |
| password | string | **Oui** | — | Le mot de passe de connexion FTP. |
| remote_path | string | **Oui** | — | Le chemin cible sur le serveur FTP (ex: /uploads/file.csv). |
| local_path | string | **Oui** | — | Le chemin du fichier local Ã  tÃ©lÃ©verser. |
