# data.validate

_Valide les lignes d'un jeu de donnÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©es (CSV, JSON, Parquet) par rapport ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â  des rÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¨gles d'assertions et sÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©pare les lignes rejetÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©es dans un fichier de quarantaine._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier de donnÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©es source. |
| destination | string | **Oui** | — | Le chemin du fichier de destination recevant les lignes valides. |
| quarantine | string | **Oui** | — | Le chemin du fichier de destination recevant les rejets. |
| rules | string | **Oui** | — | Tableau JSON de rÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¨gles d'assertions. Ex: [{"column": "age", "operator": ">=", "value": 0}, {"column": "email", "operator": "matches", "value": "^[^@]+@[^@]+\\.[^@]+$"}] |
| streaming | boolean | Non | False | Optionnel : Activer l'exÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©cution en flux (streaming) dans Polars pour optimiser la mÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©moire RAM. |

_5 parametres_
