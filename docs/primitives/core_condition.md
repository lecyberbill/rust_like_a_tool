# core.condition

_Primitive d'orchestration logique. Évalue une expression conditionnelle et exécute les branches de manière conditionnelle._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| expression | string | **Oui** | — | L'expression logique à évaluer (ex: ${FILE_EXISTS} == true ou ${FILE_SIZE} > 1000). |
| then_steps | array | **Oui** | — | Liste d'étapes à exécuter si la condition est vraie. |
| else_steps | array | Non | — | Liste d'étapes facultatives à exécuter si la condition est fausse. |
