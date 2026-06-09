// [WFGY] Zone: SAFE | λ: 0.2 | Action: Rust s3_connector.rs implementation
use crate::MuscleError;
use s3::bucket::Bucket;
use s3::creds::Credentials;
use s3::region::Region;
use std::fs::File;
use std::io::Read;
use std::path::Path;

pub fn upload_to_s3(
    bucket_name: &str,
    file_path: &str,
    object_key: &str,
    access_key: &str,
    secret_key: &str,
    region_str: &str,
    endpoint: Option<&str>,
) -> Result<(), MuscleError> {
    let path = Path::new(file_path);
    if !path.exists() {
        return Err(MuscleError::SourceNotFound(format!(
            "Local file '{}' to upload not found.",
            file_path
        )));
    }

    let mut file = File::open(path)
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to open file: {}", e)))?;
    let mut contents = Vec::new();
    file.read_to_end(&mut contents)
        .map_err(|e| MuscleError::Generic(format!("Failed to read file contents: {}", e)))?;

    let credentials = Credentials::new(Some(access_key), Some(secret_key), None, None, None)
        .map_err(|e| MuscleError::Generic(format!("Invalid S3 credentials: {}", e)))?;

    let region = if let Some(ep) = endpoint {
        Region::Custom {
            region: region_str.to_string(),
            endpoint: ep.to_string(),
        }
    } else {
        region_str.parse::<Region>().map_err(|_| {
            MuscleError::Generic(format!("Failed to parse S3 region: {}", region_str))
        })?
    };

    let bucket = Bucket::new(bucket_name, region.clone(), credentials.clone())
        .map_err(|e| MuscleError::Generic(format!("Failed to initialize bucket context: {}", e)))?;

    // Enable path-style for MinIO if custom endpoint is used
    let bucket = if endpoint.is_some() {
        bucket.with_path_style()
    } else {
        bucket
    };

    println!(
        "[RUST S3] Uploading '{}' to bucket '{}' as '{}'...",
        file_path, bucket_name, object_key
    );

    // We try block_on for async rust-s3 call inside blocking context
    let rt = tokio::runtime::Runtime::new()
        .map_err(|e| MuscleError::Generic(format!("Failed to start tokio runtime: {}", e)))?;

    rt.block_on(async {
        // Auto-create bucket using static method with path style (required for custom endpoints like MinIO)
        let create_res = Bucket::create_with_path_style(
            bucket_name,
            region.clone(),
            credentials.clone(),
            s3::bucket_ops::BucketConfiguration::default(),
        )
        .await;

        if let Err(e) = create_res {
            println!("[RUST S3] Create bucket error: {}", e);
        } else if let Ok(res) = create_res {
            println!("[RUST S3] Create bucket status code: {}", res.response_code);
        }

        bucket
            .put_object(object_key, &contents)
            .await
            .map_err(|e| MuscleError::NetworkError(format!("Failed to upload object: {}", e)))
    })?;

    println!("SUCCESS: Uploaded '{}' to S3", file_path);
    Ok(())
}

pub fn download_from_s3(
    bucket_name: &str,
    object_key: &str,
    destination: &str,
    access_key: &str,
    secret_key: &str,
    region_str: &str,
    endpoint: Option<&str>,
) -> Result<(), MuscleError> {
    let credentials = Credentials::new(Some(access_key), Some(secret_key), None, None, None)
        .map_err(|e| MuscleError::Generic(format!("Invalid S3 credentials: {}", e)))?;

    let region = if let Some(ep) = endpoint {
        Region::Custom {
            region: region_str.to_string(),
            endpoint: ep.to_string(),
        }
    } else {
        region_str.parse::<Region>().map_err(|_| {
            MuscleError::Generic(format!("Failed to parse S3 region: {}", region_str))
        })?
    };

    let bucket = Bucket::new(bucket_name, region, credentials)
        .map_err(|e| MuscleError::Generic(format!("Failed to initialize bucket context: {}", e)))?;

    let bucket = if endpoint.is_some() {
        bucket.with_path_style()
    } else {
        bucket
    };

    println!(
        "[RUST S3] Downloading '{}' from bucket '{}' to '{}'...",
        object_key, bucket_name, destination
    );

    let rt = tokio::runtime::Runtime::new()
        .map_err(|e| MuscleError::Generic(format!("Failed to start tokio runtime: {}", e)))?;

    let response_data = rt.block_on(async {
        let res = bucket.get_object(object_key).await.map_err(|e| {
            MuscleError::NetworkError(format!("Failed to get object from S3: {}", e))
        })?;
        Ok::<Vec<u8>, MuscleError>(res.bytes().to_vec())
    })?;

    let dest_path = Path::new(destination);
    if let Some(parent) = dest_path.parent() {
        if !parent.exists() {
            std::fs::create_dir_all(parent).map_err(|e| {
                MuscleError::DestDirCreation(format!(
                    "Failed to create destination directory structure: {}",
                    e
                ))
            })?;
        }
    }

    std::fs::write(dest_path, response_data).map_err(|e| {
        MuscleError::PermissionDenied(format!(
            "Failed to write downloaded data to destination file: {}",
            e
        ))
    })?;

    println!("SUCCESS: Downloaded object from S3 to '{}'", destination);
    Ok(())
}
