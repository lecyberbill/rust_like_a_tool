# data.split_out

_Éclate les colonnes contenant des listes ou des chaînes sérialisées JSON vers des lignes distinctes (explode)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accès au fichier source. |
| destination | string | **Oui** | — | Le chemin d'accès au fichier de destination propre éclaté. |
| column | string | **Oui** | — | Le nom de la colonne à éclater. |
| delimiter | string | Non | — | Optionnel: Délimiteur de texte pour éclater si ce n'est pas un tableau JSON direct (ex: virgule). |
