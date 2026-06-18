# db.query

_ExÃ©cute une requÃªte SQL SELECT sur une base de donnÃ©es (SQLite, Postgres, MySQL, Snowflake, ODBC) et Ã©crit le rÃ©sultat dans un fichier._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | ChaÃ®ne de connexion (ex: sqlite://db.sqlite ou postgresql://user:pass@host:5432/db). |
| query | string | **Oui** | — | La requÃªte SQL SELECT Ã  exÃ©cuter. |
| destination | string | **Oui** | — | Le fichier de sortie destination (.csv ou .json). |
