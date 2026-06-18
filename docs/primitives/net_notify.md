# net.notify

_Envoie une alerte de notification par Email (SMTP) ou par Webhook (HTTP POST)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| type | string | **Oui** | — | Le type de notification (email ou webhook). (email, webhook) |
| smtp_host | string | Non | localhost | L'adresse du serveur SMTP (requis pour email). |
| smtp_port | string | Non | 25 | Le port du serveur SMTP (requis pour email). |
| smtp_user | string | Non | — | L'identifiant du serveur SMTP (optionnel). |
| smtp_pass | string | Non | — | Le mot de passe du serveur SMTP (optionnel). |
| to | string | Non | — | L'adresse email du destinataire (requis pour email). |
| subject | string | Non | ETL Job Notification | Le sujet du mail (optionnel). |
| url | string | Non | — | L'URL de destination du Webhook (requis pour webhook). |
| message | string | **Oui** | — | Le corps du message ou de la payload. |
| attachment | string | Non | — | Chemin d'un fichier à joindre (ex: résultat d'une étape précédente). |
