// [WFGY] Zone: SAFE | λ: 0.1 | Action: Data transform primitives

use std::fs;
use std::path::Path;
use std::io::Write;
use crate::MuscleError;

pub fn handle_data_filter(args: &[String]) -> Result<(), MuscleError> {
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
            "--column_index" | "--column-index" => {
                if i + 1 < args.len() {
                    // Try parsing as usize; if negative or invalid, parse it but handle gracefully or error.
                    // Note: usize parse fails for negative integers like -1.
                    let parsed = args[i + 1].parse::<usize>()
                        .map_err(|_| MuscleError::Generic("Invalid integer for --column-index".to_string()))?;
                    column_index = Some(parsed);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --column-index".to_string()));
                }
            }
            "--column_name" | "--column-name" => {
                if i + 1 < args.len() {
                    column_name = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --column-name".to_string()));
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
                    return Err(MuscleError::Generic("Missing value for --has-headers".to_string()));
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
    
    let mut resolved_index = column_index;
    if has_headers {
        if let Some(header_line) = lines.next() {
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
            None => line.trim(),
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

pub fn handle_data_split(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination_prefix = None;
    let mut by_column = None;

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
            "--destination-prefix" | "--destination_prefix" => {
                if i + 1 < args.len() {
                    destination_prefix = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --destination-prefix".to_string()));
                }
            }
            "--by-column" | "--by_column" => {
                if i + 1 < args.len() {
                    by_column = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --by-column".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let source = source.ok_or_else(|| MuscleError::Generic("Missing argument --source".to_string()))?;
    let destination_prefix = destination_prefix.ok_or_else(|| MuscleError::Generic("Missing argument --destination-prefix".to_string()))?;
    let by_column = by_column.ok_or_else(|| MuscleError::Generic("Missing argument --by-column".to_string()))?;

    analytical_engine::split(source, destination_prefix, by_column)
        .map_err(|e| MuscleError::Generic(e))
}

pub fn handle_data_merge(args: &[String]) -> Result<(), MuscleError> {
    let mut sources = None;
    let mut destination = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--sources" => {
                if i + 1 < args.len() {
                    sources = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --sources".to_string()));
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

    let sources_str = sources.ok_or_else(|| MuscleError::Generic("Missing argument --sources".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing argument --destination".to_string()))?;

    let sources_list: Vec<String> = sources_str.split(',').map(|s| s.trim().to_string()).collect();

    analytical_engine::merge(sources_list, destination)
        .map_err(|e| MuscleError::Generic(e))
}

pub fn handle_data_chunk_cumulative(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination_prefix = None;
    let mut accumulate_column = None;
    let mut threshold = None;

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
            "--destination-prefix" | "--destination_prefix" => {
                if i + 1 < args.len() {
                    destination_prefix = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --destination-prefix".to_string()));
                }
            }
            "--accumulate-column" | "--accumulate_column" => {
                if i + 1 < args.len() {
                    accumulate_column = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --accumulate-column".to_string()));
                }
            }
            "--threshold" => {
                if i + 1 < args.len() {
                    let parsed = args[i + 1].parse::<f64>()
                        .map_err(|_| MuscleError::Generic("Invalid float for --threshold".to_string()))?;
                    threshold = Some(parsed);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --threshold".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let source = source.ok_or_else(|| MuscleError::Generic("Missing argument --source".to_string()))?;
    let destination_prefix = destination_prefix.ok_or_else(|| MuscleError::Generic("Missing argument --destination-prefix".to_string()))?;
    let accumulate_column = accumulate_column.ok_or_else(|| MuscleError::Generic("Missing argument --accumulate-column".to_string()))?;
    let threshold = threshold.ok_or_else(|| MuscleError::Generic("Missing argument --threshold".to_string()))?;

    analytical_engine::chunk_cumulative(source, destination_prefix, accumulate_column, threshold)
        .map_err(|e| MuscleError::Generic(e))
}
