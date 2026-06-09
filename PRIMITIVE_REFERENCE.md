# PRIMITIVE_REFERENCE.md — Documentation des Nœuds

## Catalogue des Primitives ETL

Ce document référence les **54 primitives** disponibles dans l'orchestrateur ETL modulaire (WFGY-Core V3).
Chaque primitive est documentée avec sa description, ses paramètres, et des notes d'utilisation.

---
## 📁 I/O (Fichiers)

Opérations de base sur les fichiers : copie, déplacement, suppression, métadonnées, écriture, compression ZIP.

### `data.unzip`

**Description :** Décompresse une archive ZIP dans un dossier de destination.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination` | `string` | **Oui** | — | Dossier cible pour extraire le contenu. |
| `source` | `string` | **Oui** | — | Chemin de l'archive ZIP source. |

### `data.zip`

**Description :** Compresse un dossier ou un fichier dans une archive ZIP.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination` | `string` | **Oui** | — | Chemin de l'archive ZIP destination à générer. |
| `source` | `string` | **Oui** | — | Chemin du fichier ou dossier source à compresser. |

### `io.copy`

**Description :** Copie un flux de données ou un fichier local.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `conflict` | `string` | Non | `overwrite` | Mode de résolution si le fichier de destination existe. Valeurs autorisées : overwrite, skip, newer |
| `destination` | `string` | **Oui** | — | Le chemin de destination. |
| `mode` | `string` | Non | `binary` | Mode de copie: text ou binary. Valeurs autorisées : binary, text |
| `source` | `string` | **Oui** | — | Le chemin d'accès au fichier source. |

### `io.delete`

**Description :** Supprime un fichier ou un dossier local, avec option de mise à la corbeille.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `path` | `string` | **Oui** | — | Le chemin du fichier ou dossier à supprimer. |
| `retention_days` | `integer` | Non | — | Si secure est trash, nettoie automatiquement les fichiers de la corbeille datant de plus de N jours. |
| `secure` | `string` | Non | `trash` | Mode de suppression: trash (corbeille locale .trash) ou permanent (définitive). Valeurs autorisées : trash, permanent |

### `io.metadata`

**Description :** Lit les métadonnées de base d'un fichier ou d'un dossier.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `path` | `string` | **Oui** | — | Le chemin d'accès au fichier ou dossier. |

### `io.move`

**Description :** Déplace ou renomme un fichier local.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `conflict` | `string` | Non | `overwrite` | Mode de résolution si le fichier de destination existe. Valeurs autorisées : overwrite, skip, newer |
| `destination` | `string` | **Oui** | — | Le chemin cible de destination. |
| `source` | `string` | **Oui** | — | Le chemin du fichier à déplacer ou renommer. |

### `io.write_file`

**Description :** Crée ou écrase un fichier local avec le contenu textuel spécifié.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `content` | `string` | **Oui** | — | Le contenu textuel à écrire dans le fichier. |
| `path` | `string` | **Oui** | — | Le chemin d'accès au fichier à créer/écrire. |

---
## 📁 Réseau & Services

Transferts réseau (HTTP, FTP, SFTP), notifications SMTP/Webhook, intégrations Google Sheets et stockage S3.

### `net.download`

**Description :** Télécharge un fichier depuis une URL HTTP/HTTPS.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination` | `string` | **Oui** | — | Le chemin local où enregistrer le fichier téléchargé. |
| `url` | `string` | **Oui** | — | L'URL HTTP ou HTTPS du fichier à télécharger. |

### `net.ftp_download`

**Description :** Télécharge un fichier depuis un serveur FTP.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `host` | `string` | **Oui** | — | L'adresse IP ou nom d'hôte du serveur FTP. |
| `local_path` | `string` | **Oui** | — | Le chemin local où enregistrer le fichier téléchargé. |
| `password` | `string` | **Oui** | — | Le mot de passe de connexion FTP. |
| `port` | `string` | Non | `21` | Le port du serveur FTP. |
| `remote_path` | `string` | **Oui** | — | Le chemin du fichier sur le serveur FTP (ex: /path/to/file.csv). |
| `user` | `string` | **Oui** | — | L'identifiant de connexion FTP. |

### `net.ftp_download_filtered`

**Description :** Télécharge sélectivement des fichiers depuis FTP selon l'âge et la taille (UTC).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `host` | `string` | **Oui** | — | Hôte du serveur FTP. |
| `local_dir` | `string` | **Oui** | — | Dossier local de destination. |
| `max_age_hours` | `string` | Non | — | Optionnel: âge maximal des fichiers en heures (ex: '24' pour modifier dans les dernières 24h) |
| `max_size_mb` | `string` | Non | — | Optionnel: taille maximale en Mo (ex: '50') |
| `min_age_hours` | `string` | Non | — | Optionnel: âge minimal / ancienneté en heures (ex: '72' pour exiger 3 jours d'ancienneté) |
| `min_size_mb` | `string` | Non | — | Optionnel: taille minimale en Mo (ex: '0.1') |
| `password` | `string` | **Oui** | — | Mot de passe FTP. |
| `port` | `string` | Non | `21` | Port FTP. |
| `remote_dir` | `string` | **Oui** | — | Dossier distant contenant les fichiers. |
| `user` | `string` | **Oui** | — | Identifiant FTP. |

### `net.ftp_upload`

**Description :** Téléverse un fichier local vers un serveur FTP.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `host` | `string` | **Oui** | — | L'adresse IP ou nom d'hôte du serveur FTP. |
| `local_path` | `string` | **Oui** | — | Le chemin du fichier local à téléverser. |
| `password` | `string` | **Oui** | — | Le mot de passe de connexion FTP. |
| `port` | `string` | Non | `21` | Le port du serveur FTP. |
| `remote_path` | `string` | **Oui** | — | Le chemin cible sur le serveur FTP (ex: /uploads/file.csv). |
| `user` | `string` | **Oui** | — | L'identifiant de connexion FTP. |

### `net.http_request`

**Description :** Exécute une requête HTTP (GET, POST, etc.) avec support d'en-têtes, écriture optionnelle vers un fichier de destination, ou extraction regex du corps de la réponse.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `body` | `string` | Non | — | Corps optionnel de la requête. |
| `destination` | `string` | Non | — | Chemin de fichier local optionnel pour enregistrer la réponse brute. |
| `extract_destination` | `string` | Non | — | Fichier JSON optionnel pour sauvegarder les correspondances de la regex (tableau). |
| `extract_regex` | `string` | Non | — | Regex optionnelle pour extraire des éléments du corps (ex: liens d'images). |
| `headers` | `string` | Non | — | En-têtes HTTP au format JSON. |
| `method` | `string` | Non | `GET` | Méthode HTTP à utiliser. Valeurs autorisées : GET, POST, PUT, DELETE |
| `url` | `string` | **Oui** | — | L'URL de la requête. |

### `net.notify`

**Description :** Envoie une alerte de notification par Email (SMTP) ou par Webhook (HTTP POST).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `message` | `string` | **Oui** | — | Le corps du message ou de la payload. |
| `smtp_host` | `string` | Non | `localhost` | L'adresse du serveur SMTP (requis pour email). |
| `smtp_pass` | `string` | Non | — | Le mot de passe du serveur SMTP (optionnel). |
| `smtp_port` | `string` | Non | `25` | Le port du serveur SMTP (requis pour email). |
| `smtp_user` | `string` | Non | — | L'identifiant du serveur SMTP (optionnel). |
| `subject` | `string` | Non | `ETL Job Notification` | Le sujet du mail (optionnel). |
| `to` | `string` | Non | — | L'adresse email du destinataire (requis pour email). |
| `type` | `string` | **Oui** | — | Le type de notification (email ou webhook). Valeurs autorisées : email, webhook |
| `url` | `string` | Non | — | L'URL de destination du Webhook (requis pour webhook). |

### `net.sftp_download`

**Description :** Télécharge un fichier depuis un serveur SFTP sécurisé (SSH).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `host` | `string` | **Oui** | — | L'adresse IP ou nom d'hôte du serveur SFTP. |
| `key_passphrase` | `string` | Non | — | Optionnel : Le mot de passe/passphrase déverrouillant la clé privée SSH si nécessaire. |
| `key_path` | `string` | Non | — | Optionnel : Le chemin local vers le fichier de clé privée SSH (ex: ~/.ssh/id_rsa). |
| `local_path` | `string` | **Oui** | — | Le chemin local de destination pour enregistrer le fichier. |
| `password` | `string` | Non | — | Optionnel : Le mot de passe de connexion SSH (requis si aucune clé privée n'est fournie). |
| `port` | `string` | Non | `22` | Le port SSH/SFTP (défaut 22). |
| `remote_path` | `string` | **Oui** | — | Le chemin du fichier distant sur le serveur SFTP. |
| `user` | `string` | **Oui** | — | L'identifiant de connexion SSH. |

### `net.sftp_download_filtered`

**Description :** Télécharge sélectivement des fichiers depuis SFTP selon l'âge et la taille (UTC).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `host` | `string` | **Oui** | — | Hôte du serveur SFTP. |
| `key_passphrase` | `string` | Non | — | Optionnel: passphrase de clé privée. |
| `key_path` | `string` | Non | — | Optionnel: chemin clé privée SSH. |
| `local_dir` | `string` | **Oui** | — | Dossier local de destination. |
| `max_age_hours` | `string` | Non | — | Optionnel: âge maximal des fichiers en heures (ex: '24') |
| `max_size_mb` | `string` | Non | — | Optionnel: taille maximale en Mo (ex: '50') |
| `min_age_hours` | `string` | Non | — | Optionnel: âge minimal / ancienneté en heures (ex: '72') |
| `min_size_mb` | `string` | Non | — | Optionnel: taille minimale en Mo (ex: '0.1') |
| `password` | `string` | Non | — | Mot de passe SSH (ou clé). |
| `port` | `string` | Non | `22` | Port SSH/SFTP. |
| `remote_dir` | `string` | **Oui** | — | Dossier distant contenant les fichiers. |
| `user` | `string` | **Oui** | — | Identifiant SSH. |

### `net.sftp_upload`

**Description :** Téléverse un fichier local vers un serveur SFTP sécurisé (SSH).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `host` | `string` | **Oui** | — | L'adresse IP ou nom d'hôte du serveur SFTP. |
| `key_passphrase` | `string` | Non | — | Optionnel : Le mot de passe/passphrase déverrouillant la clé privée SSH si nécessaire. |
| `key_path` | `string` | Non | — | Optionnel : Le chemin local vers le fichier de clé privée SSH (ex: ~/.ssh/id_rsa). |
| `local_path` | `string` | **Oui** | — | Le chemin du fichier local à téléverser. |
| `password` | `string` | Non | — | Optionnel : Le mot de passe de connexion SSH (requis si aucune clé privée n'est fournie). |
| `port` | `string` | Non | `22` | Le port SSH/SFTP (défaut 22). |
| `remote_path` | `string` | **Oui** | — | Le chemin de destination sur le serveur SFTP. |
| `user` | `string` | **Oui** | — | L'identifiant de connexion SSH. |

### `net.upload`

**Description :** Téléverse un fichier local vers un serveur distant (HTTP/HTTPS).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `file_path` | `string` | **Oui** | — | Le chemin du fichier local à téléverser. |
| `headers` | `string` | Non | — | En-têtes additionnels au format JSON (ex: pour l'authentification). |
| `method` | `string` | Non | `POST` | Méthode HTTP à utiliser. Valeurs autorisées : POST, PUT |
| `url` | `string` | **Oui** | — | L'URL HTTP ou HTTPS de destination. |

### `s3.download`

**Description :** Télécharge un objet depuis un bucket compatible S3 vers le système de fichiers local.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `aws_access_key_id` | `string` | **Oui** | — | ID de clé d'accès AWS / MinIO. |
| `aws_secret_access_key` | `string` | **Oui** | — | Clé d'accès secrète AWS / MinIO. |
| `bucket` | `string` | **Oui** | — | Nom du bucket S3. |
| `destination` | `string` | **Oui** | — | Chemin local où enregistrer l'objet téléchargé. |
| `endpoint` | `string` | Non | — | Endpoint URL personnalisé optionnel (nécessaire pour MinIO local, ex: http://localhost:9000). |
| `object_key` | `string` | **Oui** | — | Clé de l'objet dans S3. |
| `region` | `string` | Non | `us-east-1` | Région S3 (ex: us-east-1). |

### `s3.upload`

**Description :** Téléverse un fichier local vers un bucket compatible S3 (AWS, MinIO, etc.).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `aws_access_key_id` | `string` | **Oui** | — | ID de clé d'accès AWS / MinIO. |
| `aws_secret_access_key` | `string` | **Oui** | — | Clé d'accès secrète AWS / MinIO. |
| `bucket` | `string` | **Oui** | — | Nom du bucket S3. |
| `endpoint` | `string` | Non | — | Endpoint URL personnalisé optionnel (nécessaire pour MinIO local, ex: http://localhost:9000). |
| `file_path` | `string` | **Oui** | — | Chemin du fichier local à téléverser. |
| `object_key` | `string` | **Oui** | — | Clé sous laquelle enregistrer l'objet dans S3. |
| `region` | `string` | Non | `us-east-1` | Région S3 (ex: us-east-1). |

---
## 📁 Transformations de données

Filtrage, nettoyage, validation, conversion de formats, typage, anonymisation, pivot, déduplication.

### `data.anonymize`

**Description :** Anonymise et masque les colonnes sensibles (PII) d'un jeu de données.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination` | `string` | **Oui** | — | Le fichier de destination propre. |
| `rules` | `string` | **Oui** | — | Mappings de règles d'anonymisation au format col1:strategy1,col2:strategy2. Stratégies: hash, mask, mask_email, replace. |
| `source` | `string` | **Oui** | — | Le fichier de données source. |

### `data.clean`

**Description :** Nettoie et transforme un jeu de données (CSV, JSON, Parquet). Supporte le tri, le dédoublonnage, la sélection/renommage de colonnes, le traitement des valeurs nulles (fill/drop) et l'ajout de colonnes calculées ou conditionnelles via un compilateur d'expression léger.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `deduplicate` | `boolean` | Non | `False` | Optionnel : Supprimer les lignes doublons si vrai. |
| `deduplicate_on` | `string` | Non | — | Optionnel : Liste de colonnes séparées par des virgules pour le dédoublonnage. |
| `derive_columns` | `string` | Non | — | Optionnel : Création de colonnes calculées ou conditionnelles séparées par des virgules au format col_nouvelle=EXPRESSION. L'expression supporte : 1. Opérateurs mathématiques (+, -, *, /) ex: total = qty * price. 2. Concaténations textuelles (+ et guillemets) ex: nom_complet = prenom + ' ' + nom. 3. Conditions IF-THEN-ELSE avec opérateurs (==, !=, >, >=, <, <=) ex: statut = IF age >= 18 THEN 'adulte' ELSE 'mineur'. |
| `destination` | `string` | **Oui** | — | Le chemin d'accès au fichier de destination propre. |
| `drop_na` | `boolean` | Non | `False` | Optionnel : Supprime toutes les lignes contenant des valeurs nulles/vides. |
| `fill_na` | `string` | Non | — | Optionnel : Valeurs de remplacement pour les nulls au format col1:valeur1,col2:valeur2. |
| `how_join` | `string` | Non | `left` | Optionnel : Le type de jointure relationnelle. Valeurs autorisées : left, inner, outer |
| `left_on` | `string` | Non | — | Optionnel : La colonne clé de jointure du fichier source principal. |
| `rename_columns` | `string` | Non | — | Optionnel : Mappings de renommage au format col_ancienne:col_nouvelle,col2:col2_nouv. |
| `right_on` | `string` | Non | — | Optionnel : La colonne clé de jointure du second fichier. |
| `right_source` | `string` | Non | — | Optionnel : Le chemin du second fichier à joindre. |
| `select_columns` | `string` | Non | — | Optionnel : Liste de colonnes à conserver séparées par des virgules (ex: age,nom_complet). |
| `sort_by` | `string` | Non | — | Optionnel : Nom de la colonne sur laquelle trier. |
| `sort_descending` | `boolean` | Non | `False` | Optionnel : Trier par ordre décroissant si vrai. |
| `source` | `string` | **Oui** | — | Le chemin d'accès au fichier source. |
| `streaming` | `boolean` | Non | `False` | Optionnel : Activer l'exécution en flux (streaming) dans Polars pour optimiser la mémoire RAM. |

### `data.csv_to_json`

**Description :** Convertit un fichier délimité (CSV) en un fichier structuré JSON (tableau d'objets).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `delimiter` | `string` | Non | `,` | Délimiteur de champs (ex: , ou ;). |
| `destination` | `string` | **Oui** | — | Le chemin du fichier JSON de destination. |
| `has_headers` | `boolean` | Non | `True` | Indique si la première ligne contient les clés du dictionnaire JSON. |
| `source` | `string` | **Oui** | — | Le chemin d'accès au fichier CSV source. |

### `data.deduplicate`

**Description :** Supprime les lignes en doublons basées sur des clés spécifiques.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination` | `string` | **Oui** | — | Le fichier de destination nettoyé. |
| `keep` | `string` | Non | `first` | Laquelle des occurrences en doublons conserver: first ou last. Valeurs autorisées : first, last |
| `source` | `string` | **Oui** | — | Le fichier de données source. |
| `subset` | `string` | **Oui** | — | Liste des colonnes de clé de dédoublonnage, séparées par virgules (ex: id,email). |

### `data.delta`

**Description :** Compare deux jeux de données (CSV, JSON, Parquet) sur clés primaires pour calculer les différences incrémentales (upserts, deletes et optionnellement synchronisation complète).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination_delete` | `string` | **Oui** | — | Fichier pour enregistrer les lignes supprimées. |
| `destination_sync` | `string` | Non | — | Optionnel: Fichier pour enregistrer le jeu de données consolidé et entièrement synchronisé. |
| `destination_upsert` | `string` | **Oui** | — | Fichier pour enregistrer les nouvelles lignes et les lignes mises à jour (inserts + updates). |
| `keys` | `string` | **Oui** | — | Nom(s) de la ou des clés primaires séparées par des virgules (ex: id,code). |
| `source` | `string` | **Oui** | — | Le fichier de données source le plus récent. |
| `target` | `string` | **Oui** | — | Le fichier de données cible de référence (historique). |

### `data.filter`

**Description :** Filtre les lignes d'un fichier texte structuré (CSV) selon une règle logique sur une colonne.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `column_index` | `integer` | Non | — | Index 0-based de la colonne à filtrer (utilisé si pas d'en-tête). |
| `column_name` | `string` | Non | — | Nom de la colonne à filtrer (nécessite has_headers=true). |
| `delimiter` | `string` | Non | `,` | Délimiteur de champs (ex: , ou ;). |
| `destination` | `string` | **Oui** | — | Le chemin du fichier de destination filtré. |
| `has_headers` | `boolean` | Non | `False` | Indique si la première ligne du fichier contient les en-têtes. |
| `operator` | `string` | **Oui** | — | Opérateur de comparaison logique. Valeurs autorisées : equals, contains, starts_with, ends_with, regex, greater_than, less_than |
| `source` | `string` | **Oui** | — | Le chemin d'accès au fichier source. |
| `value` | `string` | **Oui** | — | La valeur cible de comparaison. |

### `data.json_to_csv`

**Description :** Convertit un fichier structuré JSON (tableau d'objets) en un fichier délimité CSV.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `delimiter` | `string` | Non | `,` | Délimiteur de champs (ex: , ou ;). |
| `destination` | `string` | **Oui** | — | Le chemin du fichier CSV de destination. |
| `has_headers` | `boolean` | Non | `True` | Indique s'il faut générer la première ligne du fichier CSV avec les clés comme en-têtes. |
| `source` | `string` | **Oui** | — | Le chemin d'accès au fichier JSON source. |

### `data.json_to_xml`

**Description :** Convertit un tableau d'objets JSON ou un CSV en fichier XML structuré.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination` | `string` | **Oui** | — | Le chemin d'accès au fichier XML de destination. |
| `root_element` | `string` | Non | `root` | Nom du nœud XML racine (optionnel). |
| `row_element` | `string` | Non | `row` | Nom du nœud XML pour chaque ligne (optionnel). |
| `source` | `string` | **Oui** | — | Le chemin d'accès au fichier JSON ou CSV source. |

### `data.lookup`

**Description :** Recherche et joint des données depuis un référentiel externe (jointure gauche Polars).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination` | `string` | **Oui** | — | Le fichier de destination enrichi. |
| `lookup_file` | `string` | **Oui** | — | Le fichier dictionnaire / référentiel externe. |
| `lookup_key` | `string` | **Oui** | — | La clé de liaison dans le fichier dictionnaire. |
| `lookup_value` | `string` | **Oui** | — | La colonne du dictionnaire à ramener dans le fichier principal. |
| `source` | `string` | **Oui** | — | Le fichier de données principal (CSV/JSON/Parquet). |
| `source_key` | `string` | **Oui** | — | La clé de liaison dans le fichier principal. |

### `data.pivot`

**Description :** Pivote une table de données du format long au format large (lignes en colonnes).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `aggregate` | `string` | Non | `first` | Fonction d'agrégation à appliquer pour les valeurs. Valeurs autorisées : first, last, sum, mean, min, max, count |
| `destination` | `string` | **Oui** | — | Le fichier de destination propre. |
| `index` | `string` | **Oui** | — | Nom(s) des colonnes d'index de ligne séparés par des virgules (ex: year,country). |
| `on` | `string` | **Oui** | — | Nom de la colonne dont les valeurs distinctes deviendront les en-têtes des nouvelles colonnes. |
| `source` | `string` | **Oui** | — | Le fichier de données source. |
| `values` | `string` | **Oui** | — | Nom de la colonne contenant les valeurs à ventiler dans les nouvelles colonnes. |

### `data.split_out`

**Description :** Éclate les colonnes contenant des listes ou des chaînes sérialisées JSON vers des lignes distinctes (explode).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `column` | `string` | **Oui** | — | Le nom de la colonne à éclater. |
| `delimiter` | `string` | Non | — | Optionnel: Délimiteur de texte pour éclater si ce n'est pas un tableau JSON direct (ex: virgule). |
| `destination` | `string` | **Oui** | — | Le chemin d'accès au fichier de destination propre éclaté. |
| `source` | `string` | **Oui** | — | Le chemin d'accès au fichier source. |

### `data.to_xlsx`

**Description :** Exporte un fichier de données (CSV ou JSON) vers une feuille de calcul Excel (.xlsx).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination` | `string` | **Oui** | — | Le chemin d'accès au fichier Excel (.xlsx) de destination. |
| `sheet_name` | `string` | Non | `Sheet1` | Le nom de l'onglet/feuille de calcul Excel (optionnel). |
| `source` | `string` | **Oui** | — | Le chemin d'accès au fichier source (CSV ou JSON). |

### `data.type_cast`

**Description :** Convertit et formate les colonnes d'un jeu de données selon des types cibles stricts (integer, float, boolean, string, date).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `casts` | `string` | **Oui** | — | Chaîne au format JSON définissant le type des colonnes à convertir (ex: {"id": "int", "price": "float", "date": "date:%Y-%m-%d"}). |
| `destination` | `string` | **Oui** | — | Le fichier de destination propre avec les colonnes typées. |
| `source` | `string` | **Oui** | — | Le fichier de données source. |

### `data.unpivot`

**Description :** Dépivote une table de données du format large au format long (colonnes en lignes).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination` | `string` | **Oui** | — | Le fichier de destination propre. |
| `index` | `string` | **Oui** | — | Nom(s) des colonnes d'identifiants à conserver séparées par des virgules (ex: id,name). |
| `on` | `string` | Non | — | Optionnel: Nom(s) des colonnes de mesures à dépivoter séparées par des virgules. Si vide, toutes les autres colonnes. |
| `source` | `string` | **Oui** | — | Le fichier de données source. |
| `value_name` | `string` | Non | `value` | Nom de la colonne finale contenant les valeurs des mesures (défaut: value). |
| `variable_name` | `string` | Non | `variable` | Nom de la colonne finale contenant les anciens en-têtes (défaut: variable). |

### `data.validate`

**Description :** Valide les lignes d'un jeu de données (CSV, JSON, Parquet) par rapport à des règles d'assertions et sépare les lignes rejetées dans un fichier de quarantaine.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination` | `string` | **Oui** | — | Le chemin du fichier de destination recevant les lignes valides. |
| `quarantine` | `string` | **Oui** | — | Le chemin du fichier de destination recevant les rejets. |
| `rules` | `string` | **Oui** | — | Tableau JSON de règles d'assertions. Ex: [{"column": "age", "operator": ">=", "value": 0}, {"column": "email", "operator": "matches", "value": "^[^@]+@[^@]+\\.[^@]+$"}] |
| `source` | `string` | **Oui** | — | Le chemin du fichier de données source. |
| `streaming` | `boolean` | Non | `False` | Optionnel : Activer l'exécution en flux (streaming) dans Polars pour optimiser la mémoire RAM. |

### `data.xml_to_json`

**Description :** Convertit un fichier XML hiérarchique en fichier JSON standard.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination` | `string` | **Oui** | — | Le chemin du fichier JSON de destination. |
| `source` | `string` | **Oui** | — | Le chemin d'accès au fichier XML source. |

### `data.xml_transform`

**Description :** Applique une transformation structurelle XSLT sur un fichier XML source.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination` | `string` | **Oui** | — | Le chemin d'accès au fichier de sortie transformé. |
| `source` | `string` | **Oui** | — | Le chemin d'accès au fichier XML source. |
| `stylesheet` | `string` | **Oui** | — | Le chemin d'accès au fichier de feuille de style XSLT (.xsl ou .xslt). |

---
## 📁 Bases de Données

Requêtes SQL, insertions, upserts et intégrations MongoDB.

### `db.insert`

**Description :** Importe les données d'un fichier (CSV ou JSON) dans une table de base de données (SQLite, Postgres, MySQL, Snowflake, ODBC).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `connection_string` | `string` | **Oui** | — | Chaîne de connexion de la base de données. |
| `mode` | `string` | Non | `insert` | Mode d'insertion : insert (ajout simple) ou replace (remplacement complet). Valeurs autorisées : insert, replace |
| `schema_drift` | `boolean` | Non | `False` | Activer la dérive de schéma automatique pour ajouter les colonnes manquantes dans la base. |
| `source` | `string` | **Oui** | — | Le chemin du fichier de données source (.csv ou .json). |
| `table_name` | `string` | **Oui** | — | Le nom de la table cible. |

### `db.query`

**Description :** Exécute une requête SQL SELECT sur une base de données (SQLite, Postgres, MySQL, Snowflake, ODBC) et écrit le résultat dans un fichier.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `connection_string` | `string` | **Oui** | — | Chaîne de connexion (ex: sqlite://db.sqlite ou postgresql://user:pass@host:5432/db). |
| `destination` | `string` | **Oui** | — | Le fichier de sortie destination (.csv ou .json). |
| `query` | `string` | **Oui** | — | La requête SQL SELECT à exécuter. |

### `db.upsert`

**Description :** Upsert (mise à jour ou insertion) idempotent des lignes d'un fichier dans une table SQL sur clés primaires de conflit.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `connection_string` | `string` | **Oui** | — | Chaîne de connexion de la base de données (ex: sqlite://db.sqlite). |
| `keys` | `string` | **Oui** | — | Clé(s) primaire(s) pour détecter les doublons et faire la mise à jour, séparées par virgules (ex: id). |
| `schema_drift` | `boolean` | Non | `False` | Activer la dérive de schéma automatique pour ajouter les colonnes manquantes dans la base. |
| `source` | `string` | **Oui** | — | Le chemin du fichier de données source (.csv ou .json). |
| `table_name` | `string` | **Oui** | — | Le nom de la table cible. |

### `mongodb.find`

**Description :** Extrait des documents depuis une collection MongoDB et les sauvegarde au format JSON.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `collection` | `string` | **Oui** | — | Nom de la collection. |
| `connection_string` | `string` | **Oui** | — | URI de connexion MongoDB (ex: mongodb://localhost:27017). |
| `database` | `string` | **Oui** | — | Nom de la base de données. |
| `destination` | `string` | **Oui** | — | Fichier JSON de destination. |
| `filter` | `string` | Non | — | Chaîne JSON représentant le filtre de recherche (par défaut {}). |
| `projection` | `string` | Non | — | Chaîne JSON représentant la projection des champs. |

### `mongodb.insert`

**Description :** Importe les données d'un fichier (CSV ou JSON) dans une collection MongoDB.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `collection` | `string` | **Oui** | — | Nom de la collection. |
| `connection_string` | `string` | **Oui** | — | URI de connexion MongoDB. |
| `database` | `string` | **Oui** | — | Nom de la base de données. |
| `mode` | `string` | Non | `insert` | Mode d'insertion : insert (ajout simple) ou replace (vide la collection avant insertion). Valeurs autorisées : insert, replace |
| `source` | `string` | **Oui** | — | Le chemin du fichier de données source (.csv ou .json). |

---
## 📁 Analytique & Statistiques

Agrégations, métriques statistiques, jointures, segmentation, fusion verticale et partitionnement.

### `data.chunk_cumulative`

**Description :** Découpe séquentiellement un jeu de données en plusieurs fichiers (parts) dès qu'un seuil cumulé sur une colonne est franchi.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `accumulate_column` | `string` | **Oui** | — | Le nom de la colonne numérique sur laquelle faire le cumul. |
| `destination_prefix` | `string` | **Oui** | — | Le préfixe des fichiers créés (ex: outputs/part). |
| `source` | `string` | **Oui** | — | Le fichier de données source. |
| `threshold` | `number` | **Oui** | — | Le seuil d'accumulation pour déclencher la sauvegarde d'un fichier partition. |

### `data.groupby`

**Description :** Groupe les lignes d'un jeu de données (CSV, JSON, Parquet) et calcule des agrégations (somme, moyenne, min, max, count).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `aggregate_column` | `string` | **Oui** | — | Nom de la colonne numérique sur laquelle calculer l'agrégat. |
| `destination` | `string` | **Oui** | — | Fichier de destination pour stocker le résultat de l'agrégation. |
| `groupby_columns` | `string` | **Oui** | — | Noms des colonnes de regroupement séparés par des virgules (ex: status,country). |
| `operation` | `string` | **Oui** | — | Opération d'agrégation à réaliser. Valeurs autorisées : sum, mean, min, max, count |
| `source` | `string` | **Oui** | — | Fichier source (CSV, JSON ou Parquet). |

### `data.join`

**Description :** Réalise une jointure relationnelle entre deux fichiers de données (CSV, JSON, Parquet) et écrit le résultat dans un fichier cible.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination` | `string` | **Oui** | — | Fichier cible pour écrire le résultat de la jointure. |
| `how` | `string` | Non | `inner` | Type de jointure relationnelle. Valeurs autorisées : inner, left, outer |
| `left_on` | `string` | **Oui** | — | Colonne clé dans le fichier de gauche. |
| `left_source` | `string` | **Oui** | — | Fichier de données de gauche (CSV, JSON ou Parquet). |
| `right_on` | `string` | **Oui** | — | Colonne clé dans le fichier de droite. |
| `right_source` | `string` | **Oui** | — | Fichier de données de droite (CSV, JSON ou Parquet). |

### `data.merge`

**Description :** Fusionne verticalement plusieurs fichiers de données (CSV, JSON, Parquet) de structure identique en un unique fichier cible.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `destination` | `string` | **Oui** | — | Le fichier de destination consolidé. |
| `sources` | `string` | **Oui** | — | Liste des chemins de fichiers sources séparés par des virgules (ex: file1.csv,file2.csv). |

### `data.metrics`

**Description :** Calcule une métrique statistique ou textuelle (somme, moyenne, min, max, count, null_count, n_unique, match_regex, non_match_regex) sur une colonne.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `column_name` | `string` | **Oui** | — | Le nom de la colonne cible. |
| `destination_variable` | `string` | **Oui** | — | Le nom de la variable dans l'orchestrateur pour stocker le résultat. |
| `limit_rows` | `integer` | Non | — | Optionnel: limiter les N premières lignes pour le calcul. |
| `operation` | `string` | **Oui** | — | Le type de métrique à calculer. Valeurs autorisées : sum, mean, min, max, count, null_count, n_unique, match_regex, non_match_regex |
| `regex_pattern` | `string` | Non | — | Expression régulière utilisée si l'opération est match_regex ou non_match_regex. |
| `source` | `string` | **Oui** | — | Le fichier de données source (CSV, JSON, Parquet). |

### `data.split`

**Description :** Divise un jeu de données (CSV, JSON, Parquet) en plusieurs fichiers selon les valeurs uniques d'une colonne cible.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `by_column` | `string` | **Oui** | — | Le nom de la colonne sur laquelle effectuer la division. |
| `destination_prefix` | `string` | **Oui** | — | Le préfixe des fichiers créés (ex: outputs/user_split). |
| `source` | `string` | **Oui** | — | Le fichier de données source. |

---
## 📁 Intelligence Artificielle

Traitement NLP via LLM : résumé de texte et extraction d'entités structurées.

### `ai.extract`

**Description :** Extrait des informations structurées (JSON) via LLM depuis une colonne textuelle vers de nouvelles colonnes.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `base_url` | `string` | Non | — | URL de base de l'API LLM locale pour cette étape (optionnel). |
| `column` | `string` | **Oui** | — | Le nom de la colonne de texte source à analyser. |
| `destination` | `string` | **Oui** | — | Le chemin d'accès au fichier de destination propre généré. |
| `model_id` | `string` | Non | — | L'identifiant du modèle LLM à utiliser pour cette étape (optionnel). |
| `model_provider` | `string` | Non | — | Le provider de modèle LLM à utiliser (optionnel). Valeurs autorisées : openai_compatible, gemini |
| `prompt` | `string` | Non | — | Instructions système additionnelles pour guider l'extraction LLM (optionnel). |
| `schema` | `string` | **Oui** | — | Le schéma JSON décrivant les propriétés à extraire (ex: {"properties": {"nom": {"type": "string"}}}). |
| `source` | `string` | **Oui** | — | Le chemin d'accès au fichier de données source (CSV/JSON). |

### `ai.summarize`

**Description :** Génère des résumés concis via LLM d'une colonne textuelle et les écrit dans une colonne cible.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `base_url` | `string` | Non | — | URL de base de l'API LLM locale pour cette étape (optionnel). |
| `column` | `string` | **Oui** | — | Le nom de la colonne de texte source à résumer. |
| `destination` | `string` | **Oui** | — | Le chemin d'accès au fichier de destination propre généré. |
| `model_id` | `string` | Non | — | L'identifiant du modèle LLM à utiliser pour cette étape (optionnel). |
| `model_provider` | `string` | Non | — | Le provider de modèle LLM à utiliser (optionnel). Valeurs autorisées : openai_compatible, gemini |
| `prompt` | `string` | Non | — | Consignes de prompt système pour guider le résumé (optionnel). |
| `source` | `string` | **Oui** | — | Le chemin d'accès au fichier de données source (CSV/JSON). |
| `target_column` | `string` | Non | — | Le nom de la colonne de destination recevant le résumé (optionnel, ex: res_col). |

---
## 📁 Contrôle

Primitives d'orchestration : conditions, boucles, sous-flux, switch et pauses.

### `core.condition`

**Description :** Primitive d'orchestration logique. Évalue une expression conditionnelle et exécute les branches de manière conditionnelle.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `else_steps` | `array` | Non | — | Liste d'étapes facultatives à exécuter si la condition est fausse. |
| `expression` | `string` | **Oui** | — | L'expression logique à évaluer (ex: ${FILE_EXISTS} == true ou ${FILE_SIZE} > 1000). |
| `then_steps` | `array` | **Oui** | — | Liste d'étapes à exécuter si la condition est vraie. |

### `core.loop`

**Description :** Itère l'exécution d'une liste d'étapes sur des variables, des lignes de fichier ou des chemins de fichiers filtrés.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `items_source` | `string` | **Oui** | — | Source des éléments (valeurs séparées par des virgules, chemin d'accès au dossier ou fichier). |
| `loop_over` | `string` | **Oui** | — | Type d'éléments à parcourir. Valeurs autorisées : variables, files, rows |
| `max_age_hours` | `string` | Non | — | Optionnel (pour files) : Âge maximum du fichier en heures (ex: '24' pour les fichiers modifiés dans les dernières 24h). |
| `max_size_mb` | `string` | Non | — | Optionnel (pour files) : Taille maximale du fichier en Mo (ex: '10'). |
| `min_age_hours` | `string` | Non | — | Optionnel (pour files) : Âge minimum / ancienneté en heures (ex: '72' pour exiger au moins 3 jours d'ancienneté). |
| `min_size_mb` | `string` | Non | — | Optionnel (pour files) : Taille minimale du fichier en Mo (ex: '0.5'). |
| `pattern` | `string` | Non | `*` | Optionnel (pour files) : Filtre de motif de glob (ex: *.csv). |
| `steps` | `array` | **Oui** | — | Liste d'étapes enfants à exécuter à chaque itération. |

### `core.sub_flow`

**Description :** Exécute un ensemble d'étapes imbriquées comme sous-graphe dans la recette principale.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `steps` | `array` | **Oui** | — | La liste des étapes imbriquées à exécuter comme sous-flux. |

### `core.switch`

**Description :** Primitive d'orchestration logique. Route l'exécution vers différents sous-graphes selon la valeur d'une clé ou d'un paramètre.

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `cases` | `object` | **Oui** | — | Dictionnaire associant des valeurs de cas à des listes d'étapes d'exécution (ex: {"dev": [...], "prod": [...]}). |
| `value` | `string` | **Oui** | — | La valeur ou variable à tester (ex: ${ENV_MODE} ou ${STATUS}). |

### `core.wait`

**Description :** Met en pause l'exécution du workflow pendant une durée spécifiée (secondes ou HH:MM:SS).

**Paramètres :**

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `duration` | `string` | **Oui** | — | Durée de l'attente. Exemples: '5' (5 secondes), '02:30' (2 min 30 s), '01:00:00' (1 heure). |
