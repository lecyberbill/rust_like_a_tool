// [WFGY] Zone: SAFE | λ: 0.2 | Action: Analytical engine with Polars multi-format support
use polars::prelude::*;
use std::path::Path;

/// Détecte le format de fichier et charge un LazyFrame Polars
fn read_df(file_path: &str) -> Result<LazyFrame, String> {
    let path = Path::new(file_path);
    let ext = path.extension()
        .and_then(|s| s.to_str())
        .map(|s| s.to_lowercase())
        .ok_or_else(|| format!("Impossible de detecter l'extension du fichier : {}", file_path))?;

    match ext.as_str() {
        "csv" => {
            LazyCsvReader::new(file_path)
                .has_header(true)
                .finish()
                .map_err(|e| format!("Erreur de lecture CSV Polars: {}", e))
        },
        "json" => {
            // Pour le JSON, Polars requiert de charger en memoire d'abord avec Crayon/Standard Reader ou JsonReader
            // On peut le lire de maniere standard puis le convertir en LazyFrame
            let f = std::fs::File::open(path).map_err(|e| e.to_string())?;
            let df = JsonReader::new(f)
                .finish()
                .map_err(|e| format!("Erreur de lecture JSON Polars: {}", e))?;
            Ok(df.lazy())
        },
        "parquet" => {
            LazyFrame::scan_parquet(file_path, ScanArgsParquet::default())
                .map_err(|e| format!("Erreur de lecture Parquet Polars: {}", e))
        },
        other => Err(format!("Format de fichier non supporte par le moteur analytique : .{}", other))
    }
}

/// Écrit un LazyFrame collecté vers la destination selon le format
fn write_df(df: DataFrame, file_path: &str) -> Result<(), String> {
    let path = Path::new(file_path);
    let ext = path.extension()
        .and_then(|s| s.to_str())
        .map(|s| s.to_lowercase())
        .ok_or_else(|| format!("Impossible de detecter l'extension pour l'ecriture : {}", file_path))?;

    // S'assurer que le dossier parent existe
    if let Some(parent) = path.parent() {
        if !parent.exists() {
            std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
        }
    }

    let f = std::fs::File::create(path).map_err(|e| e.to_string())?;

    match ext.as_str() {
        "csv" => {
            let mut writer = CsvWriter::new(f);
            writer.finish(&mut df.clone())
                .map_err(|e| format!("Erreur d'ecriture CSV: {}", e))?;
        },
        "json" => {
            let mut writer = JsonWriter::new(f);
            writer.finish(&mut df.clone())
                .map_err(|e| format!("Erreur d'ecriture JSON: {}", e))?;
        },
        "parquet" => {
            let writer = ParquetWriter::new(f);
            writer.finish(&mut df.clone())
                .map_err(|e| format!("Erreur d'ecriture Parquet: {}", e))?;
        },
        other => return Err(format!("Format d'ecriture non supporte : .{}", other))
    }
    Ok(())
}

/// Execute un groupby et aggrege sur la colonne cible
pub fn groupby(
    source: &str,
    destination: &str,
    groupby_cols: Vec<String>,
    agg_col: &str,
    operation: &str,
) -> Result<(), String> {
    let lf = read_df(source)?;

    // Conversion des colonnes de groupby
    let group_exprs: Vec<Expr> = groupby_cols.iter().map(|c| col(c)).collect();

    // Preparation de l'aggregation
    let agg_expr = match operation.to_lowercase().as_str() {
        "sum" => col(agg_col).sum().alias(&format!("{}_sum", agg_col)),
        "mean" | "avg" => col(agg_col).mean().alias(&format!("{}_mean", agg_col)),
        "min" => col(agg_col).min().alias(&format!("{}_min", agg_col)),
        "max" => col(agg_col).max().alias(&format!("{}_max", agg_col)),
        "count" => col(agg_col).count().alias(&format!("{}_count", agg_col)),
        other => return Err(format!("Operation d'aggregation non supportee : {}", other)),
    };

    let result_df = lf.group_by(group_exprs)
        .agg(vec![agg_expr])
        .collect()
        .map_err(|e| format!("Erreur d'aggregation: {}", e))?;

    write_df(result_df, destination)?;
    println!("SUCCESS: Executed groupby on '{}' -> '{}'", source, destination);
    Ok(())
}

/// Effectue une jointure (Join) entre deux fichiers (left et right)
pub fn join(
    left_source: &str,
    right_source: &str,
    destination: &str,
    left_on: &str,
    right_on: &str,
    how: &str,
) -> Result<(), String> {
    let left_lf = read_df(left_source)?;
    let right_lf = read_df(right_source)?;

    // Determine type de jointure
    let join_type = match how.to_lowercase().as_str() {
        "left" => JoinType::Left,
        "outer" => JoinType::Outer { coalesce: true },
        _ => JoinType::Inner,
    };

    let result_df = left_lf.join(
        right_lf,
        vec![col(left_on)],
        vec![col(right_on)],
        join_type.into(),
    )
    .collect()
    .map_err(|e| format!("Erreur lors de la jointure Polars: {}", e))?;

    write_df(result_df, destination)?;
    println!("SUCCESS: Joined '{}' and '{}' -> '{}'", left_source, right_source, destination);
    Ok(())
}

/// Divise (Split) un jeu de donnees en plusieurs fichiers selon les valeurs uniques d'une colonne
pub fn split(
    source: &str,
    destination_prefix: &str,
    by_column: &str,
) -> Result<(), String> {
    let lf = read_df(source)?;

    // Recuperer les valeurs uniques de la colonne cible en collectant temporairement
    let df_temp = lf.clone().select([col(by_column)]).collect()
        .map_err(|e| format!("Erreur lors de la recuperation de la colonne de split : {}", e))?;
    
    let unique_series = df_temp.column(by_column)
        .map_err(|e| format!("Colonne de split introuvable : {}", e))?
        .unique()
        .map_err(|e| format!("Impossible d'extraire les valeurs uniques : {}", e))?;

    // Determiner l'extension du fichier source pour les fichiers de sortie
    let src_path = Path::new(source);
    let ext = src_path.extension()
        .and_then(|s| s.to_str())
        .unwrap_or("csv");

    println!("[RUST SPLIT] Found {} unique values for column '{}'", unique_series.len(), by_column);

    for i in 0..unique_series.len() {
        let val_any = unique_series.get(i)
            .map_err(|e| format!("Erreur de lecture de la valeur unique : {}", e))?;
        
        let val_str = val_any.to_string().replace("\"", "");

        // Filtrer la DataFrame pour cette valeur unique
        let filtered_lf = lf.clone().filter(col(by_column).eq(lit(val_str.clone())));
        let filtered_df = filtered_lf.collect()
            .map_err(|e| format!("Erreur lors du filtrage pour la valeur '{}' : {}", val_str, e))?;

        // Construire le fichier de destination : <prefix>_<value>.<ext>
        let dest_file = format!("{}_{}.{}", destination_prefix, val_str, ext);
        write_df(filtered_df, &dest_file)?;
        println!("[RUST SPLIT] Saved split partition to '{}'", dest_file);
    }

    println!("SUCCESS: Splitted '{}' by column '{}' into prefix '{}'", source, by_column, destination_prefix);
    Ok(())
}

/// Fusionne (Merge/Union) verticalement plusieurs fichiers de donnees de meme type
pub fn merge(
    sources: Vec<String>,
    destination: &str,
) -> Result<(), String> {
    if sources.is_empty() {
        return Err("La liste des fichiers sources a fusionner est vide".to_string());
    }

    let mut lfs = Vec::new();
    for src in &sources {
        let lf = read_df(src)?;
        lfs.push(lf);
    }

    // Fusionner verticalement via concat
    let result_lf = concat(lfs, UnionArgs::default())
        .map_err(|e| format!("Erreur de fusion verticale concat Polars : {}", e))?;

    let result_df = result_lf.collect()
        .map_err(|e| format!("Erreur lors de la collection de la fusion : {}", e))?;

    write_df(result_df, destination)?;
    println!("SUCCESS: Merged {} files into '{}'", sources.len(), destination);
    Ok(())
}

/// Calcule une métrique spécifique sur une colonne d'un jeu de données
pub fn calculate_metric(
    source: &str,
    target_column: &str,
    metric_type: &str,
    regex_pattern: Option<&str>,
    limit_rows: Option<usize>,
) -> Result<String, String> {
    let mut lf = read_df(source)?;

    if let Some(limit) = limit_rows {
        lf = lf.limit(limit as u32);
    }

    let expr = match metric_type.to_lowercase().as_str() {
        "sum" => col(target_column).sum(),
        "mean" => col(target_column).mean(),
        "min" => col(target_column).min(),
        "max" => col(target_column).max(),
        "count" => col(target_column).count(),
        "null_count" => col(target_column).null_count(),
        "n_unique" => col(target_column).n_unique(),
        "match_regex" => {
            let pattern = regex_pattern.ok_or_else(|| "regex_pattern est requis pour match_regex".to_string())?;
            col(target_column).str().contains(lit(pattern), false).cast(DataType::Int64).sum()
        },
        "non_match_regex" => {
            let pattern = regex_pattern.ok_or_else(|| "regex_pattern est requis pour non_match_regex".to_string())?;
            col(target_column).str().contains(lit(pattern), false).not().cast(DataType::Int64).sum()
        },
        other => return Err(format!("Type de métrique non supporté : {}", other)),
    };

    let metric_df = lf.select([expr]).collect()
        .map_err(|e| format!("Erreur lors de l'exécution de la métrique : {}", e))?;

    if metric_df.height() == 0 {
        return Ok(r#"{"value":null}"#.to_string());
    }

    let val_any = metric_df.column(metric_df.get_column_names()[0])
        .map_err(|e| e.to_string())?
        .get(0)
        .map_err(|e| e.to_string())?;

    let json_val = match val_any {
        AnyValue::Null => serde_json::Value::Null,
        AnyValue::Boolean(b) => serde_json::Value::Bool(b),
        AnyValue::Int8(v) => serde_json::Value::Number(v.into()),
        AnyValue::Int16(v) => serde_json::Value::Number(v.into()),
        AnyValue::Int32(v) => serde_json::Value::Number(v.into()),
        AnyValue::Int64(v) => serde_json::Value::Number(v.into()),
        AnyValue::UInt8(v) => serde_json::Value::Number(v.into()),
        AnyValue::UInt16(v) => serde_json::Value::Number(v.into()),
        AnyValue::UInt32(v) => serde_json::Value::Number(v.into()),
        AnyValue::UInt64(v) => serde_json::Value::Number(v.into()),
        AnyValue::Float32(v) => serde_json::Number::from_f64(v as f64).map(serde_json::Value::Number).unwrap_or(serde_json::Value::Null),
        AnyValue::Float64(v) => serde_json::Number::from_f64(v).map(serde_json::Value::Number).unwrap_or(serde_json::Value::Null),
        other => {
            let s = other.to_string();
            let cleaned = if s.starts_with('"') && s.ends_with('"') && s.len() >= 2 {
                s[1..s.len()-1].to_string()
            } else {
                s
            };
            if let Ok(parsed_f) = cleaned.parse::<f64>() {
                serde_json::Number::from_f64(parsed_f).map(serde_json::Value::Number).unwrap_or(serde_json::Value::Null)
            } else if let Ok(parsed_b) = cleaned.parse::<bool>() {
                serde_json::Value::Bool(parsed_b)
            } else if cleaned == "null" || cleaned == "None" {
                serde_json::Value::Null
            } else {
                serde_json::Value::String(cleaned)
            }
        }
    };

    let result_obj = serde_json::json!({
        "value": json_val
    });

    Ok(result_obj.to_string())
}

/// Découpe séquentiellement un jeu de données en plusieurs fichiers selon un seuil cumulé
pub fn chunk_cumulative(
    source: &str,
    destination_prefix: &str,
    target_column: &str,
    cumulative_threshold: f64,
) -> Result<(), String> {
    let lf = read_df(source)?;
    let df = lf.collect().map_err(|e| format!("Erreur lors de la collection du fichier source : {}", e))?;

    let col_series = df.column(target_column)
        .map_err(|e| format!("Colonne '{}' introuvable : {}", target_column, e))?;

    let col_f64 = col_series.cast(&DataType::Float64)
        .map_err(|e| format!("Impossible de convertir la colonne '{}' en Float64 : {}", target_column, e))?;

    let col_ca = col_f64.f64().map_err(|e| e.to_string())?;

    // Détecter l'extension du fichier source
    let src_path = Path::new(source);
    let ext = src_path.extension()
        .and_then(|s| s.to_str())
        .unwrap_or("csv");

    let mut current_sum = 0.0;
    let mut start_row = 0;
    let mut part_idx = 1;
    let total_rows = df.height();

    for row_idx in 0..total_rows {
        let val = col_ca.get(row_idx).unwrap_or(0.0);
        current_sum += val;

        if current_sum >= cumulative_threshold {
            let chunk_df = df.slice(start_row as i64, row_idx - start_row + 1);
            let dest_file = format!("{}_part_{}.{}", destination_prefix, part_idx, ext);
            write_df(chunk_df, &dest_file)?;
            part_idx += 1;
            start_row = row_idx + 1;
            current_sum = 0.0;
        }
    }

    // Écrire le dernier chunk restant si non vide
    if start_row < total_rows {
        let chunk_df = df.slice(start_row as i64, total_rows - start_row);
        let dest_file = format!("{}_part_{}.{}", destination_prefix, part_idx, ext);
        write_df(chunk_df, &dest_file)?;
    }

    println!("SUCCESS: Chunked '{}' by cumulative threshold {} on column '{}'", source, cumulative_threshold, target_column);
    Ok(())
}

fn find_op_outside_quotes(s: &str, op: &str) -> Option<usize> {
    let mut in_single_quote = false;
    let mut in_double_quote = false;
    let bytes = s.as_bytes();
    let op_bytes = op.as_bytes();
    
    if bytes.len() < op_bytes.len() {
        return None;
    }
    
    for i in 0..=(bytes.len() - op_bytes.len()) {
        let c = bytes[i] as char;
        if c == '\'' && !in_double_quote {
            in_single_quote = !in_single_quote;
        } else if c == '"' && !in_single_quote {
            in_double_quote = !in_double_quote;
        }
        
        if !in_single_quote && !in_double_quote {
            if &bytes[i..i+op_bytes.len()] == op_bytes {
                return Some(i);
            }
        }
    }
    None
}

fn parse_simple_expr(s: &str) -> Result<Expr, String> {
    let math_ops = [("+", "add"), ("-", "sub"), ("*", "mul"), ("/", "div")];
    for (op, op_name) in &math_ops {
        if let Some(idx) = find_op_outside_quotes(s, op) {
            let left = parse_simple_expr(&s[..idx])?;
            let right = parse_simple_expr(&s[idx + op.len()..])?;
            return match *op_name {
                "add" => Ok(left + right),
                "sub" => Ok(left - right),
                "mul" => Ok(left * right),
                "div" => Ok(left / right),
                _ => Err("Invalid math operator".to_string()),
            };
        }
    }

    let s_clean = s.trim();
    if s_clean.starts_with('\'') && s_clean.ends_with('\'') && s_clean.len() >= 2 {
        Ok(lit(&s_clean[1..s_clean.len() - 1]))
    } else if s_clean.starts_with('"') && s_clean.ends_with('"') && s_clean.len() >= 2 {
        Ok(lit(&s_clean[1..s_clean.len() - 1]))
    } else if let Ok(val) = s_clean.parse::<i64>() {
        Ok(lit(val))
    } else if let Ok(val) = s_clean.parse::<f64>() {
        Ok(lit(val))
    } else if s_clean.to_lowercase() == "true" {
        Ok(lit(true))
    } else if s_clean.to_lowercase() == "false" {
        Ok(lit(false))
    } else {
        Ok(col(s_clean))
    }
}

fn parse_comparison_expr(s: &str) -> Result<Expr, String> {
    let operators = [("==", "eq"), ("!=", "ne"), (">=", "gt_eq"), (">", "gt"), ("<=", "lt_eq"), ("<", "lt")];
    for (op, op_name) in &operators {
        if let Some(idx) = s.find(op) {
            let left_part = s[..idx].trim();
            let right_part = s[idx + op.len()..].trim();
            let left_expr = parse_simple_expr(left_part)?;
            let right_expr = parse_simple_expr(right_part)?;
            
            return match *op_name {
                "eq" => Ok(left_expr.eq(right_expr)),
                "ne" => Ok(left_expr.neq(right_expr)),
                "gt_eq" => Ok(left_expr.gt_eq(right_expr)),
                "gt" => Ok(left_expr.gt(right_expr)),
                "lt_eq" => Ok(left_expr.lt_eq(right_expr)),
                "lt" => Ok(left_expr.lt(right_expr)),
                _ => Err("Invalid comparison operator".to_string()),
            };
        }
    }
    parse_simple_expr(s)
}

fn parse_conditional_expr(expr_str: &str) -> Result<Expr, String> {
    let s = expr_str.trim();
    if s.starts_with("IF ") || s.starts_with("if ") {
        let then_idx = s.find(" THEN ").or_else(|| s.find(" then ")).ok_or("Syntax Error: Missing THEN")?;
        let else_idx = s.find(" ELSE ").or_else(|| s.find(" else ")).ok_or("Syntax Error: Missing ELSE")?;
        
        let cond_part = &s[3..then_idx].trim();
        let then_part = &s[then_idx + 6..else_idx].trim();
        let else_part = &s[else_idx + 6..].trim();
        
        let cond_expr = parse_comparison_expr(cond_part)?;
        let then_expr = parse_simple_expr(then_part)?;
        let else_expr = parse_simple_expr(else_part)?;
        
        Ok(when(cond_expr).then(then_expr).otherwise(else_expr))
    } else {
        parse_simple_expr(s)
    }
}

/// Clean dataset: sort, deduplicate, rename/select columns, fill/drop NA, and derive columns.
pub fn clean(
    source: &str,
    destination: &str,
    sort_by: Option<String>,
    sort_descending: bool,
    deduplicate: bool,
    deduplicate_on: Option<Vec<String>>,
    select_columns: Option<Vec<String>>,
    rename_columns: Option<Vec<(String, String)>>,
    fill_na: Option<Vec<(String, String)>>,
    drop_na: bool,
    derive_columns: Option<Vec<(String, String)>>,
) -> Result<(), String> {
    let mut lf = read_df(source)?;

    // 1. Select columns if specified
    if let Some(cols) = select_columns {
        let select_exprs: Vec<Expr> = cols.iter().map(|c| col(c)).collect();
        lf = lf.select(select_exprs);
    }

    // 2. Rename columns if specified
    if let Some(renames) = rename_columns {
        let (existing, new): (Vec<String>, Vec<String>) = renames.into_iter().unzip();
        lf = lf.rename(existing, new);
    }

    // 3. Fill NA if specified
    if let Some(fills) = fill_na {
        for (col_name, fill_value) in fills {
            let expr = if let Ok(val) = fill_value.parse::<i64>() {
                lit(val)
            } else if let Ok(val) = fill_value.parse::<f64>() {
                lit(val)
            } else if let Ok(val) = fill_value.parse::<bool>() {
                lit(val)
            } else {
                lit(fill_value)
            };
            lf = lf.with_column(col(&col_name).fill_null(expr).alias(&col_name));
        }
    }

    // 4. Drop NA rows if specified
    if drop_na {
        lf = lf.drop_nulls(None);
    }

    // 5. Derive columns if specified
    if let Some(derives) = derive_columns {
        for (new_col, expr_str) in derives {
            let compiled_expr = parse_conditional_expr(&expr_str)?;
            lf = lf.with_column(compiled_expr.alias(&new_col));
        }
    }

    // 6. Deduplicate if specified
    if deduplicate {
        let subset = deduplicate_on;
        lf = lf.unique(subset, UniqueKeepStrategy::First);
    }

    // 7. Sort if specified
    if let Some(sort_col) = sort_by {
        let sort_options = SortOptions {
            descending: sort_descending,
            nulls_last: true,
            multithreaded: true,
            maintain_order: true,
        };
        lf = lf.sort(&sort_col, sort_options);
    }

    let df = lf.collect().map_err(|e| format!("Erreur lors de la collection de nettoyage : {}", e))?;
    write_df(df, destination)?;

    println!("SUCCESS: Cleaned dataset '{}' -> '{}'", source, destination);
    Ok(())
}
