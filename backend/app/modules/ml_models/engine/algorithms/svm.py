from __future__ import annotations

from app.modules.ml_models.engine.algorithms.weighted_svm import WeightedSVMEngine
from app.modules.ml_models.engine.base import TrainingConfig


class SVMEngine(WeightedSVMEngine):
    """Standard SVM engine; unlike Weighted SVM it defaults to no class weights."""

    @property
    def algorithm_name(self) -> str:
        return "svm"

    def train(self, dataset, config: TrainingConfig):
        params = dict(config.hyperparameters)
        params.setdefault("class_weight", None)
        return super().train(
            dataset,
            TrainingConfig(hyperparameters=params, random_state=config.random_state),
        )
