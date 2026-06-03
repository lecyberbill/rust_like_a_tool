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
