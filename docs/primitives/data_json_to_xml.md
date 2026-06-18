# data.json_to_xml

_Convertit un tableau d'objets JSON ou un CSV en fichier XML structuré._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accès au fichier JSON ou CSV source. |
| destination | string | **Oui** | — | Le chemin d'accès au fichier XML de destination. |
| root_element | string | Non | root | Nom du nœud XML racine (optionnel). |
| row_element | string | Non | row | Nom du nœud XML pour chaque ligne (optionnel). |
