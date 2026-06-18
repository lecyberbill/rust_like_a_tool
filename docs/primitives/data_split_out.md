# data.split_out

_Ã‰clate les colonnes contenant des listes ou des chaÃ®nes sÃ©rialisÃ©es JSON vers des lignes distinctes (explode)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃ¨s au fichier source. |
| destination | string | **Oui** | — | Le chemin d'accÃ¨s au fichier de destination propre Ã©clatÃ©. |
| column | string | **Oui** | — | Le nom de la colonne Ã  Ã©clater. |
| delimiter | string | Non | — | Optionnel: DÃ©limiteur de texte pour Ã©clater si ce n'est pas un tableau JSON direct (ex: virgule). |
