# io.read_file

_Lit un fichier de données (CSV, JSON, XLSX, Parquet) et le met à disposition des étapes suivantes._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accès au fichier à lire. |
| destination | string | Non | — | Le chemin où copier/rendre les données disponibles (auto-généré si vide). |
| format | string | Non | auto | Format du fichier source (auto = déduit de l'extension). (csv, json, xlsx, parquet, auto) |
