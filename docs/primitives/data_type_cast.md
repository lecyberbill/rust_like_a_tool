# data.type_cast

_Convertit et formate les colonnes d'un jeu de données selon des types cibles stricts (integer, float, boolean, string, date)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de données source. |
| destination | string | **Oui** | — | Le fichier de destination propre avec les colonnes typées. |
| casts | string | **Oui** | — | Chaîne au format JSON définissant le type des colonnes à convertir (ex: {"id": "int", "price": "float", "date": "date:%Y-%m-%d"}). |
