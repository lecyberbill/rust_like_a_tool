// [WFGY] Zone: SAFE | λ: 0.1 | Action: Local File IO primitives

use crate::MuscleError;
use std::fs;
use std::io::{Read, Write};
use std::path::Path;

pub fn handle_io_write_file(args: &[String]) -> Result<(), MuscleError> {
    let mut path = None;
    let mut content = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--path" => {
                if i + 1 < args.len() {
                    path = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --path".to_string(),
                    ));
                }
            }
            "--content" => {
                if i + 1 < args.len() {
                    content = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --content".to_string(),
                    ));
                }
            }
            other => {
                return Err(MuscleError::InvalidArg(format!(
                    "Unknown argument '{}'",
                    other
                )));
            }
        }
    }

    let path = path
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --path".to_string()))?;
    let content = content.ok_or_else(|| {
        MuscleError::MissingArg("Missing required argument --content".to_string())
    })?;

    io_write_file(path, content)
}

fn io_write_file(path_str: &str, content: &str) -> Result<(), MuscleError> {
    let dest_path = Path::new(path_str);
    if let Some(parent) = dest_path.parent() {
        if !parent.exists() {
            fs::create_dir_all(parent).map_err(|e| {
                MuscleError::DestDirCreation(format!(
                    "Failed to create destination directories: {}",
                    e
                ))
            })?;
        }
    }

    fs::write(dest_path, content)
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to write file: {}", e)))?;

    println!(
        "SUCCESS: Created/Overwrote file '{}' ({} bytes)",
        path_str,
        content.len()
    );
    Ok(())
}

pub fn handle_io_copy(args: &[String]) -> Result<(), MuscleError> {
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
                    return Err(MuscleError::MissingArg(
                        "Missing value for --source".to_string(),
                    ));
                }
            }
            "--destination" => {
                if i + 1 < args.len() {
                    destination = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --destination".to_string(),
                    ));
                }
            }
            "--mode" => {
                if i + 1 < args.len() {
                    mode = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --mode".to_string(),
                    ));
                }
            }
            "--conflict" => {
                if i + 1 < args.len() {
                    conflict = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --conflict".to_string(),
                    ));
                }
            }
            other => {
                return Err(MuscleError::InvalidArg(format!(
                    "Unknown argument '{}'",
                    other
                )));
            }
        }
    }

    let source = source
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --source".to_string()))?;
    let destination = destination.ok_or_else(|| {
        MuscleError::MissingArg("Missing required argument --destination".to_string())
    })?;

    copy_file(source, destination, &mode, &conflict)
}

fn copy_file(
    source: &str,
    destination: &str,
    mode: &str,
    conflict: &str,
) -> Result<(), MuscleError> {
    let src_path = Path::new(source);
    let dest_path = Path::new(destination);

    if !src_path.exists() {
        return Err(MuscleError::SourceNotFound(format!(
            "Source path '{}' does not exist",
            source
        )));
    }

    if src_path.is_dir() {
        return Err(MuscleError::InvalidArg(
            "Directory copy not supported in basic io.copy file mode".to_string(),
        ));
    }

    let mut resolved_dest = dest_path.to_path_buf();
    let is_dir = destination.ends_with('/')
        || destination.ends_with('\\')
        || (dest_path.exists() && dest_path.is_dir());

    if is_dir {
        if let Some(filename) = src_path.file_name() {
            if !dest_path.exists() {
                fs::create_dir_all(dest_path).map_err(|e| {
                    MuscleError::DestDirCreation(format!(
                        "Failed to create destination directory: {}",
                        e
                    ))
                })?;
            }
            resolved_dest = dest_path.join(filename);
        } else {
            return Err(MuscleError::IoError(
                "Failed to resolve filename from source path".to_string(),
            ));
        }
    } else {
        if let Some(parent) = dest_path.parent() {
            if !parent.exists() {
                fs::create_dir_all(parent).map_err(|e| {
                    MuscleError::DestDirCreation(format!(
                        "Failed to create destination directories: {}",
                        e
                    ))
                })?;
            }
        }
    }

    if resolved_dest.exists() {
        match conflict {
            "skip" => {
                println!("SUCCESS: Skipped copying. Destination file already exists.");
                return Ok(());
            }
            "newer" => {
                let src_meta = src_path.metadata().map_err(|e| {
                    MuscleError::PermissionDenied(format!("Failed to read source metadata: {}", e))
                })?;
                let dest_meta = resolved_dest.metadata().map_err(|e| {
                    MuscleError::PermissionDenied(format!(
                        "Failed to read destination metadata: {}",
                        e
                    ))
                })?;

                let src_modified = src_meta.modified().map_err(|e| {
                    MuscleError::IoError(format!("Failed to read source modified time: {}", e))
                })?;
                let dest_modified = dest_meta.modified().map_err(|e| {
                    MuscleError::IoError(format!("Failed to read destination modified time: {}", e))
                })?;

                if src_modified <= dest_modified {
                    println!("SUCCESS: Skipped copying. Source is not newer than destination.");
                    return Ok(());
                }
            }
            _ => {}
        }
    }

    if mode == "text" {
        let content = fs::read_to_string(src_path).map_err(|e| {
            MuscleError::PermissionDenied(format!("Failed to read source file in text mode: {}", e))
        })?;
        fs::write(&resolved_dest, content).map_err(|e| {
            MuscleError::PermissionDenied(format!(
                "Failed to write destination file in text mode: {}",
                e
            ))
        })?;
    } else {
        let mut src_file = fs::File::open(src_path).map_err(|e| {
            MuscleError::PermissionDenied(format!("Failed to open source file: {}", e))
        })?;
        let mut dest_file = fs::File::create(&resolved_dest).map_err(|e| {
            MuscleError::PermissionDenied(format!("Failed to create destination file: {}", e))
        })?;

        let mut buffer = [0; 64 * 1024];
        loop {
            let bytes_read = src_file.read(&mut buffer).map_err(|e| {
                MuscleError::PermissionDenied(format!("Failed to read source file: {}", e))
            })?;
            if bytes_read == 0 {
                break;
            }
            dest_file.write_all(&buffer[..bytes_read]).map_err(|e| {
                MuscleError::PermissionDenied(format!("Failed to write destination file: {}", e))
            })?;
        }
    }

    println!(
        "SUCCESS: Copied '{}' to '{}' in '{}' mode",
        source,
        resolved_dest.to_string_lossy(),
        mode
    );
    Ok(())
}

pub fn handle_io_move(args: &[String]) -> Result<(), MuscleError> {
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
                    return Err(MuscleError::MissingArg(
                        "Missing value for --source".to_string(),
                    ));
                }
            }
            "--destination" => {
                if i + 1 < args.len() {
                    destination = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --destination".to_string(),
                    ));
                }
            }
            "--conflict" => {
                if i + 1 < args.len() {
                    conflict = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --conflict".to_string(),
                    ));
                }
            }
            other => {
                return Err(MuscleError::InvalidArg(format!(
                    "Unknown argument '{}'",
                    other
                )));
            }
        }
    }

    let source = source
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --source".to_string()))?;
    let destination = destination.ok_or_else(|| {
        MuscleError::MissingArg("Missing required argument --destination".to_string())
    })?;

    move_file(source, destination, &conflict)
}

fn move_file(source: &str, destination: &str, conflict: &str) -> Result<(), MuscleError> {
    let src_path = Path::new(source);
    let dest_path = Path::new(destination);

    if !src_path.exists() {
        return Err(MuscleError::SourceNotFound(format!(
            "Source path '{}' does not exist",
            source
        )));
    }

    let mut resolved_dest = dest_path.to_path_buf();
    let is_dir = destination.ends_with('/')
        || destination.ends_with('\\')
        || (dest_path.exists() && dest_path.is_dir());

    if is_dir {
        if let Some(filename) = src_path.file_name() {
            if !dest_path.exists() {
                fs::create_dir_all(dest_path).map_err(|e| {
                    MuscleError::DestDirCreation(format!(
                        "Failed to create destination directory: {}",
                        e
                    ))
                })?;
            }
            resolved_dest = dest_path.join(filename);
        } else {
            return Err(MuscleError::IoError(
                "Failed to resolve filename from source path".to_string(),
            ));
        }
    } else {
        if let Some(parent) = dest_path.parent() {
            if !parent.exists() {
                fs::create_dir_all(parent).map_err(|e| {
                    MuscleError::DestDirCreation(format!(
                        "Failed to create destination directories: {}",
                        e
                    ))
                })?;
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
                let src_meta = src_path.metadata().map_err(|e| {
                    MuscleError::PermissionDenied(format!("Failed to read source metadata: {}", e))
                })?;
                let dest_meta = resolved_dest.metadata().map_err(|e| {
                    MuscleError::PermissionDenied(format!(
                        "Failed to read destination metadata: {}",
                        e
                    ))
                })?;

                let src_modified = src_meta.modified().map_err(|e| {
                    MuscleError::IoError(format!("Failed to read source modified time: {}", e))
                })?;
                let dest_modified = dest_meta.modified().map_err(|e| {
                    MuscleError::IoError(format!("Failed to read destination modified time: {}", e))
                })?;

                if src_modified <= dest_modified {
                    println!("SUCCESS: Skipped moving. Source is not newer than destination.");
                    return Ok(());
                }
            }
            _ => {
                if resolved_dest.is_file() {
                    let _ = fs::remove_file(&resolved_dest);
                } else if resolved_dest.is_dir() {
                    let _ = fs::remove_dir_all(&resolved_dest);
                }
            }
        }
    }

    if let Err(_) = fs::rename(src_path, &resolved_dest) {
        println!("[RUST] Fast rename failed. Initiating cross-volume copy and delete fallback...");
        if src_path.is_file() {
            fs::copy(src_path, &resolved_dest).map_err(|e| {
                MuscleError::CrossVolumeFail(format!("Cross-volume copy failed: {}", e))
            })?;
            fs::remove_file(src_path).map_err(|e| {
                MuscleError::PermissionDenied(format!("Clean up of source file failed: {}", e))
            })?;
        } else if src_path.is_dir() {
            copy_dir_all(src_path, &resolved_dest)?;
            fs::remove_dir_all(src_path).map_err(|e| {
                MuscleError::PermissionDenied(format!("Clean up of source directory failed: {}", e))
            })?;
        }
    }

    println!(
        "SUCCESS: Moved '{}' to '{}'",
        source,
        resolved_dest.to_string_lossy()
    );
    Ok(())
}

fn copy_dir_all(src: &Path, dst: &Path) -> Result<(), MuscleError> {
    if !dst.exists() {
        fs::create_dir_all(dst).map_err(|e| {
            MuscleError::DestDirCreation(format!(
                "Failed to create directory '{}': {}",
                dst.to_string_lossy(),
                e
            ))
        })?;
    }

    let entries = fs::read_dir(src).map_err(|e| {
        MuscleError::PermissionDenied(format!(
            "Failed to read directory '{}': {}",
            src.to_string_lossy(),
            e
        ))
    })?;

    for entry in entries {
        let entry = entry
            .map_err(|e| MuscleError::IoError(format!("Error reading directory entry: {}", e)))?;
        let file_type = entry
            .file_type()
            .map_err(|e| MuscleError::IoError(format!("Failed to read file type: {}", e)))?;

        let src_entry_path = entry.path();
        let dst_entry_path = dst.join(entry.file_name());

        if file_type.is_dir() {
            copy_dir_all(&src_entry_path, &dst_entry_path)?;
        } else {
            fs::copy(&src_entry_path, &dst_entry_path).map_err(|e| {
                MuscleError::CrossVolumeFail(format!(
                    "Failed to copy file '{}' to '{}': {}",
                    src_entry_path.to_string_lossy(),
                    dst_entry_path.to_string_lossy(),
                    e
                ))
            })?;
        }
    }
    Ok(())
}

pub fn handle_io_delete(args: &[String]) -> Result<(), MuscleError> {
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
                    return Err(MuscleError::MissingArg(
                        "Missing value for --path".to_string(),
                    ));
                }
            }
            "--secure" => {
                if i + 1 < args.len() {
                    secure = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --secure".to_string(),
                    ));
                }
            }
            "--retention-days" => {
                if i + 1 < args.len() {
                    let parsed = args[i + 1].parse::<u64>().map_err(|_| {
                        MuscleError::InvalidArg("Invalid integer for --retention-days".to_string())
                    })?;
                    retention_days = Some(parsed);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --retention-days".to_string(),
                    ));
                }
            }
            other => {
                return Err(MuscleError::InvalidArg(format!(
                    "Unknown argument '{}'",
                    other
                )));
            }
        }
    }

    let path = path
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --path".to_string()))?;

    delete_file_or_dir(path, &secure)?;

    if secure == "trash" {
        if let Some(days) = retention_days {
            clean_old_trash_items(days)?;
        }
    }

    Ok(())
}

fn delete_file_or_dir(target: &str, secure: &str) -> Result<(), MuscleError> {
    let target_path = Path::new(target);
    if !target_path.exists() {
        println!(
            "SUCCESS: Path '{}' does not exist. Nothing to delete.",
            target
        );
        return Ok(());
    }

    if secure == "trash" {
        let root_dir = Path::new(".");
        let trash_dir = root_dir.join(".trash");
        if !trash_dir.exists() {
            fs::create_dir_all(&trash_dir).map_err(|e| {
                MuscleError::TrashCreation(format!("Failed to create local trash directory: {}", e))
            })?;
        }

        if let Some(filename) = target_path.file_name() {
            use std::time::SystemTime;
            let timestamp = SystemTime::now()
                .duration_since(SystemTime::UNIX_EPOCH)
                .map(|d| d.as_secs())
                .unwrap_or(0);

            let trashed_name = format!("{}_{}", timestamp, filename.to_string_lossy());
            let dest_path = trash_dir.join(trashed_name);

            fs::rename(target_path, &dest_path).map_err(|e| {
                MuscleError::TrashCreation(format!("Failed to move file to trash: {}", e))
            })?;

            println!(
                "SUCCESS: Moved '{}' to local trash bin: '{}'",
                target,
                dest_path.to_string_lossy()
            );
        } else {
            return Err(MuscleError::IoError(
                "Failed to resolve filename from path for trashing".to_string(),
            ));
        }
    } else {
        if target_path.is_file() {
            fs::remove_file(target_path).map_err(|e| {
                MuscleError::PermissionDenied(format!("Failed to delete file permanently: {}", e))
            })?;
        } else if target_path.is_dir() {
            fs::remove_dir_all(target_path).map_err(|e| {
                MuscleError::PermissionDenied(format!(
                    "Failed to delete directory permanently: {}",
                    e
                ))
            })?;
        }
        println!("SUCCESS: Permanently deleted '{}'", target);
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
    let entries = fs::read_dir(trash_dir).map_err(|e| {
        MuscleError::TrashCreation(format!("Failed to read trash directory: {}", e))
    })?;

    for entry in entries {
        if let Ok(entry) = entry {
            let path = entry.path();
            if let Some(filename) = path.file_name() {
                let filename_str = filename.to_string_lossy();
                if let Some(pos) = filename_str.find('_') {
                    if let Ok(timestamp) = filename_str[..pos].parse::<u64>() {
                        if now > timestamp && (now - timestamp) > max_age_seconds {
                            if path.is_file() {
                                let _ = fs::remove_file(&path);
                            } else if path.is_dir() {
                                let _ = fs::remove_dir_all(&path);
                            }
                            println!(
                                "[RUST] Trashed item '{}' permanently deleted due to retention policy (N={} days).",
                                filename_str, retention_days
                            );
                        }
                    }
                }
            }
        }
    }

    Ok(())
}

pub fn handle_io_metadata(args: &[String]) -> Result<(), MuscleError> {
    let mut path = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--path" => {
                if i + 1 < args.len() {
                    path = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --path".to_string(),
                    ));
                }
            }
            other => {
                return Err(MuscleError::InvalidArg(format!(
                    "Unknown argument '{}'",
                    other
                )));
            }
        }
    }

    let path_str = path
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --path".to_string()))?;
    let path = Path::new(path_str);

    if !path.exists() {
        println!("{{\"exists\": false}}");
        return Ok(());
    }

    let metadata = path.metadata().map_err(|e| {
        MuscleError::PermissionDenied(format!("Failed to read metadata for '{}': {}", path_str, e))
    })?;

    let is_dir = metadata.is_dir();
    let size_bytes = metadata.len();

    use std::time::SystemTime;
    let modified_epoch = metadata
        .modified()
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

pub fn handle_io_zip(args: &[String]) -> Result<(), MuscleError> {
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
                    return Err(MuscleError::MissingArg(
                        "Missing value for --source".to_string(),
                    ));
                }
            }
            "--destination" => {
                if i + 1 < args.len() {
                    destination = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --destination".to_string(),
                    ));
                }
            }
            other => {
                return Err(MuscleError::InvalidArg(format!(
                    "Unknown argument '{}'",
                    other
                )));
            }
        }
    }

    let source = source
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --source".to_string()))?;
    let destination = destination.ok_or_else(|| {
        MuscleError::MissingArg("Missing required argument --destination".to_string())
    })?;

    run_archive_helper("zip", source, destination)
}

pub fn handle_io_unzip(args: &[String]) -> Result<(), MuscleError> {
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
                    return Err(MuscleError::MissingArg(
                        "Missing value for --source".to_string(),
                    ));
                }
            }
            "--destination" => {
                if i + 1 < args.len() {
                    destination = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --destination".to_string(),
                    ));
                }
            }
            other => {
                return Err(MuscleError::InvalidArg(format!(
                    "Unknown argument '{}'",
                    other
                )));
            }
        }
    }

    let source = source
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --source".to_string()))?;
    let destination = destination.ok_or_else(|| {
        MuscleError::MissingArg("Missing required argument --destination".to_string())
    })?;

    run_archive_helper("unzip", source, destination)
}

fn run_archive_helper(mode: &str, source: &str, destination: &str) -> Result<(), MuscleError> {
    use std::process::Command;
    let py_path = if cfg!(windows) {
        ".venv\\Scripts\\python.exe"
    } else {
        ".venv/bin/python"
    };
    let helper_path = "brain/archive_helper.py";

    let mut cmd = Command::new(py_path);
    cmd.arg(helper_path).arg(mode).arg(source).arg(destination);

    let output = cmd.output().map_err(|e| {
        MuscleError::IoError(format!("Failed to execute Python archive helper: {}", e))
    })?;

    if !output.status.success() {
        let err_msg = String::from_utf8_lossy(&output.stderr).to_string();
        return Err(MuscleError::IoError(format!(
            "Archive helper failed: {}",
            err_msg
        )));
    }

    let stdout_msg = String::from_utf8_lossy(&output.stdout).to_string();
    print!("{}", stdout_msg);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::io::Write;
    use tempfile::TempDir;

    fn s(item: &str) -> String {
        item.to_string()
    }

    fn write_test_file(dir: &TempDir, name: &str, content: &str) -> String {
        let path = dir.path().join(name);
        let mut f = fs::File::create(&path).unwrap();
        f.write_all(content.as_bytes()).unwrap();
        path.to_string_lossy().to_string()
    }

    // --- io.copy ---

    #[test]
    fn test_io_copy_basic() {
        let tmp = TempDir::new().unwrap();
        let src = write_test_file(&tmp, "src.txt", "hello");
        let dst = tmp.path().join("dst.txt").to_string_lossy().to_string();
        let args: Vec<String> = vec![s("--source"), s(&src), s("--destination"), s(&dst)];
        let result = handle_io_copy(&args);
        assert!(result.is_ok());
        assert!(std::path::Path::new(&dst).exists());
        assert_eq!(fs::read_to_string(&dst).unwrap(), "hello");
    }

    #[test]
    fn test_io_copy_missing_source() {
        let tmp = TempDir::new().unwrap();
        let dst = tmp.path().join("nope.txt").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s("/nonexistent/file"),
            s("--destination"),
            s(&dst),
        ];
        let result = handle_io_copy(&args);
        assert!(result.is_err());
    }

    #[test]
    fn test_io_copy_mode_binary() {
        let tmp = TempDir::new().unwrap();
        let src = write_test_file(&tmp, "a.bin", "hello");
        let dst = tmp.path().join("b.bin").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination"),
            s(&dst),
            s("--mode"),
            s("binary"),
        ];
        let result = handle_io_copy(&args);
        assert!(result.is_ok());
        assert!(std::path::Path::new(&dst).exists());
    }

    #[test]
    fn test_io_copy_conflict_skip() {
        let tmp = TempDir::new().unwrap();
        let src = write_test_file(&tmp, "src.txt", "hello");
        let dst = write_test_file(&tmp, "dst.txt", "existing");
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination"),
            s(&dst),
            s("--conflict"),
            s("skip"),
        ];
        let result = handle_io_copy(&args);
        assert!(result.is_ok());
        assert_eq!(fs::read_to_string(&dst).unwrap(), "existing");
    }

    #[test]
    fn test_io_copy_missing_args() {
        let args: Vec<String> = vec![s("--source"), s("x")];
        let result = handle_io_copy(&args);
        assert!(result.is_err());
    }

    // --- io.move ---

    #[test]
    fn test_io_move_basic() {
        let tmp = TempDir::new().unwrap();
        let src = write_test_file(&tmp, "mov_src.txt", "move me");
        let dst = tmp.path().join("mov_dst.txt").to_string_lossy().to_string();
        let args: Vec<String> = vec![s("--source"), s(&src), s("--destination"), s(&dst)];
        let result = handle_io_move(&args);
        assert!(result.is_ok());
        assert!(std::path::Path::new(&dst).exists());
        assert!(!std::path::Path::new(&src).exists());
    }

    // --- io.delete ---

    #[test]
    fn test_io_delete_basic() {
        let tmp = TempDir::new().unwrap();
        let path = write_test_file(&tmp, "del.txt", "delete me");
        let args: Vec<String> = vec![s("--path"), s(&path), s("--secure"), s("permanent")];
        let result = handle_io_delete(&args);
        assert!(result.is_ok());
        assert!(!std::path::Path::new(&path).exists());
    }

    #[test]
    fn test_io_delete_missing_file() {
        let args: Vec<String> = vec![
            s("--path"),
            s("/nonexistent/file"),
            s("--secure"),
            s("permanent"),
        ];
        let result = handle_io_delete(&args);
        assert!(result.is_ok()); // handler returns Ok if path does not exist
    }

    // --- io.metadata ---

    #[test]
    fn test_io_metadata_file() {
        let tmp = TempDir::new().unwrap();
        let path = write_test_file(&tmp, "meta.txt", "metadata test");
        let args: Vec<String> = vec![s("--path"), s(&path)];
        let result = handle_io_metadata(&args);
        assert!(result.is_ok());
    }

    #[test]
    fn test_io_metadata_nonexistent() {
        let args: Vec<String> = vec![s("--path"), s("/nonexistent")];
        let result = handle_io_metadata(&args);
        assert!(result.is_ok());
    }

    // --- io.write_file ---

    #[test]
    fn test_io_write_file_basic() {
        let tmp = TempDir::new().unwrap();
        let path = tmp.path().join("written.txt").to_string_lossy().to_string();
        let args: Vec<String> = vec![s("--path"), s(&path), s("--content"), s("hello world")];
        let result = handle_io_write_file(&args);
        assert!(result.is_ok());
        assert_eq!(fs::read_to_string(&path).unwrap(), "hello world");
    }

    #[test]
    fn test_io_write_file_overwrite() {
        let tmp = TempDir::new().unwrap();
        let path = write_test_file(&tmp, "overwrite.txt", "old");
        let args: Vec<String> = vec![s("--path"), s(&path), s("--content"), s("new")];
        let result = handle_io_write_file(&args);
        assert!(result.is_ok());
        assert_eq!(fs::read_to_string(&path).unwrap(), "new");
    }
}
