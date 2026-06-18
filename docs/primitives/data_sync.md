# data.sync

_Synchronise un dataset CSV avec une table SQL (INSERT/UPDATE/DELETE automatique)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Fichier CSV source. |
| connection_string | string | **Oui** | — | URL de connexion SQL (sqlite:///...). |
| table_name | string | **Oui** | — | Nom de la table cible. |
| key_columns | string | **Oui** | — | Colonnes cles pour la jointure (separees par des virgules). |

_4 parametres_
