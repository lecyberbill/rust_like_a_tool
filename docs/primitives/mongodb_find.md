# mongodb.find

_Extrait des documents depuis une collection MongoDB et les sauvegarde au format JSON._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | URI de connexion MongoDB (ex: mongodb://localhost:27017). |
| database | string | **Oui** | — | Nom de la base de donnÃ©es. |
| collection | string | **Oui** | — | Nom de la collection. |
| filter | string | Non | — | ChaÃ®ne JSON reprÃ©sentant le filtre de recherche (par dÃ©faut {}). |
| projection | string | Non | — | ChaÃ®ne JSON reprÃ©sentant la projection des champs. |
| destination | string | **Oui** | — | Fichier JSON de destination. |
