# data.validate

_Valide les lignes d'un jeu de données (CSV, JSON, Parquet) par rapport à des règles d'assertions et sépare les lignes rejetées dans un fichier de quarantaine._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier de données source. |
| destination | string | **Oui** | — | Le chemin du fichier de destination recevant les lignes valides. |
| quarantine | string | **Oui** | — | Le chemin du fichier de destination recevant les rejets. |
| rules | string | **Oui** | — | Tableau JSON de règles d'assertions. Ex: [{"column": "age", "operator": ">=", "value": 0}, {"column": "email", "operator": "matches", "value": "^[^@]+@[^@]+\\.[^@]+$"}] |
| streaming | boolean | Non | False | Optionnel : Activer l'exécution en flux (streaming) dans Polars pour optimiser la mémoire RAM. |
