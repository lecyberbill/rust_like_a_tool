// [WFGY] Zone: TRANSIT | λ: 0.2 | Action: Register data.generate_fake primitive dispatch

use std::env;
use std::process;

mod db_connector;
mod error;
mod primitives;
mod s3_connector;

pub use error::MuscleError;

fn init_logging() {
    use tracing_subscriber::filter::EnvFilter;
    let filter = EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info"));
    tracing_subscriber::fmt()
        .with_env_filter(filter)
        .with_target(true)
        .with_thread_ids(true)
        .json()
        .with_writer(std::io::stderr)
        .init();
}

fn main() {
    init_logging();

    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        tracing::error!("Missing primitive name. Usage: rust_muscle <primitive> [args]");
        eprintln!("Missing primitive name. Usage: rust_muscle <primitive> [args]");
        process::exit(1);
    }

    let primitive = &args[1];
    tracing::info!(primitive = %primitive, args_count = args.len() - 2, "Executing primitive");
    let result = match primitive.as_str() {
        // io
        "io.copy" => primitives::io::handle_io_copy(&args[2..]),
        "io.move" => primitives::io::handle_io_move(&args[2..]),
        "io.delete" => primitives::io::handle_io_delete(&args[2..]),
        "io.metadata" => primitives::io::handle_io_metadata(&args[2..]),
        "io.write_file" => primitives::io::handle_io_write_file(&args[2..]),
        "io.read_file" => primitives::io::handle_io_copy(&args[2..]),
        "data.zip" => primitives::io::handle_io_zip(&args[2..]),
        "data.unzip" => primitives::io::handle_io_unzip(&args[2..]),

        // net
        "net.download" => primitives::net::handle_net_download(&args[2..]),
        "net.upload" => primitives::net::handle_net_upload(&args[2..]),
        "net.ftp_download" => primitives::net::handle_net_ftp_download(&args[2..]),
        "net.ftp_download_filtered" => {
            primitives::net::handle_net_ftp_download_filtered(&args[2..])
        }
        "net.ftp_upload" => primitives::net::handle_net_ftp_upload(&args[2..]),
        "net.sftp_download" => primitives::net::handle_net_sftp_download(&args[2..]),
        "net.sftp_download_filtered" => {
            primitives::net::handle_net_sftp_download_filtered(&args[2..])
        }
        "net.sftp_upload" => primitives::net::handle_net_sftp_upload(&args[2..]),
        "google.sheets_read" => primitives::net::handle_google_sheets_read(&args[2..]),
        "google.sheets_write" => primitives::net::handle_google_sheets_write(&args[2..]),
        "net.http_request" => primitives::net::handle_net_http_request(&args[2..]),
        "net.notify" => primitives::net::handle_net_notify(&args[2..]),
        "net.download_images" => Err(MuscleError::UnsupportedPrimitive(
            "Deprecated: use net.http_request".to_string(),
        )),

        // data format
        "data.csv_to_json" => primitives::data_format::handle_csv_to_json(&args[2..]),
        "data.json_to_csv" => primitives::data_format::handle_json_to_csv(&args[2..]),
        "data.xml_to_json" => primitives::data_format::handle_xml_to_json(&args[2..]),
        "data.xml_transform" => primitives::data_format::handle_xml_transform(&args[2..]),
        "data.to_xlsx" => primitives::data_format::handle_to_xlsx(&args[2..]),
        "data.json_to_xml" => primitives::data_format::handle_json_to_xml(&args[2..]),
        "data.read" => primitives::data_format::handle_data_read(&args[2..]),
        "data.write" => primitives::data_format::handle_data_write(&args[2..]),
        "data.convert" => primitives::data_format::handle_data_convert(&args[2..]),
        "data.generate_fake" => primitives::data_format::handle_generate_fake(&args[2..]),

        // data transform
        "data_filter" | "data.filter" => primitives::data_transform::handle_data_filter(&args[2..]),
        "data.split" => primitives::data_transform::handle_data_split(&args[2..]),
        "data.merge" => primitives::data_transform::handle_data_merge(&args[2..]),
        "data.chunk_cumulative" => {
            primitives::data_transform::handle_data_chunk_cumulative(&args[2..])
        }
        "data.clean" => primitives::data_transform::handle_data_clean(&args[2..]),
        "data.validate" => primitives::data_transform::handle_data_validate(&args[2..]),

        // analytical
        "data.groupby" => primitives::analytical::handle_data_groupby(&args[2..]),
        "data.join" => primitives::analytical::handle_data_join(&args[2..]),
        "data.metrics" => primitives::analytical::handle_data_metrics(&args[2..]),
        "data.lookup" => primitives::analytical::handle_data_lookup(&args[2..]),
        "data.deduplicate" => primitives::analytical::handle_data_deduplicate(&args[2..]),
        "data.anonymize" => primitives::analytical::handle_data_anonymize(&args[2..]),
        "data.pivot" => primitives::analytical::handle_data_pivot(&args[2..]),
        "data.unpivot" => primitives::analytical::handle_data_unpivot(&args[2..]),
        "data.delta" => primitives::analytical::handle_data_delta(&args[2..]),
        "data.type_cast" => primitives::analytical::handle_data_type_cast(&args[2..]),
        "data.scd" => primitives::analytical::handle_data_scd(&args[2..]),
        "data.partition" => primitives::analytical::handle_data_partition(&args[2..]),
        "data.split_out" => primitives::analytical::handle_data_split_out(&args[2..]),

        // db
        "db.query" => primitives::db::handle_db_query(&args[2..]),
        "db.insert" => primitives::db::handle_db_insert(&args[2..]),
        "db.upsert" => primitives::db::handle_db_upsert(&args[2..]),

        // mongodb
        "mongodb.find" => primitives::net::handle_mongodb_find(&args[2..]),
        "mongodb.insert" => primitives::net::handle_mongodb_insert(&args[2..]),

        // ai
        "ai.summarize" => primitives::ai::handle_ai_summarize(&args[2..]),
        "ai.extract" => primitives::ai::handle_ai_extract(&args[2..]),

        // s3
        "s3.upload" => primitives::s3::handle_s3_upload(&args[2..]),
        "s3.download" => primitives::s3::handle_s3_download(&args[2..]),

        _ => Err(MuscleError::UnsupportedPrimitive(format!(
            "Unknown primitive '{}'",
            primitive
        ))),
    };

    match result {
        Ok(_) => process::exit(0),
        Err(err) => {
            tracing::error!(exit_code = err.exit_code(), message = %err.message(), "Primitive failed");
            eprintln!("{}", err.message());
            process::exit(err.exit_code());
        }
    }
}
