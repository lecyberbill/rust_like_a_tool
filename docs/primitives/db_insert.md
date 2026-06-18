# db.insert

_Importe les données d'un fichier (CSV ou JSON) dans une table de base de données (SQLite, Postgres, MySQL, Snowflake, ODBC)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | Chaîne de connexion de la base de données. |
| table_name | string | **Oui** | — | Le nom de la table cible. |
| source | string | **Oui** | — | Le chemin du fichier de données source (.csv ou .json). |
| mode | string | Non | insert | Mode d'insertion : insert (ajout simple) ou replace (remplacement complet). (insert, replace) |
| schema_drift | boolean | Non | False | Activer la dérive de schéma automatique pour ajouter les colonnes manquantes dans la base. |
