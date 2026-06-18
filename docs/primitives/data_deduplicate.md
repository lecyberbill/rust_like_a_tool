# data.deduplicate

_Supprime les lignes en doublons basées sur des clés spécifiques._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de données source. |
| destination | string | **Oui** | — | Le fichier de destination nettoyé. |
| subset | string | **Oui** | — | Liste des colonnes de clé de dédoublonnage, séparées par virgules (ex: id,email). |
| keep | string | Non | first | Laquelle des occurrences en doublons conserver: first ou last. (first, last) |
