# io.move

_DÃ©place ou renomme un fichier local._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier Ã  dÃ©placer ou renommer. |
| destination | string | **Oui** | — | Le chemin cible de destination. |
| conflict | string | Non | overwrite | Mode de rÃ©solution si le fichier de destination existe. Valeurs: overwrite, skip, newer |
