class ExperimentError(Exception):
    """Base domain error."""


class ExperimentNotFound(ExperimentError): pass
class ExperimentConflict(ExperimentError): pass
class ExperimentValidationError(ExperimentError, ValueError): pass
