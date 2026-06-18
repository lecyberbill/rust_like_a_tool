# data.to_db

_Ecrit un dataset dans une table SQL avec creation automatique du schema._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Fichier source. |
| connection_string | string | **Oui** | — | URL de connexion SQL. |
| table_name | string | **Oui** | — | Nom de la table. |
| mode | string | Non | replace | Mode d ecriture. Valeurs: replace, append |

_4 parametres_
