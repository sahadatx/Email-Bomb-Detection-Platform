from .errors import ExperimentValidationError


def validate_training_config(value):
    if not isinstance(value, dict): raise ExperimentValidationError("Training configuration must be a JSON object.")
    if set(value) - {"random_state", "hyperparameters"}: raise ExperimentValidationError("Only random_state and hyperparameters are configurable.")
    random_state = value.get("random_state", 42)
    if isinstance(random_state, bool) or not isinstance(random_state, int) or random_state < 0: raise ExperimentValidationError("random_state must be a non-negative integer.")
    hyperparameters = value.get("hyperparameters", {})
    if not isinstance(hyperparameters, dict): raise ExperimentValidationError("hyperparameters must be a JSON object.")
    return {"random_state": random_state, "hyperparameters": hyperparameters}


def validate_split_counts(training_count, validation_count, testing_count, evaluation_split):
    if evaluation_split not in {"validation", "testing"}:
        raise ExperimentValidationError("Evaluation split must be validation or testing.")
    evaluation_count = validation_count if evaluation_split == "validation" else testing_count
    if training_count < 1:
        raise ExperimentValidationError("Preprocessing run needs a non-empty training split.")
    if evaluation_count < 1:
        raise ExperimentValidationError(
            f"Preprocessing run needs a non-empty {evaluation_split} split."
        )
