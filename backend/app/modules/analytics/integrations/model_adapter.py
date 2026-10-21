from app.modules.ml_models.models import MLModelDefinition, MLModelVersion


class ModelAdapter:
    def __init__(self, db): self.db = db

    def definition_for_version(self, version_id):
        version = self.db.get(MLModelVersion, version_id)
        return self.db.get(MLModelDefinition, version.model_definition_id) if version else None
