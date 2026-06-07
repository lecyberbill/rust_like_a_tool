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
    if let Some(idx) = s.to_uppercase().find(" CONTAINS ") {
        let left_part = s[..idx].trim();
        let right_part = s[idx + 10..].trim();
        let left_expr = parse_simple_expr(left_part)?;
        
        let right_clean = right_part.trim();
        let right_val = if right_clean.starts_with('\'') && right_clean.ends_with('\'') && right_clean.len() >= 2 {
            right_clean[1..right_clean.len() - 1].to_string()
        } else if right_clean.starts_with('"') && right_clean.ends_with('"') && right_clean.len() >= 2 {
            right_clean[1..right_clean.len() - 1].to_string()
        } else {
            right_clean.to_string()
        };
        return Ok(left_expr.str().contains(lit(right_val), false));
    }

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
    right_source: Option<String>,
    left_on: Option<String>,
    right_on: Option<String>,
    how_join: Option<String>,
) -> Result<(), String> {
    let mut lf = read_df(source)?;

    // 0. Jointure relationnelle optionnelle
    if let Some(r_src) = right_source {
        let l_on = left_on.ok_or_else(|| "left_on est requis pour la jointure".to_string())?;
        let r_on = right_on.ok_or_else(|| "right_on est requis pour la jointure".to_string())?;
        let r_lf = read_df(&r_src)?;

        let join_type = match how_join.as_deref().unwrap_or("left").to_lowercase().as_str() {
            "inner" => JoinType::Inner,
            "outer" => JoinType::Outer { coalesce: true },
            _ => JoinType::Left,
        };

        lf = lf.join(
            r_lf,
            vec![col(&l_on)],
            vec![col(&r_on)],
            join_type.into(),
        );
    }

    // 1. Derive columns if specified (must happen first so they can use original columns)
    if let Some(derives) = derive_columns {
        for (new_col, expr_str) in derives {
            let compiled_expr = parse_conditional_expr(&expr_str)?;
            lf = lf.with_column(compiled_expr.alias(&new_col));
        }
    }

    // 2. Fill NA if specified
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

    // 3. Drop NA rows if specified
    if drop_na {
        lf = lf.drop_nulls(None);
    }

    // 4. Rename columns if specified
    if let Some(renames) = rename_columns {
        let (existing, new): (Vec<String>, Vec<String>) = renames.into_iter().unzip();
        lf = lf.rename(existing, new);
    }

    // 5. Select columns if specified (acts as the final projection schema)
    if let Some(cols) = select_columns {
        let select_exprs: Vec<Expr> = cols.iter().map(|c| col(c)).collect();
        lf = lf.select(select_exprs);
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

/// Valide les lignes d'un jeu de données par rapport à un ensemble de règles et sépare les rejets
pub fn validate(
    source: &str,
    destination: &str,
    quarantine: &str,
    rules_json: &str,
) -> Result<(), String> {
    let lf = read_df(source)?;

    let rules: serde_json::Value = serde_json::from_str(rules_json)
        .map_err(|e| format!("Erreur lors du parsing des regles JSON: {}", e))?;

    let rules_arr = rules.as_array()
        .ok_or_else(|| "Les regles de validation doivent former un tableau JSON".to_string())?;

    if rules_arr.is_empty() {
        let df = lf.collect().map_err(|e| e.to_string())?;
        write_df(df.clone(), destination)?;
        let empty_df = df.clear();
        write_df(empty_df, quarantine)?;
        return Ok(());
    }

    let mut combined_expr: Option<Expr> = None;

    for rule in rules_arr {
        let col_name = rule.get("column")
            .and_then(|v| v.as_str())
            .ok_or_else(|| "Regle manquante : 'column'".to_string())?;

        let op = rule.get("operator")
            .and_then(|v| v.as_str())
            .ok_or_else(|| "Regle manquante : 'operator'".to_string())?;

        let val = rule.get("value")
            .ok_or_else(|| "Regle manquante : 'value'".to_string())?;

        let expr = match op.to_lowercase().as_str() {
            "equals" | "==" => {
                if let Some(s) = val.as_str() {
                    col(col_name).eq(lit(s))
                } else if let Some(i) = val.as_i64() {
                    col(col_name).eq(lit(i))
                } else if let Some(f) = val.as_f64() {
                    col(col_name).eq(lit(f))
                } else if let Some(b) = val.as_bool() {
                    col(col_name).eq(lit(b))
                } else {
                    return Err(format!("Type de valeur non supporte pour l'operateur '{}'", op));
                }
            },
            "not_equals" | "!=" => {
                if let Some(s) = val.as_str() {
                    col(col_name).neq(lit(s))
                } else if let Some(i) = val.as_i64() {
                    col(col_name).neq(lit(i))
                } else if let Some(f) = val.as_f64() {
                    col(col_name).neq(lit(f))
                } else if let Some(b) = val.as_bool() {
                    col(col_name).neq(lit(b))
                } else {
                    return Err(format!("Type de valeur non supporte pour l'operateur '{}'", op));
                }
            },
            "contains" => {
                let s = val.as_str().ok_or_else(|| "L'operateur 'contains' necessite une chaine de caracteres".to_string())?;
                col(col_name).str().contains(lit(s), true)
            },
            "starts_with" => {
                let s = val.as_str().ok_or_else(|| "L'operateur 'starts_with' necessite une chaine de caracteres".to_string())?;
                col(col_name).str().starts_with(lit(s))
            },
            "ends_with" => {
                let s = val.as_str().ok_or_else(|| "L'operateur 'ends_with' necessite une chaine de caracteres".to_string())?;
                col(col_name).str().ends_with(lit(s))
            },
            "regex" | "matches" => {
                let s = val.as_str().ok_or_else(|| "L'operateur 'regex' necessite une chaine de caracteres".to_string())?;
                col(col_name).str().contains(lit(s), false)
            },
            "greater_than" | ">" => {
                if let Some(i) = val.as_i64() {
                    col(col_name).gt(lit(i))
                } else if let Some(f) = val.as_f64() {
                    col(col_name).gt(lit(f))
                } else {
                    return Err(format!("L'operateur '{}' necessite une valeur numerique", op));
                }
            },
            "less_than" | "<" => {
                if let Some(i) = val.as_i64() {
                    col(col_name).lt(lit(i))
                } else if let Some(f) = val.as_f64() {
                    col(col_name).lt(lit(f))
                } else {
                    return Err(format!("L'operateur '{}' necessite une valeur numerique", op));
                }
            },
            "greater_than_or_equal" | ">=" => {
                if let Some(i) = val.as_i64() {
                    col(col_name).gt_eq(lit(i))
                } else if let Some(f) = val.as_f64() {
                    col(col_name).gt_eq(lit(f))
                } else {
                    return Err(format!("L'operateur '{}' necessite une valeur numerique", op));
                }
            },
            "less_than_or_equal" | "<=" => {
                if let Some(i) = val.as_i64() {
                    col(col_name).lt_eq(lit(i))
                } else if let Some(f) = val.as_f64() {
                    col(col_name).lt_eq(lit(f))
                } else {
                    return Err(format!("L'operateur '{}' necessite une valeur numerique", op));
                }
            },
            "is_null" => {
                col(col_name).is_null()
            },
            "is_not_null" => {
                col(col_name).is_not_null()
            },
            other => return Err(format!("Operateur de validation non supporte : '{}'", other)),
        };

        combined_expr = Some(match combined_expr {
            Some(curr) => curr.and(expr),
            None => expr,
        });
    }

    let filter_expr = combined_expr.ok_or_else(|| "Aucune regle de validation definie".to_string())?;

    // Filtrer les lignes valides
    let valid_lf = lf.clone().filter(filter_expr.clone());
    let valid_df = valid_lf.collect().map_err(|e| format!("Erreur lors de la collection des lignes valides: {}", e))?;
    let valid_count = valid_df.height();
    write_df(valid_df, destination)?;

    // Filtrer les lignes rejetees (negation du filtre combiné)
    let invalid_lf = lf.filter(filter_expr.not());
    let invalid_df = invalid_lf.collect().map_err(|e| format!("Erreur lors de la collection des lignes rejetees: {}", e))?;
    let invalid_count = invalid_df.height();
    write_df(invalid_df, quarantine)?;

    println!("SUCCESS: Validated dataset. Valid: {}, Quarantine: {}", valid_count, invalid_count);
    Ok(())
}

/// Recherche et fusionne des informations de référentiel externe (jointure gauche Polars)
pub fn lookup(
    source: &str,
    lookup_file: &str,
    source_key: &str,
    lookup_key: &str,
    lookup_value: &str,
    destination: &str,
) -> Result<(), String> {
    let left_lf = read_df(source)?;
    let right_lf = read_df(lookup_file)?;

    // Projection de la table dictionnaire pour ne garder que lookup_key et lookup_value
    let right_projected = right_lf.select([col(lookup_key), col(lookup_value)]);

    let result_df = left_lf.join(
        right_projected,
        vec![col(source_key)],
        vec![col(lookup_key)],
        JoinType::Left.into(),
    )
    .collect()
    .map_err(|e| format!("Erreur lors du lookup Polars: {}", e))?;

    write_df(result_df, destination)?;
    println!("SUCCESS: Lookup join executed on '{}' using dictionary '{}' -> '{}'", source, lookup_file, destination);
    Ok(())
}

/// Supprime les lignes en doublons basées sur des clés spécifiques
pub fn deduplicate(
    source: &str,
    destination: &str,
    subset: Vec<String>,
    keep: &str,
) -> Result<(), String> {
    let lf = read_df(source)?;

    let strategy = match keep.to_lowercase().as_str() {
        "last" => UniqueKeepStrategy::Last,
        _ => UniqueKeepStrategy::First,
    };

    let subset_refs: Vec<String> = subset.iter().map(|s| s.clone()).collect();
    let result_df = lf.unique(Some(subset_refs), strategy)
        .collect()
        .map_err(|e| format!("Erreur lors du dedoublonnage Polars: {}", e))?;

    write_df(result_df, destination)?;
    println!("SUCCESS: Deduplicated dataset '{}' -> '{}' keeping {}", source, destination, keep);
    Ok(())
}

fn fnv1a_hash(s: &str) -> String {
    let mut hash: u64 = 0xcbf29ce484222325;
    for byte in s.as_bytes() {
        hash ^= *byte as u64;
        hash = hash.wrapping_mul(0x100000001b3);
    }
    format!("{:016x}", hash)
}

fn mask_string(s: &str) -> String {
    let chars: Vec<char> = s.chars().collect();
    let len = chars.len();
    if len <= 2 {
        return "*".repeat(len);
    }
    let mut result = String::new();
    result.push(chars[0]);
    for _ in 1..len - 1 {
        result.push('*');
    }
    result.push(chars[len - 1]);
    result
}

fn mask_email(s: &str) -> String {
    if let Some(pos) = s.find('@') {
        let (local, domain) = s.split_at(pos);
        let masked_local = mask_string(local);
        format!("{}{}", masked_local, domain)
    } else {
        mask_string(s)
    }
}

/// Anonymise les colonnes spécifiées selon les règles (colonne:stratégie)
pub fn anonymize(
    source: &str,
    destination: &str,
    rules: Vec<(String, String)>,
) -> Result<(), String> {
    let mut lf = read_df(source)?;

    for (col_name, strategy) in rules {
        let strategy_clone = strategy.clone();
        lf = lf.with_column(
            col(&col_name).cast(DataType::String).map(move |s| {
                let ca = s.str()?;
                let anonymized: StringChunked = ca.into_iter().map(|opt_val| {
                    opt_val.map(|val| {
                        match strategy_clone.as_str() {
                            "replace" => "[REDACTED]".to_string(),
                            "hash" => fnv1a_hash(val),
                            "mask" => mask_string(val),
                            "mask_email" => mask_email(val),
                            _ => "[REDACTED]".to_string()
                        }
                    })
                }).collect();
                Ok(Some(anonymized.into_series()))
            }, GetOutput::from_type(DataType::String)).alias(&col_name)
        );
    }

    let df = lf.collect().map_err(|e| format!("Erreur lors de la collection de l'anonymisation : {}", e))?;
    write_df(df, destination)?;
    println!("SUCCESS: Anonymized dataset '{}' -> '{}'", source, destination);
    Ok(())
}

/// Pivote une table du format long au format large (lignes en colonnes)
pub fn pivot(
    source: &str,
    destination: &str,
    index: Vec<String>,
    on: &str,
    values: &str,
    aggregate: &str,
) -> Result<(), String> {
    let df = read_df(source)?.collect()
        .map_err(|e| format!("Erreur de lecture du fichier source pour pivot : {}", e))?;

    let pivot_agg = match aggregate.to_lowercase().as_str() {
        "sum" => col(values).sum(),
        "mean" => col(values).mean(),
        "min" => col(values).min(),
        "max" => col(values).max(),
        "count" => col(values).count(),
        "last" => col(values).last(),
        _ => col(values).first(),
    };

    let index_refs: Vec<&str> = index.iter().map(|s| s.as_str()).collect();

    let res_df = polars::prelude::pivot::pivot(
        &df,
        &[values],
        &index_refs,
        &[on],
        true, // sort_columns
        Some(pivot_agg),
        None, // separator
    ).map_err(|e| format!("Erreur lors de l'execution du pivot Polars : {}", e))?;

    write_df(res_df, destination)?;
    println!("SUCCESS: Pivoted dataset '{}' -> '{}'", source, destination);
    Ok(())
}

/// Dépivote une table du format large au format long (colonnes en lignes)
pub fn unpivot(
    source: &str,
    destination: &str,
    index: Vec<String>,
    on: Option<Vec<String>>,
    variable_name: &str,
    value_name: &str,
) -> Result<(), String> {
    let lf = read_df(source)?;

    let id_vars = index.into_iter().map(|s| s.into()).collect();
    let value_vars = on.unwrap_or_default().into_iter().map(|s| s.into()).collect();

    let var_name_opt = if variable_name.is_empty() { None } else { Some(variable_name.to_string().into()) };
    let val_name_opt = if value_name.is_empty() { None } else { Some(value_name.to_string().into()) };

    let melt_args = polars::prelude::MeltArgs {
        id_vars,
        value_vars,
        variable_name: var_name_opt,
        value_name: val_name_opt,
        streamable: false,
    };

    let res_lf = lf.melt(melt_args);
    let res_df = res_lf.collect().map_err(|e| format!("Erreur lors du depivotement Melt Polars : {}", e))?;

    write_df(res_df, destination)?;
    println!("SUCCESS: Unpivoted dataset '{}' -> '{}'", source, destination);
    Ok(())
}

/// Calcule les différences incrémentales entre un fichier source et cible sur clés primaires
pub fn delta(
    source: &str,
    target: &str,
    keys: Vec<String>,
    destination_upsert: &str,
    destination_delete: &str,
    destination_sync: Option<&str>,
) -> Result<(), String> {
    let source_lf = read_df(source)?;
    let target_lf = read_df(target)?;

    // Les clés de jointure sous forme d'expressions
    let key_exprs: Vec<Expr> = keys.iter().map(|k| col(k)).collect();

    // 1. Les deletes : présents dans target mais absents de source (anti-join)
    let deletes_lf = target_lf.clone().join(
        source_lf.clone(),
        key_exprs.clone(),
        key_exprs.clone(),
        JoinType::Anti.into(),
    );
    let deletes_df = deletes_lf.collect().map_err(|e| format!("Erreur lors du calcul des deletes : {}", e))?;
    write_df(deletes_df, destination_delete)?;

    // 2. Les upserts : tous les enregistrements du fichier source (inserts + updates)
    let source_df = source_lf.clone().collect().map_err(|e| format!("Erreur lors de la collection de source : {}", e))?;
    write_df(source_df.clone(), destination_upsert)?;

    // 3. Si destination_sync est spécifiée, on écrit la table finale synchronisée
    if let Some(dest_sync) = destination_sync {
        let kept_target_lf = target_lf.join(
            source_lf,
            key_exprs.clone(),
            key_exprs,
            JoinType::Anti.into(),
        );
        let kept_target_df = kept_target_lf.collect().map_err(|e| format!("Erreur lors du calcul des conservations : {}", e))?;

        let synced_df = if kept_target_df.height() > 0 {
            let synced_lf = concat(
                vec![source_df.lazy(), kept_target_df.lazy()],
                UnionArgs::default(),
            ).map_err(|e| format!("Erreur lors de la fusion du sync : {}", e))?;
            synced_lf.collect().map_err(|e| format!("Erreur de collection du sync : {}", e))?
        } else {
            source_df
        };
        write_df(synced_df, dest_sync)?;
    }

    println!("SUCCESS: Computed delta CDC from '{}' and '{}'", source, target);
    Ok(())
}

/// Convertit les types de colonnes selon une configuration JSON
pub fn type_cast(
    source: &str,
    destination: &str,
    casts_json: &str,
) -> Result<(), String> {
    let mut lf = read_df(source)?;
    
    let casts: serde_json::Map<String, serde_json::Value> = serde_json::from_str(casts_json)
        .map_err(|e| format!("Invalid JSON casts specification: {}", e))?;

    for (col_name, type_val) in casts {
        let type_str = type_val.as_str()
            .ok_or_else(|| format!("Cast value for column '{}' must be a string", col_name))?;
        
        let col_expr = col(&col_name);
        
        let cast_expr = if type_str.starts_with("date") {
            let fmt = if type_str.contains(':') {
                type_str.split(':').nth(1).unwrap_or("%Y-%m-%d")
            } else {
                "%Y-%m-%d"
            };
            col_expr.cast(DataType::String).str().strptime(
                DataType::Date,
                StrptimeOptions {
                    format: Some(fmt.to_string()),
                    strict: false,
                    exact: false,
                    cache: false,
                },
                lit("raise")
            )
        } else if type_str.starts_with("datetime") {
            let fmt = if type_str.contains(':') {
                type_str.split(':').nth(1).unwrap_or("%Y-%m-%d %H:%M:%S")
            } else {
                "%Y-%m-%d %H:%M:%S"
            };
            col_expr.cast(DataType::String).str().strptime(
                DataType::Datetime(TimeUnit::Milliseconds, None),
                StrptimeOptions {
                    format: Some(fmt.to_string()),
                    strict: false,
                    exact: false,
                    cache: false,
                },
                lit("raise")
            )
        } else {
            match type_str.to_lowercase().as_str() {
                "integer" | "int" | "i64" => col_expr.cast(DataType::Int64),
                "float" | "double" | "f64" => col_expr.cast(DataType::Float64),
                "boolean" | "bool" => col_expr.cast(DataType::Boolean),
                "string" | "str" | "varchar" => col_expr.cast(DataType::String),
                other => return Err(format!("Unsupported cast target type '{}' for column '{}'", other, col_name)),
            }
        };
        
        lf = lf.with_column(cast_expr.alias(&col_name));
    }

    let df = lf.collect().map_err(|e| format!("Erreur lors de l'execution du type_cast Polars : {}", e))?;
    write_df(df, destination)?;
    println!("SUCCESS: Executed type_cast on '{}' -> '{}'", source, destination);
    Ok(())
}



