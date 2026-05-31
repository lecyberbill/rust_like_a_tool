// [WFGY] Zone: SAFE | λ: 0.2 | Action: Rust io.copy primitive implementation
use std::env;
use std::fs;
use std::io::{Read, Write};
use std::path::Path;
use std::process;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Error: Missing command/primitive name. Usage: rust_muscle <primitive> [args]");
        process::exit(1);
    }

    let primitive = &args[1];
    match primitive.as_str() {
        "io.copy" => {
            if let Err(e) = handle_io_copy(&args[2..]) {
                eprintln!("Error during io.copy: {}", e);
                process::exit(1);
            }
        }
        _ => {
            eprintln!("Error: Unknown primitive '{}'", primitive);
            process::exit(1);
        }
    }
}

fn handle_io_copy(args: &[String]) -> Result<(), String> {
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
                    return Err("Missing value for --source".to_string());
                }
            }
            "--destination" => {
                if i + 1 < args.len() {
                    destination = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err("Missing value for --destination".to_string());
                }
            }
            "--mode" => {
                if i + 1 < args.len() {
                    mode = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err("Missing value for --mode".to_string());
                }
            }
            "--conflict" => {
                if i + 1 < args.len() {
                    conflict = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err("Missing value for --conflict".to_string());
                }
            }
            other => {
                return Err(format!("Unknown argument '{}'", other));
            }
        }
    }

    let source = source.ok_or_else(|| "Missing required argument --source".to_string())?;
    let destination = destination.ok_or_else(|| "Missing required argument --destination".to_string())?;

    copy_file(source, destination, &mode, &conflict)
}

fn copy_file(source: &str, destination: &str, mode: &str, conflict: &str) -> Result<(), String> {
    let src_path = Path::new(source);
    let dest_path = Path::new(destination);

    if !src_path.exists() {
        return Err(format!("Source path '{}' does not exist", source));
    }

    if src_path.is_dir() {
        return Err("Directory copy not supported in basic io.copy file mode".to_string());
    }

    let mut resolved_dest = dest_path.to_path_buf();
    let is_dir = destination.ends_with('/') 
        || destination.ends_with('\\') 
        || (dest_path.exists() && dest_path.is_dir());

    if is_dir {
        if let Some(filename) = src_path.file_name() {
            if !dest_path.exists() {
                fs::create_dir_all(dest_path)
                    .map_err(|e| format!("Failed to create destination directory: {}", e))?;
            }
            resolved_dest = dest_path.join(filename);
        } else {
            return Err("Failed to resolve filename from source path".to_string());
        }
    } else {
        // Ensure parent directory of destination exists
        if let Some(parent) = dest_path.parent() {
            if !parent.exists() {
                fs::create_dir_all(parent)
                    .map_err(|e| format!("Failed to create destination directories: {}", e))?;
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
                let src_meta = src_path.metadata().map_err(|e| format!("Failed to read source metadata: {}", e))?;
                let dest_meta = resolved_dest.metadata().map_err(|e| format!("Failed to read destination metadata: {}", e))?;
                
                let src_modified = src_meta.modified().map_err(|e| format!("Failed to read source modified time: {}", e))?;
                let dest_modified = dest_meta.modified().map_err(|e| format!("Failed to read destination modified time: {}", e))?;
                
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
            .map_err(|e| format!("Failed to read source file in text mode: {}", e))?;
        fs::write(&resolved_dest, content)
            .map_err(|e| format!("Failed to write destination file in text mode: {}", e))?;
    } else {
        // Binary mode: efficient buffered copy
        let mut src_file = fs::File::open(src_path)
            .map_err(|e| format!("Failed to open source file: {}", e))?;
        let mut dest_file = fs::File::create(&resolved_dest)
            .map_err(|e| format!("Failed to create destination file: {}", e))?;
        
        let mut buffer = [0; 64 * 1024]; // 64KB buffer
        loop {
            let bytes_read = src_file.read(&mut buffer)
                .map_err(|e| format!("Failed to read source file: {}", e))?;
            if bytes_read == 0 {
                break;
            }
            dest_file.write_all(&buffer[..bytes_read])
                .map_err(|e| format!("Failed to write destination file: {}", e))?;
        }
    }

    println!("SUCCESS: Copied '{}' to '{}' in '{}' mode", source, resolved_dest.to_string_lossy(), mode);
    Ok(())
}
