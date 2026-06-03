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
        }
    }
}
