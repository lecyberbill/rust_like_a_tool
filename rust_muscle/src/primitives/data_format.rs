// [WFGY] Zone: SAFE | λ: 0.1 | Action: Format conversion primitives (CSV, JSON, XML)

use crate::MuscleError;
use quick_xml::events::Event;
use quick_xml::reader::Reader;
use std::fs;
use std::path::Path;

pub fn handle_csv_to_json(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut delimiter = String::from(",");
    let mut has_headers = true;

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
            "--has_headers" | "--has-headers" => {
                if i + 1 < args.len() {
                    has_headers = args[i + 1].parse::<bool>().unwrap_or(true);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --has_headers".to_string(),
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

    csv_to_json(source, destination, &delimiter, has_headers)
}

fn csv_to_json(
    source: &str,
    destination: &str,
    delimiter: &str,
    has_headers: bool,
) -> Result<(), MuscleError> {
    let src_path = Path::new(source);
    if !src_path.exists() {
        return Err(MuscleError::SourceNotFound(format!(
            "Source file '{}' does not exist",
            source
        )));
    }

    let content = fs::read_to_string(src_path)
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to read source file: {}", e)))?;

    let mut lines = content.lines();
    let mut headers = Vec::new();

    if has_headers {
        if let Some(header_line) = lines.next() {
            headers = header_line
                .split(delimiter)
                .map(|s| s.trim().to_string())
                .collect();
        }
    }

    let mut json_list = Vec::new();

    for line in lines {
        if line.trim().is_empty() {
            continue;
        }

        let fields: Vec<&str> = line.split(delimiter).map(|s| s.trim()).collect();
        let mut obj = serde_json::Map::new();

        if has_headers {
            for (idx, &field) in fields.iter().enumerate() {
                let key = if idx < headers.len() {
                    headers[idx].clone()
                } else {
                    format!("column_{}", idx)
                };
                obj.insert(key, serde_json::Value::String(field.to_string()));
            }
        } else {
            for (idx, &field) in fields.iter().enumerate() {
                obj.insert(
                    idx.to_string(),
                    serde_json::Value::String(field.to_string()),
                );
            }
        }

        json_list.push(serde_json::Value::Object(obj));
    }

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

    let json_bytes = serde_json::to_vec_pretty(&json_list)
        .map_err(|e| MuscleError::IoError(format!("Failed to serialize JSON: {}", e)))?;

    fs::write(dest_path, json_bytes).map_err(|e| {
        MuscleError::PermissionDenied(format!("Failed to write JSON target: {}", e))
    })?;

    println!(
        "SUCCESS: Converted CSV '{}' to JSON '{}'. Rows: {}",
        source,
        destination,
        json_list.len()
    );
    Ok(())
}

pub fn handle_json_to_csv(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut delimiter = String::from(",");
    let mut has_headers = true;

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
            "--has_headers" | "--has-headers" => {
                if i + 1 < args.len() {
                    has_headers = args[i + 1].parse::<bool>().unwrap_or(true);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --has_headers".to_string(),
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

    json_to_csv(source, destination, &delimiter, has_headers)
}

fn json_to_csv(
    source: &str,
    destination: &str,
    delimiter: &str,
    has_headers: bool,
) -> Result<(), MuscleError> {
    let src_path = Path::new(source);
    if !src_path.exists() {
        return Err(MuscleError::SourceNotFound(format!(
            "Source file '{}' does not exist",
            source
        )));
    }

    let content = fs::read_to_string(src_path)
        .map_err(|e| MuscleError::PermissionDenied(format!("Failed to read source file: {}", e)))?;

    let json_val: serde_json::Value = serde_json::from_str(&content)
        .map_err(|e| MuscleError::IoError(format!("Failed to parse JSON: {}", e)))?;

    let array = json_val.as_array().ok_or_else(|| {
        MuscleError::InvalidArg("JSON source must be an array of objects".to_string())
    })?;

    if array.is_empty() {
        println!("WARNING: JSON array is empty. No CSV rows written.");
        return Ok(());
    }

    let mut headers = Vec::new();
    for item in array {
        if let Some(obj) = item.as_object() {
            for key in obj.keys() {
                if !headers.contains(key) {
                    headers.push(key.clone());
                }
            }
        }
    }

    if headers.is_empty() {
        return Err(MuscleError::InvalidArg(
            "JSON array objects have no keys to form headers".to_string(),
        ));
    }

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

    let delimiter_byte = if delimiter.len() == 1 {
        delimiter.as_bytes()[0]
    } else if delimiter == "\\t" || delimiter == "\t" {
        b'\t'
    } else {
        b','
    };

    let file = fs::File::create(dest_path).map_err(|e| {
        MuscleError::PermissionDenied(format!("Failed to create destination file: {}", e))
    })?;

    let mut wtr = csv::WriterBuilder::new()
        .delimiter(delimiter_byte)
        .has_headers(has_headers)
        .from_writer(file);

    if has_headers {
        wtr.write_record(&headers)
            .map_err(|e| MuscleError::IoError(format!("Failed to write CSV headers: {}", e)))?;
    }

    for item in array {
        let mut record = Vec::new();
        let obj = item.as_object();
        for header in &headers {
            let val_str = if let Some(o) = obj {
                match o.get(header) {
                    Some(serde_json::Value::Null) => String::new(),
                    Some(serde_json::Value::Bool(b)) => b.to_string(),
                    Some(serde_json::Value::Number(n)) => n.to_string(),
                    Some(serde_json::Value::String(s)) => s.clone(),
                    Some(other) => other.to_string(),
                    None => String::new(),
                }
            } else {
                String::new()
            };
            record.push(val_str);
        }
        wtr.write_record(&record)
            .map_err(|e| MuscleError::IoError(format!("Failed to write CSV record: {}", e)))?;
    }

    wtr.flush()
        .map_err(|e| MuscleError::IoError(format!("Failed to flush CSV writer: {}", e)))?;

    println!(
        "SUCCESS: Converted JSON '{}' to CSV '{}'. Rows: {}",
        source,
        destination,
        array.len()
    );
    Ok(())
}

pub fn handle_xml_to_json(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;

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

    xml_to_json(source, destination)
}

fn xml_to_json(source: &str, destination: &str) -> Result<(), MuscleError> {
    let src_path = Path::new(source);
    if !src_path.exists() {
        return Err(MuscleError::SourceNotFound(format!(
            "Source XML file '{}' does not exist",
            source
        )));
    }

    let xml_content = fs::read_to_string(src_path).map_err(|e| {
        MuscleError::PermissionDenied(format!("Failed to read XML source file: {}", e))
    })?;

    let mut reader = Reader::from_str(&xml_content);
    reader.trim_text(true);

    let mut buf = Vec::new();
    let mut stack: Vec<(String, serde_json::Map<String, serde_json::Value>)> = Vec::new();
    let mut root_obj = serde_json::Map::new();

    stack.push(("root".to_string(), serde_json::Map::new()));

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(ref e)) => {
                let name = String::from_utf8_lossy(e.name().as_ref()).to_string();
                let mut local_map = serde_json::Map::new();

                for attr in e.attributes() {
                    if let Ok(attr) = attr {
                        let key = format!("@{}", String::from_utf8_lossy(attr.key.as_ref()));
                        let val = String::from_utf8_lossy(&attr.value).to_string();
                        local_map.insert(key, serde_json::Value::String(val));
                    }
                }

                stack.push((name, local_map));
            }
            Ok(Event::Text(ref e)) => {
                let text = e.unescape().unwrap_or_default().into_owned();
                if !text.is_empty() {
                    if let Some((_, map)) = stack.last_mut() {
                        map.insert("#text".to_string(), serde_json::Value::String(text));
                    }
                }
            }
            Ok(Event::End(ref _e)) => {
                if stack.len() > 1 {
                    let (name, map) = stack.pop().unwrap();
                    let val = if map.len() == 1 && map.contains_key("#text") {
                        map.get("#text").unwrap().clone()
                    } else if map.is_empty() {
                        serde_json::Value::Null
                    } else {
                        serde_json::Value::Object(map)
                    };

                    if let Some((_, parent_map)) = stack.last_mut() {
                        if let Some(existing) = parent_map.get_mut(&name) {
                            if let Some(arr) = existing.as_array_mut() {
                                arr.push(val);
                            } else {
                                let old_val = existing.take();
                                *existing = serde_json::Value::Array(vec![old_val, val]);
                            }
                        } else {
                            parent_map.insert(name, val);
                        }
                    }
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => {
                return Err(MuscleError::ParseError(format!(
                    "Error parsing XML on line {}: {}",
                    reader.buffer_position(),
                    e
                )));
            }
            _ => {}
        }
        buf.clear();
    }

    if let Some((_, final_map)) = stack.pop() {
        root_obj = final_map;
    }

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

    let json_bytes =
        serde_json::to_vec_pretty(&serde_json::Value::Object(root_obj)).map_err(|e| {
            MuscleError::IoError(format!(
                "Failed to serialize final XML-to-JSON structure: {}",
                e
            ))
        })?;

    fs::write(dest_path, json_bytes).map_err(|e| {
        MuscleError::PermissionDenied(format!("Failed to write JSON output: {}", e))
    })?;

    println!(
        "SUCCESS: Converted XML '{}' to JSON '{}'",
        source, destination
    );
    Ok(())
}

pub fn handle_xml_transform(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut stylesheet = None;
    let mut destination = None;

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
            "--stylesheet" => {
                if i + 1 < args.len() {
                    stylesheet = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --stylesheet".to_string(),
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

    let source = source
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --source".to_string()))?;
    let stylesheet = stylesheet.ok_or_else(|| {
        MuscleError::MissingArg("Missing required argument --stylesheet".to_string())
    })?;
    let destination = destination.ok_or_else(|| {
        MuscleError::MissingArg("Missing required argument --destination".to_string())
    })?;

    xml_transform(source, stylesheet, destination)
}

fn xml_transform(source: &str, stylesheet: &str, destination: &str) -> Result<(), MuscleError> {
    use xrust::Node;
    use xrust::SequenceTrait;
    use xrust::item::Item;
    use xrust::parser::ParseError;
    use xrust::parser::xml::parse;
    use xrust::transform::context::StaticContextBuilder;
    use xrust::trees::smite::RNode;
    use xrust::xdmerror::{Error, ErrorKind};
    use xrust::xslt::from_document;

    let src_path = Path::new(source);
    let style_path = Path::new(stylesheet);

    if !src_path.exists() {
        return Err(MuscleError::SourceNotFound(format!(
            "Source XML file '{}' does not exist",
            source
        )));
    }
    if !style_path.exists() {
        return Err(MuscleError::SourceNotFound(format!(
            "Stylesheet XSLT file '{}' does not exist",
            stylesheet
        )));
    }

    let src_content = fs::read_to_string(src_path).map_err(|e| {
        MuscleError::PermissionDenied(format!("Failed to read source XML file: {}", e))
    })?;
    let style_content = fs::read_to_string(style_path).map_err(|e| {
        MuscleError::PermissionDenied(format!("Failed to read stylesheet XSLT file: {}", e))
    })?;

    let make_from_str = |s: &str| -> Result<RNode, Error> {
        let doc = RNode::new_document();
        parse(
            doc.clone(),
            s,
            Some(|_: &_| Err(ParseError::MissingNameSpace)),
        )
        .map_err(|e| Error::new(ErrorKind::TypeError, format!("XML Parsing error: {:?}", e)))?;
        Ok(doc)
    };

    let src_doc = make_from_str(&src_content)
        .map_err(|e| MuscleError::IoError(format!("Failed to parse source XML: {:?}", e)))?;
    let style_doc = make_from_str(&style_content)
        .map_err(|e| MuscleError::IoError(format!("Failed to parse stylesheet XSLT: {:?}", e)))?;

    let mut static_context = StaticContextBuilder::new()
        .message(|_| Ok(()))
        .fetcher(|_| Err(Error::new(ErrorKind::NotImplemented, "not implemented")))
        .parser(|_| Err(Error::new(ErrorKind::NotImplemented, "not implemented")))
        .build();

    let mut ctxt = from_document(style_doc, None, make_from_str, |_| Ok(String::new()))
        .map_err(|e| MuscleError::IoError(format!("Failed to compile stylesheet: {:?}", e)))?;

    let src_item = Item::Node(src_doc);
    ctxt.context(vec![src_item], 0);
    ctxt.result_document(RNode::new_document());

    let seq = ctxt
        .evaluate(&mut static_context)
        .map_err(|e| MuscleError::IoError(format!("XSLT evaluation failed: {:?}", e)))?;

    let output_str = seq.to_xml();

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

    fs::write(dest_path, output_str).map_err(|e| {
        MuscleError::PermissionDenied(format!("Failed to write output XML file: {}", e))
    })?;

    println!(
        "SUCCESS: Applied XML transformation from '{}' using stylesheet '{}' to '{}'",
        source, stylesheet, destination
    );
    Ok(())
}

fn run_format_helper(mode: &str, args: &[&str]) -> Result<(), MuscleError> {
    use std::process::Command;
    let python_path = if cfg!(target_os = "windows") {
        Path::new(".venv/Scripts/python.exe")
    } else {
        Path::new(".venv/bin/python")
    };

    let mut cmd = if python_path.exists() {
        Command::new(python_path)
    } else {
        Command::new("python")
    };

    let mut cmd = cmd.arg("brain/format_helper.py").arg(mode);
    for arg in args {
        cmd = cmd.arg(arg);
    }

    let output = cmd.output().map_err(|e| {
        MuscleError::IoError(format!("Failed to start Python format helper: {}", e))
    })?;

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        print!("{}", stdout);
        Ok(())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(MuscleError::IoError(format!(
            "Format helper execution failed: {}",
            stderr.trim()
        )))
    }
}

pub fn handle_to_xlsx(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut sheet_name = String::from("Sheet1");

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
            "--sheet-name" | "--sheet_name" => {
                if i + 1 < args.len() {
                    sheet_name = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --sheet-name".to_string(),
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

    run_format_helper("xlsx", &[source, destination, &sheet_name])
}

pub fn handle_json_to_xml(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut root_element = String::from("root");
    let mut row_element = String::from("row");

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
            "--root-element" | "--root_element" => {
                if i + 1 < args.len() {
                    root_element = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --root-element".to_string(),
                    ));
                }
            }
            "--row-element" | "--row_element" => {
                if i + 1 < args.len() {
                    row_element = args[i + 1].clone();
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --row-element".to_string(),
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

    run_format_helper("xml", &[source, destination, &root_element, &row_element])
}

/// data.read — lit tout format supporté (CSV, JSON, Parquet, JSONL) et écrit en CSV
pub fn handle_data_read(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--source" => {
                source = args.get(i + 1).map(|s| s.as_str());
                i += 2;
            }
            "--destination" => {
                destination = args.get(i + 1).map(|s| s.as_str());
                i += 2;
            }
            other => {
                return Err(MuscleError::InvalidArg(format!(
                    "Unknown argument '{}'",
                    other
                )));
            }
        }
    }
    let source = source.ok_or_else(|| MuscleError::MissingArg("Missing --source".to_string()))?;
    let destination =
        destination.ok_or_else(|| MuscleError::MissingArg("Missing --destination".to_string()))?;
    let df = analytical_engine::read_df(source)
        .map_err(|e| MuscleError::IoError(format!("Read error: {}", e)))?
        .collect()
        .map_err(|e| MuscleError::IoError(format!("Collect error: {}", e)))?;
    analytical_engine::write_df(df, destination)
        .map_err(|e| MuscleError::IoError(format!("Write error: {}", e)))?;
    println!("SUCCESS: Read '{}' -> '{}'", source, destination);
    Ok(())
}

/// data.write — lit CSV source, écrit dans le format détecté par l'extension destination
pub fn handle_data_write(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--source" => {
                source = args.get(i + 1).map(|s| s.as_str());
                i += 2;
            }
            "--destination" => {
                destination = args.get(i + 1).map(|s| s.as_str());
                i += 2;
            }
            other => {
                return Err(MuscleError::InvalidArg(format!(
                    "Unknown argument '{}'",
                    other
                )));
            }
        }
    }
    let source = source.ok_or_else(|| MuscleError::MissingArg("Missing --source".to_string()))?;
    let destination =
        destination.ok_or_else(|| MuscleError::MissingArg("Missing --destination".to_string()))?;
    let df = analytical_engine::read_df(source)
        .map_err(|e| MuscleError::IoError(format!("Read error: {}", e)))?
        .collect()
        .map_err(|e| MuscleError::IoError(format!("Collect error: {}", e)))?;
    analytical_engine::write_df(df, destination)
        .map_err(|e| MuscleError::IoError(format!("Write error: {}", e)))?;
    println!("SUCCESS: Wrote '{}' -> '{}'", source, destination);
    Ok(())
}

/// data.convert — convertit entre tous formats supportés (auto-détection par extension)
pub fn handle_data_convert(args: &[String]) -> Result<(), MuscleError> {
    handle_data_read(args)
}
