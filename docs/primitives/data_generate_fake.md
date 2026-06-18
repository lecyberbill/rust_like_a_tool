# data.generate_fake

_Génère des données factices (PII, montants, patterns, dates) à l'aide d'un dictionnaire de référence personnalisable._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| columns | string | **Oui** | — | Description des colonnes au format col1:type1,col2:type2 (ex: client_id:id,name:fullName,email:email) ou JSON riche. |
| count | integer | **Oui** | — | Nombre de lignes à générer (ex: 1000). |
| destination | string | Non | — | Le chemin du fichier de sortie généré. |
| format | string | Non | csv | Format d'exportation : csv ou json. (csv, json) |
