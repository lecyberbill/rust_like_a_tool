# net.ftp_download

_Télécharge un fichier depuis un serveur FTP._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| host | string | **Oui** | — | L'adresse IP ou nom d'hôte du serveur FTP. |
| port | string | Non | 21 | Le port du serveur FTP. |
| user | string | **Oui** | — | L'identifiant de connexion FTP. |
| password | string | **Oui** | — | Le mot de passe de connexion FTP. |
| remote_path | string | **Oui** | — | Le chemin du fichier sur le serveur FTP (ex: /path/to/file.csv). |
| local_path | string | **Oui** | — | Le chemin local où enregistrer le fichier téléchargé. |
