# s3.upload

_Téléverse un fichier local vers un bucket compatible S3 (AWS, MinIO, etc.)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| bucket | string | **Oui** | — | Nom du bucket S3. |
| file_path | string | **Oui** | — | Chemin du fichier local à téléverser. |
| object_key | string | **Oui** | — | Clé sous laquelle enregistrer l'objet dans S3. |
| aws_access_key_id | string | **Oui** | — | ID de clé d'accès AWS / MinIO. |
| aws_secret_access_key | string | **Oui** | — | Clé d'accès secrète AWS / MinIO. |
| region | string | Non | us-east-1 | Région S3 (ex: us-east-1). |
| endpoint | string | Non | — | Endpoint URL personnalisé optionnel (nécessaire pour MinIO local, ex: http://localhost:9000). |
