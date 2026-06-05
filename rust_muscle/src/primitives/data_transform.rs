// [WFGY] Zone: SAFE | λ: 0.2 | Action: RFC 4180 CSV filter implementation

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

    let delim_byte = delimiter.as_bytes().first().copied().unwrap_or(b',');

    let mut reader = csv::ReaderBuilder::new()
        .delimiter(delim_byte)
        .has_headers(has_headers)
        .from_path(src_path)
        .map_err(|e| MuscleError::Generic(format!("Failed to open CSV reader: {}", e)))?;

    let dest_path = Path::new(destination);
    if let Some(parent) = dest_path.parent() {
        if !parent.exists() {
            fs::create_dir_all(parent)
                .map_err(|e| MuscleError::DestDirCreation(format!("Failed to create destination directories: {}", e)))?;
        }
    }

    let mut writer = csv::WriterBuilder::new()
        .delimiter(delim_byte)
        .from_path(dest_path)
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to create destination CSV writer: {}", e)))?;

    let mut resolved_index = column_index;
    let headers = reader.headers()
        .map_err(|e| MuscleError::Generic(format!("Failed to read CSV headers: {}", e)))?
        .clone();

    if has_headers {
        writer.write_record(&headers)
            .map_err(|e| MuscleError::PermissionDenied(format!("Failed to write CSV headers: {}", e)))?;

        if let Some(col_name) = column_name {
            if let Some(idx) = headers.iter().position(|h| h.trim() == col_name.trim()) {
                resolved_index = Some(idx);
            } else {
                return Err(MuscleError::Generic(format!("Header column '{}' not found in headers row: {:?}", col_name, headers)));
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

    for result in reader.records() {
        let record = result.map_err(|e| MuscleError::Generic(format!("Error reading CSV record: {}", e)))?;
        
        let target_field = match resolved_index {
            Some(idx) => {
                if idx < record.len() {
                    record[idx].trim()
                } else {
                    ""
                }
            }
            None => ""
        };

        let line_to_match = if resolved_index.is_none() {
            record.iter().collect::<Vec<_>>().join(delimiter)
        } else {
            target_field.to_string()
        };

        let is_match = match operator {
            "equals" => (resolved_index.is_none() && line_to_match == value) || (resolved_index.is_some() && target_field == value),
            "contains" => (resolved_index.is_none() && line_to_match.contains(value)) || (resolved_index.is_some() && target_field.contains(value)),
            "starts_with" => (resolved_index.is_none() && line_to_match.starts_with(value)) || (resolved_index.is_some() && target_field.starts_with(value)),
            "ends_with" => (resolved_index.is_none() && line_to_match.ends_with(value)) || (resolved_index.is_some() && target_field.ends_with(value)),
            "regex" => {
                let target = if resolved_index.is_none() { &line_to_match } else { target_field };
                if let Some(re) = &regex_pattern {
                    re.is_match(target)
                } else {
                    false
                }
            }
            "greater_than" => {
                let target = if resolved_index.is_none() { &line_to_match } else { target_field };
                if let (Ok(f_val), Ok(t_val)) = (target.parse::<f64>(), value.parse::<f64>()) {
                    f_val > t_val
                } else {
                    target > value
                }
            }
            "less_than" => {
                let target = if resolved_index.is_none() { &line_to_match } else { target_field };
                if let (Ok(f_val), Ok(t_val)) = (target.parse::<f64>(), value.parse::<f64>()) {
                    f_val < t_val
                } else {
                    target < value
                }
            }
            _ => return Err(MuscleError::Generic(format!("Unsupported operator '{}'", operator))),
        };

        if is_match {
            writer.write_record(&record)
                .map_err(|e| MuscleError::PermissionDenied(format!("Failed to write CSV record: {}", e)))?;
            matched_count += 1;
        }
    }

    writer.flush()
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to flush CSV writer: {}", e)))?;

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

pub fn handle_data_clean(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut sort_by = None;
    let mut sort_descending = false;
    let mut deduplicate = false;
    let mut deduplicate_on = None;
    let mut select_columns = None;
    let mut rename_columns = None;
    let mut fill_na = None;
    let mut drop_na = false;
    let mut derive_columns = None;

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
            "--sort-by" | "--sort_by" => {
                if i + 1 < args.len() {
                    sort_by = Some(args[i + 1].clone());
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --sort-by".to_string()));
                }
            }
            "--sort-descending" | "--sort_descending" => {
                if i + 1 < args.len() {
                    sort_descending = args[i + 1].parse::<bool>()
                        .unwrap_or(false);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --sort-descending".to_string()));
                }
            }
            "--deduplicate" => {
                if i + 1 < args.len() {
                    deduplicate = args[i + 1].parse::<bool>()
                        .unwrap_or(false);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --deduplicate".to_string()));
                }
            }
            "--deduplicate-on" | "--deduplicate_on" => {
                if i + 1 < args.len() {
                    let cols: Vec<String> = args[i + 1].split(',').map(|s| s.trim().to_string()).collect();
                    deduplicate_on = Some(cols);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --deduplicate-on".to_string()));
                }
            }
            "--select-columns" | "--select_columns" => {
                if i + 1 < args.len() {
                    let cols: Vec<String> = args[i + 1].split(',').map(|s| s.trim().to_string()).collect();
                    select_columns = Some(cols);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --select-columns".to_string()));
                }
            }
            "--rename-columns" | "--rename_columns" => {
                if i + 1 < args.len() {
                    let pairs: Vec<(String, String)> = args[i + 1]
                        .split(',')
                        .filter_map(|pair| {
                            let parts: Vec<&str> = pair.split(':').collect();
                            if parts.len() == 2 {
                                Some((parts[0].trim().to_string(), parts[1].trim().to_string()))
                            } else {
                                None
                            }
                        })
                        .collect();
                    rename_columns = Some(pairs);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --rename-columns".to_string()));
                }
            }
            "--fill-na" | "--fill_na" => {
                if i + 1 < args.len() {
                    let pairs: Vec<(String, String)> = args[i + 1]
                        .split(',')
                        .filter_map(|pair| {
                            let parts: Vec<&str> = pair.split(':').collect();
                            if parts.len() == 2 {
                                Some((parts[0].trim().to_string(), parts[1].trim().to_string()))
                            } else {
                                None
                            }
                        })
                        .collect();
                    fill_na = Some(pairs);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --fill-na".to_string()));
                }
            }
            "--drop-na" | "--drop_na" => {
                if i + 1 < args.len() {
                    drop_na = args[i + 1].parse::<bool>()
                        .unwrap_or(false);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --drop-na".to_string()));
                }
            }
            "--derive-columns" | "--derive_columns" => {
                if i + 1 < args.len() {
                    let pairs: Vec<(String, String)> = args[i + 1]
                        .split(',')
                        .filter_map(|pair| {
                            // Find the first '=' character to split the column name and the expression
                            let eq_idx = pair.find('=');
                            if let Some(idx) = eq_idx {
                                let col_name = pair[..idx].trim().to_string();
                                let expr = pair[idx + 1..].trim().to_string();
                                Some((col_name, expr))
                            } else {
                                None
                            }
                        })
                        .collect();
                    derive_columns = Some(pairs);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --derive-columns".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let source = source.ok_or_else(|| MuscleError::Generic("Missing required argument --source".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing required argument --destination".to_string()))?;

    analytical_engine::clean(
        source,
        destination,
        sort_by,
        sort_descending,
        deduplicate,
        deduplicate_on,
        select_columns,
        rename_columns,
        fill_na,
        drop_na,
        derive_columns
    ).map_err(|e| MuscleError::Generic(e))
}

pub fn handle_data_validate(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut quarantine = None;
    let mut rules = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--source" => {
                if i + 1 < args.len() { source = Some(&args[i+1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --source".to_string())); }
            }
            "--destination" => {
                if i + 1 < args.len() { destination = Some(&args[i+1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --destination".to_string())); }
            }
            "--quarantine" => {
                if i + 1 < args.len() { quarantine = Some(&args[i+1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --quarantine".to_string())); }
            }
            "--rules" => {
                if i + 1 < args.len() { rules = Some(&args[i+1]); i += 2; }
                else { return Err(MuscleError::Generic("Missing value for --rules".to_string())); }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let source = source.ok_or_else(|| MuscleError::Generic("Missing required argument --source".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing required argument --destination".to_string()))?;
    let quarantine = quarantine.ok_or_else(|| MuscleError::Generic("Missing required argument --quarantine".to_string()))?;
    let rules = rules.ok_or_else(|| MuscleError::Generic("Missing required argument --rules".to_string()))?;

    analytical_engine::validate(source, destination, quarantine, rules)
        .map_err(|e| MuscleError::Generic(e))
}
