from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from app.modules.detection.models import BehavioralResult, DetectionBatch, DetectionInput, DetectionRecord, DetectionSettings, RiskAssessment
from app.modules.detection.repository import DetectionRepository
from app.modules.detection.risk.service import RiskService
from app.modules.detection.behavioral.service import BehavioralService
from app.modules.ml_models.models import MLTrainingRun
from app.modules.ml_models.registry.manager import ModelRegistryManager
from app.modules.ml_models.service import MLModelService
from app.modules.ml_models.storage.artifact_store import ModelArtifactStore
from app.modules.preprocessing.storage.artifact_store import ArtifactStore


class DetectionError(Exception):
    pass


class DetectionService:
    def __init__(self, db):
        self.db = db
        self.repo = DetectionRepository(db)
        self.risk_service = RiskService(db)
        self.behavioral_service = BehavioralService(db)

    def _record_detection_activity(self, detection, email, version, prediction, confidence, risk):
        from app.modules.audit_security_admin.audit.service import record_audit
        from app.modules.audit_security_admin.security_monitoring.event_processor import process_security_event

        risk_level = getattr(risk, "level", None) if risk else None
        label = getattr(email, "sender", None) or "Uploaded email"
        completed = detection.status == "completed"
        record_audit(self.db, action="detection.completed" if completed else "detection.failed", target_type="detection", target_id=detection.id, target_label=label, status="success" if completed else "failure", severity=risk_level if risk_level in {"critical", "high", "medium", "low"} else None, source="Detection", details={"prediction": prediction, "confidence": confidence, "risk_level": risk_level, "model_version_id": str(version.id)})
        if prediction == "bomb" or risk_level in {"critical", "high"}:
            process_security_event(self.db, {"event_type": "email_detection.risk", "title": "Bomb email detected" if prediction == "bomb" else "High risk email detected", "description": "A completed detection was classified as bombing or high risk.", "severity": "critical" if risk_level == "critical" else "high", "source": "Detection", "details": {"detection_id": str(detection.id), "prediction": prediction, "risk_level": risk_level, "model_version_id": str(version.id)}})

    @staticmethod
    def transform_feature_row(raw_features: dict[str, Any], preprocessing_run_id: UUID, feature_names: list[str]) -> tuple[list[str], list[float]]:
        names = list(feature_names or [])
        if not names:
            raise DetectionError("Registered model does not include its training feature order.")
        numeric = {k: float(v) for k, v in raw_features.items() if k != "F1"}
        store = ArtifactStore()
        imputer = json.loads(store.read_bytes(preprocessing_run_id, "imputer.json"))
        scaler = json.loads(store.read_bytes(preprocessing_run_id, "scaler.json"))
        imputer_values = imputer.get("feature_values", {})
        scaler_states = scaler.get("feature_states", {})
        scaled = []
        for name in names:
            if name in numeric:
                value = numeric[name]
            elif name in imputer_values:
                value = float(imputer_values[name])
            else:
                raise DetectionError(
                    f"Required model feature '{name}' is missing from the extracted email."
                )

            if not math.isfinite(value):
                raise DetectionError(
                    f"Extracted model feature '{name}' is not a finite number."
                )

            # The preprocessing scaler stores state only for selected
            # scaling_features. A feature absent from feature_states was
            # intentionally left unchanged in the training artifacts.
            state = scaler_states.get(name)
            strategy = state.get("strategy") if state else "none"
            if strategy == "standard":
                scale = state.get("scale")
                mean = state.get("mean")
                if scale is None or mean is None:
                    raise DetectionError(
                        f"Scaler state for feature '{name}' is incomplete."
                    )
                value = 0.0 if scale == 0 else (value - mean) / scale
            elif strategy == "minmax":
                minimum, maximum = state.get("minimum"), state.get("maximum")
                if minimum is None or maximum is None:
                    raise DetectionError(
                        f"Scaler state for feature '{name}' is incomplete."
                    )
                span = maximum - minimum
                value = 0.0 if span == 0 else (value - minimum) / span
            scaled.append(float(value))
        return names, scaled

    @staticmethod
    def _prediction_payload(model, raw_features: dict[str, Any], preprocessing_run_id: UUID, feature_names: list[str]):
        names = feature_names or list(getattr(model, "feature_names_in_", []))
        if not names:
            raise DetectionError("Registered model does not include its training feature order.")
        _, scaled = DetectionService.transform_feature_row(raw_features, preprocessing_run_id, names)
        vector = [scaled]
        prediction = int(model.predict(vector)[0])
        confidence = None
        try:
            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(vector)[0]
                confidence = float(max(probabilities))
        except (AttributeError, NotImplementedError):
            confidence = None
        return ("bomb" if prediction == 1 else "normal"), confidence

    def create(self, email_id: UUID | None, model_version_id: UUID | None, run_behavioral: bool, calculate_risk: bool, uploaded: tuple[str, bytes] | None = None, batch_id: UUID | None = None):
        email = feature_row = input_row = None
        if uploaded:
            from datetime import datetime, timezone
            from types import SimpleNamespace
            from email.utils import parsedate_to_datetime
            from app.modules.parsing.parser import EmailParser
            from app.modules.features.extractor import ParsedEmailInput, extract_features
            filename, payload = uploaded
            parsed = EmailParser().parse(payload)
            if not parsed.is_valid:
                raise DetectionError("Email could not be parsed: " + "; ".join(parsed.validation_errors))
            def first(key):
                for header, values in parsed.headers.items():
                    if header.lower() == key.lower() and values:
                        return values[0]
                return None
            received_at = None
            try:
                if parsed.date:
                    try:
                        received_at = datetime.fromisoformat(parsed.date)
                    except ValueError:
                        received_at = parsedate_to_datetime(parsed.date)
            except (TypeError, ValueError, OverflowError):
                pass
            received_at = received_at or datetime.now(timezone.utc)
            history_timestamps = self.repo.received_at_values()
            history_timestamps.append(received_at)
            extract = extract_features(ParsedEmailInput(sender=parsed.sender, subject=parsed.subject, message_id=parsed.message_id, received_at=received_at, auto_submitted=first("auto-submitted"), precedence=first("precedence"), list_id=first("list-id"), x_beenthere=first("x-beenthere"), x_anti_abuse=first("x-anti-abuse"), text_body=parsed.text_body or "", all_received_at=history_timestamps))
            if not extract.is_valid:
                raise DetectionError("Feature extraction failed: " + "; ".join(extract.errors))
            input_row = DetectionInput(batch_id=batch_id, filename=Path(filename).name, raw_content=payload.decode("utf-8", errors="replace"), sender=parsed.sender, subject=parsed.subject, feature_snapshot=extract.feature_vector)
            features = dict(extract.feature_vector)
            email = SimpleNamespace(sender=parsed.sender, received_at=received_at, collected_at=received_at)
        else:
            source = self.repo.email_input(email_id)
            if source is None:
                raise DetectionError("Email was not found or feature extraction has not completed.")
            email, feature_row = source
            if getattr(feature_row.status, "value", feature_row.status) not in {"extracted", "warning"}:
                raise DetectionError("Email features are not in a usable state.")
            if feature_row is not None:
                features = dict(feature_row.feature_vector or {})
        settings = self.repo.settings()
        default_version_id = model_version_id or settings.default_model_version_id
        selected = self.repo.get_version(default_version_id) if default_version_id else self.repo.active_version()
        if selected is None:
            raise DetectionError("No active model version is available. Register and activate a trained model first.")
        version, model_definition = selected
        if version.status != "active" or model_definition.status != "active":
            raise DetectionError("The selected model version is not active.")
        training_run = self.db.get(MLTrainingRun, version.training_run_id)
        if training_run is None or training_run.status != "completed":
            raise DetectionError("The model's successful training run could not be found.")
        store = ModelArtifactStore(os.getenv("ML_MODEL_ARTIFACT_DIR", "data/models"))
        manager = ModelRegistryManager(service=MLModelService(self.db), artifact_store=store)
        inference_error = None
        try:
            model = manager.load_model(version.id)
            if feature_row is not None:
                features = dict(feature_row.feature_vector or {})
            feature_names = (version.metadata_json or {}).get("feature_names", [])
            prediction, confidence = self._prediction_payload(model, features, training_run.preprocessing_run_id, feature_names)
        except Exception as exc:
            inference_error = str(exc)
            prediction, confidence = "unknown", None
        risk = None
        if calculate_risk:
            try:
                if inference_error:
                    raise DetectionError(inference_error)
                risk = self.risk_service.assess(prediction, confidence, features, settings)
            except Exception:
                risk = RiskAssessment(score=None, level="unavailable", factors=[], status="failed")
        behavioral = None
        if email is not None and run_behavioral and settings.enable_behavioral_analysis:
            try:
                behavioral = self.behavioral_service.analyze(email, self.repo.recent_features_for_sender(email.sender), True)
            except Exception as exc:
                behavioral = BehavioralResult(status="failed", summary=f"Behavioral analysis unavailable: {exc}", metrics={}, anomalies=[])
        if settings.store_detection_history:
            if input_row is not None:
                if not settings.save_feature_snapshots:
                    input_row.feature_snapshot = {}
                self.db.add(input_row)
                self.db.flush()
            detection = DetectionRecord(email_id=email.id if email_id else None, input_id=input_row.id if input_row else None, batch_id=batch_id, model_version_id=version.id, predicted_label=prediction, confidence=confidence, feature_snapshot=features if settings.save_feature_snapshots else {}, status="failed" if inference_error else "completed", error_message=f"Inference failed: {inference_error}" if inference_error else None)
            self.repo.insert(detection, risk, behavioral)
            if email_id:
                # Attach a persisted threat match to the detection created for
                # this canonical email; the matching subsystem owns match data.
                from sqlalchemy import update
                from app.modules.threat_intelligence.models import ThreatMatch
                self.db.execute(update(ThreatMatch).where(ThreatMatch.email_id == email_id, ThreatMatch.detection_id.is_(None)).values(detection_id=detection.id))
            self._record_detection_activity(detection, email, version, prediction, confidence, risk)
            return self.detail(detection.id)
        from datetime import datetime, timezone
        detection = DetectionRecord(id=uuid4(), email_id=email.id if email_id else None, input_id=None, batch_id=batch_id, model_version_id=version.id, predicted_label=prediction, confidence=confidence, feature_snapshot=features if settings.save_feature_snapshots else {}, status="failed" if inference_error else "completed", error_message=f"Inference failed: {inference_error}" if inference_error else None, created_at=datetime.now(timezone.utc))
        self._record_detection_activity(detection, email, version, prediction, confidence, risk)
        return self.serialize((detection, email if email_id else None, version, model_definition, risk, behavioral), input_row)

    def create_batch(self, items, model_version_id, run_behavioral, calculate_risk):
        batch = DetectionBatch(total_count=len(items), succeeded_count=0, failed_count=0)
        self.db.add(batch)
        self.db.flush()
        results = []
        for item in items:
            filename = item[0] if item[0] is not None else None
            email_id = item[1]
            uploaded = item[2]
            try:
                detection = self.create(email_id, model_version_id, run_behavioral, calculate_risk, uploaded, batch.id)
                completed = detection["status"] == "completed"
                results.append({"filename": filename, "email_id": email_id, "status": detection["status"], "detection": detection, "error": detection.get("error_message")})
                if completed:
                    batch.succeeded_count += 1
                else:
                    batch.failed_count += 1
            except DetectionError as exc:
                results.append({"filename": filename, "email_id": email_id, "status": "failed", "detection": None, "error": str(exc)})
                batch.failed_count += 1
        self.db.flush()
        return {"batch_id": batch.id, "total_count": batch.total_count, "succeeded_count": batch.succeeded_count, "failed_count": batch.failed_count, "items": results}

    def serialize(self, row, input_override=None):
        detection, email, version, model, risk, behavior = row
        input_row = input_override or (self.db.get(DetectionInput, detection.input_id) if detection.input_id else None)
        return {"id": detection.id, "email_id": email.id if email else None, "input_id": detection.input_id, "input_filename": input_row.filename if input_row else None, "model_version_id": version.id, "predicted_label": detection.predicted_label, "confidence": detection.confidence, "status": detection.status, "feature_snapshot": detection.feature_snapshot, "error_message": detection.error_message, "created_at": detection.created_at, "email_subject": email.subject if email else (input_row.subject if input_row else None), "sender": email.sender if email else (input_row.sender if input_row else None), "model_name": model.name, "version": version.version, "risk": ({"score": risk.score, "level": risk.level, "factors": risk.factors, "status": risk.status} if risk else None), "behavioral": ({"status": behavior.status, "summary": behavior.summary, "metrics": behavior.metrics, "anomalies": behavior.anomalies} if behavior else None)}

    def list(self, **filters):
        rows, total = self.repo.list(**filters)
        return [self.serialize(row) for row in rows], total

    def detail(self, detection_id: UUID):
        row = self.repo.detail(detection_id)
        if row is not None:
            return self.serialize(row)
        raise DetectionError("Detection record was not found.")

    def overview(self, period: str = "7d"):
        summary = self.repo.summary()
        recent_rows = self.repo.recent_detections(8)
        recent = [self.serialize(row) for row in recent_rows]
        # Bucket persisted detections by UTC date/hour; charts remain empty when no records exist.
        from datetime import datetime, timedelta, timezone
        days = {"24h": 1, "7d": 7, "30d": 30}.get(period, 7)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        rows = self.db.query(DetectionRecord).filter(DetectionRecord.created_at >= cutoff).order_by(DetectionRecord.created_at.asc()).all()
        buckets: dict[str, int] = {}
        for item in rows:
            key = item.created_at.strftime("%Y-%m-%d %H:00" if period == "24h" else "%Y-%m-%d")
            buckets[key] = buckets.get(key, 0) + 1
        return {**summary, "activity": [{"time": key, "count": value} for key, value in list(buckets.items())[-30:]], "recent": recent}

    def update_settings(self, values):
        if values["critical_risk_threshold"] <= values["high_risk_threshold"]:
            raise DetectionError("Critical threshold must be greater than high threshold.")
        row = self.repo.settings()
        version_id = values.get("default_model_version_id")
        if version_id is not None:
            selected = self.repo.get_version(version_id)
            if selected is None or selected[0].status != "active" or selected[1].status != "active":
                raise DetectionError("Default model version must be an active registered version.")
        for key, value in values.items():
            setattr(row, key, value)
        self.db.flush()
        return row
