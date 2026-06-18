# data.clean

_Nettoie et transforme un jeu de donnÃ©es (CSV, JSON, Parquet). Supporte le tri, le dÃ©doublonnage, la sÃ©lection/renommage de colonnes, le traitement des valeurs nulles (fill/drop) et l'ajout de colonnes calculÃ©es ou conditionnelles via un compilateur d'expression lÃ©ger._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃ¨s au fichier source. |
| destination | string | **Oui** | — | Le chemin d'accÃ¨s au fichier de destination propre. |
| sort_by | string | Non | — | Optionnel : Nom de la colonne sur laquelle trier. |
| sort_descending | boolean | Non | False | Optionnel : Trier par ordre dÃ©croissant si vrai. |
| deduplicate | boolean | Non | False | Optionnel : Supprimer les lignes doublons si vrai. |
| deduplicate_on | string | Non | — | Optionnel : Liste de colonnes sÃ©parÃ©es par des virgules pour le dÃ©doublonnage. |
| select_columns | string | Non | — | Optionnel : Liste de colonnes Ã  conserver sÃ©parÃ©es par des virgules (ex: age,nom_complet). |
| rename_columns | string | Non | — | Optionnel : Mappings de renommage au format col_ancienne:col_nouvelle,col2:col2_nouv. |
| fill_na | string | Non | — | Optionnel : Valeurs de remplacement pour les nulls au format col1:valeur1,col2:valeur2. |
| drop_na | boolean | Non | False | Optionnel : Supprime toutes les lignes contenant des valeurs nulles/vides. |
| derive_columns | string | Non | — | Optionnel : CrÃ©ation de colonnes calculÃ©es ou conditionnelles sÃ©parÃ©es par des virgules au format col_nouvelle=EXPRESSION. L'expression supporte : 1. OpÃ©rateurs mathÃ©matiques (+, -, *, /) ex: total = qty * price. 2. ConcatÃ©nations textuelles (+ et guillemets) ex: nom_complet = prenom + ' ' + nom. 3. Conditions IF-THEN-ELSE avec opÃ©rateurs (==, !=, >, >=, <, <=) ex: statut = IF age >= 18 THEN 'adulte' ELSE 'mineur'. |
| right_source | string | Non | — | Optionnel : Le chemin du second fichier Ã  joindre. |
| left_on | string | Non | — | Optionnel : La colonne clÃ© de jointure du fichier source principal. |
| right_on | string | Non | — | Optionnel : La colonne clÃ© de jointure du second fichier. |
| how_join | string | Non | left | Optionnel : Le type de jointure relationnelle. (left, inner, outer) |
| streaming | boolean | Non | False | Optionnel : Activer l'exÃ©cution en flux (streaming) dans Polars pour optimiser la mÃ©moire RAM. |
