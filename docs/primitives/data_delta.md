# data.delta

_Compare deux jeux de donnÃ©es (CSV, JSON, Parquet) sur clÃ©s primaires pour calculer les diffÃ©rences incrÃ©mentales (upserts, deletes et optionnellement synchronisation complÃ¨te)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃ©es source le plus rÃ©cent. |
| target | string | **Oui** | — | Le fichier de donnÃ©es cible de rÃ©fÃ©rence (historique). |
| keys | string | **Oui** | — | Nom(s) de la ou des clÃ©s primaires sÃ©parÃ©es par des virgules (ex: id,code). |
| destination_upsert | string | **Oui** | — | Fichier pour enregistrer les nouvelles lignes et les lignes mises Ã  jour (inserts + updates). |
| destination_delete | string | **Oui** | — | Fichier pour enregistrer les lignes supprimÃ©es. |
| destination_sync | string | Non | — | Optionnel: Fichier pour enregistrer le jeu de donnÃ©es consolidÃ© et entiÃ¨rement synchronisÃ©. |
