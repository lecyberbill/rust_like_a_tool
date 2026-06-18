# data.deduplicate

_Supprime les lignes en doublons basÃ©es sur des clÃ©s spÃ©cifiques._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃ©es source. |
| destination | string | **Oui** | — | Le fichier de destination nettoyÃ©. |
| subset | string | **Oui** | — | Liste des colonnes de clÃ© de dÃ©doublonnage, sÃ©parÃ©es par virgules (ex: id,email). |
| keep | string | Non | first | Laquelle des occurrences en doublons conserver: first ou last. (first, last) |
