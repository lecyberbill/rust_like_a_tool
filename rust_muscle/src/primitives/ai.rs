// [WFGY] Zone: SAFE | λ: 0.2 | Action: Native AI Inference CLI primitive wrappers delegating to Python helper

use crate::MuscleError;
use std::path::Path;
use std::process::Command;

fn run_ai_helper(mode: &str, helper_args: &[&str]) -> Result<(), MuscleError> {
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

    let mut cmd = cmd.arg("brain/ai_helper.py").arg("--mode").arg(mode);
    for arg in helper_args {
        cmd = cmd.arg(arg);
    }

    let output = cmd
        .output()
        .map_err(|e| MuscleError::IoError(format!("Failed to start Python AI helper: {}", e)))?;

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);
        print!("{}", stdout);
        if !stderr.is_empty() {
            eprintln!("{}", stderr);
        }
        Ok(())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(MuscleError::IoError(format!(
            "AI helper execution failed: {}",
            stderr.trim()
        )))
    }
}

pub fn handle_ai_summarize(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut column = None;
    let mut target_column = None;
    let mut prompt = None;
    let mut model_provider = None;
    let mut model_id = None;
    let mut base_url = None;

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
            "--column" => {
                if i + 1 < args.len() {
                    column = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --column".to_string(),
                    ));
                }
            }
            "--target-column" | "--target_column" => {
                if i + 1 < args.len() {
                    target_column = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --target-column".to_string(),
                    ));
                }
            }
            "--prompt" => {
                if i + 1 < args.len() {
                    prompt = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --prompt".to_string(),
                    ));
                }
            }
            "--model-provider" | "--model_provider" => {
                if i + 1 < args.len() {
                    model_provider = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --model-provider".to_string(),
                    ));
                }
            }
            "--model-id" | "--model_id" => {
                if i + 1 < args.len() {
                    model_id = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --model-id".to_string(),
                    ));
                }
            }
            "--base-url" | "--base_url" => {
                if i + 1 < args.len() {
                    base_url = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --base-url".to_string(),
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

    let src = source
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --source".to_string()))?;
    let dest = destination.ok_or_else(|| {
        MuscleError::MissingArg("Missing required argument --destination".to_string())
    })?;
    let col = column
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --column".to_string()))?;

    let mut helper_args = vec!["--source", src, "--destination", dest, "--column", col];
    if let Some(tc) = target_column {
        helper_args.extend(&["--target-column", tc]);
    }
    if let Some(p) = prompt {
        helper_args.extend(&["--prompt", p]);
    }
    if let Some(mp) = model_provider {
        helper_args.extend(&["--model-provider", mp]);
    }
    if let Some(mi) = model_id {
        helper_args.extend(&["--model-id", mi]);
    }
    if let Some(bu) = base_url {
        helper_args.extend(&["--base-url", bu]);
    }

    run_ai_helper("summarize", &helper_args)
}

pub fn handle_ai_extract(args: &[String]) -> Result<(), MuscleError> {
    let mut source = None;
    let mut destination = None;
    let mut column = None;
    let mut schema = None;
    let mut prompt = None;
    let mut model_provider = None;
    let mut model_id = None;
    let mut base_url = None;

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
            "--column" => {
                if i + 1 < args.len() {
                    column = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --column".to_string(),
                    ));
                }
            }
            "--schema" => {
                if i + 1 < args.len() {
                    schema = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --schema".to_string(),
                    ));
                }
            }
            "--prompt" => {
                if i + 1 < args.len() {
                    prompt = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --prompt".to_string(),
                    ));
                }
            }
            "--model-provider" | "--model_provider" => {
                if i + 1 < args.len() {
                    model_provider = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --model-provider".to_string(),
                    ));
                }
            }
            "--model-id" | "--model_id" => {
                if i + 1 < args.len() {
                    model_id = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --model-id".to_string(),
                    ));
                }
            }
            "--base-url" | "--base_url" => {
                if i + 1 < args.len() {
                    base_url = Some(&args[i + 1]);
                    i += 2;
                } else {
                    return Err(MuscleError::MissingArg(
                        "Missing value for --base-url".to_string(),
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

    let src = source
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --source".to_string()))?;
    let dest = destination.ok_or_else(|| {
        MuscleError::MissingArg("Missing required argument --destination".to_string())
    })?;
    let col = column
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --column".to_string()))?;
    let sch = schema
        .ok_or_else(|| MuscleError::MissingArg("Missing required argument --schema".to_string()))?;

    let mut helper_args = vec![
        "--source",
        src,
        "--destination",
        dest,
        "--column",
        col,
        "--schema",
        sch,
    ];
    if let Some(p) = prompt {
        helper_args.extend(&["--prompt", p]);
    }
    if let Some(mp) = model_provider {
        helper_args.extend(&["--model-provider", mp]);
    }
    if let Some(mi) = model_id {
        helper_args.extend(&["--model-id", mi]);
    }
    if let Some(bu) = base_url {
        helper_args.extend(&["--base-url", bu]);
    }

    run_ai_helper("extract", &helper_args)
}
