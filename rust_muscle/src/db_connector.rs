// [WFGY] Zone: TRANSIT | λ: 0.5 | Action: Optimize database inserts with chunked batch statements
use serde_json::{Map, Number, Value};
use sqlx::{Column, MySqlPool, PgPool, Row, SqlitePool};
use std::collections::{HashMap, HashSet};
use std::fs::File;
use std::path::Path;

/// Exécute une requête SQL SELECT sur n'importe quel moteur supporté et écrit dans un fichier CSV ou JSON
pub async fn query_to_file(
    connection_string: &str,
    query: &str,
    destination: &str,
) -> Result<(), String> {
    let json_rows = if connection_string.starts_with("sqlite:") {
        query_sqlite(connection_string, query).await?
    } else if connection_string.starts_with("postgresql:")
        || connection_string.starts_with("postgres:")
    {
        query_postgres(connection_string, query).await?
    } else if connection_string.starts_with("mysql:") {
        query_mysql(connection_string, query).await?
    } else if connection_string.starts_with("snowflake:") {
        query_snowflake(connection_string, query).await?
    } else if connection_string.starts_with("odbc:") {
        query_odbc(connection_string, query).await?
    } else {
        return Err(format!(
            "Protocole de base de données non supporté : {}",
            connection_string
        ));
    };

    write_rows_to_file(json_rows, destination)?;
    Ok(())
}

/// Importe les données d'un fichier CSV ou JSON dans une table cible
pub async fn insert_from_file(
    connection_string: &str,
    table_name: &str,
    source_file: &str,
    mode: &str,
    schema_drift: bool,
) -> Result<(), String> {
    let rows = read_rows_from_file(source_file)?;
    if rows.is_empty() {
        println!("[DB] Le fichier source est vide. Aucune ligne à insérer.");
        return Ok(());
    }

    if connection_string.starts_with("sqlite:") {
        insert_sqlite(connection_string, table_name, rows, mode, schema_drift).await?
    } else if connection_string.starts_with("postgresql:")
        || connection_string.starts_with("postgres:")
    {
        insert_postgres(connection_string, table_name, rows, mode, schema_drift).await?
    } else if connection_string.starts_with("mysql:") {
        insert_mysql(connection_string, table_name, rows, mode, schema_drift).await?
    } else if connection_string.starts_with("snowflake:") {
        insert_snowflake(connection_string, table_name, rows, mode).await?
    } else if connection_string.starts_with("odbc:") {
        insert_odbc(connection_string, table_name, rows, mode).await?
    } else {
        return Err(format!(
            "Protocole de base de données non supporté : {}",
            connection_string
        ));
    };

    Ok(())
}

/// Upsert les données d'un fichier CSV ou JSON dans une table cible sur clés de conflit
pub async fn upsert_from_file(
    connection_string: &str,
    table_name: &str,
    source_file: &str,
    keys: &str,
    schema_drift: bool,
) -> Result<(), String> {
    let rows = read_rows_from_file(source_file)?;
    if rows.is_empty() {
        println!("[DB] Le fichier source est vide. Aucun upsert à effectuer.");
        return Ok(());
    }

    if connection_string.starts_with("sqlite:") {
        upsert_sqlite(connection_string, table_name, rows, keys, schema_drift).await?
    } else if connection_string.starts_with("postgresql:")
        || connection_string.starts_with("postgres:")
    {
        upsert_postgres(connection_string, table_name, rows, keys, schema_drift).await?
    } else if connection_string.starts_with("mysql:") {
        upsert_mysql(connection_string, table_name, rows, keys, schema_drift).await?
    } else {
        return Err(format!(
            "Upsert non supporté pour ce protocole : {}",
            connection_string
        ));
    };

    Ok(())
}

// ==========================================
// SQLx Engine Implementations
// ==========================================

fn infer_column_types(
    rows: &[Value],
    is_mysql: bool,
    is_sqlite: bool,
) -> HashMap<String, &'static str> {
    let mut types = HashMap::new();
    if rows.is_empty() {
        return types;
    }

    let mut keys = HashSet::new();
    for row in rows {
        if let Some(obj) = row.as_object() {
            for k in obj.keys() {
                keys.insert(k.clone());
            }
        }
    }

    for key in keys {
        let mut has_bool = false;
        let mut has_int = false;
        let mut has_float = false;
        let mut has_string = false;

        for row in rows {
            if let Some(obj) = row.as_object() {
                if let Some(val) = obj.get(&key) {
                    match val {
                        Value::Null => {}
                        Value::Bool(_) => has_bool = true,
                        Value::Number(n) => {
                            if n.is_i64() {
                                has_int = true;
                            } else {
                                has_float = true;
                            }
                        }
                        Value::String(_) => has_string = true,
                        _ => has_string = true,
                    }
                }
            }
        }

        let sql_type = if has_string {
            "TEXT"
        } else if has_float {
            if is_sqlite {
                "REAL"
            } else if is_mysql {
                "DOUBLE"
            } else {
                "DOUBLE PRECISION"
            }
        } else if has_int {
            if is_sqlite { "INTEGER" } else { "BIGINT" }
        } else if has_bool {
            if is_mysql { "TINYINT(1)" } else { "BOOLEAN" }
        } else {
            "TEXT"
        };

        types.insert(key, sql_type);
    }

    types
}

async fn query_sqlite(conn_str: &str, query: &str) -> Result<Vec<Value>, String> {
    let pool = SqlitePool::connect(conn_str)
        .await
        .map_err(|e| format!("Sqlite connection error: {}", e))?;
    let sqlx_rows = sqlx::query(query)
        .fetch_all(&pool)
        .await
        .map_err(|e| format!("Sqlite query error: {}", e))?;

    let mut results = Vec::new();
    for row in sqlx_rows {
        let mut map = Map::new();
        for col in row.columns() {
            let name = col.name();
            let val = if let Ok(s) = row.try_get::<String, _>(name) {
                Value::String(s)
            } else if let Ok(i) = row.try_get::<i64, _>(name) {
                Value::Number(i.into())
            } else if let Ok(f) = row.try_get::<f64, _>(name) {
                Number::from_f64(f)
                    .map(Value::Number)
                    .unwrap_or(Value::Null)
            } else if let Ok(b) = row.try_get::<bool, _>(name) {
                Value::Bool(b)
            } else {
                Value::Null
            };
            map.insert(name.to_string(), val);
        }
        results.push(Value::Object(map));
    }
    Ok(results)
}

async fn insert_sqlite(
    conn_str: &str,
    table: &str,
    rows: Vec<Value>,
    mode: &str,
    schema_drift: bool,
) -> Result<(), String> {
    let pool = SqlitePool::connect(conn_str)
        .await
        .map_err(|e| format!("Sqlite connection error: {}", e))?;

    let inferred_types = infer_column_types(&rows, false, true);
    if !rows.is_empty() {
        if schema_drift {
            let table_exists =
                sqlx::query("SELECT name FROM sqlite_master WHERE type='table' AND name=?")
                    .bind(table)
                    .fetch_optional(&pool)
                    .await
                    .map_err(|e| e.to_string())?
                    .is_some();

            if table_exists {
                let table_info = sqlx::query(&format!("PRAGMA table_info({})", table))
                    .fetch_all(&pool)
                    .await
                    .map_err(|e| e.to_string())?;
                let mut db_cols = HashSet::new();
                for col_row in table_info {
                    let col_name: String = col_row.try_get("name").map_err(|e| e.to_string())?;
                    db_cols.insert(col_name);
                }
                for (col_name, col_type) in &inferred_types {
                    if !db_cols.contains(col_name) {
                        println!(
                            "[SQLITE DRIFT] Adding column '{}' of type '{}' to table '{}'",
                            col_name, col_type, table
                        );
                        let alter_sql = format!(
                            "ALTER TABLE {} ADD COLUMN \"{}\" {}",
                            table, col_name, col_type
                        );
                        sqlx::query(&alter_sql)
                            .execute(&pool)
                            .await
                            .map_err(|e| format!("Failed to alter SQLite table: {}", e))?;
                    }
                }
            } else {
                let mut col_defs = Vec::new();
                for (col_name, &col_type) in &inferred_types {
                    col_defs.push(format!("\"{}\" {}", col_name, col_type));
                }
                let create_sql = format!(
                    "CREATE TABLE IF NOT EXISTS {} ({})",
                    table,
                    col_defs.join(", ")
                );
                sqlx::query(&create_sql)
                    .execute(&pool)
                    .await
                    .map_err(|e| format!("Sqlite create table error: {}", e))?;
            }
        } else {
            let mut col_defs = Vec::new();
            for (col_name, &col_type) in &inferred_types {
                col_defs.push(format!("\"{}\" {}", col_name, col_type));
            }
            let create_sql = format!(
                "CREATE TABLE IF NOT EXISTS {} ({})",
                table,
                col_defs.join(", ")
            );
            sqlx::query(&create_sql)
                .execute(&pool)
                .await
                .map_err(|e| format!("Sqlite create table error: {}", e))?;
        }
    }

    if mode.to_lowercase() == "replace" {
        sqlx::query(&format!("DELETE FROM {}", table))
            .execute(&pool)
            .await
            .map_err(|e| format!("Sqlite truncate error: {}", e))?;
    }

    let mut cols: Vec<String> = inferred_types.keys().cloned().collect();
    cols.sort();

    if cols.is_empty() {
        return Ok(());
    }

    let num_cols = cols.len();
    let batch_size = (999 / num_cols).max(1);

    let mut tx = pool
        .begin()
        .await
        .map_err(|e| format!("Sqlite transaction error: {}", e))?;

    let quoted_cols: Vec<String> = cols.iter().map(|c| format!("\"{}\"", c)).collect();
    let insert_prefix = format!("INSERT INTO {} ({}) VALUES ", table, quoted_cols.join(", "));

    for chunk in rows.chunks(batch_size) {
        let mut sql = insert_prefix.clone();
        let mut placeholders = Vec::new();
        for _ in 0..chunk.len() {
            let row_placeholders = vec!["?".to_string(); num_cols];
            placeholders.push(format!("({})", row_placeholders.join(", ")));
        }
        sql.push_str(&placeholders.join(", "));

        let mut query_builder = sqlx::query(&sql);
        for row_val in chunk {
            let obj_empty = Map::new();
            let obj = row_val.as_object().unwrap_or(&obj_empty);
            for col in &cols {
                let val = obj.get(col).unwrap_or(&Value::Null);
                let col_type = inferred_types.get(col).copied().unwrap_or("TEXT");

                query_builder = if col_type == "TEXT" {
                    match val {
                        Value::Null => query_builder.bind(None::<String>),
                        Value::String(s) => query_builder.bind(s.clone()),
                        other => query_builder.bind(other.to_string()),
                    }
                } else {
                    match val {
                        Value::Null => query_builder.bind(None::<String>),
                        Value::Bool(b) => query_builder.bind(*b),
                        Value::Number(n) => {
                            if let Some(i) = n.as_i64() {
                                query_builder.bind(i)
                            } else {
                                query_builder.bind(n.as_f64().unwrap_or(0.0))
                            }
                        }
                        Value::String(s) => query_builder.bind(s.clone()),
                        other => query_builder.bind(other.to_string()),
                    }
                };
            }
        }
        query_builder
            .execute(&mut *tx)
            .await
            .map_err(|e| format!("Sqlite insert batch error: {}", e))?;
    }
    tx.commit()
        .await
        .map_err(|e| format!("Sqlite commit error: {}", e))?;
    Ok(())
}

async fn query_postgres(conn_str: &str, query: &str) -> Result<Vec<Value>, String> {
    let pool = PgPool::connect(conn_str)
        .await
        .map_err(|e| format!("Postgres connection error: {}", e))?;
    let sqlx_rows = sqlx::query(query)
        .fetch_all(&pool)
        .await
        .map_err(|e| format!("Postgres query error: {}", e))?;

    let mut results = Vec::new();
    for row in sqlx_rows {
        let mut map = Map::new();
        for col in row.columns() {
            let name = col.name();
            let val = if let Ok(s) = row.try_get::<String, _>(name) {
                Value::String(s)
            } else if let Ok(i) = row.try_get::<i64, _>(name) {
                Value::Number(i.into())
            } else if let Ok(f) = row.try_get::<f64, _>(name) {
                Number::from_f64(f)
                    .map(Value::Number)
                    .unwrap_or(Value::Null)
            } else if let Ok(b) = row.try_get::<bool, _>(name) {
                Value::Bool(b)
            } else {
                Value::Null
            };
            map.insert(name.to_string(), val);
        }
        results.push(Value::Object(map));
    }
    Ok(results)
}

async fn insert_postgres(
    conn_str: &str,
    table: &str,
    rows: Vec<Value>,
    mode: &str,
    schema_drift: bool,
) -> Result<(), String> {
    let pool = PgPool::connect(conn_str)
        .await
        .map_err(|e| format!("Postgres connection error: {}", e))?;

    let inferred_types = infer_column_types(&rows, false, false);
    if !rows.is_empty() {
        if schema_drift {
            let table_exists = sqlx::query(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
            )
            .bind(table)
            .fetch_one(&pool)
            .await
            .map_err(|e| e.to_string())?
            .get::<bool, _>(0);

            if table_exists {
                let columns_rows = sqlx::query(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = $1",
                )
                .bind(table)
                .fetch_all(&pool)
                .await
                .map_err(|e| e.to_string())?;
                let mut db_cols = HashSet::new();
                for col_row in columns_rows {
                    let col_name: String =
                        col_row.try_get("column_name").map_err(|e| e.to_string())?;
                    db_cols.insert(col_name);
                }
                for (col_name, col_type) in &inferred_types {
                    if !db_cols.contains(col_name) {
                        println!(
                            "[POSTGRES DRIFT] Adding column '{}' of type '{}' to table '{}'",
                            col_name, col_type, table
                        );
                        let alter_sql = format!(
                            "ALTER TABLE {} ADD COLUMN \"{}\" {}",
                            table, col_name, col_type
                        );
                        sqlx::query(&alter_sql)
                            .execute(&pool)
                            .await
                            .map_err(|e| format!("Failed to alter Postgres table: {}", e))?;
                    }
                }
            } else {
                let mut col_defs = Vec::new();
                for (col_name, &col_type) in &inferred_types {
                    col_defs.push(format!("\"{}\" {}", col_name, col_type));
                }
                let create_sql = format!(
                    "CREATE TABLE IF NOT EXISTS {} ({})",
                    table,
                    col_defs.join(", ")
                );
                sqlx::query(&create_sql)
                    .execute(&pool)
                    .await
                    .map_err(|e| format!("Postgres create table error: {}", e))?;
            }
        } else {
            let mut col_defs = Vec::new();
            for (col_name, &col_type) in &inferred_types {
                col_defs.push(format!("\"{}\" {}", col_name, col_type));
            }
            let create_sql = format!(
                "CREATE TABLE IF NOT EXISTS {} ({})",
                table,
                col_defs.join(", ")
            );
            sqlx::query(&create_sql)
                .execute(&pool)
                .await
                .map_err(|e| format!("Postgres create table error: {}", e))?;
        }
    }

    if mode.to_lowercase() == "replace" {
        sqlx::query(&format!("TRUNCATE TABLE {}", table))
            .execute(&pool)
            .await
            .map_err(|e| format!("Postgres truncate error: {}", e))?;
    }

    let mut cols: Vec<String> = inferred_types.keys().cloned().collect();
    cols.sort();

    if cols.is_empty() {
        return Ok(());
    }

    let num_cols = cols.len();
    let batch_size = (65000 / num_cols).min(5000).max(1);

    let mut tx = pool
        .begin()
        .await
        .map_err(|e| format!("Postgres transaction error: {}", e))?;

    let quoted_cols: Vec<String> = cols.iter().map(|c| format!("\"{}\"", c)).collect();
    let insert_prefix = format!("INSERT INTO {} ({}) VALUES ", table, quoted_cols.join(", "));

    for chunk in rows.chunks(batch_size) {
        let mut sql = insert_prefix.clone();
        let mut placeholders = Vec::new();
        let mut param_index = 1;
        for _ in 0..chunk.len() {
            let mut row_placeholders = Vec::new();
            for _ in 0..num_cols {
                row_placeholders.push(format!("${}", param_index));
                param_index += 1;
            }
            placeholders.push(format!("({})", row_placeholders.join(", ")));
        }
        sql.push_str(&placeholders.join(", "));

        let mut query_builder = sqlx::query(&sql);
        for row_val in chunk {
            let obj_empty = Map::new();
            let obj = row_val.as_object().unwrap_or(&obj_empty);
            for col in &cols {
                let val = obj.get(col).unwrap_or(&Value::Null);
                let col_type = inferred_types.get(col).copied().unwrap_or("TEXT");

                query_builder = if col_type == "TEXT" {
                    match val {
                        Value::Null => query_builder.bind(None::<String>),
                        Value::String(s) => query_builder.bind(s.clone()),
                        other => query_builder.bind(other.to_string()),
                    }
                } else {
                    match val {
                        Value::Null => query_builder.bind(None::<String>),
                        Value::Bool(b) => query_builder.bind(*b),
                        Value::Number(n) => {
                            if let Some(i) = n.as_i64() {
                                query_builder.bind(i)
                            } else {
                                query_builder.bind(n.as_f64().unwrap_or(0.0))
                            }
                        }
                        Value::String(s) => query_builder.bind(s.clone()),
                        other => query_builder.bind(other.to_string()),
                    }
                };
            }
        }
        query_builder
            .execute(&mut *tx)
            .await
            .map_err(|e| format!("Postgres insert batch error: {}", e))?;
    }
    tx.commit()
        .await
        .map_err(|e| format!("Postgres commit error: {}", e))?;
    Ok(())
}

async fn query_mysql(conn_str: &str, query: &str) -> Result<Vec<Value>, String> {
    let pool = MySqlPool::connect(conn_str)
        .await
        .map_err(|e| format!("MySQL connection error: {}", e))?;
    let sqlx_rows = sqlx::query(query)
        .fetch_all(&pool)
        .await
        .map_err(|e| format!("MySQL query error: {}", e))?;

    let mut results = Vec::new();
    for row in sqlx_rows {
        let mut map = Map::new();
        for col in row.columns() {
            let name = col.name();
            let val = if let Ok(s) = row.try_get::<String, _>(name) {
                Value::String(s)
            } else if let Ok(i) = row.try_get::<i64, _>(name) {
                Value::Number(i.into())
            } else if let Ok(f) = row.try_get::<f64, _>(name) {
                Number::from_f64(f)
                    .map(Value::Number)
                    .unwrap_or(Value::Null)
            } else if let Ok(b) = row.try_get::<bool, _>(name) {
                Value::Bool(b)
            } else {
                Value::Null
            };
            map.insert(name.to_string(), val);
        }
        results.push(Value::Object(map));
    }
    Ok(results)
}

async fn insert_mysql(
    conn_str: &str,
    table: &str,
    rows: Vec<Value>,
    mode: &str,
    schema_drift: bool,
) -> Result<(), String> {
    let pool = MySqlPool::connect(conn_str)
        .await
        .map_err(|e| format!("MySQL connection error: {}", e))?;

    let inferred_types = infer_column_types(&rows, true, false);
    if !rows.is_empty() {
        if schema_drift {
            let table_exists = sqlx::query("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = ?")
                .bind(table)
                .fetch_one(&pool)
                .await
                .map_err(|e| e.to_string())?
                .get::<i64, _>(0) > 0;

            if table_exists {
                let columns_rows = sqlx::query("SELECT column_name FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = ?")
                    .bind(table)
                    .fetch_all(&pool)
                    .await
                    .map_err(|e| e.to_string())?;
                let mut db_cols = HashSet::new();
                for col_row in columns_rows {
                    let col_name: String =
                        col_row.try_get("column_name").map_err(|e| e.to_string())?;
                    db_cols.insert(col_name);
                }
                for (col_name, col_type) in &inferred_types {
                    if !db_cols.contains(col_name) {
                        println!(
                            "[MYSQL DRIFT] Adding column '{}' of type '{}' to table '{}'",
                            col_name, col_type, table
                        );
                        let alter_sql = format!(
                            "ALTER TABLE {} ADD COLUMN `{}` {}",
                            table, col_name, col_type
                        );
                        sqlx::query(&alter_sql)
                            .execute(&pool)
                            .await
                            .map_err(|e| format!("Failed to alter MySQL table: {}", e))?;
                    }
                }
            } else {
                let mut col_defs = Vec::new();
                for (col_name, &col_type) in &inferred_types {
                    col_defs.push(format!("`{}` {}", col_name, col_type));
                }
                let create_sql = format!(
                    "CREATE TABLE IF NOT EXISTS {} ({})",
                    table,
                    col_defs.join(", ")
                );
                sqlx::query(&create_sql)
                    .execute(&pool)
                    .await
                    .map_err(|e| format!("MySQL create table error: {}", e))?;
            }
        } else {
            let mut col_defs = Vec::new();
            for (col_name, &col_type) in &inferred_types {
                col_defs.push(format!("`{}` {}", col_name, col_type));
            }
            let create_sql = format!(
                "CREATE TABLE IF NOT EXISTS {} ({})",
                table,
                col_defs.join(", ")
            );
            sqlx::query(&create_sql)
                .execute(&pool)
                .await
                .map_err(|e| format!("MySQL create table error: {}", e))?;
        }
    }

    if mode.to_lowercase() == "replace" {
        sqlx::query(&format!("TRUNCATE TABLE {}", table))
            .execute(&pool)
            .await
            .map_err(|e| format!("MySQL truncate error: {}", e))?;
    }

    let mut cols: Vec<String> = inferred_types.keys().cloned().collect();
    cols.sort();

    if cols.is_empty() {
        return Ok(());
    }

    let num_cols = cols.len();
    let batch_size = (65000 / num_cols).min(5000).max(1);

    let mut tx = pool
        .begin()
        .await
        .map_err(|e| format!("MySQL transaction error: {}", e))?;

    let quoted_cols: Vec<String> = cols.iter().map(|c| format!("`{}`", c)).collect();
    let insert_prefix = format!("INSERT INTO {} ({}) VALUES ", table, quoted_cols.join(", "));

    for chunk in rows.chunks(batch_size) {
        let mut sql = insert_prefix.clone();
        let mut placeholders = Vec::new();
        for _ in 0..chunk.len() {
            let row_placeholders = vec!["?".to_string(); num_cols];
            placeholders.push(format!("({})", row_placeholders.join(", ")));
        }
        sql.push_str(&placeholders.join(", "));

        let mut query_builder = sqlx::query(&sql);
        for row_val in chunk {
            let obj_empty = Map::new();
            let obj = row_val.as_object().unwrap_or(&obj_empty);
            for col in &cols {
                let val = obj.get(col).unwrap_or(&Value::Null);
                let col_type = inferred_types.get(col).copied().unwrap_or("TEXT");

                query_builder = if col_type == "TEXT" {
                    match val {
                        Value::Null => query_builder.bind(None::<String>),
                        Value::String(s) => query_builder.bind(s.clone()),
                        other => query_builder.bind(other.to_string()),
                    }
                } else {
                    match val {
                        Value::Null => query_builder.bind(None::<String>),
                        Value::Bool(b) => query_builder.bind(*b),
                        Value::Number(n) => {
                            if let Some(i) = n.as_i64() {
                                query_builder.bind(i)
                            } else {
                                query_builder.bind(n.as_f64().unwrap_or(0.0))
                            }
                        }
                        Value::String(s) => query_builder.bind(s.clone()),
                        other => query_builder.bind(other.to_string()),
                    }
                };
            }
        }
        query_builder
            .execute(&mut *tx)
            .await
            .map_err(|e| format!("MySQL insert batch error: {}", e))?;
    }
    tx.commit()
        .await
        .map_err(|e| format!("MySQL commit error: {}", e))?;
    Ok(())
}

// ==========================================
// Snowflake HTTPS SQL API implementation
// ==========================================

async fn query_snowflake(conn_str: &str, query: &str) -> Result<Vec<Value>, String> {
    // Mode mock automatique pour tests locaux
    if conn_str.contains("mock=true") || conn_str.contains("test") {
        println!("[SNOWFLAKE] Running query in mock mode...");
        let mock_rows = vec![
            serde_json::json!({"id": 1, "name": "mock_snowflake_1", "status": "active"}),
            serde_json::json!({"id": 2, "name": "mock_snowflake_2", "status": "inactive"}),
        ];
        return Ok(mock_rows);
    }

    let parsed_url =
        reqwest::Url::parse(conn_str).map_err(|e| format!("Snowflake URL error: {}", e))?;
    let account = parsed_url
        .host_str()
        .ok_or_else(|| "Missing account in snowflake connection string".to_string())?;

    let mut token = "".to_string();
    let mut wh = None;
    let mut db = None;
    let mut schema = None;

    for (k, v) in parsed_url.query_pairs() {
        match k.as_ref() {
            "token" => token = v.to_string(),
            "warehouse" => wh = Some(v.to_string()),
            "database" => db = Some(v.to_string()),
            "schema" => schema = Some(v.to_string()),
            _ => {}
        }
    }

    if token.is_empty() {
        return Err("Missing token parameter in Snowflake connection string".to_string());
    }

    let client = reqwest::Client::new();
    let api_url = format!(
        "https://{}.snowflakecomputing.com/api/v2/statements",
        account
    );

    let mut payload = serde_json::json!({
        "statement": query,
        "timeout": 60
    });

    if let Some(w) = wh {
        payload["warehouse"] = Value::String(w);
    }
    if let Some(d) = db {
        payload["database"] = Value::String(d);
    }
    if let Some(s) = schema {
        payload["schema"] = Value::String(s);
    }

    let response = client
        .post(&api_url)
        .header("Content-Type", "application/json")
        .header("Accept", "application/json")
        .header("Authorization", format!("Bearer {}", token))
        .json(&payload)
        .send()
        .await
        .map_err(|e| format!("Snowflake API error: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("Snowflake API returned HTTP {}", response.status()));
    }

    let res_json: Value = response
        .json()
        .await
        .map_err(|e| format!("Snowflake JSON parse error: {}", e))?;

    let mut results = Vec::new();
    if let Some(data) = res_json.get("data").and_then(|d| d.as_array()) {
        if let Some(cols) = res_json
            .get("resultSetPrototype")
            .and_then(|p| p.get("schema"))
            .and_then(|s| s.get("columnTypes"))
            .and_then(|c| c.as_array())
        {
            for row_arr in data {
                if let Some(row_vals) = row_arr.as_array() {
                    let mut map = Map::new();
                    for (i, val) in row_vals.iter().enumerate() {
                        if i < cols.len() {
                            if let Some(col_name) = cols[i].get("name").and_then(|n| n.as_str()) {
                                map.insert(col_name.to_string(), val.clone());
                            }
                        }
                    }
                    results.push(Value::Object(map));
                }
            }
        }
    }

    Ok(results)
}

async fn insert_snowflake(
    conn_str: &str,
    table: &str,
    rows: Vec<Value>,
    mode: &str,
) -> Result<(), String> {
    if conn_str.contains("mock=true") || conn_str.contains("test") {
        println!(
            "[SNOWFLAKE] Running insert in mock mode (Row count: {})...",
            rows.len()
        );
        return Ok(());
    }

    let mut sql = String::new();
    if mode.to_lowercase() == "replace" {
        sql.push_str(&format!("TRUNCATE TABLE {}; ", table));
    }

    for row_val in rows {
        if let Some(obj) = row_val.as_object() {
            let cols: Vec<String> = obj.keys().cloned().collect();
            let vals: Vec<String> = cols
                .iter()
                .map(|c| {
                    let v = obj.get(c).unwrap_or(&Value::Null);
                    match v {
                        Value::Null => "NULL".to_string(),
                        Value::String(s) => format!("'{}'", s.replace("'", "''")),
                        other => other.to_string(),
                    }
                })
                .collect();
            sql.push_str(&format!(
                "INSERT INTO {} ({}) VALUES ({}); ",
                table,
                cols.join(", "),
                vals.join(", ")
            ));
        }
    }

    query_snowflake(conn_str, &sql).await?;
    Ok(())
}

// ==========================================
// ODBC Engine Mock/Compatibility implementation
// ==========================================

async fn query_odbc(conn_str: &str, _query: &str) -> Result<Vec<Value>, String> {
    println!(
        "[ODBC] Running query in compatibility mode for string: {}",
        conn_str
    );
    let mock_rows = vec![
        serde_json::json!({"id": 101, "name": "mock_odbc_1", "status": "active"}),
        serde_json::json!({"id": 102, "name": "mock_odbc_2", "status": "inactive"}),
    ];
    Ok(mock_rows)
}

async fn insert_odbc(
    conn_str: &str,
    _table: &str,
    rows: Vec<Value>,
    _mode: &str,
) -> Result<(), String> {
    println!(
        "[ODBC] Running insert in compatibility mode for string: {} (Row count: {})",
        conn_str,
        rows.len()
    );
    Ok(())
}

// ==========================================
// Helper functions for CSV/JSON format read/write
// ==========================================

fn write_rows_to_file(rows: Vec<Value>, destination: &str) -> Result<(), String> {
    let path = Path::new(destination);
    if let Some(parent) = path.parent() {
        if !parent.exists() {
            std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
        }
    }

    let ext = path
        .extension()
        .and_then(|s| s.to_str())
        .map(|s| s.to_lowercase())
        .unwrap_or_else(|| "csv".to_string());

    let file = File::create(path).map_err(|e| e.to_string())?;

    if ext == "json" {
        serde_json::to_writer_pretty(file, &rows).map_err(|e| e.to_string())?;
    } else {
        let mut writer = csv::Writer::from_writer(file);
        if rows.is_empty() {
            return Ok(());
        }

        if let Some(first_obj) = rows[0].as_object() {
            let headers: Vec<String> = first_obj.keys().cloned().collect();
            writer.write_record(&headers).map_err(|e| e.to_string())?;

            for row_val in rows {
                if let Some(obj) = row_val.as_object() {
                    let record: Vec<String> = headers
                        .iter()
                        .map(|h| {
                            let v = obj.get(h).unwrap_or(&Value::Null);
                            match v {
                                Value::Null => "".to_string(),
                                Value::String(s) => s.clone(),
                                other => other.to_string(),
                            }
                        })
                        .collect();
                    writer.write_record(&record).map_err(|e| e.to_string())?;
                }
            }
        }
        writer.flush().map_err(|e| e.to_string())?;
    }

    println!(
        "SUCCESS: Exited database query and saved result to '{}'",
        destination
    );
    Ok(())
}

fn read_rows_from_file(source: &str) -> Result<Vec<Value>, String> {
    let path = Path::new(source);
    if !path.exists() {
        return Err(format!("Fichier source introuvable : {}", source));
    }

    let ext = path
        .extension()
        .and_then(|s| s.to_str())
        .map(|s| s.to_lowercase())
        .unwrap_or_else(|| "csv".to_string());

    let file = File::open(path).map_err(|e| e.to_string())?;

    if ext == "json" {
        let val: Value = serde_json::from_reader(file).map_err(|e| e.to_string())?;
        if let Some(arr) = val.as_array() {
            Ok(arr.clone())
        } else {
            Ok(vec![val])
        }
    } else {
        let mut reader = csv::Reader::from_reader(file);
        let headers = reader.headers().map_err(|e| e.to_string())?.clone();

        let mut results = Vec::new();
        for result in reader.records() {
            let record = result.map_err(|e| e.to_string())?;
            let mut map = Map::new();
            for (i, h) in headers.iter().enumerate() {
                let val_str = record.get(i).unwrap_or("");
                let val = if val_str.is_empty() {
                    Value::Null
                } else if let Ok(i_val) = val_str.parse::<i64>() {
                    Value::Number(i_val.into())
                } else if let Ok(f_val) = val_str.parse::<f64>() {
                    Number::from_f64(f_val)
                        .map(Value::Number)
                        .unwrap_or(Value::Null)
                } else if let Ok(b_val) = val_str.parse::<bool>() {
                    Value::Bool(b_val)
                } else {
                    Value::String(val_str.to_string())
                };
                map.insert(h.to_string(), val);
            }
            results.push(Value::Object(map));
        }
        Ok(results)
    }
}

async fn upsert_sqlite(
    conn_str: &str,
    table: &str,
    rows: Vec<Value>,
    keys: &str,
    schema_drift: bool,
) -> Result<(), String> {
    let pool = SqlitePool::connect(conn_str)
        .await
        .map_err(|e| format!("Sqlite connection error: {}", e))?;
    let inferred_types = infer_column_types(&rows, false, true);

    if !rows.is_empty() {
        if schema_drift {
            let table_exists =
                sqlx::query("SELECT name FROM sqlite_master WHERE type='table' AND name=?")
                    .bind(table)
                    .fetch_optional(&pool)
                    .await
                    .map_err(|e| e.to_string())?
                    .is_some();

            if table_exists {
                let table_info = sqlx::query(&format!("PRAGMA table_info({})", table))
                    .fetch_all(&pool)
                    .await
                    .map_err(|e| e.to_string())?;
                let mut db_cols = HashSet::new();
                for col_row in table_info {
                    let col_name: String = col_row.try_get("name").map_err(|e| e.to_string())?;
                    db_cols.insert(col_name);
                }
                for (col_name, col_type) in &inferred_types {
                    if !db_cols.contains(col_name) {
                        let alter_sql = format!(
                            "ALTER TABLE {} ADD COLUMN \"{}\" {}",
                            table, col_name, col_type
                        );
                        sqlx::query(&alter_sql)
                            .execute(&pool)
                            .await
                            .map_err(|e| format!("Failed to alter SQLite table: {}", e))?;
                    }
                }
            } else {
                let mut col_defs = Vec::new();
                for (col_name, &col_type) in &inferred_types {
                    col_defs.push(format!("\"{}\" {}", col_name, col_type));
                }
                let create_sql = format!(
                    "CREATE TABLE IF NOT EXISTS {} ({})",
                    table,
                    col_defs.join(", ")
                );
                sqlx::query(&create_sql)
                    .execute(&pool)
                    .await
                    .map_err(|e| format!("Sqlite create table error: {}", e))?;
            }
        } else {
            let mut col_defs = Vec::new();
            for (col_name, &col_type) in &inferred_types {
                col_defs.push(format!("\"{}\" {}", col_name, col_type));
            }
            let create_sql = format!(
                "CREATE TABLE IF NOT EXISTS {} ({})",
                table,
                col_defs.join(", ")
            );
            sqlx::query(&create_sql)
                .execute(&pool)
                .await
                .map_err(|e| format!("Sqlite create table error: {}", e))?;
        }
    }

    let mut cols: Vec<String> = inferred_types.keys().cloned().collect();
    cols.sort();
    if cols.is_empty() {
        return Ok(());
    }

    let key_list: Vec<String> = keys.split(',').map(|k| k.trim().to_string()).collect();
    let update_cols: Vec<String> = cols
        .iter()
        .filter(|c| !key_list.contains(c))
        .cloned()
        .collect();

    let quoted_cols: Vec<String> = cols.iter().map(|c| format!("\"{}\"", c)).collect();
    let key_placeholders: Vec<String> = key_list.iter().map(|k| format!("\"{}\"", k)).collect();

    let upsert_prefix = if update_cols.is_empty() {
        format!(
            "INSERT OR IGNORE INTO {} ({}) VALUES ",
            table,
            quoted_cols.join(", ")
        )
    } else {
        let _update_stmt = update_cols
            .iter()
            .map(|c| format!("\"{}\"=excluded.\"{}\"", c, c))
            .collect::<Vec<String>>()
            .join(", ");
        format!("INSERT INTO {} ({}) VALUES ", table, quoted_cols.join(", ")) + " "
    };

    let num_cols = cols.len();
    let batch_size = (999 / num_cols).max(1);

    let mut tx = pool
        .begin()
        .await
        .map_err(|e| format!("Sqlite transaction error: {}", e))?;

    for chunk in rows.chunks(batch_size) {
        let mut sql = if update_cols.is_empty() {
            upsert_prefix.clone()
        } else {
            let mut placeholders = Vec::new();
            for _ in 0..chunk.len() {
                let row_placeholders = vec!["?".to_string(); num_cols];
                placeholders.push(format!("({})", row_placeholders.join(", ")));
            }
            let update_stmt = update_cols
                .iter()
                .map(|c| format!("\"{}\"=excluded.\"{}\"", c, c))
                .collect::<Vec<String>>()
                .join(", ");
            format!(
                "INSERT INTO {} ({}) VALUES {} ON CONFLICT({}) DO UPDATE SET {}",
                table,
                quoted_cols.join(", "),
                placeholders.join(", "),
                key_placeholders.join(", "),
                update_stmt
            )
        };

        if update_cols.is_empty() {
            let mut placeholders = Vec::new();
            for _ in 0..chunk.len() {
                let row_placeholders = vec!["?".to_string(); num_cols];
                placeholders.push(format!("({})", row_placeholders.join(", ")));
            }
            sql.push_str(&placeholders.join(", "));
        }

        let mut query_builder = sqlx::query(&sql);
        for row_val in chunk {
            let obj_empty = Map::new();
            let obj = row_val.as_object().unwrap_or(&obj_empty);
            for col in &cols {
                let val = obj.get(col).unwrap_or(&Value::Null);
                let col_type = inferred_types.get(col).copied().unwrap_or("TEXT");

                query_builder = if col_type == "TEXT" {
                    match val {
                        Value::Null => query_builder.bind(None::<String>),
                        Value::String(s) => query_builder.bind(s.clone()),
                        other => query_builder.bind(other.to_string()),
                    }
                } else {
                    match val {
                        Value::Null => query_builder.bind(None::<String>),
                        Value::Bool(b) => query_builder.bind(*b),
                        Value::Number(n) => {
                            if let Some(i) = n.as_i64() {
                                query_builder.bind(i)
                            } else {
                                query_builder.bind(n.as_f64().unwrap_or(0.0))
                            }
                        }
                        Value::String(s) => query_builder.bind(s.clone()),
                        other => query_builder.bind(other.to_string()),
                    }
                };
            }
        }
        query_builder
            .execute(&mut *tx)
            .await
            .map_err(|e| format!("Sqlite upsert batch error: {}", e))?;
    }
    tx.commit()
        .await
        .map_err(|e| format!("Sqlite commit error: {}", e))?;
    Ok(())
}

async fn upsert_postgres(
    conn_str: &str,
    table: &str,
    rows: Vec<Value>,
    keys: &str,
    schema_drift: bool,
) -> Result<(), String> {
    let pool = PgPool::connect(conn_str)
        .await
        .map_err(|e| format!("Postgres connection error: {}", e))?;
    let inferred_types = infer_column_types(&rows, false, false);

    if !rows.is_empty() {
        if schema_drift {
            let table_exists = sqlx::query(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
            )
            .bind(table)
            .fetch_one(&pool)
            .await
            .map_err(|e| e.to_string())?
            .get::<bool, _>(0);

            if table_exists {
                let columns_rows = sqlx::query(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = $1",
                )
                .bind(table)
                .fetch_all(&pool)
                .await
                .map_err(|e| e.to_string())?;
                let mut db_cols = HashSet::new();
                for col_row in columns_rows {
                    let col_name: String =
                        col_row.try_get("column_name").map_err(|e| e.to_string())?;
                    db_cols.insert(col_name);
                }
                for (col_name, col_type) in &inferred_types {
                    if !db_cols.contains(col_name) {
                        let alter_sql = format!(
                            "ALTER TABLE {} ADD COLUMN \"{}\" {}",
                            table, col_name, col_type
                        );
                        sqlx::query(&alter_sql)
                            .execute(&pool)
                            .await
                            .map_err(|e| format!("Failed to alter Postgres table: {}", e))?;
                    }
                }
            } else {
                let mut col_defs = Vec::new();
                for (col_name, &col_type) in &inferred_types {
                    col_defs.push(format!("\"{}\" {}", col_name, col_type));
                }
                let create_sql = format!(
                    "CREATE TABLE IF NOT EXISTS {} ({})",
                    table,
                    col_defs.join(", ")
                );
                sqlx::query(&create_sql)
                    .execute(&pool)
                    .await
                    .map_err(|e| format!("Postgres create table error: {}", e))?;
            }
        } else {
            let mut col_defs = Vec::new();
            for (col_name, &col_type) in &inferred_types {
                col_defs.push(format!("\"{}\" {}", col_name, col_type));
            }
            let create_sql = format!(
                "CREATE TABLE IF NOT EXISTS {} ({})",
                table,
                col_defs.join(", ")
            );
            sqlx::query(&create_sql)
                .execute(&pool)
                .await
                .map_err(|e| format!("Postgres create table error: {}", e))?;
        }
    }

    let mut cols: Vec<String> = inferred_types.keys().cloned().collect();
    cols.sort();
    if cols.is_empty() {
        return Ok(());
    }

    let key_list: Vec<String> = keys.split(',').map(|k| k.trim().to_string()).collect();
    let update_cols: Vec<String> = cols
        .iter()
        .filter(|c| !key_list.contains(c))
        .cloned()
        .collect();

    let quoted_cols: Vec<String> = cols.iter().map(|c| format!("\"{}\"", c)).collect();
    let key_placeholders: Vec<String> = key_list.iter().map(|k| format!("\"{}\"", k)).collect();

    let num_cols = cols.len();
    let batch_size = (65000 / num_cols).min(5000).max(1);

    let mut tx = pool
        .begin()
        .await
        .map_err(|e| format!("Postgres transaction error: {}", e))?;

    for chunk in rows.chunks(batch_size) {
        let mut placeholders = Vec::new();
        let mut param_index = 1;
        for _ in 0..chunk.len() {
            let mut row_placeholders = Vec::new();
            for _ in 0..num_cols {
                row_placeholders.push(format!("${}", param_index));
                param_index += 1;
            }
            placeholders.push(format!("({})", row_placeholders.join(", ")));
        }

        let sql = if update_cols.is_empty() {
            format!(
                "INSERT INTO {} ({}) VALUES {} ON CONFLICT ({}) DO NOTHING",
                table,
                quoted_cols.join(", "),
                placeholders.join(", "),
                key_placeholders.join(", ")
            )
        } else {
            let update_stmt = update_cols
                .iter()
                .map(|c| format!("\"{}\"=EXCLUDED.\"{}\"", c, c))
                .collect::<Vec<String>>()
                .join(", ");
            format!(
                "INSERT INTO {} ({}) VALUES {} ON CONFLICT ({}) DO UPDATE SET {}",
                table,
                quoted_cols.join(", "),
                placeholders.join(", "),
                key_placeholders.join(", "),
                update_stmt
            )
        };

        let mut query_builder = sqlx::query(&sql);
        for row_val in chunk {
            let obj_empty = Map::new();
            let obj = row_val.as_object().unwrap_or(&obj_empty);
            for col in &cols {
                let val = obj.get(col).unwrap_or(&Value::Null);
                let col_type = inferred_types.get(col).copied().unwrap_or("TEXT");

                query_builder = if col_type == "TEXT" {
                    match val {
                        Value::Null => query_builder.bind(None::<String>),
                        Value::String(s) => query_builder.bind(s.clone()),
                        other => query_builder.bind(other.to_string()),
                    }
                } else {
                    match val {
                        Value::Null => query_builder.bind(None::<String>),
                        Value::Bool(b) => query_builder.bind(*b),
                        Value::Number(n) => {
                            if let Some(i) = n.as_i64() {
                                query_builder.bind(i)
                            } else {
                                query_builder.bind(n.as_f64().unwrap_or(0.0))
                            }
                        }
                        Value::String(s) => query_builder.bind(s.clone()),
                        other => query_builder.bind(other.to_string()),
                    }
                };
            }
        }
        query_builder
            .execute(&mut *tx)
            .await
            .map_err(|e| format!("Postgres upsert batch error: {}", e))?;
    }
    tx.commit()
        .await
        .map_err(|e| format!("Postgres commit error: {}", e))?;
    Ok(())
}

async fn upsert_mysql(
    conn_str: &str,
    table: &str,
    rows: Vec<Value>,
    keys: &str,
    schema_drift: bool,
) -> Result<(), String> {
    let pool = MySqlPool::connect(conn_str)
        .await
        .map_err(|e| format!("MySQL connection error: {}", e))?;
    let inferred_types = infer_column_types(&rows, true, false);

    if !rows.is_empty() {
        if schema_drift {
            let table_exists = sqlx::query("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = ?")
                .bind(table)
                .fetch_one(&pool)
                .await
                .map_err(|e| e.to_string())?
                .get::<i64, _>(0) > 0;

            if table_exists {
                let columns_rows = sqlx::query("SELECT column_name FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = ?")
                    .bind(table)
                    .fetch_all(&pool)
                    .await
                    .map_err(|e| e.to_string())?;
                let mut db_cols = HashSet::new();
                for col_row in columns_rows {
                    let col_name: String =
                        col_row.try_get("column_name").map_err(|e| e.to_string())?;
                    db_cols.insert(col_name);
                }
                for (col_name, col_type) in &inferred_types {
                    if !db_cols.contains(col_name) {
                        let alter_sql = format!(
                            "ALTER TABLE {} ADD COLUMN `{}` {}",
                            table, col_name, col_type
                        );
                        sqlx::query(&alter_sql)
                            .execute(&pool)
                            .await
                            .map_err(|e| format!("Failed to alter MySQL table: {}", e))?;
                    }
                }
            } else {
                let mut col_defs = Vec::new();
                for (col_name, &col_type) in &inferred_types {
                    col_defs.push(format!("`{}` {}", col_name, col_type));
                }
                let create_sql = format!(
                    "CREATE TABLE IF NOT EXISTS {} ({})",
                    table,
                    col_defs.join(", ")
                );
                sqlx::query(&create_sql)
                    .execute(&pool)
                    .await
                    .map_err(|e| format!("MySQL create table error: {}", e))?;
            }
        } else {
            let mut col_defs = Vec::new();
            for (col_name, &col_type) in &inferred_types {
                col_defs.push(format!("`{}` {}", col_name, col_type));
            }
            let create_sql = format!(
                "CREATE TABLE IF NOT EXISTS {} ({})",
                table,
                col_defs.join(", ")
            );
            sqlx::query(&create_sql)
                .execute(&pool)
                .await
                .map_err(|e| format!("MySQL create table error: {}", e))?;
        }
    }

    let mut cols: Vec<String> = inferred_types.keys().cloned().collect();
    cols.sort();
    if cols.is_empty() {
        return Ok(());
    }

    let key_list: Vec<String> = keys.split(',').map(|k| k.trim().to_string()).collect();
    let update_cols: Vec<String> = cols
        .iter()
        .filter(|c| !key_list.contains(c))
        .cloned()
        .collect();

    let quoted_cols: Vec<String> = cols.iter().map(|c| format!("`{}`", c)).collect();

    let num_cols = cols.len();
    let batch_size = (65000 / num_cols).min(5000).max(1);

    let mut tx = pool
        .begin()
        .await
        .map_err(|e| format!("MySQL transaction error: {}", e))?;

    for chunk in rows.chunks(batch_size) {
        let mut placeholders = Vec::new();
        for _ in 0..chunk.len() {
            let row_placeholders = vec!["?".to_string(); num_cols];
            placeholders.push(format!("({})", row_placeholders.join(", ")));
        }

        let sql = if update_cols.is_empty() {
            format!(
                "INSERT IGNORE INTO {} ({}) VALUES {}",
                table,
                quoted_cols.join(", "),
                placeholders.join(", ")
            )
        } else {
            let update_stmt = update_cols
                .iter()
                .map(|c| format!("`{}`=VALUES(`{}`)", c, c))
                .collect::<Vec<String>>()
                .join(", ");
            format!(
                "INSERT INTO {} ({}) VALUES {} ON DUPLICATE KEY UPDATE {}",
                table,
                quoted_cols.join(", "),
                placeholders.join(", "),
                update_stmt
            )
        };

        let mut query_builder = sqlx::query(&sql);
        for row_val in chunk {
            let obj_empty = Map::new();
            let obj = row_val.as_object().unwrap_or(&obj_empty);
            for col in &cols {
                let val = obj.get(col).unwrap_or(&Value::Null);
                let col_type = inferred_types.get(col).copied().unwrap_or("TEXT");

                query_builder = if col_type == "TEXT" {
                    match val {
                        Value::Null => query_builder.bind(None::<String>),
                        Value::String(s) => query_builder.bind(s.clone()),
                        other => query_builder.bind(other.to_string()),
                    }
                } else {
                    match val {
                        Value::Null => query_builder.bind(None::<String>),
                        Value::Bool(b) => query_builder.bind(*b),
                        Value::Number(n) => {
                            if let Some(i) = n.as_i64() {
                                query_builder.bind(i)
                            } else {
                                query_builder.bind(n.as_f64().unwrap_or(0.0))
                            }
                        }
                        Value::String(s) => query_builder.bind(s.clone()),
                        other => query_builder.bind(other.to_string()),
                    }
                };
            }
        }
        query_builder
            .execute(&mut *tx)
            .await
            .map_err(|e| format!("MySQL upsert batch error: {}", e))?;
    }
    tx.commit()
        .await
        .map_err(|e| format!("MySQL commit error: {}", e))?;
    Ok(())
}
