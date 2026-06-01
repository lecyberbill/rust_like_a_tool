// [WFGY] Zone: SAFE | λ: 0.2 | Action: Rust io.copy primitive implementation
use std::env;
use std::fs;
use std::io::{Read, Write};
use std::path::Path;
use std::process;

#[derive(Debug)]
enum MuscleError {
    Generic(String),
    SourceNotFound(String),
    PermissionDenied(String),
    DestDirCreation(String),
    CrossVolumeFail(String),
    TrashCreation(String),
    NetworkError(String),
}

impl MuscleError {
    fn exit_code(&self) -> i32 {
        match self {
            MuscleError::Generic(_) => 1,
            MuscleError::SourceNotFound(_) => 2,
            MuscleError::PermissionDenied(_) => 3,
            MuscleError::DestDirCreation(_) => 4,
            MuscleError::CrossVolumeFail(_) => 5,
            MuscleError::TrashCreation(_) => 6,
            MuscleError::NetworkError(_) => 7,
        }
    }

    fn message(&self) -> String {
        match self {
            MuscleError::Generic(m) => format!("ERR_GENERIC: {}", m),
            MuscleError::SourceNotFound(m) => format!("ERR_SOURCE_NOT_FOUND: {}", m),
            MuscleError::PermissionDenied(m) => format!("ERR_PERMISSION_DENIED: {}", m),
            MuscleError::DestDirCreation(m) => format!("ERR_DEST_DIR_CREATION: {}", m),
            MuscleError::CrossVolumeFail(m) => format!("ERR_CROSS_VOLUME_FAIL: {}", m),
            MuscleError::TrashCreation(m) => format!("ERR_TRASH_CREATION: {}", m),
            MuscleError::NetworkError(m) => format!("ERR_NETWORK_ERROR: {}", m),
        }
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Error: Missing command/primitive name. Usage: rust_muscle <primitive> [args]");
        process::exit(1);
    }

    let primitive = &args[1];
    let result = match primitive.as_str() {
        "io.copy" => handle_io_copy(&args[2..]),
        "io.move" => handle_io_move(&args[2..]),
        "io.delete" => handle_io_delete(&args[2..]),
        "io.metadata" => handle_io_metadata(&args[2..]),
        "net.download" => handle_net_download(&args[2..]),
        "net.upload" => handle_net_upload(&args[2..]),
        "data_filter" | "data.filter" => handle_data_filter(&args[2..]),
        "data.csv_to_json" => handle_csv_to_json(&args[2..]),
        "data.xml_to_json" => handle_xml_to_json(&args[2..]),
        "net.download_images" => Err(MuscleError::Generic("Deprecated: use net.http_request".to_string())),
        "net.http_request" => handle_net_http_request(&args[2..]),
        _ => Err(MuscleError::Generic(format!("Unknown primitive '{}'", primitive))),
    };

    match result {
        Ok(_) => process::exit(0),
        Err(err) => {
            eprintln!("{}", err.message());
            process::exit(err.exit_code());
        }
    }
}

// ... rest of the functions (copy, move, delete, metadata, download) remain ...


fn handle_io_copy(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut mode = String::from("binary");
    let mut conflict = String::from("overwrite");

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--source" => {
                if i + 1 < args.len() {
                    source = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --source".to_string()));
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
            "--mode" => {
                if i + 1 < args.len() {
                    mode = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --mode".to_string()));
                }
            }
            "--conflict" => {
                if i + 1 < args.len() {
                    conflict = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --conflict".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let source = source.ok_or_else(|| MuscleError::Generic("Missing required argument --source".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing required argument --destination".to_string()))?;

    copy_file(source, destination, &mode, &conflict)
}

fn copy_file(source: &str, destination: &str, mode: &str, conflict: &str) -> Result<(), MuscleError> {
    let src_path = Path::new(source);
    let dest_path = Path::new(destination);

    if !src_path.exists() {
        return Err(MuscleError::SourceNotFound(format!("Source path '{}' does not exist", source)));
    }

    if src_path.is_dir() {
        return Err(MuscleError::Generic("Directory copy not supported in basic io.copy file mode".to_string()));
    }

    let mut resolved_dest = dest_path.to_path_buf();
    let is_dir = destination.ends_with('/') 
        || destination.ends_with('\\') 
        || (dest_path.exists() && dest_path.is_dir());

    if is_dir {
        if let Some(filename) = src_path.file_name() {
            if !dest_path.exists() {
                fs::create_dir_all(dest_path)
                    .map_err(|e| MuscleError::DestDirCreation(format!("Failed to create destination directory: {}", e)))?;
            }
            resolved_dest = dest_path.join(filename);
        } else {
            return Err(MuscleError::Generic("Failed to resolve filename from source path".to_string()));
        }
    } else {
        // Ensure parent directory of destination exists
        if let Some(parent) = dest_path.parent() {
            if !parent.exists() {
                fs::create_dir_all(parent)
                    .map_err(|e| MuscleError::DestDirCreation(format!("Failed to create destination directories: {}", e)))?;
            }
        }
    }

    // Conflict resolution logic
    if resolved_dest.exists() {
        match conflict {
            "skip" => {
                println!("SUCCESS: Skipped copying. Destination file already exists.");
                return Ok(());
            }
            "newer" => {
                let src_meta = src_path.metadata().map_err(|e| MuscleError::PermissionDenied(format!("Failed to read source metadata: {}", e)))?;
                let dest_meta = resolved_dest.metadata().map_err(|e| MuscleError::PermissionDenied(format!("Failed to read destination metadata: {}", e)))?;
                
                let src_modified = src_meta.modified().map_err(|e| MuscleError::Generic(format!("Failed to read source modified time: {}", e)))?;
                let dest_modified = dest_meta.modified().map_err(|e| MuscleError::Generic(format!("Failed to read destination modified time: {}", e)))?;
                
                if src_modified <= dest_modified {
                    println!("SUCCESS: Skipped copying. Source is not newer than destination.");
                    return Ok(());
                }
            }
            _ => {} // default to overwrite
        }
    }

    if mode == "text" {
        // Text mode copy: might handle encoding transitions or standard line-by-line streaming
        let content = fs::read_to_string(src_path)
            .map_err(|e| MuscleError::PermissionDenied(format!("Failed to read source file in text mode: {}", e)))?;
        fs::write(&resolved_dest, content)
            .map_err(|e| MuscleError::PermissionDenied(format!("Failed to write destination file in text mode: {}", e)))?;
    } else {
        // Binary mode: efficient buffered copy
        let mut src_file = fs::File::open(src_path)
            .map_err(|e| MuscleError::PermissionDenied(format!("Failed to open source file: {}", e)))?;
        let mut dest_file = fs::File::create(&resolved_dest)
            .map_err(|e| MuscleError::PermissionDenied(format!("Failed to create destination file: {}", e)))?;
        
        let mut buffer = [0; 64 * 1024]; // 64KB buffer
        loop {
            let bytes_read = src_file.read(&mut buffer)
                .map_err(|e| MuscleError::PermissionDenied(format!("Failed to read source file: {}", e)))?;
            if bytes_read == 0 {
                break;
            }
            dest_file.write_all(&buffer[..bytes_read])
                .map_err(|e| MuscleError::PermissionDenied(format!("Failed to write destination file: {}", e)))?;
        }
    }

    println!("SUCCESS: Copied '{}' to '{}' in '{}' mode", source, resolved_dest.to_string_lossy(), mode);
    Ok(())
}

fn handle_io_move(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut conflict = String::from("overwrite");

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--source" => {
                if i + 1 < args.len() {
                    source = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --source".to_string()));
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
            "--conflict" => {
                if i + 1 < args.len() {
                    conflict = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --conflict".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let source = source.ok_or_else(|| MuscleError::Generic("Missing required argument --source".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing required argument --destination".to_string()))?;

    move_file(source, destination, &conflict)
}

fn move_file(source: &str, destination: &str, conflict: &str) -> Result<(), MuscleError> {
    let src_path = Path::new(source);
    let dest_path = Path::new(destination);

    if !src_path.exists() {
        return Err(MuscleError::SourceNotFound(format!("Source path '{}' does not exist", source)));
    }

    let mut resolved_dest = dest_path.to_path_buf();
    let is_dir = destination.ends_with('/') 
        || destination.ends_with('\\') 
        || (dest_path.exists() && dest_path.is_dir());

    if is_dir {
        if let Some(filename) = src_path.file_name() {
            if !dest_path.exists() {
                fs::create_dir_all(dest_path)
                    .map_err(|e| MuscleError::DestDirCreation(format!("Failed to create destination directory: {}", e)))?;
            }
            resolved_dest = dest_path.join(filename);
        } else {
            return Err(MuscleError::Generic("Failed to resolve filename from source path".to_string()));
        }
    } else {
        if let Some(parent) = dest_path.parent() {
            if !parent.exists() {
                fs::create_dir_all(parent)
                    .map_err(|e| MuscleError::DestDirCreation(format!("Failed to create destination directories: {}", e)))?;
            }
        }
    }

    if resolved_dest.exists() {
        match conflict {
            "skip" => {
                println!("SUCCESS: Skipped moving. Destination file already exists.");
                return Ok(());
            }
            "newer" => {
                let src_meta = src_path.metadata().map_err(|e| MuscleError::PermissionDenied(format!("Failed to read source metadata: {}", e)))?;
                let dest_meta = resolved_dest.metadata().map_err(|e| MuscleError::PermissionDenied(format!("Failed to read destination metadata: {}", e)))?;
                
                let src_modified = src_meta.modified().map_err(|e| MuscleError::Generic(format!("Failed to read source modified time: {}", e)))?;
                let dest_modified = dest_meta.modified().map_err(|e| MuscleError::Generic(format!("Failed to read destination modified time: {}", e)))?;
                
                if src_modified <= dest_modified {
                    println!("SUCCESS: Skipped moving. Source is not newer than destination.");
                    return Ok(());
                }
            }
            _ => {
                // If overwrite, delete first to avoid rename errors on some OS
                if resolved_dest.is_file() {
                    let _ = fs::remove_file(&resolved_dest);
                } else if resolved_dest.is_dir() {
                    let _ = fs::remove_dir_all(&resolved_dest);
                }
            }
        }
    }

    // Try fast atomic rename first
    if let Err(_) = fs::rename(src_path, &resolved_dest) {
        // Fallback: Cross-device link error or permissions, try copying then deleting
        println!("[RUST] Fast rename failed. Initiating cross-volume copy and delete fallback...");
        if src_path.is_file() {
            fs::copy(src_path, &resolved_dest)
                .map_err(|e| MuscleError::CrossVolumeFail(format!("Cross-volume copy failed: {}", e)))?;
            fs::remove_file(src_path)
                .map_err(|e| MuscleError::PermissionDenied(format!("Clean up of source file failed: {}", e)))?;
        } else if src_path.is_dir() {
            copy_dir_all(src_path, &resolved_dest)?;
            fs::remove_dir_all(src_path)
                .map_err(|e| MuscleError::PermissionDenied(format!("Clean up of source directory failed: {}", e)))?;
        }
    }

    println!("SUCCESS: Moved '{}' to '{}'", source, resolved_dest.to_string_lossy());
    Ok(())
}

fn copy_dir_all(src: &Path, dst: &Path) -> Result<(), MuscleError> {
    if !dst.exists() {
        fs::create_dir_all(dst)
            .map_err(|e| MuscleError::DestDirCreation(format!("Failed to create directory '{}': {}", dst.to_string_lossy(), e)))?;
    }

    let entries = fs::read_dir(src)
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to read directory '{}': {}", src.to_string_lossy(), e)))?;

    for entry in entries {
        let entry = entry.map_err(|e| MuscleError::Generic(format!("Error reading directory entry: {}", e)))?;
        let file_type = entry.file_type()
            .map_err(|e| MuscleError::Generic(format!("Failed to read file type: {}", e)))?;
        
        let src_entry_path = entry.path();
        let dst_entry_path = dst.join(entry.file_name());

        if file_type.is_dir() {
            copy_dir_all(&src_entry_path, &dst_entry_path)?;
        } else {
            fs::copy(&src_entry_path, &dst_entry_path)
                .map_err(|e| MuscleError::CrossVolumeFail(format!("Failed to copy file '{}' to '{}': {}", src_entry_path.to_string_lossy(), dst_entry_path.to_string_lossy(), e)))?;
        }
    }
    Ok(())
}

fn delete_file_or_dir(target: &str, secure: &str) -> Result<(), MuscleError> {
    let target_path = Path::new(target);
    if !target_path.exists() {
        println!("SUCCESS: Path '{}' does not exist. Nothing to delete.", target);
        return Ok(());
    }

    if secure == "trash" {
        // Local trash directory folder named '.trash' in the workspace
        let root_dir = Path::new(".");
        let trash_dir = root_dir.join(".trash");
        if !trash_dir.exists() {
            fs::create_dir_all(&trash_dir)
                .map_err(|e| MuscleError::TrashCreation(format!("Failed to create local trash directory: {}", e)))?;
        }

        if let Some(filename) = target_path.file_name() {
            use std::time::SystemTime;
            let timestamp = SystemTime::now()
                .duration_since(SystemTime::UNIX_EPOCH)
                .map(|d| d.as_secs())
                .unwrap_or(0);
            
            let trashed_name = format!("{}_{}", timestamp, filename.to_string_lossy());
            let dest_path = trash_dir.join(trashed_name);
            
            fs::rename(target_path, &dest_path)
                .map_err(|e| MuscleError::TrashCreation(format!("Failed to move file to trash: {}", e)))?;
            
            println!("SUCCESS: Moved '{}' to local trash bin: '{}'", target, dest_path.to_string_lossy());
        } else {
            return Err(MuscleError::Generic("Failed to resolve filename from path for trashing".to_string()));
        }
    } else {
        // Permanent deletion
        if target_path.is_file() {
            fs::remove_file(target_path)
                .map_err(|e| MuscleError::PermissionDenied(format!("Failed to delete file permanently: {}", e)))?;
        } else if target_path.is_dir() {
            fs::remove_dir_all(target_path)
                .map_err(|e| MuscleError::PermissionDenied(format!("Failed to delete directory permanently: {}", e)))?;
        }
        println!("SUCCESS: Permanently deleted '{}'", target);
    }

    Ok(())
}

fn handle_io_delete(args: &[String]) -> Result<(), MuscleError> {
    let mut path = None;
    let mut secure = String::from("trash");
    let mut retention_days: Option<u64> = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--path" => {
                if i + 1 < args.len() {
                    path = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --path".to_string()));
                }
            }
            "--secure" => {
                if i + 1 < args.len() {
                    secure = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --secure".to_string()));
                }
            }
            "--retention-days" => {
                if i + 1 < args.len() {
                    let parsed = args[i + 1].parse::<u64>()
                        .map_err(|_| MuscleError::Generic("Invalid integer for --retention-days".to_string()))?;
                    retention_days = Some(parsed);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --retention-days".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let path = path.ok_or_else(|| MuscleError::Generic("Missing required argument --path".to_string()))?;
    
    // 1. Execute deletion of the target path
    delete_file_or_dir(path, &secure)?;

    // 2. Perform trash clean up if secure == "trash" and retention_days is set
    if secure == "trash" {
        if let Some(days) = retention_days {
            clean_old_trash_items(days)?;
        }
    }

    Ok(())
}

fn clean_old_trash_items(retention_days: u64) -> Result<(), MuscleError> {
    let trash_dir = Path::new(".trash");
    if !trash_dir.exists() || !trash_dir.is_dir() {
        return Ok(());
    }

    use std::time::SystemTime;
    let now = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    
    let max_age_seconds = retention_days * 24 * 60 * 60;
    let entries = fs::read_dir(trash_dir)
        .map_err(|e| MuscleError::TrashCreation(format!("Failed to read trash directory: {}", e)))?;

    for entry in entries {
        if let Ok(entry) = entry {
            let path = entry.path();
            if let Some(filename) = path.file_name() {
                let filename_str = filename.to_string_lossy();
                // Extract timestamp from the prefix (format: "timestamp_name")
                if let Some(pos) = filename_str.find('_') {
                    if let Ok(timestamp) = filename_str[..pos].parse::<u64>() {
                        if now > timestamp && (now - timestamp) > max_age_seconds {
                            // Item expired, delete permanently
                            if path.is_file() {
                                let _ = fs::remove_file(&path);
                            } else if path.is_dir() {
                                let _ = fs::remove_dir_all(&path);
                            }
                            println!("[RUST] Trashed item '{}' permanently deleted due to retention policy (N={} days).", filename_str, retention_days);
                        }
                    }
                }
            }
        }
    }

    Ok(())
}

fn handle_io_metadata(args: &[String]) -> Result<(), MuscleError> {
    let mut path = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--path" => {
                if i + 1 < args.len() {
                    path = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --path".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let path_str = path.ok_or_else(|| MuscleError::Generic("Missing required argument --path".to_string()))?;
    let path = Path::new(path_str);

    if !path.exists() {
        println!("{{\"exists\": false}}");
        return Ok(());
    }

    let metadata = path.metadata()
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to read metadata for '{}': {}", path_str, e)))?;

    let is_dir = metadata.is_dir();
    let size_bytes = metadata.len();
    
    use std::time::SystemTime;
    let modified_epoch = metadata.modified()
        .unwrap_or(SystemTime::UNIX_EPOCH)
        .duration_since(SystemTime::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);

    println!(
        "{{\"exists\": true, \"is_dir\": {}, \"size_bytes\": {}, \"modified_epoch\": {}}}",
        is_dir, size_bytes, modified_epoch
    );

    Ok(())
}

fn handle_net_download(args: &[String]) -> Result<(), MuscleError> {
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
    
    // Ensure parent directory of destination exists
    if let Some(parent) = dest_path.parent() {
        if !parent.exists() {
            fs::create_dir_all(parent)
                .map_err(|e| MuscleError::DestDirCreation(format!("Failed to create destination directories: {}", e)))?;
        }
    }

    // Call blocking GET request with User-Agent
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

    // Copy stream response to local file
    response.copy_to(&mut dest_file)
        .map_err(|e| MuscleError::Generic(format!("Failed to write downloaded data to file: {}", e)))?;

    println!("SUCCESS: Downloaded file from '{}' to '{}'", url, destination);
    Ok(())
}

fn handle_net_http_request(args: &[String]) -> Result<(), MuscleError> {
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

    // Create client
    let client = reqwest::blocking::Client::builder()
        .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        .build()
        .map_err(|e| MuscleError::Generic(format!("Failed to build HTTP client: {}", e)))?;

    // Select method
    let req_method = match method.to_uppercase().as_str() {
        "POST" => reqwest::Method::POST,
        "PUT" => reqwest::Method::PUT,
        "DELETE" => reqwest::Method::DELETE,
        _ => reqwest::Method::GET,
    };

    let mut req = client.request(req_method, url);

    // Apply headers if provided
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

    // Apply body if provided
    if let Some(b) = body {
        req = req.body(b.to_string());
    }

    // Send request
    println!("[RUST HTTP] Sending {} request to '{}'...", method.to_uppercase(), url);
    let response = req.send()
        .map_err(|e| MuscleError::NetworkError(format!("HTTP Request failed: {}", e)))?;

    if !response.status().is_success() {
        return Err(MuscleError::NetworkError(format!("Server returned error status: {}", response.status())));
    }

    // Read body text
    let body_text = response.text()
        .map_err(|e| MuscleError::Generic(format!("Failed to read response body: {}", e)))?;

    // If destination is set, write raw response
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

    // If regex extraction is requested
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
                // Resolve relative URLs if it looks like one and base is valid
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

fn handle_net_upload(args: &[String]) -> Result<(), MuscleError> {
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

    // Apply custom headers if present
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

fn handle_data_filter(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut delimiter = String::from(",");
    let mut column_index: Option<usize> = None;
    let mut column_name = None;
    let mut operator = None;
    let mut value = None;
    let mut has_headers = false;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--source" => {
                if i + 1 < args.len() {
                    source = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --source".to_string()));
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
            "--delimiter" => {
                if i + 1 < args.len() {
                    delimiter = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --delimiter".to_string()));
                }
            }
            "--column_index" => {
                if i + 1 < args.len() {
                    let parsed = args[i + 1].parse::<usize>()
                        .map_err(|_| MuscleError::Generic("Invalid integer for --column_index".to_string()))?;
                    column_index = Some(parsed);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --column_index".to_string()));
                }
            }
            "--column_name" | "--column-name" => {
                if i + 1 < args.len() {
                    column_name = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --column_name".to_string()));
                }
            }
            "--operator" => {
                if i + 1 < args.len() {
                    operator = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --operator".to_string()));
                }
            }
            "--value" => {
                if i + 1 < args.len() {
                    value = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --value".to_string()));
                }
            }
            "--has_headers" | "--has-headers" => {
                if i + 1 < args.len() {
                    has_headers = args[i + 1].parse::<bool>()
                        .unwrap_or(false);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --has_headers".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let source = source.ok_or_else(|| MuscleError::Generic("Missing required argument --source".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing required argument --destination".to_string()))?;
    let operator = operator.ok_or_else(|| MuscleError::Generic("Missing required argument --operator".to_string()))?;
    let value = value.ok_or_else(|| MuscleError::Generic("Missing required argument --value".to_string()))?;

    filter_data(source, destination, &delimiter, column_index, column_name.map(|s| s.as_str()), operator, value, has_headers)
}

fn filter_data(
    source: &str,
    destination: &str,
    delimiter: &str,
    column_index: Option<usize>,
    column_name: Option<&str>,
    operator: &str,
    value: &str,
    has_headers: bool,
) -> Result<(), MuscleError> {
    let src_path = Path::new(source);
    if !src_path.exists() {
        return Err(MuscleError::SourceNotFound(format!("Source file '{}' does not exist", source)));
    }

    // Read source lines
    let content = fs::read_to_string(src_path)
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to read source file: {}", e)))?;

    let dest_path = Path::new(destination);
    if let Some(parent) = dest_path.parent() {
        if !parent.exists() {
            fs::create_dir_all(parent)
                .map_err(|e| MuscleError::DestDirCreation(format!("Failed to create destination directories: {}", e)))?;
        }
    }

    let mut out_file = fs::File::create(dest_path)
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to create destination file: {}", e)))?;

    let mut lines = content.lines();
    
    // Resolve column index from name if has_headers is active
    let mut resolved_index = column_index;
    if has_headers {
        if let Some(header_line) = lines.next() {
            // Write headers row directly to output
            writeln!(out_file, "{}", header_line)
                .map_err(|e| MuscleError::PermissionDenied(format!("Failed to write header to destination: {}", e)))?;
            
            if let Some(col_name) = column_name {
                let headers: Vec<&str> = header_line.split(delimiter).collect();
                if let Some(idx) = headers.iter().position(|&h| h.trim() == col_name.trim()) {
                    resolved_index = Some(idx);
                } else {
                    return Err(MuscleError::Generic(format!("Header column '{}' not found in headers row: {:?}", col_name, headers)));
                }
            }
        }
    }

    // Compile regex if target operator is regex
    let regex_pattern = if operator == "regex" {
        Some(regex::Regex::new(value)
            .map_err(|e| MuscleError::Generic(format!("Invalid Regex pattern: {}", e)))?)
    } else {
        None
    };

    let mut matched_count = 0;

    for line in lines {
        if line.trim().is_empty() {
            continue;
        }

        let fields: Vec<&str> = line.split(delimiter).collect();
        let target_field = match resolved_index {
            Some(idx) => {
                if idx < fields.len() {
                    fields[idx].trim()
                } else {
                    ""
                }
            }
            None => line.trim(), // fallback to line-level search if no column filter requested
        };

        let is_match = match operator {
            "equals" => target_field == value,
            "contains" => target_field.contains(value),
            "starts_with" => target_field.starts_with(value),
            "ends_with" => target_field.ends_with(value),
            "regex" => {
                if let Some(re) = &regex_pattern {
                    re.is_match(target_field)
                } else {
                    false
                }
            }
            "greater_than" => {
                if let (Ok(f_val), Ok(t_val)) = (target_field.parse::<f64>(), value.parse::<f64>()) {
                    f_val > t_val
                } else {
                    target_field > value
                }
            }
            "less_than" => {
                if let (Ok(f_val), Ok(t_val)) = (target_field.parse::<f64>(), value.parse::<f64>()) {
                    f_val < t_val
                } else {
                    target_field < value
                }
            }
            _ => return Err(MuscleError::Generic(format!("Unsupported operator '{}'", operator))),
        };

        if is_match {
            writeln!(out_file, "{}", line)
                .map_err(|e| MuscleError::PermissionDenied(format!("Failed to write line to output file: {}", e)))?;
            matched_count += 1;
        }
    }

    println!("SUCCESS: Filtered data from '{}' to '{}'. Matched rows: {}", source, destination, matched_count);
    Ok(())
}

fn handle_csv_to_json(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut delimiter = String::from(",");
    let mut has_headers = true;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--source" => {
                if i + 1 < args.len() {
                    source = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --source".to_string()));
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
            "--delimiter" => {
                if i + 1 < args.len() {
                    delimiter = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --delimiter".to_string()));
                }
            }
            "--has_headers" | "--has-headers" => {
                if i + 1 < args.len() {
                    has_headers = args[i + 1].parse::<bool>().unwrap_or(true);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --has_headers".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let source = source.ok_or_else(|| MuscleError::Generic("Missing required argument --source".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing required argument --destination".to_string()))?;

    csv_to_json(source, destination, &delimiter, has_headers)
}

fn csv_to_json(source: &str, destination: &str, delimiter: &str, has_headers: bool) -> Result<(), MuscleError> {
    let src_path = Path::new(source);
    if !src_path.exists() {
        return Err(MuscleError::SourceNotFound(format!("Source file '{}' does not exist", source)));
    }

    let content = fs::read_to_string(src_path)
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to read source file: {}", e)))?;

    let mut lines = content.lines();
    let mut headers = Vec::new();

    if has_headers {
        if let Some(header_line) = lines.next() {
            headers = header_line.split(delimiter).map(|s| s.trim().to_string()).collect();
        }
    }

    let mut json_list = Vec::new();

    for line in lines {
        if line.trim().is_empty() {
            continue;
        }

        let fields: Vec<&str> = line.split(delimiter).map(|s| s.trim()).collect();
        let mut obj = serde_json::Map::new();

        if has_headers {
            for (idx, &field) in fields.iter().enumerate() {
                let key = if idx < headers.len() {
                    headers[idx].clone()
                } else {
                    format!("column_{}", idx)
                };
                obj.insert(key, serde_json::Value::String(field.to_string()));
            }
        } else {
            for (idx, &field) in fields.iter().enumerate() {
                obj.insert(idx.to_string(), serde_json::Value::String(field.to_string()));
            }
        }

        json_list.push(serde_json::Value::Object(obj));
    }

    let dest_path = Path::new(destination);
    if let Some(parent) = dest_path.parent() {
        if !parent.exists() {
            fs::create_dir_all(parent)
                .map_err(|e| MuscleError::DestDirCreation(format!("Failed to create destination directories: {}", e)))?;
        }
    }

    let json_bytes = serde_json::to_vec_pretty(&json_list)
        .map_err(|e| MuscleError::Generic(format!("Failed to serialize JSON: {}", e)))?;

    fs::write(dest_path, json_bytes)
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to write JSON target: {}", e)))?;

    println!("SUCCESS: Converted CSV '{}' to JSON '{}'. Rows: {}", source, destination, json_list.len());
    Ok(())
}

fn handle_xml_to_json(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--source" => {
                if i + 1 < args.len() {
                    source = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --source".to_string()));
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

    let source = source.ok_or_else(|| MuscleError::Generic("Missing required argument --source".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing required argument --destination".to_string()))?;

    xml_to_json(source, destination)
}

use quick_xml::events::Event;
use quick_xml::reader::Reader;

fn xml_to_json(source: &str, destination: &str) -> Result<(), MuscleError> {
    let src_path = Path::new(source);
    if !src_path.exists() {
        return Err(MuscleError::SourceNotFound(format!("Source XML file '{}' does not exist", source)));
    }

    let xml_content = fs::read_to_string(src_path)
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to read XML source file: {}", e)))?;

    let mut reader = Reader::from_str(&xml_content);
    reader.trim_text(true);

    let mut buf = Vec::new();
    let mut stack: Vec<(String, serde_json::Map<String, serde_json::Value>)> = Vec::new();
    let mut root_obj = serde_json::Map::new();

    // Start with a generic target object
    stack.push(("root".to_string(), serde_json::Map::new()));

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(ref e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                let mut local_map = serde_json::Map::new();

                // Add XML attributes with "@" prefix
                for attr in e.attributes() {
                    if let Ok(attr) = attr {
                        let key = format!("@{}", String::from_utf8_lossy(attr.key.as_ref()));
                        let val = String::from_utf8_lossy(&attr.value).to_string();
                        local_map.insert(key, serde_json::Value::String(val));
                    }
                }

                stack.push((name, local_map));
            }
            Ok(Event::Text(ref e)) => {
                let text = e.unescape().unwrap_or_default().into_owned();
                if !text.is_empty() {
                    if let Some((_, map)) = stack.last_mut() {
                        map.insert("#text".to_string(), serde_json::Value::String(text));
                    }
                }
            }
            Ok(Event::End(ref _e)) => {
                if stack.len() > 1 {
                    let (name, map) = stack.pop().unwrap();
                    let val = if map.len() == 1 && map.contains_key("#text") {
                        // Simplify node if it only contains text
                        map.get("#text").unwrap().clone()
                    } else if map.is_empty() {
                        serde_json::Value::Null
                    } else {
                        serde_json::Value::Object(map)
                    };

                    if let Some((_, parent_map)) = stack.last_mut() {
                        // Check if tag already exists to create a list (support multiple identical child nodes)
                        if let Some(existing) = parent_map.get_mut(&name) {
                            if let Some(arr) = existing.as_array_mut() {
                                arr.push(val);
                            } else {
                                let old_val = existing.take();
                                *existing = serde_json::Value::Array(vec![old_val, val]);
                            }
                        } else {
                            parent_map.insert(name, val);
                        }
                    }
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(MuscleError::Generic(format!("Error parsing XML on line {}: {}", reader.buffer_position(), e))),
            _ => {}
        }
        buf.clear();
    }

    if let Some((_, final_map)) = stack.pop() {
        root_obj = final_map;
    }

    let dest_path = Path::new(destination);
    if let Some(parent) = dest_path.parent() {
        if !parent.exists() {
            fs::create_dir_all(parent)
                .map_err(|e| MuscleError::DestDirCreation(format!("Failed to create destination directories: {}", e)))?;
        }
    }

    let json_bytes = serde_json::to_vec_pretty(&serde_json::Value::Object(root_obj))
        .map_err(|e| MuscleError::Generic(format!("Failed to serialize final XML-to-JSON structure: {}", e)))?;

    fs::write(dest_path, json_bytes)
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to write JSON output: {}", e)))?;

    println!("SUCCESS: Converted XML '{}' to JSON '{}'", source, destination);
    Ok(())
}



