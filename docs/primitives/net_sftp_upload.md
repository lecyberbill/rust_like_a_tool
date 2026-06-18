# net.sftp_upload

_TÃ©lÃ©verse un fichier local vers un serveur SFTP sÃ©curisÃ© (SSH)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| host | string | **Oui** | — | L'adresse IP ou nom d'hÃ´te du serveur SFTP. |
| port | string | Non | 22 | Le port SSH/SFTP (dÃ©faut 22). |
| user | string | **Oui** | — | L'identifiant de connexion SSH. |
| password | string | Non | — | Optionnel : Le mot de passe de connexion SSH (requis si aucune clÃ© privÃ©e n'est fournie). |
| key_path | string | Non | — | Optionnel : Le chemin local vers le fichier de clÃ© privÃ©e SSH (ex: ~/.ssh/id_rsa). |
| key_passphrase | string | Non | — | Optionnel : Le mot de passe/passphrase dÃ©verrouillant la clÃ© privÃ©e SSH si nÃ©cessaire. |
| remote_path | string | **Oui** | — | Le chemin de destination sur le serveur SFTP. |
| local_path | string | **Oui** | — | Le chemin du fichier local Ã  tÃ©lÃ©verser. |
