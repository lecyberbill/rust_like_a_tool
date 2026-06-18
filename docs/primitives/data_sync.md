# data.sync

_Synchronise un CSV avec une table SQL (INSERT/UPDATE/DELETE)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Fichier CSV source. |
| connection_string | string | **Oui** | — | URL de connexion SQL. |
| table_name | string | **Oui** | — | Table cible. |
| key_columns | string | **Oui** | — | Cles de jointure. |
