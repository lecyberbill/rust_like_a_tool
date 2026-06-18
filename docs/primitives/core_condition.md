# core.condition

_Primitive d'orchestration logique. Ã‰value une expression conditionnelle et exÃ©cute les branches de maniÃ¨re conditionnelle._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| expression | string | **Oui** | — | L'expression logique Ã  Ã©valuer (ex: ${FILE_EXISTS} == true ou ${FILE_SIZE} > 1000). |
| then_steps | array | **Oui** | — | Liste d'Ã©tapes Ã  exÃ©cuter si la condition est vraie. |
| else_steps | array | Non | — | Liste d'Ã©tapes facultatives Ã  exÃ©cuter si la condition est fausse. |
