# flow.report

_GÃ©nÃ¨re un rapport texte depuis le contexte d'exÃ©cution du flux (${STEPS.N.STATUS}, ${FLOW.TOTAL_DURATION_MS}, etc.)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| template | string | **Oui** | — | Template texte avec placeholders ${STEPS.N.STATUS}, ${FLOW.*}, etc. |
| destination | string | **Oui** | — | Fichier de sortie du rapport. |
