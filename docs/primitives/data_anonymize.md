# data.anonymize

_Anonymise et masque les colonnes sensibles (PII) d'un jeu de données._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de données source. |
| destination | string | **Oui** | — | Le fichier de destination propre. |
| rules | string | **Oui** | — | Mappings de règles d'anonymisation au format col1:strategy1,col2:strategy2. Stratégies: hash, mask, mask_email, replace. |
