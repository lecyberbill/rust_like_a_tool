# db.query

_Exécute une requête SQL SELECT sur une base de données (SQLite, Postgres, MySQL, Snowflake, ODBC) et écrit le résultat dans un fichier._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | Chaîne de connexion (ex: sqlite://db.sqlite ou postgresql://user:pass@host:5432/db). |
| query | string | **Oui** | — | La requête SQL SELECT à exécuter. |
| destination | string | **Oui** | — | Le fichier de sortie destination (.csv ou .json). |
