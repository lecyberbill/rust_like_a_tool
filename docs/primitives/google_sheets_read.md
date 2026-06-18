# google.sheets_read

_Extrait des données depuis Google Sheets vers un fichier local CSV._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| credentials | string | **Oui** | — | Chemin vers le fichier JSON de credentials Google Service Account. |
| spreadsheet_id | string | **Oui** | — | L'identifiant du spreadsheet Google Sheets. |
| worksheet_title | string | Non | — | Le nom de l'onglet/feuille à lire (optionnel, lit la première feuille si vide). |
| local_path | string | **Oui** | — | Chemin local où sauvegarder les données extraites en CSV. |
