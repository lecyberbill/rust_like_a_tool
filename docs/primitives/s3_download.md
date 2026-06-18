# s3.download

_TÃ©lÃ©charge un objet depuis un bucket compatible S3 vers le systÃ¨me de fichiers local._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| bucket | string | **Oui** | — | Nom du bucket S3. |
| object_key | string | **Oui** | — | ClÃ© de l'objet dans S3. |
| destination | string | **Oui** | — | Chemin local oÃ¹ enregistrer l'objet tÃ©lÃ©chargÃ©. |
| aws_access_key_id | string | **Oui** | — | ID de clÃ© d'accÃ¨s AWS / MinIO. |
| aws_secret_access_key | string | **Oui** | — | ClÃ© d'accÃ¨s secrÃ¨te AWS / MinIO. |
| region | string | Non | us-east-1 | RÃ©gion S3 (ex: us-east-1). |
| endpoint | string | Non | — | Endpoint URL personnalisÃ© optionnel (nÃ©cessaire pour MinIO local, ex: http://localhost:9000). |
