# mongodb.insert

_Importe les donnÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©es d'un fichier (CSV ou JSON) dans une collection MongoDB._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | URI de connexion MongoDB. |
| database | string | **Oui** | — | Nom de la base de donnÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©es. |
| collection | string | **Oui** | — | Nom de la collection. |
| source | string | **Oui** | — | Le chemin du fichier de donnÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©es source (.csv ou .json). |
| mode | string | Non | insert | Mode d'insertion : insert (ajout simple) ou replace (vide la collection avant insertion). Valeurs: insert, replace |

_5 parametres_
