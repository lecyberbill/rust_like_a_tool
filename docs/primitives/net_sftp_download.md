# net.sftp_download

_Télécharge un fichier depuis un serveur SFTP sécurisé (SSH)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| host | string | **Oui** | — | L'adresse IP ou nom d'hôte du serveur SFTP. |
| port | string | Non | 22 | Le port SSH/SFTP (défaut 22). |
| user | string | **Oui** | — | L'identifiant de connexion SSH. |
| password | string | Non | — | Optionnel : Le mot de passe de connexion SSH (requis si aucune clé privée n'est fournie). |
| key_path | string | Non | — | Optionnel : Le chemin local vers le fichier de clé privée SSH (ex: ~/.ssh/id_rsa). |
| key_passphrase | string | Non | — | Optionnel : Le mot de passe/passphrase déverrouillant la clé privée SSH si nécessaire. |
| remote_path | string | **Oui** | — | Le chemin du fichier distant sur le serveur SFTP. |
| local_path | string | **Oui** | — | Le chemin local de destination pour enregistrer le fichier. |
