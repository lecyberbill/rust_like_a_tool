# Reference des Primitives WFGY-Core V3

Auto-generee depuis registry.json

## ai.extract
_Extrait des informations structurÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es (JSON) via LLM depuis une colonne textuelle vers de nouvelles colonnes._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source (CSV/JSON). |
| destination | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier de destination propre gÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©. |
| column | string | **Oui** | — | Le nom de la colonne de texte source ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  analyser. |
| schema | string | **Oui** | — | Le schÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ma JSON dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©crivant les propriÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  extraire (ex: {"properties": {"nom": {"type": "string"}}}). |
| prompt | string | Non | — | Instructions systÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨me additionnelles pour guider l'extraction LLM (optionnel). |
| model_provider | string | Non | — | Le provider de modÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨le LLM ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  utiliser (optionnel). Valeurs: openai_compatible, gemini |
| model_id | string | Non | — | L'identifiant du modÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨le LLM ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  utiliser pour cette ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tape (optionnel). |
| base_url | string | Non | — | URL de base de l'API LLM locale pour cette ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tape (optionnel). |

## ai.summarize
_GÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨re des rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©sumÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s concis via LLM d'une colonne textuelle et les ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©crit dans une colonne cible._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source (CSV/JSON). |
| destination | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier de destination propre gÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©. |
| column | string | **Oui** | — | Le nom de la colonne de texte source ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©sumer. |
| target_column | string | Non | — | Le nom de la colonne de destination recevant le rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©sumÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© (optionnel, ex: res_col). |
| prompt | string | Non | — | Consignes de prompt systÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨me pour guider le rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©sumÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© (optionnel). |
| model_provider | string | Non | — | Le provider de modÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨le LLM ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  utiliser (optionnel). Valeurs: openai_compatible, gemini |
| model_id | string | Non | — | L'identifiant du modÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨le LLM ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  utiliser pour cette ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tape (optionnel). |
| base_url | string | Non | — | URL de base de l'API LLM locale pour cette ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tape (optionnel). |

## core.condition
_Primitive d'orchestration logique. ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â°value une expression conditionnelle et exÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cute les branches de maniÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨re conditionnelle._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| expression | string | **Oui** | — | L'expression logique ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©valuer (ex: ${FILE_EXISTS} == true ou ${FILE_SIZE} > 1000). |
| then_steps | array | **Oui** | — | Liste d'ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tapes ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  exÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cuter si la condition est vraie. |
| else_steps | array | Non | — | Liste d'ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tapes facultatives ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  exÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cuter si la condition est fausse. |

## core.loop
_ItÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨re l'exÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cution d'une liste d'ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tapes sur des variables, des lignes de fichier ou des chemins de fichiers filtrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| loop_over | string | **Oui** | — | Type d'ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ments ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  parcourir. Valeurs: variables, files, rows |
| items_source | string | **Oui** | — | Source des ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ments (valeurs sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©parÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es par des virgules, chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au dossier ou fichier). |
| pattern | string | Non | * | Optionnel (pour files) : Filtre de motif de glob (ex: *.csv). |
| max_age_hours | string | Non | — | Optionnel (pour files) : ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ge maximum du fichier en heures (ex: '24' pour les fichiers modifiÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s dans les derniÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨res 24h). |
| min_age_hours | string | Non | — | Optionnel (pour files) : ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ge minimum / anciennetÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© en heures (ex: '72' pour exiger au moins 3 jours d'anciennetÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©). |
| min_size_mb | string | Non | — | Optionnel (pour files) : Taille minimale du fichier en Mo (ex: '0.5'). |
| max_size_mb | string | Non | — | Optionnel (pour files) : Taille maximale du fichier en Mo (ex: '10'). |
| steps | array | **Oui** | — | Liste d'ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tapes enfants ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  exÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cuter ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  chaque itÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ration. |

## core.sub_flow
_ExÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cute un ensemble d'ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tapes imbriquÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es comme sous-graphe dans la recette principale._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| steps | array | **Oui** | — | La liste des ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tapes imbriquÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  exÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cuter comme sous-flux. |

## core.switch
_Primitive d'orchestration logique. Route l'exÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cution vers diffÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rents sous-graphes selon la valeur d'une clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© ou d'un paramÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨tre._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| value | string | **Oui** | — | La valeur ou variable ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  tester (ex: ${ENV_MODE} ou ${STATUS}). |
| cases | object | **Oui** | — | Dictionnaire associant des valeurs de cas ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  des listes d'ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tapes d'exÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cution (ex: {"dev": [...], "prod": [...]}). |

## core.wait
_Met en pause l'exÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cution du workflow pendant une durÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e spÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cifiÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e (secondes ou HH:MM:SS)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| duration | string | **Oui** | — | DurÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e de l'attente. Exemples: '5' (5 secondes), '02:30' (2 min 30 s), '01:00:00' (1 heure). |

## data.anonymize
_Anonymise et masque les colonnes sensibles (PII) d'un jeu de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source. |
| destination | string | **Oui** | — | Le fichier de destination propre. |
| rules | string | **Oui** | — | Mappings de rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨gles d'anonymisation au format col1:strategy1,col2:strategy2. StratÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©gies: hash, mask, mask_email, replace. |

## data.chunk_cumulative
_DÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©coupe sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©quentiellement un jeu de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es en plusieurs fichiers (parts) dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s qu'un seuil cumulÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© sur une colonne est franchi._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source. |
| destination_prefix | string | **Oui** | — | Le prÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©fixe des fichiers crÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s (ex: outputs/part). |
| accumulate_column | string | **Oui** | — | Le nom de la colonne numÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rique sur laquelle faire le cumul. |
| threshold | number | **Oui** | — | Le seuil d'accumulation pour dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©clencher la sauvegarde d'un fichier partition. |

## data.clean
_Nettoie et transforme un jeu de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es (CSV, JSON, Parquet). Supporte le tri, le dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©doublonnage, la sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lection/renommage de colonnes, le traitement des valeurs nulles (fill/drop) et l'ajout de colonnes calculÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es ou conditionnelles via un compilateur d'expression lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ger._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier source. |
| destination | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier de destination propre. |
| sort_by | string | Non | — | Optionnel : Nom de la colonne sur laquelle trier. |
| sort_descending | boolean | Non | False | Optionnel : Trier par ordre dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©croissant si vrai. |
| deduplicate | boolean | Non | False | Optionnel : Supprimer les lignes doublons si vrai. |
| deduplicate_on | string | Non | — | Optionnel : Liste de colonnes sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©parÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es par des virgules pour le dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©doublonnage. |
| select_columns | string | Non | — | Optionnel : Liste de colonnes ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  conserver sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©parÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es par des virgules (ex: age,nom_complet). |
| rename_columns | string | Non | — | Optionnel : Mappings de renommage au format col_ancienne:col_nouvelle,col2:col2_nouv. |
| fill_na | string | Non | — | Optionnel : Valeurs de remplacement pour les nulls au format col1:valeur1,col2:valeur2. |
| drop_na | boolean | Non | False | Optionnel : Supprime toutes les lignes contenant des valeurs nulles/vides. |
| derive_columns | string | Non | — | Optionnel : CrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ation de colonnes calculÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es ou conditionnelles sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©parÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es par des virgules au format col_nouvelle=EXPRESSION. L'expression supporte : 1. OpÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rateurs mathÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©matiques (+, -, *, /) ex: total = qty * price. 2. ConcatÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nations textuelles (+ et guillemets) ex: nom_complet = prenom + ' ' + nom. 3. Conditions IF-THEN-ELSE avec opÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rateurs (==, !=, >, >=, <, <=) ex: statut = IF age >= 18 THEN 'adulte' ELSE 'mineur'. |
| right_source | string | Non | — | Optionnel : Le chemin du second fichier ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  joindre. |
| left_on | string | Non | — | Optionnel : La colonne clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© de jointure du fichier source principal. |
| right_on | string | Non | — | Optionnel : La colonne clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© de jointure du second fichier. |
| how_join | string | Non | left | Optionnel : Le type de jointure relationnelle. Valeurs: left, inner, outer |
| streaming | boolean | Non | False | Optionnel : Activer l'exÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cution en flux (streaming) dans Polars pour optimiser la mÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©moire RAM. |

## data.convert
_Convertit un fichier entre tous formats supportÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s (CSV, JSON, Parquet, JSONL/NDJSON) par auto-dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tection des extensions source et destination._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier source (format auto-dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tectÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© par extension). |
| destination | string | **Oui** | — | Le chemin du fichier de destination (format auto-dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tectÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© par extension). |

## data.csv_to_json
_Convertit un fichier dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©limitÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© (CSV) en un fichier structurÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© JSON (tableau d'objets)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier CSV source. |
| destination | string | **Oui** | — | Le chemin du fichier JSON de destination. |
| delimiter | string | Non | , | DÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©limiteur de champs (ex: , ou ;). |
| has_headers | boolean | Non | True | Indique si la premiÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨re ligne contient les clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s du dictionnaire JSON. |

## data.deduplicate
_Supprime les lignes en doublons basÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es sur des clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s spÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cifiques._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source. |
| destination | string | **Oui** | — | Le fichier de destination nettoyÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©. |
| subset | string | **Oui** | — | Liste des colonnes de clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© de dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©doublonnage, sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©parÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es par virgules (ex: id,email). |
| keep | string | Non | first | Laquelle des occurrences en doublons conserver: first ou last. Valeurs: first, last |

## data.delta
_Compare deux jeux de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es (CSV, JSON, Parquet) sur clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s primaires pour calculer les diffÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rences incrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©mentales (upserts, deletes et optionnellement synchronisation complÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨te)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source le plus rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cent. |
| target | string | **Oui** | — | Le fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es cible de rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©fÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rence (historique). |
| keys | string | **Oui** | — | Nom(s) de la ou des clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s primaires sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©parÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es par des virgules (ex: id,code). |
| destination_upsert | string | **Oui** | — | Fichier pour enregistrer les nouvelles lignes et les lignes mises ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  jour (inserts + updates). |
| destination_delete | string | **Oui** | — | Fichier pour enregistrer les lignes supprimÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es. |
| destination_sync | string | Non | — | Optionnel: Fichier pour enregistrer le jeu de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es consolidÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© et entiÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨rement synchronisÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©. |

## data.filter
_Filtre les lignes d'un fichier texte structurÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© (CSV) selon une rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨gle logique sur une colonne._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier source. |
| destination | string | **Oui** | — | Le chemin du fichier de destination filtrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©. |
| delimiter | string | Non | , | DÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©limiteur de champs (ex: , ou ;). |
| column_index | integer | Non | — | Index 0-based de la colonne ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  filtrer (utilisÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© si pas d'en-tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªte). |
| column_name | string | Non | — | Nom de la colonne ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  filtrer (nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cessite has_headers=true). |
| operator | string | **Oui** | — | OpÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rateur de comparaison logique. Valeurs: equals, not_equals, contains, not_contains, starts_with, ends_with, regex, greater_than, greater_or_equal, less_than, less_or_equal, is_null, is_not_null, in, not_in |
| value | string | **Oui** | — | La valeur cible de comparaison. |
| has_headers | boolean | Non | False | Indique si la premiÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨re ligne du fichier contient les en-tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªtes. |

## data.generate_fake
_GÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨re des donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es factices (PII, montants, patterns, dates) ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  l'aide d'un dictionnaire de rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©fÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rence personnalisable._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| columns | string | **Oui** | — | Description des colonnes au format col1:type1,col2:type2 (ex: client_id:id,name:fullName,email:email) ou JSON riche. |
| count | integer | **Oui** | — | Nombre de lignes ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  gÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rer (ex: 1000). |
| destination | string | Non | — | Le chemin du fichier de sortie gÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©. |
| format | string | Non | csv | Format d'exportation : csv ou json. Valeurs: csv, json |

## data.groupby
_Groupe les lignes d'un jeu de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es (CSV, JSON, Parquet) et calcule des agrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©gations (somme, moyenne, min, max, count)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Fichier source (CSV, JSON ou Parquet). |
| destination | string | **Oui** | — | Fichier de destination pour stocker le rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©sultat de l'agrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©gation. |
| groupby_columns | string | **Oui** | — | Noms des colonnes de regroupement sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©parÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s par des virgules (ex: status,country). |
| aggregate_column | string | **Oui** | — | Nom de la colonne numÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rique sur laquelle calculer l'agrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©gat. |
| operation | string | **Oui** | — | OpÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ration d'agrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©gation ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©aliser. Valeurs: sum, mean, min, max, count |

## data.join
_RÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©alise une jointure relationnelle entre deux fichiers de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es (CSV, JSON, Parquet) et ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©crit le rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©sultat dans un fichier cible._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| left_source | string | **Oui** | — | Fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es de gauche (CSV, JSON ou Parquet). |
| right_source | string | **Oui** | — | Fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es de droite (CSV, JSON ou Parquet). |
| destination | string | **Oui** | — | Fichier cible pour ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©crire le rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©sultat de la jointure. |
| left_on | string | **Oui** | — | Colonne clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© dans le fichier de gauche. |
| right_on | string | **Oui** | — | Colonne clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© dans le fichier de droite. |
| how | string | Non | inner | Type de jointure relationnelle. Valeurs: inner, left, outer |

## data.json_to_csv
_Convertit un fichier structurÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© JSON (tableau d'objets) en un fichier dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©limitÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© CSV._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier JSON source. |
| destination | string | **Oui** | — | Le chemin du fichier CSV de destination. |
| delimiter | string | Non | , | DÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©limiteur de champs (ex: , ou ;). |
| has_headers | boolean | Non | True | Indique s'il faut gÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rer la premiÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨re ligne du fichier CSV avec les clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s comme en-tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªtes. |

## data.json_to_xml
_Convertit un tableau d'objets JSON ou un CSV en fichier XML structurÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier JSON ou CSV source. |
| destination | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier XML de destination. |
| root_element | string | Non | root | Nom du nÃƒÆ’Ã¢â‚¬Â¦ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œud XML racine (optionnel). |
| row_element | string | Non | row | Nom du nÃƒÆ’Ã¢â‚¬Â¦ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œud XML pour chaque ligne (optionnel). |

## data.lookup
_Recherche et joint des donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es depuis un rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©fÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rentiel externe (jointure gauche Polars)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es principal (CSV/JSON/Parquet). |
| lookup_file | string | **Oui** | — | Le fichier dictionnaire / rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©fÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rentiel externe. |
| source_key | string | **Oui** | — | La clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© de liaison dans le fichier principal. |
| lookup_key | string | **Oui** | — | La clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© de liaison dans le fichier dictionnaire. |
| lookup_value | string | **Oui** | — | La colonne du dictionnaire ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  ramener dans le fichier principal. |
| destination | string | **Oui** | — | Le fichier de destination enrichi. |

## data.merge
_Fusionne verticalement plusieurs fichiers de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es (CSV, JSON, Parquet) de structure identique en un unique fichier cible._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| sources | string | **Oui** | — | Liste des chemins de fichiers sources sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©parÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s par des virgules (ex: file1.csv,file2.csv). |
| destination | string | **Oui** | — | Le fichier de destination consolidÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©. |

## data.metrics
_Calcule une mÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©trique statistique ou textuelle (somme, moyenne, min, max, count, null_count, n_unique, match_regex, non_match_regex) sur une colonne._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source (CSV, JSON, Parquet). |
| column_name | string | **Oui** | — | Le nom de la colonne cible. |
| operation | string | **Oui** | — | Le type de mÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©trique ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  calculer. Valeurs: sum, mean, min, max, count, null_count, n_unique, match_regex, non_match_regex |
| regex_pattern | string | Non | — | Expression rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©guliÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨re utilisÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e si l'opÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ration est match_regex ou non_match_regex. |
| limit_rows | integer | Non | — | Optionnel: limiter les N premiÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨res lignes pour le calcul. |
| destination_variable | string | **Oui** | — | Le nom de la variable dans l'orchestrateur pour stocker le rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©sultat. |

## data.partition
_Partitionne un dataset en plusieurs fichiers selon les valeurs d'une ou plusieurs colonnes._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier source (CSV/JSON/Parquet). |
| destination_dir | string | **Oui** | — | Le rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©pertoire de destination pour les fichiers partitionnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s. |
| by_columns | string | **Oui** | — | Les colonnes de partitionnement sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©parÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es par des virgules. |

## data.pivot
_Pivote une table de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es du format long au format large (lignes en colonnes)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source. |
| destination | string | **Oui** | — | Le fichier de destination propre. |
| index | string | **Oui** | — | Nom(s) des colonnes d'index de ligne sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©parÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s par des virgules (ex: year,country). |
| on | string | **Oui** | — | Nom de la colonne dont les valeurs distinctes deviendront les en-tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªtes des nouvelles colonnes. |
| values | string | **Oui** | — | Nom de la colonne contenant les valeurs ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  ventiler dans les nouvelles colonnes. |
| aggregate | string | Non | first | Fonction d'agrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©gation ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  appliquer pour les valeurs. Valeurs: first, last, sum, mean, min, max, count |

## data.profile
_Profile un dataset: stats, nulls, distribution par colonne._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Fichier CSV/JSON a profiler. |
| destination | string | **Oui** | — | Fichier JSON de sortie des stats. |

## data.read
_Lit un fichier dans tout format supportÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© (CSV, JSON, Parquet, JSONL/NDJSON) et l'ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©crit en CSV._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier source (auto-dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tection du format par extension). |
| destination | string | **Oui** | — | Le chemin du fichier CSV de sortie. |

## data.scd
_GÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨re les dimensions ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©volution lente (SCD Type 2) en comparant source et cible._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier source contenant les nouvelles donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es. |
| target | string | **Oui** | — | Le chemin du fichier cible existant (dimension historique). |
| keys | string | **Oui** | — | Les colonnes clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s de jointure sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©parÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es par des virgules. |
| compare_columns | string | Non | — | Les colonnes ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  comparer pour dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tecter les changements (optionnel, toutes si vide). |
| destination | string | **Oui** | — | Le chemin du fichier de sortie avec la dimension versionnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e. |
| valid_from_col | string | Non | valid_from | Nom de la colonne marquant le dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©but de validitÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©. |
| valid_to_col | string | Non | valid_to | Nom de la colonne marquant la fin de validitÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©. |
| is_current_col | string | Non | is_current | Nom de la colonne indiquant si l'enregistrement est courant. |
| valid_from_value | string | Non | — | Valeur de dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©but de validitÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© (optionnel, ex: date du jour). |

## data.schema_check
_Verifie la conformite d un dataset face a un schema attendu._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Fichier CSV/JSON a verifier. |
| expected_schema | string | **Oui** | — | Schema attendu: colonne1,colonne2 ou JSON. |
| destination | string | Non | — | Fichier JSON de sortie du rapport. |

## data.split
_Divise un jeu de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es (CSV, JSON, Parquet) en plusieurs fichiers selon les valeurs uniques d'une colonne cible._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source. |
| destination_prefix | string | **Oui** | — | Le prÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©fixe des fichiers crÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s (ex: outputs/user_split). |
| by_column | string | **Oui** | — | Le nom de la colonne sur laquelle effectuer la division. |

## data.split_out
_ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â°clate les colonnes contenant des listes ou des chaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â®nes sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rialisÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es JSON vers des lignes distinctes (explode)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier source. |
| destination | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier de destination propre ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©clatÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©. |
| column | string | **Oui** | — | Le nom de la colonne ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©clater. |
| delimiter | string | Non | — | Optionnel: DÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©limiteur de texte pour ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©clater si ce n'est pas un tableau JSON direct (ex: virgule). |

## data.to_xlsx
_Exporte un fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es (CSV ou JSON) vers une feuille de calcul Excel (.xlsx)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier source (CSV ou JSON). |
| destination | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier Excel (.xlsx) de destination. |
| sheet_name | string | Non | Sheet1 | Le nom de l'onglet/feuille de calcul Excel (optionnel). |

## data.type_cast
_Convertit et formate les colonnes d'un jeu de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es selon des types cibles stricts (integer, float, boolean, string, date)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source. |
| destination | string | **Oui** | — | Le fichier de destination propre avec les colonnes typÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es. |
| casts | string | **Oui** | — | ChaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â®ne au format JSON dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©finissant le type des colonnes ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  convertir (ex: {"id": "int", "price": "float", "date": "date:%Y-%m-%d"}). |

## data.unpivot
_DÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©pivote une table de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es du format large au format long (colonnes en lignes)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source. |
| destination | string | **Oui** | — | Le fichier de destination propre. |
| index | string | **Oui** | — | Nom(s) des colonnes d'identifiants ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  conserver sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©parÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es par des virgules (ex: id,name). |
| on | string | Non | — | Optionnel: Nom(s) des colonnes de mesures ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©pivoter sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©parÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es par des virgules. Si vide, toutes les autres colonnes. |
| variable_name | string | Non | variable | Nom de la colonne finale contenant les anciens en-tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªtes (dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©faut: variable). |
| value_name | string | Non | value | Nom de la colonne finale contenant les valeurs des mesures (dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©faut: value). |

## data.unzip
_DÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©compresse une archive ZIP dans un dossier de destination._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Chemin de l'archive ZIP source. |
| destination | string | **Oui** | — | Dossier cible pour extraire le contenu. |

## data.validate
_Valide les lignes d'un jeu de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es (CSV, JSON, Parquet) par rapport ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  des rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨gles d'assertions et sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©pare les lignes rejetÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es dans un fichier de quarantaine._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source. |
| destination | string | **Oui** | — | Le chemin du fichier de destination recevant les lignes valides. |
| quarantine | string | **Oui** | — | Le chemin du fichier de destination recevant les rejets. |
| rules | string | **Oui** | — | Tableau JSON de rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨gles d'assertions. Ex: [{"column": "age", "operator": ">=", "value": 0}, {"column": "email", "operator": "matches", "value": "^[^@]+@[^@]+\\.[^@]+$"}] |
| streaming | boolean | Non | False | Optionnel : Activer l'exÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cution en flux (streaming) dans Polars pour optimiser la mÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©moire RAM. |

## data.write
_Lit un fichier CSV source et l'ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©crit dans le format dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tectÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© par l'extension de destination (CSV, JSON, Parquet, JSONL/NDJSON)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier CSV source. |
| destination | string | **Oui** | — | Le chemin du fichier de sortie (format auto-dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tectÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© par extension). |

## data.xml_to_json
_Convertit un fichier XML hiÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rarchique en fichier JSON standard._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier XML source. |
| destination | string | **Oui** | — | Le chemin du fichier JSON de destination. |

## data.xml_transform
_Applique une transformation structurelle XSLT sur un fichier XML source._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier XML source. |
| stylesheet | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier de feuille de style XSLT (.xsl ou .xslt). |
| destination | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier de sortie transformÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©. |

## data.zip
_Compresse un dossier ou un fichier dans une archive ZIP._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Chemin du fichier ou dossier source ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  compresser. |
| destination | string | **Oui** | — | Chemin de l'archive ZIP destination ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  gÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rer. |

## db.insert
_Importe les donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es d'un fichier (CSV ou JSON) dans une table de base de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es (SQLite, Postgres, MySQL, Snowflake, ODBC)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | ChaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â®ne de connexion de la base de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es. |
| table_name | string | **Oui** | — | Le nom de la table cible. |
| source | string | **Oui** | — | Le chemin du fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source (.csv ou .json). |
| mode | string | Non | insert | Mode d'insertion : insert (ajout simple) ou replace (remplacement complet). Valeurs: insert, replace |
| schema_drift | boolean | Non | False | Activer la dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rive de schÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ma automatique pour ajouter les colonnes manquantes dans la base. |

## db.query
_ExÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cute une requÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªte SQL SELECT sur une base de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es (SQLite, Postgres, MySQL, Snowflake, ODBC) et ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©crit le rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©sultat dans un fichier._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | ChaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â®ne de connexion (ex: sqlite://db.sqlite ou postgresql://user:pass@host:5432/db). |
| query | string | **Oui** | — | La requÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªte SQL SELECT ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  exÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cuter. |
| destination | string | **Oui** | — | Le fichier de sortie destination (.csv ou .json). |

## db.upsert
_Upsert (mise ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  jour ou insertion) idempotent des lignes d'un fichier dans une table SQL sur clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©s primaires de conflit._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | ChaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â®ne de connexion de la base de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es (ex: sqlite://db.sqlite). |
| table_name | string | **Oui** | — | Le nom de la table cible. |
| source | string | **Oui** | — | Le chemin du fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source (.csv ou .json). |
| keys | string | **Oui** | — | ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©(s) primaire(s) pour dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tecter les doublons et faire la mise ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  jour, sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©parÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es par virgules (ex: id). |
| schema_drift | boolean | Non | False | Activer la dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rive de schÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ma automatique pour ajouter les colonnes manquantes dans la base. |

## flow.report
_GÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨re un rapport texte depuis le contexte d'exÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cution du flux (${STEPS.N.STATUS}, ${FLOW.TOTAL_DURATION_MS}, etc.)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| template | string | **Oui** | — | Template texte avec placeholders ${STEPS.N.STATUS}, ${FLOW.*}, etc. |
| destination | string | **Oui** | — | Fichier de sortie du rapport. |

## google.sheets_read
_Extrait des donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es depuis Google Sheets vers un fichier local CSV._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| credentials | string | **Oui** | — | Chemin vers le fichier JSON de credentials Google Service Account. |
| spreadsheet_id | string | **Oui** | — | L'identifiant du spreadsheet Google Sheets. |
| worksheet_title | string | Non | — | Le nom de l'onglet/feuille ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  lire (optionnel, lit la premiÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨re feuille si vide). |
| local_path | string | **Oui** | — | Chemin local oÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¹ sauvegarder les donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es extraites en CSV. |

## google.sheets_write
_ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â°crit des donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es depuis un fichier local CSV vers Google Sheets._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| credentials | string | **Oui** | — | Chemin vers le fichier JSON de credentials Google Service Account. |
| spreadsheet_id | string | **Oui** | — | L'identifiant du spreadsheet Google Sheets. |
| worksheet_title | string | Non | — | Le nom de l'onglet/feuille cible (optionnel). |
| local_path | string | **Oui** | — | Chemin local du fichier CSV ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  importer. |
| clear_sheet | boolean | Non | True | Vider la feuille avant d'ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©crire les nouvelles donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es. |

## io.copy
_Copie un flux de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es ou un fichier local._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier source. |
| destination | string | **Oui** | — | Le chemin de destination. |
| mode | string | Non | binary | Mode de copie: text ou binary. Valeurs: binary, text |
| conflict | string | Non | overwrite | Mode de rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©solution si le fichier de destination existe. Valeurs: overwrite, skip, newer |

## io.delete
_Supprime un fichier ou un dossier local, avec option de mise ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  la corbeille._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| path | string | **Oui** | — | Le chemin du fichier ou dossier ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  supprimer. |
| secure | string | Non | trash | Mode de suppression: trash (corbeille locale .trash) ou permanent (dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©finitive). Valeurs: trash, permanent |
| retention_days | integer | Non | — | Si secure est trash, nettoie automatiquement les fichiers de la corbeille datant de plus de N jours. |

## io.metadata
_Lit les mÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tadonnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es de base d'un fichier ou d'un dossier._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| path | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier ou dossier. |

## io.move
_DÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©place ou renomme un fichier local._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin du fichier ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©placer ou renommer. |
| destination | string | **Oui** | — | Le chemin cible de destination. |
| conflict | string | Non | overwrite | Mode de rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©solution si le fichier de destination existe. Valeurs: overwrite, skip, newer |

## io.read_file
_Lit un fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es (CSV, JSON, XLSX, Parquet) et le met ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  disposition des ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tapes suivantes._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| source | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  lire. |
| destination | string | Non | — | Le chemin oÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¹ copier/rendre les donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es disponibles (auto-gÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© si vide). |
| format | string | Non | auto | Format du fichier source (auto = dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©duit de l'extension). Valeurs: csv, json, xlsx, parquet, auto |

## io.write_file
_CrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e ou ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©crase un fichier local avec le contenu textuel spÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cifiÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| path | string | **Oui** | — | Le chemin d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s au fichier ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  crÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©er/ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©crire. |
| content | string | **Oui** | — | Le contenu textuel ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©crire dans le fichier. |

## mongodb.find
_Extrait des documents depuis une collection MongoDB et les sauvegarde au format JSON._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | URI de connexion MongoDB (ex: mongodb://localhost:27017). |
| database | string | **Oui** | — | Nom de la base de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es. |
| collection | string | **Oui** | — | Nom de la collection. |
| filter | string | Non | — | ChaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â®ne JSON reprÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©sentant le filtre de recherche (par dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©faut {}). |
| projection | string | Non | — | ChaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â®ne JSON reprÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©sentant la projection des champs. |
| destination | string | **Oui** | — | Fichier JSON de destination. |

## mongodb.insert
_Importe les donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es d'un fichier (CSV ou JSON) dans une collection MongoDB._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| connection_string | string | **Oui** | — | URI de connexion MongoDB. |
| database | string | **Oui** | — | Nom de la base de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es. |
| collection | string | **Oui** | — | Nom de la collection. |
| source | string | **Oui** | — | Le chemin du fichier de donnÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©es source (.csv ou .json). |
| mode | string | Non | insert | Mode d'insertion : insert (ajout simple) ou replace (vide la collection avant insertion). Valeurs: insert, replace |

## net.download
_TÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©charge un fichier depuis une URL HTTP/HTTPS._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| url | string | **Oui** | — | L'URL HTTP ou HTTPS du fichier ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©charger. |
| destination | string | **Oui** | — | Le chemin local oÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¹ enregistrer le fichier tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©chargÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©. |

## net.ftp_download
_TÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©charge un fichier depuis un serveur FTP._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| host | string | **Oui** | — | L'adresse IP ou nom d'hÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â´te du serveur FTP. |
| port | string | Non | 21 | Le port du serveur FTP. |
| user | string | **Oui** | — | L'identifiant de connexion FTP. |
| password | string | **Oui** | — | Le mot de passe de connexion FTP. |
| remote_path | string | **Oui** | — | Le chemin du fichier sur le serveur FTP (ex: /path/to/file.csv). |
| local_path | string | **Oui** | — | Le chemin local oÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¹ enregistrer le fichier tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©chargÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©. |

## net.ftp_download_filtered
_TÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©charge sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lectivement des fichiers depuis FTP selon l'ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ge et la taille (UTC)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| host | string | **Oui** | — | HÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â´te du serveur FTP. |
| port | string | Non | 21 | Port FTP. |
| user | string | **Oui** | — | Identifiant FTP. |
| password | string | **Oui** | — | Mot de passe FTP. |
| remote_dir | string | **Oui** | — | Dossier distant contenant les fichiers. |
| local_dir | string | **Oui** | — | Dossier local de destination. |
| max_age_hours | string | Non | — | Optionnel: ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ge maximal des fichiers en heures (ex: '24' pour modifier dans les derniÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨res 24h) |
| min_age_hours | string | Non | — | Optionnel: ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ge minimal / anciennetÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© en heures (ex: '72' pour exiger 3 jours d'anciennetÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©) |
| min_size_mb | string | Non | — | Optionnel: taille minimale en Mo (ex: '0.1') |
| max_size_mb | string | Non | — | Optionnel: taille maximale en Mo (ex: '50') |

## net.ftp_upload
_TÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©verse un fichier local vers un serveur FTP._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| host | string | **Oui** | — | L'adresse IP ou nom d'hÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â´te du serveur FTP. |
| port | string | Non | 21 | Le port du serveur FTP. |
| user | string | **Oui** | — | L'identifiant de connexion FTP. |
| password | string | **Oui** | — | Le mot de passe de connexion FTP. |
| remote_path | string | **Oui** | — | Le chemin cible sur le serveur FTP (ex: /uploads/file.csv). |
| local_path | string | **Oui** | — | Le chemin du fichier local ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©verser. |

## net.http_request
_ExÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cute une requÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªte HTTP (GET, POST, etc.) avec support d'en-tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªtes, ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©criture optionnelle vers un fichier de destination, ou extraction regex du corps de la rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ponse._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| url | string | **Oui** | — | L'URL de la requÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªte. |
| method | string | Non | GET | MÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©thode HTTP ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  utiliser. Valeurs: GET, POST, PUT, DELETE |
| destination | string | Non | — | Chemin de fichier local optionnel pour enregistrer la rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ponse brute. |
| headers | string | Non | — | En-tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªtes HTTP au format JSON. |
| body | string | Non | — | Corps optionnel de la requÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªte. |
| extract_regex | string | Non | — | Regex optionnelle pour extraire des ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©ments du corps (ex: liens d'images). |
| extract_destination | string | Non | — | Fichier JSON optionnel pour sauvegarder les correspondances de la regex (tableau). |

## net.notify
_Envoie une alerte de notification par Email (SMTP) ou par Webhook (HTTP POST)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| type | string | **Oui** | — | Le type de notification (email ou webhook). Valeurs: email, webhook |
| smtp_host | string | Non | localhost | L'adresse du serveur SMTP (requis pour email). |
| smtp_port | string | Non | 25 | Le port du serveur SMTP (requis pour email). |
| smtp_user | string | Non | — | L'identifiant du serveur SMTP (optionnel). |
| smtp_pass | string | Non | — | Le mot de passe du serveur SMTP (optionnel). |
| to | string | Non | — | L'adresse email du destinataire (requis pour email). |
| subject | string | Non | ETL Job Notification | Le sujet du mail (optionnel). |
| url | string | Non | — | L'URL de destination du Webhook (requis pour webhook). |
| message | string | **Oui** | — | Le corps du message ou de la payload. |
| attachment | string | Non | — | Chemin d'un fichier ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  joindre (ex: rÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©sultat d'une ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©tape prÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©dente). |

## net.sftp_download
_TÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©charge un fichier depuis un serveur SFTP sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©curisÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© (SSH)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| host | string | **Oui** | — | L'adresse IP ou nom d'hÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â´te du serveur SFTP. |
| port | string | Non | 22 | Le port SSH/SFTP (dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©faut 22). |
| user | string | **Oui** | — | L'identifiant de connexion SSH. |
| password | string | Non | — | Optionnel : Le mot de passe de connexion SSH (requis si aucune clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© privÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e n'est fournie). |
| key_path | string | Non | — | Optionnel : Le chemin local vers le fichier de clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© privÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e SSH (ex: ~/.ssh/id_rsa). |
| key_passphrase | string | Non | — | Optionnel : Le mot de passe/passphrase dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©verrouillant la clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© privÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e SSH si nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cessaire. |
| remote_path | string | **Oui** | — | Le chemin du fichier distant sur le serveur SFTP. |
| local_path | string | **Oui** | — | Le chemin local de destination pour enregistrer le fichier. |

## net.sftp_download_filtered
_TÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©charge sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lectivement des fichiers depuis SFTP selon l'ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ge et la taille (UTC)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| host | string | **Oui** | — | HÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â´te du serveur SFTP. |
| port | string | Non | 22 | Port SSH/SFTP. |
| user | string | **Oui** | — | Identifiant SSH. |
| password | string | Non | — | Mot de passe SSH (ou clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©). |
| key_path | string | Non | — | Optionnel: chemin clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© privÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e SSH. |
| key_passphrase | string | Non | — | Optionnel: passphrase de clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© privÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e. |
| remote_dir | string | **Oui** | — | Dossier distant contenant les fichiers. |
| local_dir | string | **Oui** | — | Dossier local de destination. |
| max_age_hours | string | Non | — | Optionnel: ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ge maximal des fichiers en heures (ex: '24') |
| min_age_hours | string | Non | — | Optionnel: ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ge minimal / anciennetÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© en heures (ex: '72') |
| min_size_mb | string | Non | — | Optionnel: taille minimale en Mo (ex: '0.1') |
| max_size_mb | string | Non | — | Optionnel: taille maximale en Mo (ex: '50') |

## net.sftp_upload
_TÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©verse un fichier local vers un serveur SFTP sÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©curisÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© (SSH)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| host | string | **Oui** | — | L'adresse IP ou nom d'hÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â´te du serveur SFTP. |
| port | string | Non | 22 | Le port SSH/SFTP (dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©faut 22). |
| user | string | **Oui** | — | L'identifiant de connexion SSH. |
| password | string | Non | — | Optionnel : Le mot de passe de connexion SSH (requis si aucune clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© privÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e n'est fournie). |
| key_path | string | Non | — | Optionnel : Le chemin local vers le fichier de clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© privÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e SSH (ex: ~/.ssh/id_rsa). |
| key_passphrase | string | Non | — | Optionnel : Le mot de passe/passphrase dÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©verrouillant la clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© privÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©e SSH si nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cessaire. |
| remote_path | string | **Oui** | — | Le chemin de destination sur le serveur SFTP. |
| local_path | string | **Oui** | — | Le chemin du fichier local ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©verser. |

## net.upload
_TÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©verse un fichier local vers un serveur distant (HTTP/HTTPS)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| file_path | string | **Oui** | — | Le chemin du fichier local ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©verser. |
| url | string | **Oui** | — | L'URL HTTP ou HTTPS de destination. |
| method | string | Non | POST | MÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©thode HTTP ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  utiliser. Valeurs: POST, PUT |
| headers | string | Non | — | En-tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªtes additionnels au format JSON (ex: pour l'authentification). |

## s3.download
_TÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©charge un objet depuis un bucket compatible S3 vers le systÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨me de fichiers local._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| bucket | string | **Oui** | — | Nom du bucket S3. |
| object_key | string | **Oui** | — | ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© de l'objet dans S3. |
| destination | string | **Oui** | — | Chemin local oÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¹ enregistrer l'objet tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©chargÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©. |
| aws_access_key_id | string | **Oui** | — | ID de clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s AWS / MinIO. |
| aws_secret_access_key | string | **Oui** | — | ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s secrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨te AWS / MinIO. |
| region | string | Non | us-east-1 | RÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©gion S3 (ex: us-east-1). |
| endpoint | string | Non | — | Endpoint URL personnalisÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© optionnel (nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cessaire pour MinIO local, ex: http://localhost:9000). |

## s3.upload
_TÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©verse un fichier local vers un bucket compatible S3 (AWS, MinIO, etc.)._

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| bucket | string | **Oui** | — | Nom du bucket S3. |
| file_path | string | **Oui** | — | Chemin du fichier local ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  tÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©lÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©verser. |
| object_key | string | **Oui** | — | ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© sous laquelle enregistrer l'objet dans S3. |
| aws_access_key_id | string | **Oui** | — | ID de clÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s AWS / MinIO. |
| aws_secret_access_key | string | **Oui** | — | ClÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© d'accÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨s secrÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¨te AWS / MinIO. |
| region | string | Non | us-east-1 | RÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©gion S3 (ex: us-east-1). |
| endpoint | string | Non | — | Endpoint URL personnalisÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â© optionnel (nÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â©cessaire pour MinIO local, ex: http://localhost:9000). |
