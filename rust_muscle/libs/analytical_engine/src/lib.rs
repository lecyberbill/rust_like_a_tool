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
