// [WFGY] Zone: SAFE | λ: 0.1 | Action: Network primitives

use std::fs;
use std::path::Path;
use crate::MuscleError;

pub fn handle_net_download(args: &[String]) -> Result<(), MuscleError> {
    let mut url = None;
    let mut destination = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--url" => {
                if i + 1 < args.len() {
                    url = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --url".to_string()));
                }
            }
            "--destination" => {
                if i + 1 < args.len() {
                    destination = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --destination".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let url = url.ok_or_else(|| MuscleError::Generic("Missing required argument --url".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing required argument --destination".to_string()))?;

    download_file(url, destination)
}

fn download_file(url: &str, destination: &str) -> Result<(), MuscleError> {
    let dest_path = Path::new(destination);
    if let Some(parent) = dest_path.parent() {
        if !parent.exists() {
            fs::create_dir_all(parent)
                .map_err(|e| MuscleError::DestDirCreation(format!("Failed to create destination directories: {}", e)))?;
        }
    }

    println!("[RUST] Downloading from '{}'...", url);
    let client = reqwest::blocking::Client::builder()
        .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        .build()
        .map_err(|e| MuscleError::Generic(format!("Failed to build HTTP client: {}", e)))?;

    let mut response = client.get(url)
        .send()
        .map_err(|e| MuscleError::NetworkError(format!("Request failed: {}", e)))?;

    if !response.status().is_success() {
        return Err(MuscleError::NetworkError(format!("Server returned HTTP status: {}", response.status())));
    }

    let mut dest_file = fs::File::create(dest_path)
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to create destination file: {}", e)))?;

    response.copy_to(&mut dest_file)
        .map_err(|e| MuscleError::Generic(format!("Failed to write downloaded data to file: {}", e)))?;

    println!("SUCCESS: Downloaded file from '{}' to '{}'", url, destination);
    Ok(())
}

pub fn handle_net_upload(args: &[String]) -> Result<(), MuscleError> {
    let mut file_path = None;
    let mut url = None;
    let mut method = String::from("POST");
    let mut headers = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--file_path" => {
                if i + 1 < args.len() {
                    file_path = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --file_path".to_string()));
                }
            }
            "--url" => {
                if i + 1 < args.len() {
                    url = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --url".to_string()));
                }
            }
            "--method" => {
                if i + 1 < args.len() {
                    method = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --method".to_string()));
                }
            }
            "--headers" => {
                if i + 1 < args.len() {
                    headers = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --headers".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let file_path = file_path.ok_or_else(|| MuscleError::Generic("Missing required argument --file_path".to_string()))?;
    let url = url.ok_or_else(|| MuscleError::Generic("Missing required argument --url".to_string()))?;

    upload_file(file_path, url, &method, headers.map(|s| s.as_str()))
}

fn upload_file(file_path: &str, url: &str, method: &str, headers_json: Option<&str>) -> Result<(), MuscleError> {
    let path = Path::new(file_path);
    if !path.exists() {
        return Err(MuscleError::SourceNotFound(format!("File to upload '{}' does not exist", file_path)));
    }

    let file_bytes = fs::read(path)
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to read file for upload: {}", e)))?;

    let client = reqwest::blocking::Client::builder()
        .build()
        .map_err(|e| MuscleError::Generic(format!("Failed to build HTTP client: {}", e)))?;

    let req_method = match method.to_uppercase().as_str() {
        "PUT" => reqwest::Method::PUT,
        _ => reqwest::Method::POST,
    };

    let mut request_builder = client.request(req_method, url)
        .body(file_bytes);

    if let Some(headers_str) = headers_json {
        if !headers_str.is_empty() {
            if let Ok(json_val) = serde_json::from_str::<serde_json::Value>(headers_str) {
                if let Some(obj) = json_val.as_object() {
                    for (k, v) in obj {
                        if let Some(v_str) = v.as_str() {
                            request_builder = request_builder.header(k, v_str);
                        }
                    }
                }
            }
        }
    }

    println!("[RUST] Uploading '{}' to '{}' using {}...", file_path, url, method);
    let response = request_builder.send()
        .map_err(|e| MuscleError::NetworkError(format!("Upload request failed: {}", e)))?;

    if !response.status().is_success() {
        return Err(MuscleError::NetworkError(format!("Server returned HTTP status: {}", response.status())));
    }

    println!("SUCCESS: Uploaded file '{}' to '{}'", file_path, url);
    Ok(())
}

pub fn handle_net_http_request(args: &[String]) -> Result<(), MuscleError> {
    let mut url = None;
    let mut method = String::from("GET");
    let mut destination = None;
    let mut headers = None;
    let mut body = None;
    let mut extract_regex = None;
    let mut extract_destination = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--url" => {
                if i + 1 < args.len() {
                    url = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --url".to_string()));
                }
            }
            "--method" => {
                if i + 1 < args.len() {
                    method = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --method".to_string()));
                }
            }
            "--destination" => {
                if i + 1 < args.len() {
                    destination = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --destination".to_string()));
                }
            }
            "--headers" => {
                if i + 1 < args.len() {
                    headers = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --headers".to_string()));
                }
            }
            "--body" => {
                if i + 1 < args.len() {
                    body = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --body".to_string()));
                }
            }
            "--extract-regex" | "--extract_regex" => {
                if i + 1 < args.len() {
                    extract_regex = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --extract-regex".to_string()));
                }
            }
            "--extract-destination" | "--extract_destination" => {
                if i + 1 < args.len() {
                    extract_destination = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --extract-destination".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let url = url.ok_or_else(|| MuscleError::Generic("Missing required argument --url".to_string()))?;

    let client = reqwest::blocking::Client::builder()
        .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        .build()
        .map_err(|e| MuscleError::Generic(format!("Failed to build HTTP client: {}", e)))?;

    let req_method = match method.to_uppercase().as_str() {
        "POST" => reqwest::Method::POST,
        "PUT" => reqwest::Method::PUT,
        "DELETE" => reqwest::Method::DELETE,
        _ => reqwest::Method::GET,
    };

    let mut req = client.request(req_method, url);

    if let Some(headers_str) = headers {
        if let Ok(json_val) = serde_json::from_str::<serde_json::Value>(headers_str) {
            if let Some(obj) = json_val.as_object() {
                for (k, v) in obj {
                    if let Some(val_str) = v.as_str() {
                        req = req.header(k, val_str);
                    }
                }
            }
        }
    }

    if let Some(b) = body {
        req = req.body(b.to_string());
    }

    println!("[RUST HTTP] Sending {} request to '{}'...", method.to_uppercase(), url);
    let response = req.send()
        .map_err(|e| MuscleError::NetworkError(format!("HTTP Request failed: {}", e)))?;

    if !response.status().is_success() {
        return Err(MuscleError::NetworkError(format!("Server returned error status: {}", response.status())));
    }

    let body_text = response.text()
        .map_err(|e| MuscleError::Generic(format!("Failed to read response body: {}", e)))?;

    if let Some(dest) = destination {
        let dest_path = Path::new(dest);
        if let Some(parent) = dest_path.parent() {
            if !parent.exists() {
                fs::create_dir_all(parent)
                    .map_err(|e| MuscleError::DestDirCreation(format!("Failed to create directories: {}", e)))?;
            }
        }
        fs::write(dest_path, &body_text)
            .map_err(|e| MuscleError::PermissionDenied(format!("Failed to write response to '{}': {}", dest, e)))?;
        println!("SUCCESS: Saved response to '{}'", dest);
    }

    if let Some(regex_str) = extract_regex {
        let ext_dest = extract_destination.ok_or_else(|| {
            MuscleError::Generic("Missing argument --extract-destination required by --extract-regex".to_string())
        })?;

        let re = regex::Regex::new(regex_str)
            .map_err(|e| MuscleError::Generic(format!("Invalid regex expression: {}", e)))?;

        let base_url = reqwest::Url::parse(url)
            .map_err(|e| MuscleError::Generic(format!("Failed to parse base URL for relative resolution: {}", e)))?;

        let mut matches = Vec::new();
        for cap in re.captures_iter(&body_text) {
            if let Some(m) = cap.get(1) {
                let matched_val = m.as_str();
                if matched_val.starts_with('/') || !matched_val.contains("://") {
                    if let Ok(abs_url) = base_url.join(matched_val) {
                        matches.push(abs_url.to_string());
                        continue;
                    }
                }
                matches.push(matched_val.to_string());
            }
        }

        let dest_path = Path::new(ext_dest);
        if let Some(parent) = dest_path.parent() {
            if !parent.exists() {
                fs::create_dir_all(parent)
                    .map_err(|e| MuscleError::DestDirCreation(format!("Failed to create directories: {}", e)))?;
            }
        }

        let json_bytes = serde_json::to_vec_pretty(&matches)
            .map_err(|e| MuscleError::Generic(format!("Failed to serialize matches list: {}", e)))?;

        fs::write(dest_path, json_bytes)
            .map_err(|e| MuscleError::PermissionDenied(format!("Failed to write extracted links to '{}': {}", ext_dest, e)))?;

        println!("SUCCESS: Extracted {} matches into '{}'", matches.len(), ext_dest);
    }

    Ok(())
}
