# data.unpivot

_DÃ©pivote une table de donnÃ©es du format large au format long (colonnes en lignes)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃ©es source. |
| destination | string | **Oui** | — | Le fichier de destination propre. |
| index | string | **Oui** | — | Nom(s) des colonnes d'identifiants Ã  conserver sÃ©parÃ©es par des virgules (ex: id,name). |
| on | string | Non | — | Optionnel: Nom(s) des colonnes de mesures Ã  dÃ©pivoter sÃ©parÃ©es par des virgules. Si vide, toutes les autres colonnes. |
| variable_name | string | Non | variable | Nom de la colonne finale contenant les anciens en-tÃªtes (dÃ©faut: variable). |
| value_name | string | Non | value | Nom de la colonne finale contenant les valeurs des mesures (dÃ©faut: value). |
