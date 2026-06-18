# mongodb.find

_Extrait des documents depuis une collection MongoDB et les sauvegarde au format JSON._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | URI de connexion MongoDB (ex: mongodb://localhost:27017). |
| database | string | **Oui** | — | Nom de la base de données. |
| collection | string | **Oui** | — | Nom de la collection. |
| filter | string | Non | — | Chaîne JSON représentant le filtre de recherche (par défaut {}). |
| projection | string | Non | — | Chaîne JSON représentant la projection des champs. |
| destination | string | **Oui** | — | Fichier JSON de destination. |
