# db.upsert

_Upsert (mise Ã  jour ou insertion) idempotent des lignes d'un fichier dans une table SQL sur clÃ©s primaires de conflit._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | ChaÃ®ne de connexion de la base de donnÃ©es (ex: sqlite://db.sqlite). |
| table_name | string | **Oui** | — | Le nom de la table cible. |
| source | string | **Oui** | — | Le chemin du fichier de donnÃ©es source (.csv ou .json). |
| keys | string | **Oui** | — | ClÃ©(s) primaire(s) pour dÃ©tecter les doublons et faire la mise Ã  jour, sÃ©parÃ©es par virgules (ex: id). |
| schema_drift | boolean | Non | False | Activer la dÃ©rive de schÃ©ma automatique pour ajouter les colonnes manquantes dans la base. |
