// [WFGY] Zone: SAFE | λ: 0.2 | Action: RFC 4180 CSV filter implementation

use crate::MuscleError;
use std::fs;
use std::path::Path;

pub fn handle_data_filter(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut delimiter = String::from(",");
    let mut column_index: Option<usize> = None;
    let mut column_name = None;
    let mut operator = None;
    let mut value = String::new();
    let mut has_headers = false;

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
            "--delimiter" => {
                if i + 1 < args.len() {
                    delimiter = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --delimiter".to_string(),
                    ));
                }
            }
            "--column_index" | "--column-index" => {
                if i + 1 < args.len() {
                    let parsed = args[i + 1].parse::<usize>().map_err(|_| {
                        MuscleError::InvalidArg("Invalid integer for --column-index".to_string())
                    })?;
                    column_index = Some(parsed);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --column-index".to_string(),
                    ));
                }
            }
            "--column_name" | "--column-name" => {
                if i + 1 < args.len() {
                    column_name = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --column-name".to_string(),
                    ));
                }
            }
            "--operator" => {
                if i + 1 < args.len() {
                    operator = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --operator".to_string(),
                    ));
                }
            }
            "--value" => {
                if i + 1 < args.len() {
                    value = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --value".to_string(),
                    ));
                }
            }
            "--has_headers" | "--has-headers" => {
                if i + 1 < args.len() {
                    has_headers = args[i + 1].parse::<bool>().unwrap_or(false);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --has-headers".to_string(),
                    ));
                }
            }
            _ => {
                return Err(MuscleError::InvalidArg(format!(
                    "Unknown argument '{}'",
                    args[i]
                )));
            }
        }
    }

    let source = source
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --source".to_string()))?;
    let destination = destination.ok_or_else(|| {
        MuscleError::MissingArg("Missing required argument --destination".to_string())
    })?;
    let operator = operator.ok_or_else(|| {
        MuscleError::MissingArg("Missing required argument --operator".to_string())
    })?;

    filter_data(
        source,
        destination,
        &delimiter,
        column_index,
        column_name.map(|s| s.as_str()),
        operator,
        &value,
        has_headers,
    )
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
        return Err(MuscleError::SourceNotFound(format!(
            "Source file '{}' does not exist",
            source
        )));
    }

    let delim_byte = delimiter.as_bytes().first().copied().unwrap_or(b',');

    let mut reader = csv::ReaderBuilder::new()
        .delimiter(delim_byte)
        .has_headers(has_headers)
        .from_path(src_path)
        .map_err(|e| MuscleError::IoError(format!("Failed to open CSV reader: {}", e)))?;

    let dest_path = Path::new(destination);
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

    let mut writer = csv::WriterBuilder::new()
        .delimiter(delim_byte)
        .from_path(dest_path)
        .map_err(|e| {
            MuscleError::PermissionDenied(format!("Failed to create destination CSV writer: {}", e))
        })?;

    let mut resolved_index = column_index;
    let headers = reader
        .headers()
        .map_err(|e| MuscleError::IoError(format!("Failed to read CSV headers: {}", e)))?
        .clone();

    if has_headers {
        writer.write_record(&headers).map_err(|e| {
            MuscleError::PermissionDenied(format!("Failed to write CSV headers: {}", e))
        })?;

        if let Some(col_name) = column_name {
            if let Some(idx) = headers.iter().position(|h| h.trim() == col_name.trim()) {
                resolved_index = Some(idx);
            } else {
                return Err(MuscleError::IoError(format!(
                    "Header column '{}' not found in headers row: {:?}",
                    col_name, headers
                )));
            }
        }
    }

    let regex_pattern = if operator == "regex" {
        Some(
            regex::Regex::new(value)
                .map_err(|e| MuscleError::InvalidArg(format!("Invalid Regex pattern: {}", e)))?,
        )
    } else {
        None
    };

    let mut matched_count = 0;

    for result in reader.records() {
        let record =
            result.map_err(|e| MuscleError::IoError(format!("Error reading CSV record: {}", e)))?;

        let target_field = match resolved_index {
            Some(idx) => {
                if idx < record.len() {
                    record[idx].trim()
                } else {
                    ""
                }
            }
            None => "",
        };

        let line_to_match = if resolved_index.is_none() {
            record.iter().collect::<Vec<_>>().join(delimiter)
        } else {
            target_field.to_string()
        };

        let is_match = match operator {
            "equals" => {
                (resolved_index.is_none() && line_to_match == value)
                    || (resolved_index.is_some() && target_field == value)
            }
            "not_equals" => {
                (resolved_index.is_none() && line_to_match != value)
                    || (resolved_index.is_some() && target_field != value)
            }
            "contains" => {
                (resolved_index.is_none() && line_to_match.contains(value))
                    || (resolved_index.is_some() && target_field.contains(value))
            }
            "not_contains" => {
                (resolved_index.is_none() && !line_to_match.contains(value))
                    || (resolved_index.is_some() && !target_field.contains(value))
            }
            "starts_with" => {
                (resolved_index.is_none() && line_to_match.starts_with(value))
                    || (resolved_index.is_some() && target_field.starts_with(value))
            }
            "ends_with" => {
                (resolved_index.is_none() && line_to_match.ends_with(value))
                    || (resolved_index.is_some() && target_field.ends_with(value))
            }
            "regex" => {
                let target = if resolved_index.is_none() {
                    &line_to_match
                } else {
                    target_field
                };
                if let Some(re) = &regex_pattern {
                    re.is_match(target)
                } else {
                    false
                }
            }
            "greater_than" | "gt" => {
                let target = if resolved_index.is_none() {
                    &line_to_match
                } else {
                    target_field
                };
                if let (Ok(f_val), Ok(t_val)) = (target.parse::<f64>(), value.parse::<f64>()) {
                    f_val > t_val
                } else {
                    target > value
                }
            }
            "greater_or_equal" | "greater_than_or_equal" | "gte" => {
                let target = if resolved_index.is_none() {
                    &line_to_match
                } else {
                    target_field
                };
                if let (Ok(f_val), Ok(t_val)) = (target.parse::<f64>(), value.parse::<f64>()) {
                    f_val >= t_val
                } else {
                    target >= value
                }
            }
            "less_than" | "lt" => {
                let target = if resolved_index.is_none() {
                    &line_to_match
                } else {
                    target_field
                };
                if let (Ok(f_val), Ok(t_val)) = (target.parse::<f64>(), value.parse::<f64>()) {
                    f_val < t_val
                } else {
                    target < value
                }
            }
            "less_or_equal" | "less_than_or_equal" | "lte" => {
                let target = if resolved_index.is_none() {
                    &line_to_match
                } else {
                    target_field
                };
                if let (Ok(f_val), Ok(t_val)) = (target.parse::<f64>(), value.parse::<f64>()) {
                    f_val <= t_val
                } else {
                    target <= value
                }
            }
            "is_null" | "is_empty" => {
                let target = if resolved_index.is_none() {
                    &line_to_match
                } else {
                    target_field
                };
                target.is_empty()
            }
            "is_not_null" | "is_not_empty" => {
                let target = if resolved_index.is_none() {
                    &line_to_match
                } else {
                    target_field
                };
                !target.is_empty()
            }
            "in" => {
                let target = if resolved_index.is_none() {
                    &line_to_match
                } else {
                    target_field
                };
                value.split(',').any(|v| v.trim() == target)
            }
            "not_in" => {
                let target = if resolved_index.is_none() {
                    &line_to_match
                } else {
                    target_field
                };
                value.split(',').all(|v| v.trim() != target)
            }
            _ => {
                return Err(MuscleError::InvalidArg(format!(
                    "Unsupported operator '{}'",
                    operator
                )));
            }
        };

        if is_match {
            writer.write_record(&record).map_err(|e| {
                MuscleError::PermissionDenied(format!("Failed to write CSV record: {}", e))
            })?;
            matched_count += 1;
        }
    }

    writer
        .flush()
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to flush CSV writer: {}", e)))?;

    println!(
        "SUCCESS: Filtered data from '{}' to '{}'. Matched rows: {}",
        source, destination, matched_count
    );
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
                    return Err(MuscleError::MissingArg(
                        "Missing value for --source".to_string(),
                    ));
                }
            }
            "--destination-prefix" | "--destination_prefix" => {
                if i + 1 < args.len() {
                    destination_prefix = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --destination-prefix".to_string(),
                    ));
                }
            }
            "--by-column" | "--by_column" => {
                if i + 1 < args.len() {
                    by_column = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --by-column".to_string(),
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

    let source =
        source.ok_or_else(|| MuscleError::MissingArg("Missing argument --source".to_string()))?;
    let destination_prefix = destination_prefix.ok_or_else(|| {
        MuscleError::MissingArg("Missing argument --destination-prefix".to_string())
    })?;
    let by_column = by_column
        .ok_or_else(|| MuscleError::MissingArg("Missing argument --by-column".to_string()))?;

    analytical_engine::split(source, destination_prefix, by_column)
        .map_err(|e| MuscleError::IoError(format!("CSV read error: {}", e)))
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
                    return Err(MuscleError::MissingArg(
                        "Missing value for --sources".to_string(),
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

    let sources_str =
        sources.ok_or_else(|| MuscleError::MissingArg("Missing argument --sources".to_string()))?;
    let destination = destination
        .ok_or_else(|| MuscleError::MissingArg("Missing argument --destination".to_string()))?;

    let sources_list: Vec<String> = sources_str
        .split(',')
        .map(|s| s.trim().to_string())
        .collect();

    analytical_engine::merge(sources_list, destination)
        .map_err(|e| MuscleError::IoError(format!("CSV read error: {}", e)))
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
                    return Err(MuscleError::MissingArg(
                        "Missing value for --source".to_string(),
                    ));
                }
            }
            "--destination-prefix" | "--destination_prefix" => {
                if i + 1 < args.len() {
                    destination_prefix = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --destination-prefix".to_string(),
                    ));
                }
            }
            "--accumulate-column" | "--accumulate_column" => {
                if i + 1 < args.len() {
                    accumulate_column = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --accumulate-column".to_string(),
                    ));
                }
            }
            "--threshold" => {
                if i + 1 < args.len() {
                    let parsed = args[i + 1].parse::<f64>().map_err(|_| {
                        MuscleError::InvalidArg("Invalid float for --threshold".to_string())
                    })?;
                    threshold = Some(parsed);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --threshold".to_string(),
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

    let source =
        source.ok_or_else(|| MuscleError::MissingArg("Missing argument --source".to_string()))?;
    let destination_prefix = destination_prefix.ok_or_else(|| {
        MuscleError::MissingArg("Missing argument --destination-prefix".to_string())
    })?;
    let accumulate_column = accumulate_column.ok_or_else(|| {
        MuscleError::MissingArg("Missing argument --accumulate-column".to_string())
    })?;
    let threshold = threshold
        .ok_or_else(|| MuscleError::MissingArg("Missing argument --threshold".to_string()))?;

    analytical_engine::chunk_cumulative(source, destination_prefix, accumulate_column, threshold)
        .map_err(|e| MuscleError::IoError(format!("CSV read error: {}", e)))
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
    let mut right_source = None;
    let mut left_on = None;
    let mut right_on = None;
    let mut how_join = None;

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
            "--sort-by" | "--sort_by" => {
                if i + 1 < args.len() {
                    sort_by = Some(args[i + 1].clone());
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --sort-by".to_string(),
                    ));
                }
            }
            "--sort-descending" | "--sort_descending" => {
                if i + 1 < args.len() {
                    sort_descending = args[i + 1].parse::<bool>().unwrap_or(false);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --sort-descending".to_string(),
                    ));
                }
            }
            "--deduplicate" => {
                if i + 1 < args.len() {
                    deduplicate = args[i + 1].parse::<bool>().unwrap_or(false);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --deduplicate".to_string(),
                    ));
                }
            }
            "--deduplicate-on" | "--deduplicate_on" => {
                if i + 1 < args.len() {
                    let cols: Vec<String> = args[i + 1]
                        .split(',')
                        .map(|s| s.trim().to_string())
                        .collect();
                    deduplicate_on = Some(cols);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --deduplicate-on".to_string(),
                    ));
                }
            }
            "--select-columns" | "--select_columns" => {
                if i + 1 < args.len() {
                    let cols: Vec<String> = args[i + 1]
                        .split(',')
                        .map(|s| s.trim().to_string())
                        .collect();
                    select_columns = Some(cols);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --select-columns".to_string(),
                    ));
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
                    return Err(MuscleError::MissingArg(
                        "Missing value for --rename-columns".to_string(),
                    ));
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
                    return Err(MuscleError::MissingArg(
                        "Missing value for --fill-na".to_string(),
                    ));
                }
            }
            "--drop-na" | "--drop_na" => {
                if i + 1 < args.len() {
                    drop_na = args[i + 1].parse::<bool>().unwrap_or(false);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --drop-na".to_string(),
                    ));
                }
            }
            "--derive-columns" | "--derive_columns" => {
                if i + 1 < args.len() {
                    let pairs: Vec<(String, String)> = args[i + 1]
                        .split(',')
                        .filter_map(|pair| {
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
                    return Err(MuscleError::MissingArg(
                        "Missing value for --derive-columns".to_string(),
                    ));
                }
            }
            "--right-source" | "--right_source" => {
                if i + 1 < args.len() {
                    right_source = Some(args[i + 1].clone());
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --right-source".to_string(),
                    ));
                }
            }
            "--left-on" | "--left_on" => {
                if i + 1 < args.len() {
                    left_on = Some(args[i + 1].clone());
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --left-on".to_string(),
                    ));
                }
            }
            "--right-on" | "--right_on" => {
                if i + 1 < args.len() {
                    right_on = Some(args[i + 1].clone());
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --right-on".to_string(),
                    ));
                }
            }
            "--how-join" | "--how_join" => {
                if i + 1 < args.len() {
                    how_join = Some(args[i + 1].clone());
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --how-join".to_string(),
                    ));
                }
            }
            "--streaming" => {
                if i + 1 < args.len() {
                    let streaming_val = args[i + 1].parse::<bool>().unwrap_or(false);
                    if streaming_val {
                        unsafe {
                            std::env::set_var("POLARS_STREAMING", "true");
                        }
                    }
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --streaming".to_string(),
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
        derive_columns,
        right_source,
        left_on,
        right_on,
        how_join,
    )
    .map_err(|e| MuscleError::IoError(format!("Merge stream error: {}", e)))
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
            "--quarantine" => {
                if i + 1 < args.len() {
                    quarantine = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --quarantine".to_string(),
                    ));
                }
            }
            "--rules" => {
                if i + 1 < args.len() {
                    rules = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --rules".to_string(),
                    ));
                }
            }
            "--streaming" => {
                if i + 1 < args.len() {
                    let streaming_val = args[i + 1].parse::<bool>().unwrap_or(false);
                    if streaming_val {
                        unsafe {
                            std::env::set_var("POLARS_STREAMING", "true");
                        }
                    }
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --streaming".to_string(),
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
    let quarantine = quarantine.ok_or_else(|| {
        MuscleError::MissingArg("Missing required argument --quarantine".to_string())
    })?;
    let rules = rules
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --rules".to_string()))?;

    analytical_engine::validate(source, destination, quarantine, rules)
        .map_err(|e| MuscleError::IoError(format!("CSV read error: {}", e)))
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

    fn write_csv(dir: &TempDir, name: &str, headers: &str, rows: &[&str]) -> String {
        let path = dir.path().join(name);
        let mut f = fs::File::create(&path).unwrap();
        writeln!(f, "{}", headers).unwrap();
        for row in rows {
            writeln!(f, "{}", row).unwrap();
        }
        path.to_string_lossy().to_string()
    }

    // --- data.filter ---

    #[test]
    fn test_filter_equals() {
        let tmp = TempDir::new().unwrap();
        let src = write_csv(&tmp, "in.csv", "a,b", &["1,x", "2,y", "3,x"]);
        let dst = tmp.path().join("out.csv").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination"),
            s(&dst),
            s("--column-name"),
            s("b"),
            s("--operator"),
            s("equals"),
            s("--value"),
            s("x"),
            s("--has-headers"),
            s("true"),
        ];
        let result = handle_data_filter(&args);
        assert!(result.is_ok(), "filter failed: {:?}", result);
        let content = fs::read_to_string(&dst).unwrap();
        assert!(content.contains("1,x"));
        assert!(content.contains("3,x"));
        assert!(!content.contains("2,y"));
    }

    #[test]
    fn test_filter_not_equals() {
        let tmp = TempDir::new().unwrap();
        let src = write_csv(&tmp, "in.csv", "a,b", &["1,x", "2,y", "3,x"]);
        let dst = tmp.path().join("out.csv").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination"),
            s(&dst),
            s("--column-name"),
            s("b"),
            s("--operator"),
            s("not_equals"),
            s("--value"),
            s("x"),
            s("--has-headers"),
            s("true"),
        ];
        let result = handle_data_filter(&args);
        assert!(result.is_ok());
        assert!(fs::read_to_string(&dst).unwrap().contains("2,y"));
    }

    #[test]
    fn test_filter_contains() {
        let tmp = TempDir::new().unwrap();
        let src = write_csv(&tmp, "in.csv", "name", &["hello", "world", "help"]);
        let dst = tmp.path().join("out.csv").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination"),
            s(&dst),
            s("--column-name"),
            s("name"),
            s("--operator"),
            s("contains"),
            s("--value"),
            s("hel"),
            s("--has-headers"),
            s("true"),
        ];
        let result = handle_data_filter(&args);
        assert!(result.is_ok());
        let out = fs::read_to_string(&dst).unwrap();
        assert!(out.contains("hello"));
        assert!(out.contains("help"));
        assert!(!out.contains("world"));
    }

    fn assert_lines_contain(out: &str, expected: &[&str]) {
        let lines: Vec<&str> = out.lines().collect();
        for exp in expected {
            assert!(
                lines.contains(exp),
                "Expected '{}' in output lines: {:?}",
                exp,
                lines
            );
        }
    }

    fn assert_lines_not_contain(out: &str, unexpected: &[&str]) {
        let lines: Vec<&str> = out.lines().collect();
        for unexp in unexpected {
            assert!(
                !lines.contains(unexp),
                "Did not expect '{}' in output lines: {:?}",
                unexp,
                lines
            );
        }
    }

    #[test]
    fn test_filter_greater_than() {
        let tmp = TempDir::new().unwrap();
        let src = write_csv(&tmp, "in.csv", "val", &["5", "10", "15"]);
        let dst = tmp.path().join("out.csv").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination"),
            s(&dst),
            s("--column-name"),
            s("val"),
            s("--operator"),
            s("greater_than"),
            s("--value"),
            s("9"),
            s("--has-headers"),
            s("true"),
        ];
        assert!(handle_data_filter(&args).is_ok());
        let out = fs::read_to_string(&dst).unwrap();
        assert_lines_contain(&out, &["10", "15"]);
        assert_lines_not_contain(&out, &["5"]);
    }

    #[test]
    fn test_filter_greater_or_equal() {
        let tmp = TempDir::new().unwrap();
        let src = write_csv(&tmp, "in.csv", "val", &["5", "10", "15"]);
        let dst = tmp.path().join("out.csv").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination"),
            s(&dst),
            s("--column-name"),
            s("val"),
            s("--operator"),
            s("greater_or_equal"),
            s("--value"),
            s("10"),
            s("--has-headers"),
            s("true"),
        ];
        assert!(handle_data_filter(&args).is_ok());
        let out = fs::read_to_string(&dst).unwrap();
        assert_lines_contain(&out, &["10", "15"]);
        assert_lines_not_contain(&out, &["5"]);
    }

    #[test]
    fn test_filter_less_than() {
        let tmp = TempDir::new().unwrap();
        let src = write_csv(&tmp, "in.csv", "val", &["5", "10", "15"]);
        let dst = tmp.path().join("out.csv").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination"),
            s(&dst),
            s("--column-name"),
            s("val"),
            s("--operator"),
            s("less_than"),
            s("--value"),
            s("11"),
            s("--has-headers"),
            s("true"),
        ];
        assert!(handle_data_filter(&args).is_ok());
        let out = fs::read_to_string(&dst).unwrap();
        assert_lines_contain(&out, &["5", "10"]);
        assert_lines_not_contain(&out, &["15"]);
    }

    #[test]
    fn test_filter_less_or_equal() {
        let tmp = TempDir::new().unwrap();
        let src = write_csv(&tmp, "in.csv", "val", &["5", "10", "15"]);
        let dst = tmp.path().join("out.csv").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination"),
            s(&dst),
            s("--column-name"),
            s("val"),
            s("--operator"),
            s("less_or_equal"),
            s("--value"),
            s("10"),
            s("--has-headers"),
            s("true"),
        ];
        assert!(handle_data_filter(&args).is_ok());
        let out = fs::read_to_string(&dst).unwrap();
        assert_lines_contain(&out, &["5", "10"]);
        assert_lines_not_contain(&out, &["15"]);
    }

    #[test]
    fn test_filter_in() {
        let tmp = TempDir::new().unwrap();
        let src = write_csv(&tmp, "in.csv", "status", &["a", "b", "c", "d"]);
        let dst = tmp.path().join("out.csv").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination"),
            s(&dst),
            s("--column-name"),
            s("status"),
            s("--operator"),
            s("in"),
            s("--value"),
            s("a,c"),
            s("--has-headers"),
            s("true"),
        ];
        let result = handle_data_filter(&args);
        assert!(result.is_ok());
        let out = fs::read_to_string(&dst).unwrap();
        assert!(out.contains("a"));
        assert!(out.contains("c"));
        assert!(!out.contains("b"));
        assert!(!out.contains("d"));
    }

    #[test]
    fn test_filter_is_null() {
        let tmp = TempDir::new().unwrap();
        let src = write_csv(&tmp, "in.csv", "val", &["x", "", "y"]);
        let dst = tmp.path().join("out.csv").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination"),
            s(&dst),
            s("--column-name"),
            s("val"),
            s("--operator"),
            s("is_null"),
            s("--has-headers"),
            s("true"),
        ];
        let result = handle_data_filter(&args);
        assert!(result.is_ok());
        let out = fs::read_to_string(&dst).unwrap();
        assert!(!out.contains("x"));
        assert!(!out.contains("y"));
        // only the empty row (header + empty val line) should remain
    }

    #[test]
    fn test_filter_is_not_null() {
        let tmp = TempDir::new().unwrap();
        let src = write_csv(&tmp, "in.csv", "val", &["x", "", "y"]);
        let dst = tmp.path().join("out.csv").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination"),
            s(&dst),
            s("--column-name"),
            s("val"),
            s("--operator"),
            s("is_not_null"),
            s("--has-headers"),
            s("true"),
        ];
        let result = handle_data_filter(&args);
        assert!(result.is_ok());
        let out = fs::read_to_string(&dst).unwrap();
        assert!(out.contains("x"));
        assert!(out.contains("y"));
        assert!(!out.contains(",,"));
    }

    #[test]
    fn test_filter_regex() {
        let tmp = TempDir::new().unwrap();
        let src = write_csv(&tmp, "in.csv", "code", &["AB12", "CD34", "EF56"]);
        let dst = tmp.path().join("out.csv").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination"),
            s(&dst),
            s("--column-name"),
            s("code"),
            s("--operator"),
            s("regex"),
            s("--value"),
            s("^[A-Z]{2}\\d{2}$"),
            s("--has-headers"),
            s("true"),
        ];
        let result = handle_data_filter(&args);
        assert!(result.is_ok());
        let out = fs::read_to_string(&dst).unwrap();
        assert!(out.contains("AB12"));
        assert!(out.contains("CD34"));
    }

    #[test]
    fn test_filter_missing_operator() {
        let tmp = TempDir::new().unwrap();
        let src = write_csv(&tmp, "in.csv", "a", &["1"]);
        let dst = tmp.path().join("out.csv").to_string_lossy().to_string();
        let args: Vec<String> = vec![s("--source"), s(&src), s("--destination"), s(&dst)];
        let result = handle_data_filter(&args);
        assert!(result.is_err());
    }

    #[test]
    fn test_filter_unsupported_operator() {
        let tmp = TempDir::new().unwrap();
        let src = write_csv(&tmp, "in.csv", "a", &["1"]);
        let dst = tmp.path().join("out.csv").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination"),
            s(&dst),
            s("--column-name"),
            s("a"),
            s("--operator"),
            s("bogus"),
            s("--value"),
            s("1"),
            s("--has-headers"),
            s("true"),
        ];
        let result = handle_data_filter(&args);
        assert!(result.is_err());
    }

    // --- data.split ---

    #[test]
    fn test_split_basic() {
        let tmp = TempDir::new().unwrap();
        let src = write_csv(&tmp, "in.csv", "cat,val", &["a,1", "b,2", "a,3"]);
        let prefix = tmp.path().join("split_").to_string_lossy().to_string();
        let args: Vec<String> = vec![
            s("--source"),
            s(&src),
            s("--destination-prefix"),
            s(&prefix),
            s("--by-column"),
            s("cat"),
        ];
        let result = handle_data_split(&args);
        assert!(result.is_ok(), "split failed: {:?}", result);
        let files: Vec<String> = std::fs::read_dir(tmp.path())
            .unwrap()
            .filter_map(|e| e.ok().map(|e| e.file_name().to_string_lossy().to_string()))
            .collect();
        // at least the split output files exist (naming depends on Polars version)
        assert!(
            files.iter().any(|f| f.contains("split_")),
            "no split_ files found in {:?}",
            files
        );
    }
}
