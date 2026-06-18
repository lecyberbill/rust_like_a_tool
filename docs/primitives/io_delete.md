# io.delete

_Supprime un fichier ou un dossier local, avec option de mise ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â  la corbeille._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| path | string | **Oui** | — | Le chemin du fichier ou dossier ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â  supprimer. |
| secure | string | Non | trash | Mode de suppression: trash (corbeille locale .trash) ou permanent (dÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â©finitive). Valeurs: trash, permanent |
| retention_days | integer | Non | — | Si secure est trash, nettoie automatiquement les fichiers de la corbeille datant de plus de N jours. |

_3 parametres_
