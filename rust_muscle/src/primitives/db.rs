// [WFGY] Zone: SAFE | λ: 0.1 | Action: Database query & insert primitives

use crate::MuscleError;
use crate::db_connector;

pub fn handle_db_query(args: &[String]) -> Result<(), MuscleError> {
    let mut connection_string = None;
    let mut query = None;
    let mut destination = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--connection-string" | "--connection_string" => {
                if i + 1 < args.len() {
                    connection_string = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --connection-string".to_string()));
                }
            }
            "--query" => {
                if i + 1 < args.len() {
                    query = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --query".to_string()));
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

    let connection_string = connection_string.ok_or_else(|| MuscleError::Generic("Missing argument --connection-string".to_string()))?;
    let query = query.ok_or_else(|| MuscleError::Generic("Missing argument --query".to_string()))?;
    let destination = destination.ok_or_else(|| MuscleError::Generic("Missing argument --destination".to_string()))?;

    let rt = tokio::runtime::Runtime::new()
        .map_err(|e| MuscleError::Generic(format!("Failed to build tokio runtime: {}", e)))?;

    rt.block_on(async {
        db_connector::query_to_file(connection_string, query, destination).await
    }).map_err(|e| MuscleError::Generic(e))
}

pub fn handle_db_insert(args: &[String]) -> Result<(), MuscleError> {
    let mut connection_string = None;
    let mut table_name = None;
    let mut source = None;
    let mut mode = String::from("insert");
    let mut schema_drift = false;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--connection-string" | "--connection_string" => {
                if i + 1 < args.len() {
                    connection_string = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --connection-string".to_string()));
                }
            }
            "--table-name" | "--table_name" => {
                if i + 1 < args.len() {
                    table_name = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --table-name".to_string()));
                }
            }
            "--source" => {
                if i + 1 < args.len() {
                    source = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --source".to_string()));
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
            "--schema-drift" | "--schema_drift" => {
                if i + 1 < args.len() {
                    schema_drift = args[i + 1].parse::<bool>().unwrap_or(false);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --schema-drift".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let connection_string = connection_string.ok_or_else(|| MuscleError::Generic("Missing argument --connection-string".to_string()))?;
    let table_name = table_name.ok_or_else(|| MuscleError::Generic("Missing argument --table-name".to_string()))?;
    let source = source.ok_or_else(|| MuscleError::Generic("Missing argument --source".to_string()))?;

    let rt = tokio::runtime::Runtime::new()
        .map_err(|e| MuscleError::Generic(format!("Failed to build tokio runtime: {}", e)))?;

    rt.block_on(async {
        db_connector::insert_from_file(connection_string, table_name, source, &mode, schema_drift).await
    }).map_err(|e| MuscleError::Generic(e))
}

pub fn handle_db_upsert(args: &[String]) -> Result<(), MuscleError> {
    let mut connection_string = None;
    let mut table_name = None;
    let mut source = None;
    let mut keys = None;
    let mut schema_drift = false;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--connection-string" | "--connection_string" => {
                if i + 1 < args.len() {
                    connection_string = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --connection-string".to_string()));
                }
            }
            "--table-name" | "--table_name" => {
                if i + 1 < args.len() {
                    table_name = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --table-name".to_string()));
                }
            }
            "--source" => {
                if i + 1 < args.len() {
                    source = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --source".to_string()));
                }
            }
            "--keys" => {
                if i + 1 < args.len() {
                    keys = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --keys".to_string()));
                }
            }
            "--schema-drift" | "--schema_drift" => {
                if i + 1 < args.len() {
                    schema_drift = args[i + 1].parse::<bool>().unwrap_or(false);
                    i += 2;
                } else {
                    return Err(MuscleError::Generic("Missing value for --schema-drift".to_string()));
                }
            }
            other => {
                return Err(MuscleError::Generic(format!("Unknown argument '{}'", other)));
            }
        }
    }

    let connection_string = connection_string.ok_or_else(|| MuscleError::Generic("Missing argument --connection-string".to_string()))?;
    let table_name = table_name.ok_or_else(|| MuscleError::Generic("Missing argument --table-name".to_string()))?;
    let source = source.ok_or_else(|| MuscleError::Generic("Missing argument --source".to_string()))?;
    let keys = keys.ok_or_else(|| MuscleError::Generic("Missing argument --keys".to_string()))?;

    let rt = tokio::runtime::Runtime::new()
        .map_err(|e| MuscleError::Generic(format!("Failed to build tokio runtime: {}", e)))?;

    rt.block_on(async {
        db_connector::upsert_from_file(connection_string, table_name, source, keys, schema_drift).await
    }).map_err(|e| MuscleError::Generic(e))
}

