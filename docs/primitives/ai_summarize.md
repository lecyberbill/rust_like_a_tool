# ai.summarize

_Génère des résumés concis via LLM d'une colonne textuelle et les écrit dans une colonne cible._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accès au fichier de données source (CSV/JSON). |
| destination | string | **Oui** | — | Le chemin d'accès au fichier de destination propre généré. |
| column | string | **Oui** | — | Le nom de la colonne de texte source à résumer. |
| target_column | string | Non | — | Le nom de la colonne de destination recevant le résumé (optionnel, ex: res_col). |
| prompt | string | Non | — | Consignes de prompt système pour guider le résumé (optionnel). |
| model_provider | string | Non | — | Le provider de modèle LLM à utiliser (optionnel). (openai_compatible, gemini) |
| model_id | string | Non | — | L'identifiant du modèle LLM à utiliser pour cette étape (optionnel). |
| base_url | string | Non | — | URL de base de l'API LLM locale pour cette étape (optionnel). |
