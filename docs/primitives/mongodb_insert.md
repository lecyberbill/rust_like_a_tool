# mongodb.insert

_Importe les données d'un fichier (CSV ou JSON) dans une collection MongoDB._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | URI de connexion MongoDB. |
| database | string | **Oui** | — | Nom de la base de données. |
| collection | string | **Oui** | — | Nom de la collection. |
| source | string | **Oui** | — | Le chemin du fichier de données source (.csv ou .json). |
| mode | string | Non | insert | Mode d'insertion : insert (ajout simple) ou replace (vide la collection avant insertion). (insert, replace) |
