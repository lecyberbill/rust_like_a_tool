# data.pivot

_Pivote une table de données du format long au format large (lignes en colonnes)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de données source. |
| destination | string | **Oui** | — | Le fichier de destination propre. |
| index | string | **Oui** | — | Nom(s) des colonnes d'index de ligne séparés par des virgules (ex: year,country). |
| on | string | **Oui** | — | Nom de la colonne dont les valeurs distinctes deviendront les en-têtes des nouvelles colonnes. |
| values | string | **Oui** | — | Nom de la colonne contenant les valeurs à ventiler dans les nouvelles colonnes. |
| aggregate | string | Non | first | Fonction d'agrégation à appliquer pour les valeurs. (first, last, sum, mean, min, max, count) |
