# data.write

_Lit un fichier CSV source et l'écrit dans le format détecté par l'extension de destination (CSV, JSON, Parquet, JSONL/NDJSON)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier CSV source. |
| destination | string | **Oui** | — | Le chemin du fichier de sortie (format auto-détecté par extension). |
