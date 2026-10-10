import re
from sqlalchemy import or_, select

from app.modules.emails.models import Email, EmailStatus


class EmailAdapter:
    def __init__(self, db):
        self.db = db

    def candidates(self, normalized_value, kind):
        escaped = normalized_value.replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        return self.db.scalars(
            select(Email)
            .where(
                Email.status == EmailStatus.INGESTED,
                or_(
                    Email.sender.ilike(pattern, escape="\\"),
                    Email.recipients.ilike(pattern, escape="\\"),
                    Email.subject.ilike(pattern, escape="\\"),
                    Email.raw_content.ilike(pattern, escape="\\"),
                ),
            )
            .order_by(Email.collected_at.desc())
        ).yield_per(500)

    @staticmethod
    def matched_field(email, value, kind):
        fields = {
            "sender": email.sender or "",
            "recipients": email.recipients or "",
            "subject": email.subject or "",
            "content": email.raw_content or "",
        }
        if kind in {"domain", "ip"}:
            pattern = re.compile(
                rf"(?<![A-Za-z0-9_.-]){re.escape(value)}(?![A-Za-z0-9_.-])", re.I
            )
            return next(
                (name for name, text in fields.items() if pattern.search(text)), None
            )
        return next(
            (
                name
                for name, text in fields.items()
                if value.casefold() in text.casefold()
            ),
            None,
        )
