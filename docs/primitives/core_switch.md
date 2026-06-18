# core.switch

_Primitive d'orchestration logique. Route l'exÃ©cution vers diffÃ©rents sous-graphes selon la valeur d'une clÃ© ou d'un paramÃ¨tre._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| value | string | **Oui** | — | La valeur ou variable Ã  tester (ex: ${ENV_MODE} ou ${STATUS}). |
| cases | object | **Oui** | — | Dictionnaire associant des valeurs de cas Ã  des listes d'Ã©tapes d'exÃ©cution (ex: {"dev": [...], "prod": [...]}). |
