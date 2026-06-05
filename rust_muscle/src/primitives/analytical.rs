// [WFGY] Zone: SAFE | λ: 0.1 | Action: Analytical Polars primitives

use crate::MuscleError;

pub fn handle_data_groupby(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut groupby_columns = None;
    let mut aggregate_column = None;
    let mut operation = None;

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
            "--groupby-columns" | "--groupby_columns" => {
                if i + 1 < args.len() {
                    groupby_columns = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --groupby-columns".to_string()));
                }
            }
            "--aggregate-column" | "--aggregate_column" => {
                if i + 1 < args.len() {
                    aggregate_column = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --aggregate-column".to_string()));
                }
            }
            "--operation" => {
                if i + 1 < args.len() {
                    operation = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --operation".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let source = source.ok_or_else(|| MuscleError::Generic("Missing argument --source".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing argument --destination".to_string()))?;
    let groupby_str = groupby_columns.ok_or_else(|| MuscleError::Generic("Missing argument --groupby-columns".to_string()))?;
    let agg_col = aggregate_column.ok_or_else(|| MuscleError::Generic("Missing argument --aggregate-column".to_string()))?;
    let op = operation.ok_or_else(|| MuscleError::Generic("Missing argument --operation".to_string()))?;

    let groupby_cols: Vec<String> = groupby_str.split(',').map(|s| s.trim().to_string()).collect();

    analytical_engine::groupby(source, destination, groupby_cols, agg_col, op)
        .map_err(|e| MuscleError::Generic(e))
}

pub fn handle_data_join(args: &[String]) -> Result<(), MuscleError> {
    let mut left_source = None;
    let mut right_source = None;
    let mut destination = None;
    let mut left_on = None;
    let mut right_on = None;
    let mut how = String::from("inner");

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--left-source" | "--left_source" => {
                if i + 1 < args.len() {
                    left_source = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --left-source".to_string()));
                }
            }
            "--right-source" | "--right_source" => {
                if i + 1 < args.len() {
                    right_source = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --right-source".to_string()));
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
            "--left-on" | "--left_on" => {
                if i + 1 < args.len() {
                    left_on = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --left-on".to_string()));
                }
            }
            "--right-on" | "--right_on" => {
                if i + 1 < args.len() {
                    right_on = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --right-on".to_string()));
                }
            }
            "--how" => {
                if i + 1 < args.len() {
                    how = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --how".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let left_source = left_source.ok_or_else(|| MuscleError::Generic("Missing argument --left-source".to_string()))?;
    let right_source = right_source.ok_or_else(|| MuscleError::Generic("Missing argument --right-source".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing argument --destination".to_string()))?;
    let left_on = left_on.ok_or_else(|| MuscleError::Generic("Missing argument --left-on".to_string()))?;
    let right_on = right_on.ok_or_else(|| MuscleError::Generic("Missing argument --right-on".to_string()))?;

    analytical_engine::join(left_source, right_source, destination, left_on, right_on, &how)
        .map_err(|e| MuscleError::Generic(e))
}

pub fn handle_data_metrics(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut column_name = None;
    let mut operation = None;
    let mut regex_pattern = None;
    let mut limit_rows = None;

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
            "--column-name" | "--column_name" => {
                if i + 1 < args.len() {
                    column_name = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --column-name".to_string()));
                }
            }
            "--operation" => {
                if i + 1 < args.len() {
                    operation = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --operation".to_string()));
                }
            }
            "--regex-pattern" | "--regex_pattern" => {
                if i + 1 < args.len() {
                    regex_pattern = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --regex-pattern".to_string()));
                }
            }
            "--limit-rows" | "--limit_rows" => {
                if i + 1 < args.len() {
                    let parsed = args[i + 1].parse::<usize>()
                        .map_err(|_| MuscleError::Generic("Invalid integer for --limit-rows".to_string()))?;
                    limit_rows = Some(parsed);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --limit-rows".to_string()));
                }
            }
            "--destination-variable" | "--destination_variable" => {
                i += 2;
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let source = source.ok_or_else(|| MuscleError::Generic("Missing argument --source".to_string()))?;
    let column_name = column_name.ok_or_else(|| MuscleError::Generic("Missing argument --column-name".to_string()))?;
    let operation = operation.ok_or_else(|| MuscleError::Generic("Missing argument --operation".to_string()))?;

    let result_json = analytical_engine::calculate_metric(
        source,
        column_name,
        operation,
        regex_pattern.map(|s| s.as_str()),
        limit_rows,
    ).map_err(|e| MuscleError::Generic(e))?;

    println!("{}", result_json);
    Ok(())
}

pub fn handle_data_lookup(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut lookup_file = None;
    let mut source_key = None;
    let mut lookup_key = None;
    let mut lookup_value = None;
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
            "--lookup-file" | "--lookup_file" => {
                if i + 1 < args.len() {
                    lookup_file = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --lookup-file".to_string()));
                }
            }
            "--source-key" | "--source_key" => {
                if i + 1 < args.len() {
                    source_key = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --source-key".to_string()));
                }
            }
            "--lookup-key" | "--lookup_key" => {
                if i + 1 < args.len() {
                    lookup_key = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --lookup-key".to_string()));
                }
            }
            "--lookup-value" | "--lookup_value" => {
                if i + 1 < args.len() {
                    lookup_value = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --lookup-value".to_string()));
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

    let source = source.ok_or_else(|| MuscleError::Generic("Missing argument --source".to_string()))?;
    let lookup_file = lookup_file.ok_or_else(|| MuscleError::Generic("Missing argument --lookup-file".to_string()))?;
    let source_key = source_key.ok_or_else(|| MuscleError::Generic("Missing argument --source-key".to_string()))?;
    let lookup_key = lookup_key.ok_or_else(|| MuscleError::Generic("Missing argument --lookup-key".to_string()))?;
    let lookup_value = lookup_value.ok_or_else(|| MuscleError::Generic("Missing argument --lookup-value".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing argument --destination".to_string()))?;

    analytical_engine::lookup(source, lookup_file, source_key, lookup_key, lookup_value, destination)
        .map_err(|e| MuscleError::Generic(e))
}

pub fn handle_data_deduplicate(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut subset = None;
    let mut keep = String::from("first");

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
            "--subset" => {
                if i + 1 < args.len() {
                    subset = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --subset".to_string()));
                }
            }
            "--keep" => {
                if i + 1 < args.len() {
                    keep = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --keep".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let source = source.ok_or_else(|| MuscleError::Generic("Missing argument --source".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing argument --destination".to_string()))?;
    let subset_str = subset.ok_or_else(|| MuscleError::Generic("Missing argument --subset".to_string()))?;

    let subset_cols: Vec<String> = subset_str.split(',').map(|s| s.trim().to_string()).collect();

    analytical_engine::deduplicate(source, destination, subset_cols, &keep)
        .map_err(|e| MuscleError::Generic(e))
}

