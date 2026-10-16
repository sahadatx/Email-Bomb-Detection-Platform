from datetime import datetime
from uuid import UUID

from sqlalchemy import MetaData, String, Table, func, inspect, or_, select
from sqlalchemy.orm import Session

JOB_TABLES = {"email_collection_jobs": "email_ingestion", "preprocessing_runs": "preprocessing", "ml_training_runs": "training", "ml_evaluation_runs": "evaluation", "investigation_reports": "report_generation"}


def _job_tables(db: Session, job_type: str | None = None):
    connection = db.connection()
    inspector = inspect(connection)
    present = set(inspector.get_table_names())
    for table_name, kind in JOB_TABLES.items():
        if table_name not in present or (job_type and job_type != kind):
            continue
        yield kind, Table(table_name, MetaData(), autoload_with=connection)


def summarize_jobs(db: Session):
    counts = {"running_jobs": 0, "failed_jobs": 0, "queued_jobs": 0, "total_jobs": 0}
    for _, table in _job_tables(db):
        state = table.c.get("status")
        if state is None:
            state = table.c.get("state")
        if state is None:
            continue
        for value, count in db.execute(select(state, func.count()).group_by(state)):
            normalized = str(value or "unknown").lower()
            counts["total_jobs"] += int(count)
            if normalized == "running":
                counts["running_jobs"] += int(count)
            if normalized == "failed":
                counts["failed_jobs"] += int(count)
            if normalized in {"queued", "pending"}:
                counts["queued_jobs"] += int(count)
    return counts


def list_jobs(db: Session, page: int = 1, page_size: int = 30, status: str | None = None, job_type: str | None = None, search: str | None = None):
    rows = []
    total = 0
    scan_limit = page * page_size
    for kind, table in _job_tables(db, job_type):
        columns = set(table.c.keys())
        sort_column = next((table.c[name] for name in ("created_at", "started_at", "updated_at") if name in columns), table.c[next(iter(columns))])
        state_column = table.c.get("status")
        if state_column is None:
            state_column = table.c.get("state")
        query = select(table)
        if status and state_column is not None:
            query = query.where(func.lower(state_column) == status.lower())
        if search and search.strip():
            term = f"%{search.strip()}%"
            searchable = [table.c[name] for name in ("id", "dataset_version_id", "model_definition_id", "model_version_id", "preprocessing_run_id", "detection_id", "report_id", "email_id", "mailbox", "source") if name in columns]
            if searchable:
                query = query.where(or_(*(func.cast(column, String).ilike(term) for column in searchable)))
        table_total = int(db.scalar(select(func.count()).select_from(query.subquery())) or 0)
        total += table_total
        for row in db.execute(query.order_by(sort_column.desc()).limit(scan_limit)).mappings():
            item = dict(row)
            status_value = str(item.get("status") or item.get("state") or "unknown").lower()
            created = item.get("started_at") or item.get("created_at")
            completed = item.get("completed_at") or item.get("finished_at")
            progress = item.get("progress_percent", item.get("progress"))
            if kind == "email_ingestion" and item.get("requested_count"):
                progress = min(100, round((item.get("fetched_count", 0) / item["requested_count"]) * 100))
            related = next((item.get(name) for name in ("dataset_version_id", "model_definition_id", "model_version_id", "detection_id", "report_id") if item.get(name)), None)
            if not item.get("duration_ms") and isinstance(created, datetime) and isinstance(completed, datetime):
                duration_ms = max(0, round((completed - created).total_seconds() * 1000))
            else:
                duration_ms = item.get("duration_ms")
            rows.append({"id": str(item.get("id") or item.get("run_id") or ""), "job_type": kind, "status": status_value, "progress": progress, "related_resource": str(related) if related else None, "error_summary": "Job failed; consult protected server logs." if status_value == "failed" else None, "started_at": created.isoformat() if isinstance(created, datetime) else None, "completed_at": completed.isoformat() if isinstance(completed, datetime) else None, "duration_ms": duration_ms, "retry_supported": False})
    rows.sort(key=lambda item: item["started_at"] or "", reverse=True)
    summary = summarize_jobs(db)
    return {"items": rows[(page - 1) * page_size:page * page_size], "total": total, "page": page, "page_size": page_size, "total_pages": max(1, (total + page_size - 1) // page_size), "summary": summary}


def job_detail(db: Session, job_id: str):
    connection = db.connection()
    present = set(inspect(connection).get_table_names())
    for table_name, kind in JOB_TABLES.items():
        if table_name not in present:
            continue
        table = Table(table_name, MetaData(), autoload_with=connection)
        if "id" not in table.c:
            continue
        try:
            identifier = UUID(job_id) if table.c.id.type.python_type is UUID else job_id
        except (ValueError, AttributeError):
            continue
        row = db.execute(select(table).where(table.c.id == identifier)).mappings().first()
        if row:
            item = dict(row)
            safe_fields = {"id", "status", "state", "progress", "progress_percent", "created_at", "started_at", "completed_at", "finished_at", "updated_at", "duration_ms", "dataset_version_id", "model_definition_id", "model_version_id", "preprocessing_run_id", "detection_id", "report_id", "email_id", "attempt", "retry_count", "requested_count", "fetched_count", "ingested_count", "duplicate_count", "failed_count", "input_sample_count", "output_sample_count", "training_sample_count", "validation_sample_count", "testing_sample_count", "sample_count", "feature_count", "evaluation_split", "source"}
            safe = {key: value for key, value in item.items() if key in safe_fields}
            if str(item.get("status") or "").lower() == "failed":
                safe["error_summary"] = "Job failed; consult protected server logs."
            return {"id": str(item["id"]), "job_type": kind, "status": str(item.get("status") or item.get("state") or "unknown").lower(), "fields": {key: (value.isoformat() if isinstance(value, datetime) else value) for key, value in safe.items()}}
    return None
