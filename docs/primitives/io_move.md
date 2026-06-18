# io.move

_Déplace ou renomme un fichier local._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier à déplacer ou renommer. |
| destination | string | **Oui** | — | Le chemin cible de destination. |
| conflict | string | Non | overwrite | Mode de résolution si le fichier de destination existe. (overwrite, skip, newer) |
