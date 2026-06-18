# google.sheets_write

_Écrit des données depuis un fichier local CSV vers Google Sheets._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| credentials | string | **Oui** | — | Chemin vers le fichier JSON de credentials Google Service Account. |
| spreadsheet_id | string | **Oui** | — | L'identifiant du spreadsheet Google Sheets. |
| worksheet_title | string | Non | — | Le nom de l'onglet/feuille cible (optionnel). |
| local_path | string | **Oui** | — | Chemin local du fichier CSV à importer. |
| clear_sheet | boolean | Non | True | Vider la feuille avant d'écrire les nouvelles données. |
