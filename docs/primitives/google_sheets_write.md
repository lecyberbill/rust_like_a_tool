# google.sheets_write

_ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â°crit des donnÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©es depuis un fichier local CSV vers Google Sheets._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| credentials | string | **Oui** | — | Chemin vers le fichier JSON de credentials Google Service Account. |
| spreadsheet_id | string | **Oui** | — | L'identifiant du spreadsheet Google Sheets. |
| worksheet_title | string | Non | — | Le nom de l'onglet/feuille cible (optionnel). |
| local_path | string | **Oui** | — | Chemin local du fichier CSV ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â  importer. |
| clear_sheet | boolean | Non | True | Vider la feuille avant d'ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©crire les nouvelles donnÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©es. |

_5 parametres_
