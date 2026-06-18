# data.generate_fake

_GÃ©nÃ¨re des donnÃ©es factices (PII, montants, patterns, dates) Ã  l'aide d'un dictionnaire de rÃ©fÃ©rence personnalisable._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| columns | string | **Oui** | — | Description des colonnes au format col1:type1,col2:type2 (ex: client_id:id,name:fullName,email:email) ou JSON riche. |
| count | integer | **Oui** | — | Nombre de lignes Ã  gÃ©nÃ©rer (ex: 1000). |
| destination | string | Non | — | Le chemin du fichier de sortie gÃ©nÃ©rÃ©. |
| format | string | Non | csv | Format d'exportation : csv ou json. (csv, json) |
