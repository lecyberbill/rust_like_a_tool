# io.delete

_Supprime un fichier ou un dossier local, avec option de mise Ã  la corbeille._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| path | string | **Oui** | — | Le chemin du fichier ou dossier Ã  supprimer. |
| secure | string | Non | trash | Mode de suppression: trash (corbeille locale .trash) ou permanent (dÃ©finitive). Valeurs: trash, permanent |
| retention_days | integer | Non | — | Si secure est trash, nettoie automatiquement les fichiers de la corbeille datant de plus de N jours. |
