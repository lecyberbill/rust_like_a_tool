// [WFGY] Zone: SAFE | λ: 0.1 | Action: Restructured entrypoint with submodules dispatch

use std::env;
use std::process;

mod error;
mod db_connector;
mod s3_connector;
mod primitives;

pub use error::MuscleError;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Error: Missing command/primitive name. Usage: rust_muscle <primitive> [args]");
        process::exit(1);
    }

    let primitive = &args[1];
    let result = match primitive.as_str() {
        // io
        "io.copy" => primitives::io::handle_io_copy(&args[2..]),
        "io.move" => primitives::io::handle_io_move(&args[2..]),
        "io.delete" => primitives::io::handle_io_delete(&args[2..]),
        "io.metadata" => primitives::io::handle_io_metadata(&args[2..]),
        "io.write_file" => primitives::io::handle_io_write_file(&args[2..]),

        // net
        "net.download" => primitives::net::handle_net_download(&args[2..]),
        "net.upload" => primitives::net::handle_net_upload(&args[2..]),
        "net.http_request" => primitives::net::handle_net_http_request(&args[2..]),
        "net.download_images" => Err(MuscleError::Generic("Deprecated: use net.http_request".to_string())),

        // data format
        "data.csv_to_json" => primitives::data_format::handle_csv_to_json(&args[2..]),
        "data.json_to_csv" => primitives::data_format::handle_json_to_csv(&args[2..]),
        "data.xml_to_json" => primitives::data_format::handle_xml_to_json(&args[2..]),
        "data.xml_transform" => primitives::data_format::handle_xml_transform(&args[2..]),

        // data transform
        "data_filter" | "data.filter" => primitives::data_transform::handle_data_filter(&args[2..]),
        "data.split" => primitives::data_transform::handle_data_split(&args[2..]),
        "data.merge" => primitives::data_transform::handle_data_merge(&args[2..]),
        "data.chunk_cumulative" => primitives::data_transform::handle_data_chunk_cumulative(&args[2..]),
        "data.clean" => primitives::data_transform::handle_data_clean(&args[2..]),

        // analytical
        "data.groupby" => primitives::analytical::handle_data_groupby(&args[2..]),
        "data.join" => primitives::analytical::handle_data_join(&args[2..]),
        "data.metrics" => primitives::analytical::handle_data_metrics(&args[2..]),

        // db
        "db.query" => primitives::db::handle_db_query(&args[2..]),
        "db.insert" => primitives::db::handle_db_insert(&args[2..]),

        // s3
        "s3.upload" => primitives::s3::handle_s3_upload(&args[2..]),
        "s3.download" => primitives::s3::handle_s3_download(&args[2..]),

        _ => Err(MuscleError::Generic(format!("Unknown primitive '{}'", primitive))),
    };

    match result {
        Ok(_) => process::exit(0),
        Err(err) => {
            eprintln!("{}", err.message());
            process::exit(err.exit_code());
        }
    }
}
