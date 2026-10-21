import pytest

from app.modules.experiments.errors import ExperimentValidationError
from app.modules.experiments.validators import validate_split_counts, validate_training_config


def test_training_config_applies_safe_defaults():
    assert validate_training_config({}) == {
        "random_state": 42,
        "hyperparameters": {},
    }


def test_training_config_preserves_supported_values():
    assert validate_training_config({
        "random_state": 7,
        "hyperparameters": {"kernel": "rbf", "C": 1.0},
    }) == {
        "random_state": 7,
        "hyperparameters": {"kernel": "rbf", "C": 1.0},
    }


@pytest.mark.parametrize(
    "value",
    [None, [], {"feature_names": ["F1"]}, {"random_state": True}, {"hyperparameters": []}],
)
def test_training_config_rejects_invalid_or_unsupported_values(value):
    with pytest.raises(ExperimentValidationError):
        validate_training_config(value)


def test_testing_evaluation_requires_a_testing_split():
    validate_split_counts(8, 2, 1, "testing")

    with pytest.raises(ExperimentValidationError, match="testing split"):
        validate_split_counts(8, 2, 0, "testing")


def test_validation_evaluation_requires_a_validation_split():
    with pytest.raises(ExperimentValidationError, match="validation split"):
        validate_split_counts(8, 0, 2, "validation")
