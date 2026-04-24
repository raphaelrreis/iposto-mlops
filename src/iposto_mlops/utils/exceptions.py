class DataQualityError(RuntimeError):
    """Raised when a dataset fails mandatory quality gates."""


class PipelineConfigurationError(RuntimeError):
    """Raised when runtime or model configuration is invalid."""
