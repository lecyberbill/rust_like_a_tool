# data.join

_Réalise une jointure relationnelle entre deux fichiers de données (CSV, JSON, Parquet) et écrit le résultat dans un fichier cible._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| left_source | string | **Oui** | — | Fichier de données de gauche (CSV, JSON ou Parquet). |
| right_source | string | **Oui** | — | Fichier de données de droite (CSV, JSON ou Parquet). |
| destination | string | **Oui** | — | Fichier cible pour écrire le résultat de la jointure. |
| left_on | string | **Oui** | — | Colonne clé dans le fichier de gauche. |
| right_on | string | **Oui** | — | Colonne clé dans le fichier de droite. |
| how | string | Non | inner | Type de jointure relationnelle. (inner, left, outer) |
