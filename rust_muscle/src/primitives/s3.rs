// [WFGY] Zone: SAFE | λ: 0.1 | Action: S3 upload & download primitives

use crate::MuscleError;
use crate::s3_connector;

pub fn handle_s3_upload(args: &[String]) -> Result<(), MuscleError> {
    let mut bucket = None;
    let mut file_path = None;
    let mut object_key = None;
    let mut aws_access_key_id = None;
    let mut aws_secret_access_key = None;
    let mut region = String::from("us-east-1");
    let mut endpoint = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--bucket" => {
                if i + 1 < args.len() { bucket = Some(&args[i + 1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --bucket".to_string())); }
            }
            "--file-path" | "--file_path" => {
                if i + 1 < args.len() { file_path = Some(&args[i + 1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --file-path".to_string())); }
            }
            "--object-key" | "--object_key" => {
                if i + 1 < args.len() { object_key = Some(&args[i + 1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --object-key".to_string())); }
            }
            "--aws-access-key-id" | "--aws_access_key_id" => {
                if i + 1 < args.len() { aws_access_key_id = Some(&args[i + 1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --aws-access-key-id".to_string())); }
            }
            "--aws-secret-access-key" | "--aws_secret_access_key" => {
                if i + 1 < args.len() { aws_secret_access_key = Some(&args[i + 1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --aws-secret-access-key".to_string())); }
            }
            "--region" => {
                if i + 1 < args.len() { region = args[i + 1].clone(); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --region".to_string())); }
            }
            "--endpoint" => {
                if i + 1 < args.len() { endpoint = Some(&args[i + 1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --endpoint".to_string())); }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let bucket = bucket.ok_or_else(|| MuscleError::Generic("Missing required argument --bucket".to_string()))?;
    let file_path = file_path.ok_or_else(|| MuscleError::Generic("Missing required argument --file-path".to_string()))?;
    let object_key = object_key.ok_or_else(|| MuscleError::Generic("Missing required argument --object-key".to_string()))?;
    let aws_access_key_id = aws_access_key_id.ok_or_else(|| MuscleError::Generic("Missing required argument --aws-access-key-id".to_string()))?;
    let aws_secret_access_key = aws_secret_access_key.ok_or_else(|| MuscleError::Generic("Missing required argument --aws-secret-access-key".to_string()))?;

    s3_connector::upload_to_s3(
        bucket,
        file_path,
        object_key,
        aws_access_key_id,
        aws_secret_access_key,
        &region,
        endpoint.map(|s| s.as_str()),
    )
}

pub fn handle_s3_download(args: &[String]) -> Result<(), MuscleError> {
    let mut bucket = None;
    let mut object_key = None;
    let mut destination = None;
    let mut aws_access_key_id = None;
    let mut aws_secret_access_key = None;
    let mut region = String::from("us-east-1");
    let mut endpoint = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--bucket" => {
                if i + 1 < args.len() { bucket = Some(&args[i + 1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --bucket".to_string())); }
            }
            "--object-key" | "--object_key" => {
                if i + 1 < args.len() { object_key = Some(&args[i + 1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --object-key".to_string())); }
            }
            "--destination" => {
                if i + 1 < args.len() { destination = Some(&args[i + 1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --destination".to_string())); }
            }
            "--aws-access-key-id" | "--aws_access_key_id" => {
                if i + 1 < args.len() { aws_access_key_id = Some(&args[i + 1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --aws-access-key-id".to_string())); }
            }
            "--aws-secret-access-key" | "--aws_secret_access_key" => {
                if i + 1 < args.len() { aws_secret_access_key = Some(&args[i + 1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --aws-secret-access-key".to_string())); }
            }
            "--region" => {
                if i + 1 < args.len() { region = args[i + 1].clone(); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --region".to_string())); }
            }
            "--endpoint" => {
                if i + 1 < args.len() { endpoint = Some(&args[i + 1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --endpoint".to_string())); }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let bucket = bucket.ok_or_else(|| MuscleError::Generic("Missing required argument --bucket".to_string()))?;
    let object_key = object_key.ok_or_else(|| MuscleError::Generic("Missing required argument --object-key".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing required argument --destination".to_string()))?;
    let aws_access_key_id = aws_access_key_id.ok_or_else(|| MuscleError::Generic("Missing required argument --aws-access-key-id".to_string()))?;
    let aws_secret_access_key = aws_secret_access_key.ok_or_else(|| MuscleError::Generic("Missing required argument --aws-secret-access-key".to_string()))?;

    s3_connector::download_from_s3(
        bucket,
        object_key,
        destination,
        aws_access_key_id,
        aws_secret_access_key,
        &region,
        endpoint.map(|s| s.as_str()),
    )
}
