# db.insert

_Importe les donnÃ©es d'un fichier (CSV ou JSON) dans une table de base de donnÃ©es (SQLite, Postgres, MySQL, Snowflake, ODBC)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | ChaÃ®ne de connexion de la base de donnÃ©es. |
| table_name | string | **Oui** | — | Le nom de la table cible. |
| source | string | **Oui** | — | Le chemin du fichier de donnÃ©es source (.csv ou .json). |
| mode | string | Non | insert | Mode d'insertion : insert (ajout simple) ou replace (remplacement complet). Valeurs: insert, replace |
| schema_drift | boolean | Non | False | Activer la dÃ©rive de schÃ©ma automatique pour ajouter les colonnes manquantes dans la base. |
