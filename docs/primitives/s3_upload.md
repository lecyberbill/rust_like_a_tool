# s3.upload

_TÃ©lÃ©verse un fichier local vers un bucket compatible S3 (AWS, MinIO, etc.)._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| bucket | string | **Oui** | — | Nom du bucket S3. |
| file_path | string | **Oui** | — | Chemin du fichier local Ã  tÃ©lÃ©verser. |
| object_key | string | **Oui** | — | ClÃ© sous laquelle enregistrer l'objet dans S3. |
| aws_access_key_id | string | **Oui** | — | ID de clÃ© d'accÃ¨s AWS / MinIO. |
| aws_secret_access_key | string | **Oui** | — | ClÃ© d'accÃ¨s secrÃ¨te AWS / MinIO. |
| region | string | Non | us-east-1 | RÃ©gion S3 (ex: us-east-1). |
| endpoint | string | Non | — | Endpoint URL personnalisÃ© optionnel (nÃ©cessaire pour MinIO local, ex: http://localhost:9000). |
