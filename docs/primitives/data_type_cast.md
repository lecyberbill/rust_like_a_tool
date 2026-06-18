# data.type_cast

_Convertit et formate les colonnes d'un jeu de donnÃ©es selon des types cibles stricts (integer, float, boolean, string, date)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃ©es source. |
| destination | string | **Oui** | — | Le fichier de destination propre avec les colonnes typÃ©es. |
| casts | string | **Oui** | — | ChaÃ®ne au format JSON dÃ©finissant le type des colonnes Ã  convertir (ex: {"id": "int", "price": "float", "date": "date:%Y-%m-%d"}). |
