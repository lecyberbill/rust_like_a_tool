# data.anonymize

_Anonymise et masque les colonnes sensibles (PII) d'un jeu de donnÃ©es._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃ©es source. |
| destination | string | **Oui** | — | Le fichier de destination propre. |
| rules | string | **Oui** | — | Mappings de rÃ¨gles d'anonymisation au format col1:strategy1,col2:strategy2. StratÃ©gies: hash, mask, mask_email, replace. |
