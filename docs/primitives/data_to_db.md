# data.to_db

_Ecrit un dataset dans une table SQL avec creation automatique du schema._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Fichier source (CSV/JSON). |
| connection_string | string | **Oui** | — | URL de connexion SQL. |
| table_name | string | **Oui** | — | Nom de la table cible. |
| mode | string | Non | replace | Mode d'ecriture (replace ou append). (replace, append) |
