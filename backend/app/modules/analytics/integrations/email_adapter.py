from app.modules.detection.models import DetectionInput
from app.modules.emails.models import Email


class EmailAdapter:
    """Resolve email labels/headers for analytics without duplicating email rows."""
    def __init__(self, db): self.db = db

    def display_data(self, detection):
        if detection.email_id:
            row = self.db.get(Email, detection.email_id)
            return {"email_id": str(row.id), "sender": row.sender, "subject": row.subject} if row else {}
        row = self.db.get(DetectionInput, detection.input_id) if detection.input_id else None
        return {"email_id": None, "sender": row.sender, "subject": row.subject} if row else {}
