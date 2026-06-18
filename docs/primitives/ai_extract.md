# ai.extract

_Extrait des informations structurÃ©es (JSON) via LLM depuis une colonne textuelle vers de nouvelles colonnes._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃ¨s au fichier de donnÃ©es source (CSV/JSON). |
| destination | string | **Oui** | — | Le chemin d'accÃ¨s au fichier de destination propre gÃ©nÃ©rÃ©. |
| column | string | **Oui** | — | Le nom de la colonne de texte source Ã  analyser. |
| schema | string | **Oui** | — | Le schÃ©ma JSON dÃ©crivant les propriÃ©tÃ©s Ã  extraire (ex: {"properties": {"nom": {"type": "string"}}}). |
| prompt | string | Non | — | Instructions systÃ¨me additionnelles pour guider l'extraction LLM (optionnel). |
| model_provider | string | Non | — | Le provider de modÃ¨le LLM Ã  utiliser (optionnel). Valeurs: openai_compatible, gemini |
| model_id | string | Non | — | L'identifiant du modÃ¨le LLM Ã  utiliser pour cette Ã©tape (optionnel). |
| base_url | string | Non | — | URL de base de l'API LLM locale pour cette Ã©tape (optionnel). |
