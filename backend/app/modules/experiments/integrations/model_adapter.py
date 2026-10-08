from sqlalchemy import select

from app.modules.ml_models.models import MLModelDefinition


class ModelAdapter:
    def __init__(self, db): self.db = db

    def active_models(self):
        rows = self.db.scalars(select(MLModelDefinition).where(MLModelDefinition.status == "active").order_by(MLModelDefinition.name)).all()
        return [{"id": str(row.id), "name": row.name, "algorithm": row.algorithm, "hyperparameters": row.hyperparameters or {}} for row in rows]
