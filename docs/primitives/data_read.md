# data.read

_Lit un fichier dans tout format supporté (CSV, JSON, Parquet, JSONL/NDJSON) et l'écrit en CSV._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier source (auto-détection du format par extension). |
| destination | string | **Oui** | — | Le chemin du fichier CSV de sortie. |
