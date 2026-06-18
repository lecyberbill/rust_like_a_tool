# data.clean

_Nettoie et transforme un jeu de données (CSV, JSON, Parquet). Supporte le tri, le dédoublonnage, la sélection/renommage de colonnes, le traitement des valeurs nulles (fill/drop) et l'ajout de colonnes calculées ou conditionnelles via un compilateur d'expression léger._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accès au fichier source. |
| destination | string | **Oui** | — | Le chemin d'accès au fichier de destination propre. |
| sort_by | string | Non | — | Optionnel : Nom de la colonne sur laquelle trier. |
| sort_descending | boolean | Non | False | Optionnel : Trier par ordre décroissant si vrai. |
| deduplicate | boolean | Non | False | Optionnel : Supprimer les lignes doublons si vrai. |
| deduplicate_on | string | Non | — | Optionnel : Liste de colonnes séparées par des virgules pour le dédoublonnage. |
| select_columns | string | Non | — | Optionnel : Liste de colonnes à conserver séparées par des virgules (ex: age,nom_complet). |
| rename_columns | string | Non | — | Optionnel : Mappings de renommage au format col_ancienne:col_nouvelle,col2:col2_nouv. |
| fill_na | string | Non | — | Optionnel : Valeurs de remplacement pour les nulls au format col1:valeur1,col2:valeur2. |
| drop_na | boolean | Non | False | Optionnel : Supprime toutes les lignes contenant des valeurs nulles/vides. |
| derive_columns | string | Non | — | Optionnel : Création de colonnes calculées ou conditionnelles séparées par des virgules au format col_nouvelle=EXPRESSION. L'expression supporte : 1. Opérateurs mathématiques (+, -, *, /) ex: total = qty * price. 2. Concaténations textuelles (+ et guillemets) ex: nom_complet = prenom + ' ' + nom. 3. Conditions IF-THEN-ELSE avec opérateurs (==, !=, >, >=, <, <=) ex: statut = IF age >= 18 THEN 'adulte' ELSE 'mineur'. |
| right_source | string | Non | — | Optionnel : Le chemin du second fichier à joindre. |
| left_on | string | Non | — | Optionnel : La colonne clé de jointure du fichier source principal. |
| right_on | string | Non | — | Optionnel : La colonne clé de jointure du second fichier. |
| how_join | string | Non | left | Optionnel : Le type de jointure relationnelle. (left, inner, outer) |
| streaming | boolean | Non | False | Optionnel : Activer l'exécution en flux (streaming) dans Polars pour optimiser la mémoire RAM. |
