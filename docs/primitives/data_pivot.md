# data.pivot

_Pivote une table de donnÃ©es du format long au format large (lignes en colonnes)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃ©es source. |
| destination | string | **Oui** | — | Le fichier de destination propre. |
| index | string | **Oui** | — | Nom(s) des colonnes d'index de ligne sÃ©parÃ©s par des virgules (ex: year,country). |
| on | string | **Oui** | — | Nom de la colonne dont les valeurs distinctes deviendront les en-tÃªtes des nouvelles colonnes. |
| values | string | **Oui** | — | Nom de la colonne contenant les valeurs Ã  ventiler dans les nouvelles colonnes. |
| aggregate | string | Non | first | Fonction d'agrÃ©gation Ã  appliquer pour les valeurs. Valeurs: first, last, sum, mean, min, max, count |
