# db.upsert

_Upsert (mise à jour ou insertion) idempotent des lignes d'un fichier dans une table SQL sur clés primaires de conflit._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | Chaîne de connexion de la base de données (ex: sqlite://db.sqlite). |
| table_name | string | **Oui** | — | Le nom de la table cible. |
| source | string | **Oui** | — | Le chemin du fichier de données source (.csv ou .json). |
| keys | string | **Oui** | — | Clé(s) primaire(s) pour détecter les doublons et faire la mise à jour, séparées par virgules (ex: id). |
| schema_drift | boolean | Non | False | Activer la dérive de schéma automatique pour ajouter les colonnes manquantes dans la base. |
