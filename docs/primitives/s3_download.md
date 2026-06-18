# s3.download

_Télécharge un objet depuis un bucket compatible S3 vers le système de fichiers local._

## Parametres

| Parametre | Type | Requis | Defaut | Description |
|-----------|------|--------|--------|-------------|
| bucket | string | **Oui** | — | Nom du bucket S3. |
| object_key | string | **Oui** | — | Clé de l'objet dans S3. |
| destination | string | **Oui** | — | Chemin local où enregistrer l'objet téléchargé. |
| aws_access_key_id | string | **Oui** | — | ID de clé d'accès AWS / MinIO. |
| aws_secret_access_key | string | **Oui** | — | Clé d'accès secrète AWS / MinIO. |
| region | string | Non | us-east-1 | Région S3 (ex: us-east-1). |
| endpoint | string | Non | — | Endpoint URL personnalisé optionnel (nécessaire pour MinIO local, ex: http://localhost:9000). |
