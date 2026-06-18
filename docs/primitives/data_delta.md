# data.delta

_Compare deux jeux de données (CSV, JSON, Parquet) sur clés primaires pour calculer les différences incrémentales (upserts, deletes et optionnellement synchronisation complète)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de données source le plus récent. |
| target | string | **Oui** | — | Le fichier de données cible de référence (historique). |
| keys | string | **Oui** | — | Nom(s) de la ou des clés primaires séparées par des virgules (ex: id,code). |
| destination_upsert | string | **Oui** | — | Fichier pour enregistrer les nouvelles lignes et les lignes mises à jour (inserts + updates). |
| destination_delete | string | **Oui** | — | Fichier pour enregistrer les lignes supprimées. |
| destination_sync | string | Non | — | Optionnel: Fichier pour enregistrer le jeu de données consolidé et entièrement synchronisé. |
