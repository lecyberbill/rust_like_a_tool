# flow.report

_GÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¨re un rapport texte depuis le contexte d'exÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©cution du flux (${STEPS.N.STATUS}, ${FLOW.TOTAL_DURATION_MS}, etc.)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| template | string | **Oui** | — | Template texte avec placeholders ${STEPS.N.STATUS}, ${FLOW.*}, etc. |
| destination | string | **Oui** | — | Fichier de sortie du rapport. |

_2 parametres_
