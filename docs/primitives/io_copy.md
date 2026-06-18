# io.copy

_Copie un flux de données ou un fichier local._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accès au fichier source. |
| destination | string | **Oui** | — | Le chemin de destination. |
| mode | string | Non | binary | Mode de copie: text ou binary. (binary, text) |
| conflict | string | Non | overwrite | Mode de résolution si le fichier de destination existe. (overwrite, skip, newer) |
