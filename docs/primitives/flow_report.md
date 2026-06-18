# flow.report

_Genere un rapport texte depuis le contexte d'execution du flux (${STEPS.N.STATUS}, ${FLOW.TOTAL_DURATION_MS}, etc.)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| template | string | **Oui** | — | Template texte avec placeholders ${STEPS.*} et ${FLOW.*}. |
| destination | string | **Oui** | — | Fichier de sortie du rapport. |
