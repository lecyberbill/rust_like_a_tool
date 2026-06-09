// [WFGY] Zone: SAFE | λ: 0.1 | Action: Extracted shared MuscleError enum

#[derive(Debug)]
pub enum MuscleError {
    Generic(String),
    SourceNotFound(String),
    PermissionDenied(String),
    DestDirCreation(String),
    CrossVolumeFail(String),
    TrashCreation(String),
    NetworkError(String),
    MissingArg(String),
    InvalidArg(String),
    ValidationFailed(String),
    IoError(String),
    ParseError(String),
    UnsupportedPrimitive(String),
    Timeout(String),
}

impl MuscleError {
    pub fn exit_code(&self) -> i32 {
        match self {
            MuscleError::Generic(_) => 1,
            MuscleError::SourceNotFound(_) => 2,
            MuscleError::PermissionDenied(_) => 3,
            MuscleError::DestDirCreation(_) => 4,
            MuscleError::CrossVolumeFail(_) => 5,
            MuscleError::TrashCreation(_) => 6,
            MuscleError::NetworkError(_) => 7,
            MuscleError::MissingArg(_) => 8,
            MuscleError::InvalidArg(_) => 9,
            MuscleError::ValidationFailed(_) => 10,
            MuscleError::IoError(_) => 11,
            MuscleError::ParseError(_) => 12,
            MuscleError::UnsupportedPrimitive(_) => 13,
            MuscleError::Timeout(_) => 14,
        }
    }

    pub fn message(&self) -> String {
        match self {
            MuscleError::Generic(m) => format!("ERR_GENERIC: {}", m),
            MuscleError::SourceNotFound(m) => format!("ERR_SOURCE_NOT_FOUND: {}", m),
            MuscleError::PermissionDenied(m) => format!("ERR_PERMISSION_DENIED: {}", m),
            MuscleError::DestDirCreation(m) => format!("ERR_DEST_DIR_CREATION: {}", m),
            MuscleError::CrossVolumeFail(m) => format!("ERR_CROSS_VOLUME_FAIL: {}", m),
            MuscleError::TrashCreation(m) => format!("ERR_TRASH_CREATION: {}", m),
            MuscleError::NetworkError(m) => format!("ERR_NETWORK_ERROR: {}", m),
            MuscleError::MissingArg(m) => format!("ERR_MISSING_ARG: {}", m),
            MuscleError::InvalidArg(m) => format!("ERR_INVALID_ARG: {}", m),
            MuscleError::ValidationFailed(m) => format!("ERR_VALIDATION_FAILED: {}", m),
            MuscleError::IoError(m) => format!("ERR_IO: {}", m),
            MuscleError::ParseError(m) => format!("ERR_PARSE: {}", m),
            MuscleError::UnsupportedPrimitive(m) => format!("ERR_UNSUPPORTED_PRIMITIVE: {}", m),
            MuscleError::Timeout(m) => format!("ERR_TIMEOUT: {}", m),
        }
    }
}
