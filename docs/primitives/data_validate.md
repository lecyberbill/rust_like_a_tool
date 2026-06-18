# data.validate

_Valide les lignes d'un jeu de donnÃ©es (CSV, JSON, Parquet) par rapport Ã  des rÃ¨gles d'assertions et sÃ©pare les lignes rejetÃ©es dans un fichier de quarantaine._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier de donnÃ©es source. |
| destination | string | **Oui** | — | Le chemin du fichier de destination recevant les lignes valides. |
| quarantine | string | **Oui** | — | Le chemin du fichier de destination recevant les rejets. |
| rules | string | **Oui** | — | Tableau JSON de rÃ¨gles d'assertions. Ex: [{"column": "age", "operator": ">=", "value": 0}, {"column": "email", "operator": "matches", "value": "^[^@]+@[^@]+\\.[^@]+$"}] |
| streaming | boolean | Non | False | Optionnel : Activer l'exÃ©cution en flux (streaming) dans Polars pour optimiser la mÃ©moire RAM. |
