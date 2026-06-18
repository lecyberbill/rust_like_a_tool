# ai.summarize

_GÃ©nÃ¨re des rÃ©sumÃ©s concis via LLM d'une colonne textuelle et les Ã©crit dans une colonne cible._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃ¨s au fichier de donnÃ©es source (CSV/JSON). |
| destination | string | **Oui** | — | Le chemin d'accÃ¨s au fichier de destination propre gÃ©nÃ©rÃ©. |
| column | string | **Oui** | — | Le nom de la colonne de texte source Ã  rÃ©sumer. |
| target_column | string | Non | — | Le nom de la colonne de destination recevant le rÃ©sumÃ© (optionnel, ex: res_col). |
| prompt | string | Non | — | Consignes de prompt systÃ¨me pour guider le rÃ©sumÃ© (optionnel). |
| model_provider | string | Non | — | Le provider de modÃ¨le LLM Ã  utiliser (optionnel). Valeurs: openai_compatible, gemini |
| model_id | string | Non | — | L'identifiant du modÃ¨le LLM Ã  utiliser pour cette Ã©tape (optionnel). |
| base_url | string | Non | — | URL de base de l'API LLM locale pour cette Ã©tape (optionnel). |
