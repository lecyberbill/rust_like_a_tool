# data.join

_RÃ©alise une jointure relationnelle entre deux fichiers de donnÃ©es (CSV, JSON, Parquet) et Ã©crit le rÃ©sultat dans un fichier cible._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| left_source | string | **Oui** | — | Fichier de donnÃ©es de gauche (CSV, JSON ou Parquet). |
| right_source | string | **Oui** | — | Fichier de donnÃ©es de droite (CSV, JSON ou Parquet). |
| destination | string | **Oui** | — | Fichier cible pour Ã©crire le rÃ©sultat de la jointure. |
| left_on | string | **Oui** | — | Colonne clÃ© dans le fichier de gauche. |
| right_on | string | **Oui** | — | Colonne clÃ© dans le fichier de droite. |
| how | string | Non | inner | Type de jointure relationnelle. Valeurs: inner, left, outer |
