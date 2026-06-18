# ai.extract

_Extrait des informations structurées (JSON) via LLM depuis une colonne textuelle vers de nouvelles colonnes._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accès au fichier de données source (CSV/JSON). |
| destination | string | **Oui** | — | Le chemin d'accès au fichier de destination propre généré. |
| column | string | **Oui** | — | Le nom de la colonne de texte source à analyser. |
| schema | string | **Oui** | — | Le schéma JSON décrivant les propriétés à extraire (ex: {"properties": {"nom": {"type": "string"}}}). |
| prompt | string | Non | — | Instructions système additionnelles pour guider l'extraction LLM (optionnel). |
| model_provider | string | Non | — | Le provider de modèle LLM à utiliser (optionnel). (openai_compatible, gemini) |
| model_id | string | Non | — | L'identifiant du modèle LLM à utiliser pour cette étape (optionnel). |
| base_url | string | Non | — | URL de base de l'API LLM locale pour cette étape (optionnel). |
