# core.switch

_Primitive d'orchestration logique. Route l'exécution vers différents sous-graphes selon la valeur d'une clé ou d'un paramètre._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| value | string | **Oui** | — | La valeur ou variable à tester (ex: ${ENV_MODE} ou ${STATUS}). |
| cases | object | **Oui** | — | Dictionnaire associant des valeurs de cas à des listes d'étapes d'exécution (ex: {"dev": [...], "prod": [...]}). |
