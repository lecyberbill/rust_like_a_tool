# data.unpivot

_Dépivote une table de données du format large au format long (colonnes en lignes)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de données source. |
| destination | string | **Oui** | — | Le fichier de destination propre. |
| index | string | **Oui** | — | Nom(s) des colonnes d'identifiants à conserver séparées par des virgules (ex: id,name). |
| on | string | Non | — | Optionnel: Nom(s) des colonnes de mesures à dépivoter séparées par des virgules. Si vide, toutes les autres colonnes. |
| variable_name | string | Non | variable | Nom de la colonne finale contenant les anciens en-têtes (défaut: variable). |
| value_name | string | Non | value | Nom de la colonne finale contenant les valeurs des mesures (défaut: value). |
