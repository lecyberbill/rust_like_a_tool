# io.copy

_Copie un flux de donnÃ©es ou un fichier local._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃ¨s au fichier source. |
| destination | string | **Oui** | — | Le chemin de destination. |
| mode | string | Non | binary | Mode de copie: text ou binary. Valeurs: binary, text |
| conflict | string | Non | overwrite | Mode de rÃ©solution si le fichier de destination existe. Valeurs: overwrite, skip, newer |
