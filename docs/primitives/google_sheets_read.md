# google.sheets_read

_Extrait des donnÃ©es depuis Google Sheets vers un fichier local CSV._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| credentials | string | **Oui** | — | Chemin vers le fichier JSON de credentials Google Service Account. |
| spreadsheet_id | string | **Oui** | — | L'identifiant du spreadsheet Google Sheets. |
| worksheet_title | string | Non | — | Le nom de l'onglet/feuille Ã  lire (optionnel, lit la premiÃ¨re feuille si vide). |
| local_path | string | **Oui** | — | Chemin local oÃ¹ sauvegarder les donnÃ©es extraites en CSV. |
