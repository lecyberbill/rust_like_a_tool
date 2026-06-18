# io.read_file

_Lit un fichier de donnÃ©es (CSV, JSON, XLSX, Parquet) et le met Ã  disposition des Ã©tapes suivantes._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃ¨s au fichier Ã  lire. |
| destination | string | Non | — | Le chemin oÃ¹ copier/rendre les donnÃ©es disponibles (auto-gÃ©nÃ©rÃ© si vide). |
| format | string | Non | auto | Format du fichier source (auto = dÃ©duit de l'extension). Valeurs: csv, json, xlsx, parquet, auto |
